#!/bin/bash
# 🐳 DOCKER DEPLOYMENT FIX SCRIPT

echo "🐳 Starting Docker-based deployment..."

# 1. Kill existing processes
echo "🔄 Stopping existing services..."
docker compose down || true
pkill -f uvicorn || true
pkill -f next || true

# 2. Fix backend import error
echo "🔧 Fixing backend import error..."
cd /app/ArtinSmartTrade

# Fix the import issue in document_classifier.py
sed -i 's/from app.models.crm import Company, Contact, Deal/from app.models.crm import CRMCompany as Company, CRMContact as Contact, CRMDeal as Deal/' backend/app/services/document_classifier.py

# 3. Start Docker services
echo "🐳 Starting Docker containers..."
docker compose up --build -d

# 4. Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# 5. Check service status
echo "🔍 Checking Docker services..."
docker compose ps

# 6. Check logs if needed
echo "📋 Checking service logs..."
docker compose logs --tail=20 backend
docker compose logs --tail=20 frontend

# 7. Health checks
echo "🔍 Checking service health..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null 2>&1 || curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend failed to start - checking logs..."
    docker compose logs backend
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "❌ Frontend failed to start - checking logs..."
    docker compose logs frontend
fi

echo ""
echo "🎉 Docker Deployment Complete!"
echo "============================"
echo "Backend API: http://localhost:8000"
echo "Frontend App: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Next Steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Test the document classification feature"
echo "3. Check the logistics timeline"
echo "4. Verify multi-tenant functionality"
echo ""
echo "🔧 If issues persist:"
echo "- Check logs: docker compose logs [service]"
echo "- Restart: docker compose restart [service]"
echo "- Rebuild: docker compose up --build -d"
