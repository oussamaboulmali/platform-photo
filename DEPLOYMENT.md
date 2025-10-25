# Agency Platform - Deployment Guide

## System Overview

This is a comprehensive two-app platform built with microservices architecture:

- **Dashboard (Internal)**: React frontend + Django backend microservices + PostgreSQL 17
  - For photographers, infographistes, validators, and admins
  - Image upload, validation workflows, bloc/ad management, subscriptions
  
- **Public Storefront**: Next.js frontend + Django backend microservices + PostgreSQL 17
  - Public browsing, search, watermarked previews
  - Purchase/subscription flows, download center

**Backend Microservices:**
- Auth Service (port 8001) - Authentication, users, 2FA, RBAC
- Image Service (port 8002) - Image management, categories, topics, places
- Order Service (port 8003) - Wallets, subscriptions, orders, payments
- Admin Service (port 8004) - Blocs and ads management

**Frontends:**
- Dashboard Backend Gateway (port 8010) - API gateway for dashboard
- Dashboard Frontend (port 3000) - React SPA
- Public Backend Gateway (port 8020) - API gateway for public site
- Public Frontend (port 3001) - Next.js SSR app

**Infrastructure:**
- PostgreSQL 17
- Redis (for Celery)
- Celery workers (image processing)

## Prerequisites

- Docker & Docker Compose (v2.0+)
- 8GB RAM minimum (16GB recommended)
- 50GB disk space minimum for images
- Linux/Ubuntu server (or compatible)

## Quick Start (Development)

### 1. Clone and Configure

```bash
cd /workspace
cp .env.example .env
```

### 2. Edit .env file

```bash
nano .env
```

Change these critical values:
- `DJANGO_SECRET_KEY` - Generate a random secret key
- `DB_PASSWORD` - Set a strong database password
- `DJANGO_DEBUG=False` in production
- `STORAGE_ROOT` - Path where images will be stored (default: /var/www/agency_storage)

### 3. Create Storage Directory

```bash
sudo mkdir -p /var/www/agency_storage
sudo chmod 777 /var/www/agency_storage  # Adjust permissions as needed
sudo mkdir -p /var/www/agency_storage/archive
```

### 4. Start All Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL
- Redis
- 4 Backend microservices
- 2 Celery workers
- 2 Gateway services
- 2 Frontend services

### 5. Run Database Migrations

```bash
# Auth service
docker-compose exec auth-service python manage.py migrate

# Image service
docker-compose exec image-service python manage.py migrate

# Order service
docker-compose exec order-service python manage.py migrate

# Admin service
docker-compose exec admin-service python manage.py migrate
```

### 6. Create Superuser (Admin)

```bash
docker-compose exec auth-service python manage.py createsuperuser
```

### 7. Seed Initial Data

```bash
python3 seed_data.py
```

This creates:
- Default users (admin, validator, photographer, infographiste, customer)
- Categories, topics, places
- Subscription plans
- Initial blocs

### 8. Access the Applications

- **Dashboard**: http://localhost:3000
  - Login: admin@agency.local / admin123
  
- **Public Site**: http://localhost:3001
  - Create account or use: customer@agency.local / customer123

- **Django Admin (Auth)**: http://localhost:8001/admin/
- **Django Admin (Images)**: http://localhost:8002/admin/
- **Django Admin (Orders)**: http://localhost:8003/admin/
- **Django Admin (Admin)**: http://localhost:8004/admin/

## Production Deployment

### 1. Server Requirements

- Ubuntu 22.04 LTS or similar
- 4+ CPU cores
- 16GB+ RAM
- 500GB+ SSD for images
- HTTPS/SSL certificate

### 2. Production Environment Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Clone repository
git clone <your-repo> /opt/agency-platform
cd /opt/agency-platform
```

### 3. Production Configuration

Create production `.env`:

```bash
DJANGO_SECRET_KEY=<generate-strong-random-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_HOST=postgres
DB_PORT=5432
DB_NAME=agency_platform
DB_USER=agency_user
DB_PASSWORD=<strong-production-password>

REDIS_HOST=redis
REDIS_PORT=6379

STORAGE_ROOT=/var/www/agency_storage
WATERMARK_TEXT="© Your Agency Name"

JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

PAYMENT_MODULE_ENABLED=False
```

### 4. Storage Setup

```bash
sudo mkdir -p /var/www/agency_storage
sudo chown -R 1000:1000 /var/www/agency_storage
sudo chmod 755 /var/www/agency_storage
```

### 5. SSL/HTTPS Setup

Use nginx as reverse proxy with Let's Encrypt:

```bash
sudo apt install nginx certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Nginx configuration (`/etc/nginx/sites-available/agency`):

