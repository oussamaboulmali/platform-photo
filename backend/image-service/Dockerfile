FROM python:3.13-slim

WORKDIR /app

# Install system dependencies including libvips
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    libvips-dev \
    libvips-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create storage directory
RUN mkdir -p /var/www/agency_storage

EXPOSE 8002

CMD ["python", "manage.py", "runserver", "0.0.0.0:8002"]
