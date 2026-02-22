# 🌍 Artin Smart Trade - Global Trade Intelligence Platform

> **Enterprise-grade B2B trade intelligence platform with AI-powered insights, automated workflows, and real-time market data**

## 📋 Table of Contents

- [🌟 Overview](#-overview)
- [🚀 Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🔧 Development](#-development)
- [📚 API Documentation](#-api-documentation)
- [🚀 Deployment](#-deployment)
- [🧪 Testing](#-testing)
- [📊 Monitoring](#-monitoring)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## 🌟 Overview

Artin Smart Trade is a comprehensive B2B trade intelligence platform that enables businesses to:
- **Discover** global trade opportunities with AI-powered market analysis
- **Analyze** real-time freight rates, currency exchange, and trade data
- **Automate** deal pipelines with intelligent workflow automation
- **Manage** customer relationships with advanced CRM features
- **Optimize** operations with data-driven insights and BI analytics

### 🎯 Key Benefits

- **🤖 AI-Powered**: Vision/voice parsing, predictive analytics, automated insights
- **🌍 Global Coverage**: UN Comtrade integration, worldwide freight rates, multi-currency support
- **⚡ Real-Time**: Live market data, instant notifications, real-time dashboards
- **🔒 Enterprise-Grade**: Multi-tenancy, RBAC, audit logging, security compliance
- **📱 Mobile-First**: Responsive design, mobile control tower, field-ready features

## 🚀 Features

### 📊 Super Admin Panel
- **MRR/ARR Dashboard**: Revenue tracking, churn prediction, growth analytics
- **Health Monitoring**: System health, connector status, performance metrics
- **Security Operations**: Key rotation, anomaly detection, compliance monitoring
- **Support Ticketing**: Complete ticket management with SLA tracking
- **Cost Dashboard**: Infrastructure costs, budget tracking, optimization insights

### 🏢 Tenant Panel
- **Mobile Control Tower**: Real-time insights on cash flow, opportunities, risks
- **Main Dashboard**: Pipeline summary, margin overview, risk heatmap
- **Deals & Operations**: Complete deal lifecycle with document management
- **Wallet & Billing**: Stripe integration, subscription management, usage tracking
- **Advanced Settings**: Custom pipelines, scoring profiles, integrations

### 🛠️ Toolbox
- **Trade Data**: UN Comtrade integration, HS Code lookup, trend analysis
- **Freight Rates**: Live container rates, route optimization, carrier comparison
- **FX Center**: Real-time currency rates, hedging recommendations, volatility analysis
- **BI Analytics**: Custom dashboards, comprehensive reporting, data visualization

### 🤝 CRM Enhancement
- **Vision/Voice Parsing**: AI-powered document processing, speech-to-text
- **Campaign A/B Testing**: Statistical testing, automated optimization
- **Pipeline Automation**: Rule-based workflows, intelligent triggers

## 🏗️ Architecture

### 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
├─────────────────────────────────────────────────────────────┤
│                    API Gateway (FastAPI)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Auth      │  │   Core      │  │   AI/ML     │         │
│  │   Service    │  │   Service    │  │   Service    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   CRM       │  │   Trade     │  │   Billing    │         │
│  │   Service    │  │   Service    │  │   Service    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                    PostgreSQL Database                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    Redis    │  │   Stripe    │  │   External  │         │
│  │   Cache     │  │   Payment   │  │   APIs      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 14+ with RLS
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT with multi-tenant support
- **Caching**: Redis
- **Background Tasks**: Celery
- **API Documentation**: OpenAPI/Swagger

#### Frontend
- **Framework**: Next.js 14+ (React 18)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **UI Components**: Shadcn/ui
- **Charts**: Recharts
- **Icons**: Lucide React

#### AI/ML
- **Vision**: Google Gemini Vision API
- **Speech**: OpenAI Whisper
- **Analytics**: NumPy, SciPy, Pandas
- **ML Models**: Custom models for trade analysis

#### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx
- **Load Balancer**: Nginx
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack
- **CI/CD**: GitHub Actions

## 📦 Installation

### 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose

### 🚀 Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/your-org/artin-smart-trade.git
cd artin-smart-trade
```

2. **Environment Setup**
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

3. **Database Setup**
```bash
# Create PostgreSQL database
createdb artin_smart_trade

# Run migrations
cd ../backend
alembic upgrade head
```

4. **Environment Configuration**
```bash
# Backend environment
cp .env.example .env
# Edit .env with your configuration

# Frontend environment
cd ../frontend
cp .env.local.example .env.local
# Edit .env.local with your configuration
```

5. **Start Services**
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or manually:
# Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev
```

6. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## ⚙️ Configuration

### 🔑 Environment Variables

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/artin_smart_trade

# Authentication
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# External APIs
COMTRADE_API_KEY=your-comtrade-api-key
FREIGHT_API_KEY=your-freight-api-key
FX_API_KEY=your-fx-api-key
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key

# Stripe
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Redis
REDIS_URL=redis://localhost:6379

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key
NEXT_PUBLIC_APP_NAME=Artin Smart Trade
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### 🗄️ Database Configuration

The application uses PostgreSQL with Row Level Security (RLS) for multi-tenant isolation. Key tables:

- **Tenants**: Multi-tenant management
- **Users**: User authentication and roles
- **Deals**: Deal lifecycle management
- **CRM**: Customer relationship management
- **Billing**: Subscription and payment processing
- **Analytics**: Business intelligence data

### 🔐 Security Configuration

- **JWT Tokens**: Short-lived access tokens (15 minutes)
- **Refresh Tokens**: Long-lived refresh tokens (7 days)
- **API Keys**: Secure API key management
- **Rate Limiting**: API rate limiting per tenant
- **CORS**: Configurable CORS policies
- **HTTPS**: SSL/TLS encryption in production

## 🔧 Development

### 🛠️ Development Setup

1. **Install development dependencies**
```bash
cd backend
pip install -r requirements-dev.txt

cd frontend
npm install --include=dev
```

2. **Pre-commit hooks**
```bash
cd backend
pre-commit install
```

3. **Database migrations**
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### 🧪 Testing

#### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py
```

#### Frontend Tests
```bash
# Run unit tests
npm test

# Run E2E tests
npm run test:e2e

# Run with coverage
npm run test:coverage
```

### 📝 Code Quality

- **Linting**: ESLint, Prettier (Frontend), Black, isort (Backend)
- **Type Checking**: TypeScript, mypy
- **Pre-commit**: Automated code formatting and linting
- **Documentation**: Comprehensive API docs and inline comments

## 📚 API Documentation

### 🌐 API Endpoints

#### Authentication
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh token
- `POST /auth/logout` - User logout

#### Super Admin (`/sys/*`)
- `GET /sys/tenants` - List tenants
- `GET /sys/revenue` - Revenue dashboard
- `GET /sys/health` - System health
- `GET /sys/security` - Security operations
- `GET /sys/support` - Support tickets
- `GET /sys/costs` - Cost dashboard

#### Tenant Panel (`/api/*`)
- `GET /api/dashboard/mobile` - Mobile control tower
- `GET /api/dashboard/main` - Main dashboard
- `GET /api/deals` - Deal management
- `GET /api/billing` - Billing and wallet
- `GET /api/settings` - Tenant settings

#### Toolbox (`/api/toolbox/*`)
- `GET /api/toolbox/trade-data` - Trade data
- `GET /api/toolbox/freight-rates` - Freight rates
- `GET /api/toolbox/fx-center` - FX rates
- `GET /api/toolbox/bi-analytics` - BI analytics

#### CRM (`/api/crm/*`)
- `POST /api/crm/vision-voice/process-document` - Document processing
- `POST /api/crm/campaign-ab/create` - A/B testing
- `POST /api/crm/pipeline-automation/trigger` - Automation

### 📖 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🚀 Deployment

### 🐳 Docker Deployment

#### Production Docker Compose
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/artin_smart_trade
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=artin_smart_trade
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
```

### ☸️ Kubernetes Deployment

#### Kubernetes Manifests
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: artin-smart-trade-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: artin-smart-trade-backend
  template:
    metadata:
      labels:
        app: artin-smart-trade-backend
    spec:
      containers:
      - name: backend
        image: artin-smart-trade/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: artin-smart-trade-secrets
              key: database-url
```

### 🌐 Cloud Deployment

#### AWS ECS
- **Container Registry**: ECR
- **Load Balancer**: Application Load Balancer
- **Database**: RDS PostgreSQL
- **Cache**: ElastiCache Redis
- **Storage**: S3 for file uploads
- **Monitoring**: CloudWatch

#### Google Cloud Run
- **Serverless**: Cloud Run for backend
- **Database**: Cloud SQL PostgreSQL
- **Cache**: Memorystore Redis
- **Storage**: Cloud Storage
- **Monitoring**: Cloud Monitoring

#### Azure Container Instances
- **Container Registry**: ACR
- **Database**: Azure Database for PostgreSQL
- **Cache**: Azure Cache for Redis
- **Storage**: Azure Blob Storage
- **Monitoring**: Azure Monitor

## 📊 Monitoring

### 📈 Application Monitoring

#### Prometheus Metrics
```python
# Custom metrics
from prometheus_client import Counter, Histogram, Gauge

# Request counter
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])

# Response time histogram
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Active users gauge
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
```

#### Grafana Dashboards
- **System Overview**: CPU, memory, disk, network
- **Application Metrics**: Request rate, response time, error rate
- **Business Metrics**: Active users, deals created, revenue
- **Database Metrics**: Connection pool, query performance

### 🔍 Logging

#### Structured Logging
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "User action completed",
    user_id=user.id,
    action="deal_created",
    deal_id=deal.id,
    tenant_id=tenant.id
)
```

#### ELK Stack
- **Elasticsearch**: Log storage and indexing
- **Logstash**: Log processing and transformation
- **Kibana**: Log visualization and analysis

### 🚨 Alerting

#### Alert Rules
- **High Error Rate**: Alert when error rate > 5%
- **Slow Response Time**: Alert when p95 latency > 2s
- **Database Connections**: Alert when connection pool > 80%
- **Disk Space**: Alert when disk usage > 85%
- **Memory Usage**: Alert when memory usage > 90%

## 🧪 Testing

### 📋 Test Coverage

#### Backend Tests
- **Unit Tests**: 90%+ coverage
- **Integration Tests**: API endpoints, database operations
- **E2E Tests**: Complete user workflows
- **Performance Tests**: Load testing, stress testing

#### Frontend Tests
- **Unit Tests**: Component testing with Jest
- **Integration Tests**: API integration testing
- **E2E Tests**: User journey testing with Playwright
- **Visual Tests**: UI regression testing

### 🔧 Test Data Management

#### Fixtures
```python
# test_fixtures.py
@pytest.fixture
def sample_tenant(db):
    tenant = Tenant(
        name="Test Tenant",
        plan="enterprise",
        created_at=datetime.utcnow()
    )
    db.add(tenant)
    db.commit()
    return tenant
```

#### Test Database
- **Separate Database**: Test database isolated from production
- **Migrations**: Test migrations applied automatically
- **Cleanup**: Automatic cleanup after each test

## 🤝 Contributing

### 📝 Contributing Guidelines

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes**: Follow coding standards and add tests
4. **Run tests**: Ensure all tests pass
5. **Commit changes**: Follow commit message conventions
6. **Push branch**: `git push origin feature/amazing-feature`
7. **Create Pull Request**: Describe changes and link issues

### 🎯 Code Standards

#### Python (Backend)
- **Style**: PEP 8, Black formatting
- **Type Hints**: Use type hints for all functions
- **Documentation**: Docstrings for all public functions
- **Testing**: Write tests for all new features

#### TypeScript (Frontend)
- **Style**: ESLint + Prettier configuration
- **Type Safety**: Strict TypeScript mode
- **Components**: Functional components with hooks
- **Testing**: Jest + React Testing Library

### 📋 Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### 📜 License Summary

- ✅ **Commercial use**: Allowed
- ✅ **Modification**: Allowed
- ✅ **Distribution**: Allowed
- ✅ **Private use**: Allowed
- ❌ **Liability**: No warranty
- ❌ **Trademark**: No trademark rights

## 🙏 Acknowledgments

### 🏢 Core Contributors
- **Development Team**: Artin Smart Trade Development Team
- **Product Management**: Product team for requirements and feedback
- **Design Team**: UI/UX design and user experience

### 📚 Third-Party Services
- **UN Comtrade**: Trade data API
- **Stripe**: Payment processing
- **Google**: Vision AI and Cloud services
- **OpenAI**: Speech-to-text and language models

### 🛠️ Open Source Libraries
- **FastAPI**: Modern Python web framework
- **Next.js**: React framework for production
- **PostgreSQL**: Powerful open source database
- **Redis**: In-memory data structure store

## 📞 Support

### 🆘 Getting Help

- **Documentation**: [docs.artin-smart-trade.com](https://docs.artin-smart-trade.com)
- **Community**: [GitHub Discussions](https://github.com/your-org/artin-smart-trade/discussions)
- **Issues**: [GitHub Issues](https://github.com/your-org/artin-smart-trade/issues)
- **Email**: support@artin-smart-trade.com

### 🐛 Bug Reports

Please report bugs using the GitHub issue tracker with:
- **Description**: Clear description of the issue
- **Steps to Reproduce**: Detailed steps to reproduce the bug
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: OS, browser, version information

### 💡 Feature Requests

We welcome feature requests! Please:
- **Check existing issues** first
- **Provide detailed description** of the feature
- **Explain the use case** and benefits
- **Consider implementation complexity**

---

## 🌟 Ready to Transform Your Trade Operations?

Artin Smart Trade is the comprehensive solution for modern B2B trade intelligence. Get started today and experience the power of AI-driven trade automation.

**🚀 [Get Started](https://artin-smart-trade.com) | [Request Demo](https://artin-smart-trade.com/demo) | [Contact Sales](https://artin-smart-trade.com/contact)**

---

*Built with ❤️ by the Artin Smart Trade Team*
