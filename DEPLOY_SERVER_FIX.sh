#!/bin/bash
# 🚀 SERVER DEPLOYMENT FIX SCRIPT

echo "🔧 Fixing Artin Smart Trade Deployment Issues..."

# 1. Kill existing processes
echo "🔄 Stopping existing services..."
pkill -f uvicorn || true
pkill -f next || true
pkill -f npm || true

# 2. Database setup
echo "🗄️ Setting up PostgreSQL..."
sudo systemctl start postgresql || sudo service postgresql start
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE artinsmarttrade;" || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER artinsmart WITH PASSWORD 'artinsmart123';" || echo "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE artinsmarttrade TO artinsmart;"
sudo -u postgres psql -c "ALTER USER artinsmart CREATEDB;"

# 3. Backend setup
echo "📦 Setting up backend..."
cd /app/ArtinSmartTrade

# Copy alembic config
cp backend/alembic.ini .
cp -r backend/alembic/ .

# Install Python dependencies
cd backend
pip install --upgrade pip
pip install -r requirements.txt
pip install celery redis httpx

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://artinsmart:artinsmart123@localhost:5432/artinsmarttrade"
export PYTHONPATH=/app/ArtinSmartTrade/backend:$PYTHONPATH
export GEMINI_API_KEY="${GEMINI_API_KEY:-your-gemini-api-key}"
export SECRET_KEY="${SECRET_KEY:-your-production-secret-key-change-this}"
export REDIS_URL="redis://localhost:6379/0"

# 4. Database migrations
echo "🗄️ Running database migrations..."
alembic upgrade head

# 5. Start Redis
echo "🔴 Starting Redis..."
sudo systemctl start redis || sudo service redis start || redis-server --daemonize yes

# 6. Start backend
echo "🔥 Starting backend server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 7. Frontend setup
echo "🎨 Setting up frontend..."
cd /app/ArtinSmartTrade/frontend

# Install dependencies
npm install

# Set environment variables
export NEXT_PUBLIC_API_URL="http://localhost:8000"
export PORT=3001

# Build frontend
echo "🏗️ Building frontend..."
npm run build

# 8. Start frontend on different port
echo "🚀 Starting frontend server..."
npm start -- --port 3001 &

# 9. Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# 10. Health checks
echo "🔍 Checking service health..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null 2>&1 || curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend failed to start"
fi

# Check frontend
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo "✅ Frontend is running on http://localhost:3001"
else
    echo "❌ Frontend failed to start"
fi

# 11. Show status
echo "📊 Service Status:"
echo "=================="
ps aux | grep uvicorn | grep -v grep || echo "Backend: Not running"
ps aux | grep next | grep -v grep || echo "Frontend: Not running"
ps aux | grep redis | grep -v grep || echo "Redis: Not running"

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "Backend API: http://localhost:8000"
echo "Frontend App: http://localhost:3001"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Next Steps:"
echo "1. Open http://localhost:3001 in your browser"
echo "2. Test the document classification feature"
echo "3. Check the logistics timeline"
echo "4. Verify multi-tenant functionality"
echo ""
echo "🔧 If issues persist:"
echo "- Check logs: tail -f /var/log/postgresql/*.log"
echo "- Restart services: ./deploy.sh"
echo "- Check environment variables"
