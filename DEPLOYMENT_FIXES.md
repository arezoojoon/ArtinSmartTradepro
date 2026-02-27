# 🚀 DEPLOYMENT FIXES FOR SERVER

## 🔧 Issues Found & Solutions

### Problem 1: alembic.ini missing
**Solution**: Copy from backend directory
```bash
# Copy alembic config to root
cp backend/alembic.ini .
cp -r backend/alembic/ .
```

### Problem 2: ModuleNotFoundError for 'app'
**Solution**: Set PYTHONPATH and run from backend directory
```bash
# Set Python path and run from backend
cd backend
export PYTHONPATH=/app/ArtinSmartTrade/backend:$PYTHONPATH
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Problem 3: Frontend package.json missing
**Solution**: Navigate to frontend directory
```bash
# Frontend is in separate directory
cd frontend
npm install
npm run build
npm start
```

## 📋 Correct Deployment Commands

### Backend Deployment:
```bash
# 1. Go to project root
cd /app/ArtinSmartTrade

# 2. Copy alembic config
cp backend/alembic.ini .
cp -r backend/alembic/ .

# 3. Run database migrations
cd backend
export PYTHONPATH=/app/ArtinSmartTrade/backend:$PYTHONPATH
alembic upgrade head

# 4. Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Deployment:
```bash
# 1. Go to frontend directory
cd /app/ArtinSmartTrade/frontend

# 2. Install dependencies
npm install

# 3. Build for production
npm run build

# 4. Start frontend server
npm start
```

## 🔍 Environment Setup

### Required Environment Variables:
```bash
# Database
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/dbname"

# Gemini API
export GEMINI_API_KEY="your-gemini-api-key"

# File Upload
export UPLOAD_DIR="/var/www/uploads"
export MAX_FILE_SIZE=10485760

# Security
export SECRET_KEY="your-production-secret-key"
```

## 🚀 Quick Start Script

Create this script on server:
```bash
#!/bin/bash
# deploy.sh

echo "🚀 Starting Artin Smart Trade Deployment..."

# Backend Setup
echo "📦 Setting up backend..."
cd /app/ArtinSmartTrade
cp backend/alembic.ini .
cp -r backend/alembic/ .

cd backend
export PYTHONPATH=/app/ArtinSmartTrade/backend:$PYTHONPATH

echo "🗄️ Running database migrations..."
alembic upgrade head

echo "🔥 Starting backend server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Frontend Setup
echo "🎨 Setting up frontend..."
cd /app/ArtinSmartTrade/frontend

echo "📦 Installing dependencies..."
npm install

echo "🏗️ Building frontend..."
npm run build

echo "🚀 Starting frontend server..."
npm start &

echo "✅ Deployment complete!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
```

## 🛠️ Troubleshooting

### If alembic still fails:
```bash
# Check alembic.ini location
find . -name "alembic.ini"

# Create minimal alembic.ini if needed
cat > alembic.ini << EOF
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://user:password@localhost/dbname
EOF
```

### If Python module errors persist:
```bash
# Install dependencies first
pip install -r backend/requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"

# Test import
cd backend
python -c "import app.main; print('Import successful')"
```

### If frontend errors:
```bash
# Check Node.js version
node --version
npm --version

# Clear npm cache
npm cache clean --force

# Reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📞 Support

If issues persist:
1. Check logs: `tail -f /var/log/app.log`
2. Verify database connection
3. Check environment variables
4. Review system resources

---
