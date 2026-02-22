# 🐳 Artin Smart Trade - Docker Configuration Guide

> **Complete Docker setup for Artin Smart Trade platform**

## 📋 Table of Contents

- [🌟 Overview](#-overview)
- [🏗️ Architecture](#️-architecture)
- [📦 Dockerfiles](#-dockerfiles)
- [🐳 Docker Compose](#-docker-compose)
- [🔧 Configuration](#-configuration)
- [🚀 Deployment](#-deployment)
- [🔍 Troubleshooting](#-troubleshooting)

## 🌟 Overview

This guide covers the complete Docker setup for Artin Smart Trade, including development, staging, and production configurations.

### 🐳 Docker Services

- **Frontend**: Next.js application
- **Backend**: FastAPI application
- **Database**: PostgreSQL with RLS
- **Cache**: Redis
- **Proxy**: Nginx
- **Background**: Celery workers
- **Monitoring**: Prometheus + Grafana

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx                                │
│                   (Load Balancer)                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│Frontend │  │Backend  │  │Backend  │
│(Next.js)│  │(FastAPI)│  │(Celery) │
└─────────┘  └─────────┘  └─────────┘
    │             │             │
    └─────────────┼─────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│PostgreSQL│  │  Redis  │  │Prometheus│
│(Database)│  │ (Cache) │  │(Metrics) │
└─────────┘  └─────────┘  └─────────┘
```

## 📦 Dockerfiles

### 🖥️ Backend Dockerfile

Create `backend/Dockerfile.prod`:

```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Copy Python dependencies
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs uploads

# Change ownership
RUN chown -R app:app /app

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 🌐 Frontend Dockerfile

Create `frontend/Dockerfile.prod`:

```dockerfile
# Multi-stage build for production
FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine as production

# Set working directory
WORKDIR /app

# Copy built application
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./

# Create app user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership
RUN chown -R nextjs:nodejs /app

# Switch to nextjs user
USER nextjs

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]
```

### 🗄️ Database Dockerfile

Create `database/Dockerfile`:

```dockerfile
FROM postgres:14-alpine

# Set environment variables
ENV POSTGRES_DB=artin_smart_trade
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=secure_password

# Copy initialization scripts
COPY init.sql /docker-entrypoint-initdb.d/

# Expose port
EXPOSE 5432

# Start PostgreSQL
CMD ["postgres"]
```

### 📊 Monitoring Dockerfile

Create `monitoring/Dockerfile`:

```dockerfile
FROM prom/prometheus:latest

# Copy configuration
COPY prometheus.yml /etc/prometheus/

# Expose port
EXPOSE 9090

# Start Prometheus
CMD ["--config.file=/etc/prometheus/prometheus.yml", "--web.enable-lifecycle"]
```

## 🐳 Docker Compose

### 🔧 Development Configuration

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - artin-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/artin_smart_trade
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=dev-secret-key
      - JWT_SECRET_KEY=dev-jwt-secret
      - DEBUG=true
    volumes:
      - ./backend:/app
      - /app/__pycache__
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - artin-network

  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=artin_smart_trade
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - artin-network

  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - artin-network

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    command: celery -A app.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/artin_smart_trade
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=dev-secret-key
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - artin-network

volumes:
  postgres_data:
  redis_data:

networks:
  artin-network:
    driver: bridge
```

### 🚀 Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://api.artin-smart-trade.com
      - NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY}
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - artin-network
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/artin_smart_trade
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - COMTRADE_API_KEY=${COMTRADE_API_KEY}
      - FREIGHT_API_KEY=${FREIGHT_API_KEY}
      - FX_API_KEY=${FX_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - artin-network
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=artin_smart_trade
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./backups:/backups
    restart: unless-stopped
    networks:
      - artin-network
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - artin-network
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
    networks:
      - artin-network

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.celery worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/artin_smart_trade
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - artin-network
    volumes:
      - ./logs:/app/logs
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.celery beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/artin_smart_trade
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - artin-network
    volumes:
      - ./logs:/app/logs

  prometheus:
    build:
      context: ./monitoring
      dockerfile: Dockerfile
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped
    networks:
      - artin-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - artin-network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  artin-network:
    driver: bridge
```

### 📊 Staging Configuration

Create `docker-compose.staging.yml`:

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=staging
      - NEXT_PUBLIC_API_URL=https://staging-api.artin-smart-trade.com
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - artin-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/artin_smart_trade_staging
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DEBUG=false
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - artin-network
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=artin_smart_trade_staging
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_staging_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - artin-network

  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_staging_data:/data
    restart: unless-stopped
    networks:
      - artin-network

volumes:
  postgres_staging_data:
  redis_staging_data:

networks:
  artin-network:
    driver: bridge
```

## 🔧 Configuration

### 📝 Environment Files

#### Development (.env.dev)
```bash
# Database
POSTGRES_PASSWORD=dev_password

# Application
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
DEBUG=true

# External APIs (use test keys)
STRIPE_SECRET_KEY=sk_test_your_test_key
COMTRADE_API_KEY=test_comtrade_key
FREIGHT_API_KEY=test_freight_key
FX_API_KEY=test_fx_key
GEMINI_API_KEY=test_gemini_key
OPENAI_API_KEY=test_openai_key

# Monitoring
GRAFANA_PASSWORD=admin123
```

#### Production (.env.prod)
```bash
# Database
POSTGRES_PASSWORD=your_very_secure_password_here

# Application
SECRET_KEY=your_very_secure_secret_key_here
JWT_SECRET_KEY=your_very_secure_jwt_secret_here
DEBUG=false

# External APIs
STRIPE_SECRET_KEY=sk_live_your_production_key
COMTRADE_API_KEY=your_production_comtrade_key
FREIGHT_API_KEY=your_production_freight_key
FX_API_KEY=your_production_fx_key
GEMINI_API_KEY=your_production_gemini_key
OPENAI_API_KEY=your_production_openai_key

# Monitoring
GRAFANA_PASSWORD=your_secure_grafana_password
```

### 🗄️ Database Initialization

Create `database/init.sql`:

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database user
CREATE USER artin_user WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE artin_smart_trade TO artin_user;

-- Enable RLS
ALTER DATABASE artin_smart_trade SET row_level_security = on;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_deals_tenant_id ON deals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
```

### 🌐 Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    server {
        listen 80;
        server_name artin-smart-trade.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name artin-smart-trade.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Login endpoint with stricter rate limiting
        location /auth/login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
```

### 📊 Monitoring Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'artin-smart-trade'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

## 🚀 Deployment

### 🏗️ Build Images

```bash
# Build backend image
docker build -f backend/Dockerfile.prod -t artin-smart-trade/backend:latest ./backend

# Build frontend image
docker build -f frontend/Dockerfile.prod -t artin-smart-trade/frontend:latest ./frontend

# Build monitoring image
docker build -f monitoring/Dockerfile -t artin-smart-trade/monitoring:latest ./monitoring
```

### 🚀 Start Services

#### Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

#### Production
```bash
# Start production environment
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Create super admin user
docker-compose -f docker-compose.prod.yml exec backend python scripts/create_admin.py

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3 --scale frontend=2
```

### 🔄 Update Services

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart services with new images
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 📊 Health Checks

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check health endpoints
curl https://api.artin-smart-trade.com/health
curl https://artin-smart-trade.com/

# Check container health
docker inspect --format='{{.State.Health.Status}}' artin-smart-trade_backend_1
```

## 🔍 Troubleshooting

### 🐛 Common Issues

#### Database Connection Issues
```bash
# Check database logs
docker-compose logs db

# Test database connection
docker-compose exec backend python -c "
from app.database import SessionLocal
db = SessionLocal()
result = db.execute('SELECT 1').scalar()
print('Database OK' if result else 'Database ERROR')
"

# Reset database
docker-compose down -v
docker-compose up -d db
docker-compose exec backend alembic upgrade head
```

#### Redis Connection Issues
```bash
# Check Redis logs
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping

# Clear Redis cache
docker-compose exec redis redis-cli flushall
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Test SSL configuration
openssl s_client -connect artin-smart-trade.com:443

# Renew certificate
sudo certbot renew --dry-run
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check container logs for errors
docker-compose logs -f backend

# Monitor database queries
docker-compose exec db psql -U postgres -d artin_smart_trade -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"
```

### 📋 Maintenance Commands

#### Backup Database
```bash
# Create backup
docker-compose exec db pg_dump -U postgres artin_smart_trade > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T db psql -U postgres artin_smart_trade < backup_20240222_103000.sql
```

#### Clean Up
```bash
# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Clean up logs
docker-compose exec backend find /app/logs -name "*.log" -mtime +30 -delete
```

#### Update Dependencies
```bash
# Update Python dependencies
docker-compose exec backend pip install --upgrade package_name

# Update Node.js dependencies
docker-compose exec frontend npm update

# Rebuild with updated dependencies
docker-compose build --no-cache
```

---

## 🎯 Docker Quick Start

1. **Clone repository**
```bash
git clone https://github.com/your-org/artin-smart-trade.git
cd artin-smart-trade
```

2. **Configure environment**
```bash
cp .env.example .env.dev
# Edit .env.dev with your configuration
```

3. **Start development**
```bash
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d
```

4. **Run migrations**
```bash
docker-compose exec backend alembic upgrade head
```

5. **Access application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📞 Docker Support

- **Documentation**: [docs.artin-smart-trade.com/docker](https://docs.artin-smart-trade.com/docker)
- **Issues**: [GitHub Issues](https://github.com/your-org/artin-smart-trade/issues)
- **Support**: docker-support@artin-smart-trade.com

---

*Built with ❤️ by the Artin Smart Trade Team*
