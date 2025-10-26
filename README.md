# Agency Platform - Complete Two-App System

A comprehensive image agency platform with microservices architecture, featuring internal dashboard and public storefront.

## 🎯 Overview

This platform provides a complete solution for image agencies with two distinct applications:

### Dashboard (Internal Management)
- **Frontend**: React 18 with Vite, TailwindCSS
- **Backend**: Django 5.1.3 microservices
- **Users**: Photographers, Infographistes, Validators, Admins
- **Features**:
  - Image upload with drag-and-drop (single & bulk ZIP)
  - Image validation workflow (approve/reject)
  - Metadata management (multilingual)
  - Category/subcategory, topics, places management
  - Bloc and ad slot management
  - Subscription plan management
  - Manual top-up approval
  - User management with RBAC
  - 2FA authentication

### Public Storefront
- **Frontend**: Next.js 14 with SSR, TailwindCSS
- **Backend**: Django microservices
- **Users**: Public customers
- **Features**:
  - Browse and search images (full-text + filters)
  - Watermarked image previews
  - Multiple license types (Standard, Extended, Exclusive)
  - Wallet system (prepaid account)
  - Subscription plans (1/3/6 months)
  - Secure download with time-limited tokens
  - Order history and account management

## 🏗️ Architecture

### Microservices Backend

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL 17                             │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────┬──────────────┬──────────────┬────────────────┐
│ Auth Service│ Image Service│ Order Service│ Admin Service  │
│  (port 8001)│  (port 8002) │  (port 8003) │  (port 8004)   │
│             │              │              │                │
│ • Users     │ • Images     │ • Wallets    │ • Blocs        │
│ • 2FA       │ • Categories │ • Subscript. │ • Ad Slots     │
│ • RBAC      │ • Topics     │ • Orders     │                │
│ • Audit     │ • Places     │ • Payments   │                │
└─────────────┴──────────────┴──────────────┴────────────────┘
                            ↕
                   ┌────────────────┐
                   │ Redis + Celery │
                   │ (Image Process)│
                   └────────────────┘
```

### Frontend Applications

```
Dashboard                          Public Site
┌──────────────────┐              ┌──────────────────┐
│  React Frontend  │              │ Next.js Frontend │
│   (port 3000)    │              │   (port 3001)    │
└────────┬─────────┘              └────────┬─────────┘
         ↓                                  ↓
┌──────────────────┐              ┌──────────────────┐
│Dashboard Gateway │              │ Public Gateway   │
│   (port 8010)    │              │   (port 8020)    │
└──────────────────┘              └──────────────────┘
         ↓                                  ↓
         └──────────────────┬───────────────┘
                            ↓
                  Backend Microservices
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB RAM minimum
- 50GB disk space

### Installation

```bash
# 1. Clone repository
cd /workspace

# 2. Configure environment
cp .env.example .env
# Edit .env and set:
#   - DJANGO_SECRET_KEY
#   - DB_PASSWORD
#   - STORAGE_ROOT

# 3. Create storage directory
sudo mkdir -p /var/www/agency_storage
sudo chmod 777 /var/www/agency_storage

# 4. Start all services
docker-compose up -d

# 5. Run migrations
docker-compose exec auth-service python manage.py migrate
docker-compose exec image-service python manage.py migrate
docker-compose exec order-service python manage.py migrate
docker-compose exec admin-service python manage.py migrate

# 6. Seed initial data
python3 seed_data.py
```

### Access Applications

- **Dashboard**: http://localhost:3000
  - Admin: `admin@agency.local` / `admin123`
  - Validator: `validator@agency.local` / `validator123`
  - Photographer: `photographer@agency.local` / `photo123`
  - Infographiste: `infographiste@agency.local` / `design123`

- **Public Site**: http://localhost:3001
  - Customer: `customer@agency.local` / `customer123`

## 📁 Project Structure

```
/workspace/
├── backend/
│   ├── auth-service/           # Authentication & user management
│   ├── image-service/          # Image management & processing
│   ├── order-service/          # Orders, wallets, subscriptions
│   └── admin-service/          # Blocs & ads management
├── dashboard/
│   ├── frontend/               # React dashboard
│   └── backend/                # Dashboard API gateway (Node.js)
├── public/
│   ├── frontend/               # Next.js public site
│   └── backend/                # Public API gateway (Node.js)
├── docker-compose.yml          # All services orchestration
├── .env.example                # Environment variables template
├── seed_data.py                # Initial data seeding script
├── DEPLOYMENT.md               # Comprehensive deployment guide
└── README.md                   # This file
```

## 🔑 Key Features

### Authentication & Security
- JWT-based authentication
- 2FA with TOTP (QR code setup)
- Role-based access control (RBAC)
- Argon2 password hashing
- Audit logging for all actions
- Rate limiting on API endpoints

### Image Management
- Local filesystem storage (structured by year/month/user)
- Automatic derivative generation:
  - Thumbnail (200px)
  - Preview (1024px, watermarked)
  - Medium (2048px)
  - Original (high-res)
- MD5 checksum for duplicate detection
- Celery background processing with libvips/Pillow
- Full-text search (PostgreSQL)
- Multilingual metadata (EN/FR/AR)