```nginx
upstream dashboard_frontend {
    server localhost:3000;
}

upstream public_frontend {
    server localhost:3001;
}

upstream dashboard_api {
    server localhost:8010;
}

upstream public_api {
    server localhost:8020;
}

# Dashboard
server {
    listen 443 ssl http2;
    server_name dashboard.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/dashboard.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://dashboard_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://dashboard_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Public Site
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://public_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://public_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Serve media files
    location /media/ {
        alias /var/www/agency_storage/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 6. Start Production

```bash
docker-compose -f docker-compose.yml up -d
```

### 7. Backup Strategy

#### Database Backup

Create daily backup script (`/opt/agency-platform/backup.sh`):

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/agency"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker-compose exec -T postgres pg_dump -U agency_user agency_platform > $BACKUP_DIR/db_$DATE.sql

# Backup storage (incremental)
rsync -av --link-dest=$BACKUP_DIR/latest /var/www/agency_storage/ $BACKUP_DIR/storage_$DATE/
ln -nsf $BACKUP_DIR/storage_$DATE $BACKUP_DIR/latest

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete
find $BACKUP_DIR -type d -name "storage_*" -mtime +7 -exec rm -rf {} +

echo "Backup completed: $DATE"
```

Add to crontab:
```bash
sudo crontab -e
# Add:
0 2 * * * /opt/agency-platform/backup.sh
```

## Monitoring & Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f auth-service
docker-compose logs -f celery-worker
```

### Health Checks

```bash
# Auth Service
curl http://localhost:8001/health

# Image Service
curl http://localhost:8002/health

# Dashboard Gateway
curl http://localhost:8010/health

# Public Gateway
curl http://localhost:8020/health
```

## Troubleshooting

### Services won't start

```bash
docker-compose down
docker-compose up -d
docker-compose logs -f
```

### Database connection issues

```bash
docker-compose exec postgres psql -U agency_user -d agency_platform
```

### Celery workers not processing

```bash
docker-compose logs celery-worker
docker-compose restart celery-worker
```

### Storage permission issues

```bash
sudo chown -R 1000:1000 /var/www/agency_storage
sudo chmod -R 755 /var/www/agency_storage
```

## Scaling

### Horizontal Scaling

To handle more load:

1. **Use NFS for shared storage** (if multiple app servers)
2. **Scale workers**:
   ```bash
   docker-compose up -d --scale celery-worker=4
   ```
3. **Load balance gateways** behind nginx
4. **Use PostgreSQL replication** for read replicas

### Storage Planning

- Average photo: 5-10 MB
- 1000 images = ~7.5 GB
- Budget 3x for derivatives (thumbnail, preview, medium)
- Plan for 1TB storage per 40,000 images

## Payment Module Activation

The payment module is developed but disabled. To enable:

1. Set in `.env`:
   ```
   PAYMENT_MODULE_ENABLED=True
   ```

2. Configure payment provider credentials (Eldahabia, CIB, Algérie Poste)

3. Test in sandbox mode first

4. Update webhook URLs in payment provider dashboard

## Support & Maintenance

### Regular Maintenance

- Weekly: Check disk space, review logs
- Monthly: Update dependencies, review security patches
- Quarterly: Full backup restore test

### Updates

```bash
cd /opt/agency-platform
git pull
docker-compose build
docker-compose down
docker-compose up -d
```

## API Documentation

- Auth Service: http://localhost:8001/swagger/
- Image Service: http://localhost:8002/swagger/
- Order Service: http://localhost:8003/swagger/
- Admin Service: http://localhost:8004/swagger/

## Default Credentials

**After deployment, change all default passwords!**

- Admin: admin@agency.local / admin123
- Validator: validator@agency.local / validator123
- Photographer: photographer@agency.local / photo123
- Infographiste: infographiste@agency.local / design123
- Customer: customer@agency.local / customer123

## Security Checklist

- [ ] Change all default passwords
- [ ] Set strong DJANGO_SECRET_KEY
- [ ] Set DJANGO_DEBUG=False in production
- [ ] Configure firewall (ufw/iptables)
- [ ] Enable HTTPS/SSL
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Rate limiting configured
- [ ] Database password rotation policy

## License

Proprietary - All rights reserved
