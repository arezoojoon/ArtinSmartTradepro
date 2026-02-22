# 🚀 Artin Smart Trade - Deployment Guide

> **Complete deployment guide for Artin Smart Trade platform**

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [🏗️ Prerequisites](#️-prerequisites)
- [🐳 Docker Deployment](#-docker-deployment)
- [☸️ Kubernetes Deployment](#-kubernetes-deployment)
- [☁️ Cloud Deployment](#-cloud-deployment)
- [🔧 Configuration](#-configuration)
- [📊 Monitoring](#-monitoring)
- [🔒 Security](#-security)
- [🧪 Testing](#-testing)
- [🚨 Troubleshooting](#-troubleshooting)

## 🎯 Overview

This guide covers the complete deployment process for Artin Smart Trade, including local development, staging, and production environments.

### 🌍 Deployment Options

1. **Docker Compose** - Local development and small deployments
2. **Kubernetes** - Enterprise-grade scalable deployments
3. **Cloud Services** - Managed cloud deployments (AWS, GCP, Azure)

## 🏗️ Prerequisites

### 📋 System Requirements

#### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **Network**: 100Mbps

#### Recommended Requirements
- **CPU**: 8 cores
- **RAM**: 16GB
- **Storage**: 100GB SSD
- **Network**: 1Gbps

### 🛠️ Software Requirements

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Kubernetes**: 1.24+ (for K8s deployment)
- **Node.js**: 18+
- **Python**: 3.9+

### 🔐 External Services

- **PostgreSQL**: 14+
- **Redis**: 6+
- **Nginx**: 1.20+
- **SSL Certificate**: For HTTPS

## 🐳 Docker Deployment

### 📦 Production Docker Compose

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

  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=artin_smart_trade
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    networks:
      - artin-network

  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - artin-network

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
    command: celery -A app.celery worker --loglevel=info
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

volumes:
  postgres_data:
  redis_data:

networks:
  artin-network:
    driver: bridge
```

### 🔧 Environment Configuration

Create `.env.prod`:

```bash
# Database
POSTGRES_PASSWORD=your_secure_password_here

# Application Secrets
SECRET_KEY=your_very_secure_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# Payment
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key

# External APIs
COMTRADE_API_KEY=your_comtrade_api_key
FREIGHT_API_KEY=your_freight_api_key
FX_API_KEY=your_fx_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=your_app_password
```

### 🚀 Deployment Commands

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Create super admin user
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.database import SessionLocal
from app.models.phase6 import SystemAdmin
from app.core.security import get_password_hash
db = SessionLocal()
admin = SystemAdmin(
    email='admin@artin-smart-trade.com',
    full_name='Super Admin',
    hashed_password=get_password_hash('your_secure_password'),
    is_active=True
)
db.add(admin)
db.commit()
print('Super admin created successfully')
"

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

## ☸️ Kubernetes Deployment

### 📋 Kubernetes Manifests

#### Namespace
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: artin-smart-trade
  labels:
    name: artin-smart-trade
```

#### ConfigMap
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: artin-config
  namespace: artin-smart-trade
data:
  NODE_ENV: "production"
  NEXT_PUBLIC_API_URL: "https://api.artin-smart-trade.com"
  REDIS_URL: "redis://redis-service:6379"
```

#### Secrets
```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: artin-secrets
  namespace: artin-smart-trade
type: Opaque
data:
  DATABASE_URL: <base64-encoded-database-url>
  SECRET_KEY: <base64-encoded-secret-key>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>
  STRIPE_SECRET_KEY: <base64-encoded-stripe-secret>
```

#### Backend Deployment
```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  namespace: artin-smart-trade
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: artin-smart-trade/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: artin-config
        - secretRef:
            name: artin-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: artin-smart-trade
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### Frontend Deployment
```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deployment
  namespace: artin-smart-trade
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: artin-smart-trade/frontend:latest
        ports:
        - containerPort: 3000
        envFrom:
        - configMapRef:
            name: artin-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: artin-smart-trade
spec:
  selector:
    app: frontend
  ports:
  - protocol: TCP
    port: 3000
    targetPort: 3000
  type: ClusterIP
```

#### Ingress
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: artin-ingress
  namespace: artin-smart-trade
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
spec:
  tls:
  - hosts:
    - artin-smart-trade.com
    - api.artin-smart-trade.com
    secretName: artin-tls
  rules:
  - host: artin-smart-trade.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
  - host: api.artin-smart-trade.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
```

### 🚀 Kubernetes Deployment Commands

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check deployment status
kubectl get pods -n artin-smart-trade
kubectl get services -n artin-smart-trade
kubectl get ingress -n artin-smart-trade

# View logs
kubectl logs -f deployment/backend-deployment -n artin-smart-trade

# Scale deployment
kubectl scale deployment backend-deployment --replicas=5 -n artin-smart-trade
```

## ☁️ Cloud Deployment

### 🟦 AWS ECS Deployment

#### Task Definition
```json
{
  "family": "artin-smart-trade",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/artin-smart-trade/backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:password@rds-endpoint:5432/artin_smart_trade"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/artin-smart-trade",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### ECS Service
```yaml
# ecs-service.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Artin Smart Trade ECS Service

Parameters:
  VpcId:
    Type: AWS::EC2::VPC::Id
  SubnetIds:
    Type: List<AWS::EC2::Subnet::Id>

Resources:
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: artin-smart-trade
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT

  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: artin-smart-trade
      Cpu: 512
      Memory: 1024
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      ExecutionRoleArn: !Ref ExecutionRole
      TaskRoleArn: !Ref TaskRole
      ContainerDefinitions:
        - Name: backend
          Image: !Sub '${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/artin-smart-trade/backend:latest'
          PortMappings:
            - ContainerPort: 8000
              Protocol: tcp
          Environment:
            - Name: DATABASE_URL
              Value: !Ref DatabaseUrl

  Service:
    Type: AWS::ECS::Service
    Properties:
      ServiceName: artin-smart-trade-service
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          Subnets: !Ref SubnetIds
          AssignPublicIp: DISABLED
      LoadBalancers:
        - TargetGroupArn: !Ref TargetGroup
          ContainerName: backend
          ContainerPort: 8000
```

### 🟢 Google Cloud Run

#### Cloud Run Service
```bash
# Build and push image
gcloud builds submit --tag gcr.io/your-project/artin-smart-trade/backend

# Deploy to Cloud Run
gcloud run deploy artin-smart-trade-backend \
  --image gcr.io/your-project/artin-smart-trade/backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://user:password@cloud-sql-proxy:5432/artin_smart_trade \
  --set-secrets SECRET_KEY=artin-secret-key:latest \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 1
```

### 🔵 Azure Container Instances

#### ACI Deployment
```bash
# Create resource group
az group create artin-smart-trade --location eastus

# Deploy container
az container create \
  --resource-group artin-smart-trade \
  --name artin-smart-trade-backend \
  --image yourregistry.azurecr.io/artin-smart-trade/backend:latest \
  --cpu 1 \
  --memory 2 \
  --ports 8000 \
  --environment-variables DATABASE_URL=postgresql://user:password@postgres:5432/artin_smart_trade \
  --dns-name-label artin-smart-trade \
  --secure-signal
```

## 🔧 Configuration

### 🗄️ Database Setup

#### PostgreSQL Configuration
```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database
CREATE DATABASE artin_smart_trade;

-- Create user
CREATE USER artin_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE artin_smart_trade TO artin_user;

-- Enable RLS
ALTER DATABASE artin_smart_trade SET row_level_security = on;
```

#### Redis Configuration
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
```

### 🌐 Nginx Configuration

```nginx
# nginx.conf
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

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
```

## 📊 Monitoring

### 📈 Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

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
```

### 📊 Grafana Dashboards

#### System Dashboard
- CPU and memory usage
- Network traffic
- Disk I/O
- Container health

#### Application Dashboard
- Request rate and latency
- Error rate
- Active users
- Business metrics

#### Database Dashboard
- Connection pool
- Query performance
- Replication lag
- Storage usage

## 🔒 Security

### 🔐 SSL/TLS Setup

#### Let's Encrypt Certbot
```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d artin-smart-trade.com -d api.artin-smart-trade.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 🛡️ Security Headers

```nginx
# Security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";
```

### 🔑 API Security

- **Rate Limiting**: 100 requests/minute per IP
- **CORS**: Strict CORS policies
- **Input Validation**: Comprehensive input validation
- **SQL Injection**: Parameterized queries
- **XSS Protection**: Output encoding and CSP

## 🧪 Testing

### 🧪 Pre-deployment Tests

#### Health Checks
```bash
# Backend health check
curl -f https://api.artin-smart-trade.com/health

# Frontend health check
curl -f https://artin-smart-trade.com/

# Database connectivity
docker-compose exec backend python -c "
from app.database import SessionLocal
db = SessionLocal()
result = db.execute('SELECT 1').scalar()
print('Database OK' if result else 'Database ERROR')
"
```

#### Load Testing
```bash
# Install k6
curl https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz | tar xz
sudo mv k6 /usr/local/bin/

# Run load test
k6 run --vus 10 --duration 30s load-test.js
```

### 📋 Load Test Script
```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 10,
  duration: '30s',
};

export default function () {
  let response = http.get('https://api.artin-smart-trade.com/health');
  check(response, {
    'health check status': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  sleep(1);
}
```

## 🚨 Troubleshooting

### 🔧 Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec backend python -c "
from app.database import SessionLocal
try:
    db = SessionLocal()
    db.execute('SELECT 1')
    print('Database OK')
except Exception as e:
    print(f'Database Error: {e}')
"

# Check database logs
docker-compose logs db
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew --dry-run

# Test SSL configuration
openssl s_client -connect artin-smart-trade.com:443
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check logs for errors
docker-compose logs -f backend

# Monitor database queries
docker-compose exec db psql -U postgres -d artin_smart_trade -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"
```

### 📋 Health Check Endpoints

#### Backend Health
```bash
curl https://api.artin-smart-trade.com/health
```

#### Database Health
```bash
curl https://api.artin-smart-trade.com/health/db
```

#### Redis Health
```bash
curl https://api.artin-smart-trade.com/health/redis
```

### 🔄 Rollback Procedures

#### Docker Rollback
```bash
# Rollback to previous version
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

#### Kubernetes Rollback
```bash
# Rollback deployment
kubectl rollout undo deployment/backend-deployment -n artin-smart-trade

# Check rollback status
kubectl rollout status deployment/backend-deployment -n artin-smart-trade
```

---

## 🎯 Deployment Checklist

### ✅ Pre-deployment
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database created and migrated
- [ ] External API keys configured
- [ ] Security headers configured
- [ ] Monitoring setup completed
- [ ] Backup strategy implemented

### ✅ Deployment
- [ ] Images built and pushed
- [ ] Services deployed
- [ ] Load balancer configured
- [ ] Health checks passing
- [ ] SSL certificate active
- [ ] Monitoring alerts configured

### ✅ Post-deployment
- [ ] Smoke tests passed
- [ ] Load tests completed
- [ ] Monitoring dashboards active
- [ ] Backup verification
- [ ] Security scan completed
- [ ] Performance benchmarks met

---

## 🚀 Ready for Production!

Your Artin Smart Trade platform is now ready for production deployment. Follow this guide carefully and ensure all security and monitoring measures are in place.

**📞 Need Help?**
- **Documentation**: [docs.artin-smart-trade.com](https://docs.artin-smart-trade.com)
- **Support**: support@artin-smart-trade.com
- **Issues**: [GitHub Issues](https://github.com/your-org/artin-smart-trade/issues)

---

*Built with ❤️ by the Artin Smart Trade Team*