### Taxonomy & Organization
- Hierarchical categories/subcategories
- Topics: event, document, top_shot, custom
- Places: cities, venues, countries (with coordinates)
- Image types: photo, infographie

### Workflow
1. **Upload** → Photographer/Infographiste uploads
2. **Process** → Celery creates derivatives
3. **Submit** → User submits for review
4. **Review** → Validator approves/rejects
5. **Publish** → Appears in public search
6. **Purchase** → Customer buys via wallet/subscription
7. **Download** → Time-limited download token

### Payment System
- Prepaid wallet (DZD currency)
- Manual top-up approval by admin
- Subscription plans: 1/3/6 months
- License types: Standard, Extended, Exclusive
- **Payment module**: Developed but disabled
  - Supports: Eldahabia, CIB, Algérie Poste
  - Webhook endpoints ready
  - Enable with `PAYMENT_MODULE_ENABLED=True`

### Content Management (Admin)
- Create/manage blocs for homepage
- Configure ad slots (header, sidebar, etc.)
- Schedule visibility (start/end dates)
- Assign content sources (manual, category, topic)
- Page placement configuration

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 5.1.3
- **API**: Django REST Framework 3.15.2
- **Database**: PostgreSQL 17
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery 5.4.0
- **Image Processing**: Pillow 10.4.0, pyvips 2.2.3
- **Authentication**: JWT (djangorestframework-simplejwt)

### Frontend
- **Dashboard**: React 18, Vite, TailwindCSS 3
- **Public**: Next.js 14, TailwindCSS 3
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Forms**: React Hook Form
- **UI Icons**: Heroicons

### DevOps
- **Containerization**: Docker, Docker Compose
- **Gateway**: Node.js/Express (API gateways)
- **Reverse Proxy**: Nginx (production)
- **SSL**: Let's Encrypt (production)

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register
- `POST /api/auth/logout` - Logout
- `POST /api/auth/2fa/setup` - Enable 2FA
- `POST /api/auth/2fa/verify` - Verify 2FA code

### Images (Dashboard)
- `GET /api/images` - List images
- `POST /api/images/upload` - Upload image
- `PUT /api/images/{id}/metadata` - Update metadata
- `POST /api/images/{id}/submit` - Submit for review

### Review (Validator)
- `GET /api/reviews/queue` - Get review queue
- `POST /api/reviews/{id}/approve` - Approve image
- `POST /api/reviews/{id}/reject` - Reject image

### Public Search
- `GET /api/images/search` - Search images
- `GET /api/images/{id}` - Get image details

### Orders (Customer)
- `POST /api/order` - Create order
- `GET /api/orders` - List orders
- `GET /api/download/{token}` - Download image

### Wallet
- `GET /api/wallet` - Get wallet balance
- `POST /api/topup` - Request top-up
- `GET /api/wallet/transactions` - Transaction history

### Subscriptions
- `GET /api/plans` - List subscription plans
- `POST /api/subscribe` - Subscribe to plan
- `GET /api/subscriptions` - My subscriptions

## 📖 Documentation

- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Documentation**: 
  - Auth: http://localhost:8001/swagger/
  - Images: http://localhost:8002/swagger/
  - Orders: http://localhost:8003/swagger/
  - Admin: http://localhost:8004/swagger/

## 🔒 Security Features

- HTTPS enforced (production)
- JWT token authentication
- 2FA with TOTP
- Role-based access control
- Password hashing with Argon2
- Rate limiting
- Audit logging
- CORS configuration
- SQL injection protection (ORM)
- XSS protection (Django templates)

## 📈 Scaling & Performance

- Microservices architecture (horizontal scaling)
- Celery workers (scale independently)
- PostgreSQL connection pooling
- Redis caching
- CDN-ready (watermarked previews)
- Efficient image processing with libvips
- Database indexing on critical fields
- Full-text search optimization

## 🐛 Troubleshooting

### Services not starting
```bash
docker-compose logs -f
docker-compose restart <service-name>
```

### Database issues
```bash
docker-compose exec postgres psql -U agency_user -d agency_platform
```

### Celery not processing
```bash
docker-compose logs celery-worker
docker-compose restart celery-worker
```

### Storage permissions
```bash
sudo chown -R 1000:1000 /var/www/agency_storage
```

## 📝 Testing

### Run backend tests
```bash
docker-compose exec auth-service python manage.py test
docker-compose exec image-service python manage.py test
```

### End-to-end test flow
1. Login as photographer
2. Upload image
3. Add metadata and submit
4. Login as validator
5. Approve image
6. Login as customer (public site)
7. Search and find image
8. Purchase with wallet
9. Download image

## 🚧 Roadmap & Future Enhancements

- [ ] Elasticsearch integration for advanced search
- [ ] ML auto-tagging (when ML modules added)
- [ ] Mobile apps (React Native)
- [ ] Advanced analytics dashboard
- [ ] Bulk operations UI
- [ ] API rate limiting per user
- [ ] WebSocket notifications
- [ ] Advanced image filters (face detection, etc.)

## 📄 License

Proprietary - All rights reserved

## 👥 Support

For deployment assistance or technical support, refer to [DEPLOYMENT.md](DEPLOYMENT.md) or contact your system administrator.

---

**Built with ❤️ using Django, React, and Next.js**
