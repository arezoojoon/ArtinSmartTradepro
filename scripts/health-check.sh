#!/bin/bash

# =============================================================================
# Artin Smart Trade - Health Check Script
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
GRAFANA_URL="http://localhost:3001"
PROMETHEUS_URL="http://localhost:9090"

# Overall status
OVERALL_STATUS="HEALTHY"
FAILED_CHECKS=0

# Function to check HTTP endpoint
check_http_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    log_info "Checking $name: $url"
    
    if curl -f -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        log_success "$name is healthy"
        return 0
    else
        log_error "$name is unhealthy"
        ((FAILED_CHECKS++))
        OVERALL_STATUS="UNHEALTHY"
        return 1
    fi
}

# Function to check Docker container
check_container() {
    local name="$1"
    local container="$2"
    
    log_info "Checking container: $container"
    
    if docker-compose ps "$container" | grep -q "Up"; then
        log_success "$container is running"
        return 0
    else
        log_error "$container is not running"
        ((FAILED_CHECKS++))
        OVERALL_STATUS="UNHEALTHY"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    log_info "Checking database connectivity"
    
    if docker-compose exec -T db pg_isready -U postgres &> /dev/null; then
        log_success "Database is ready"
        
        # Check if database exists and is accessible
        if docker-compose exec -T db psql -U postgres -d artin_smart_trade -c "SELECT 1;" &> /dev/null; then
            log_success "Database is accessible"
            return 0
        else
            log_error "Database is not accessible"
            ((FAILED_CHECKS++))
            OVERALL_STATUS="UNHEALTHY"
            return 1
        fi
    else
        log_error "Database is not ready"
        ((FAILED_CHECKS++))
        OVERALL_STATUS="UNHEALTHY"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis() {
    log_info "Checking Redis connectivity"
    
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis is responsive"
        return 0
    else
        log_error "Redis is not responsive"
        ((FAILED_CHECKS++))
        OVERALL_STATUS="UNHEALTHY"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    log_info "Checking disk space"
    
    # Get disk usage percentage
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$DISK_USAGE" -lt 80 ]; then
        log_success "Disk space is sufficient (${DISK_USAGE}%)"
        return 0
    elif [ "$DISK_USAGE" -lt 90 ]; then
        log_warning "Disk space is getting low (${DISK_USAGE}%)"
        return 0
    else
        log_error "Disk space is critically low (${DISK_USAGE}%)"
        ((FAILED_CHECKS++))
        OVERALL_STATUS="UNHEALTHY"
        return 1
    fi
}

# Function to check memory usage
check_memory_usage() {
    log_info "Checking memory usage"
    
    # Get memory usage percentage
    MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$MEMORY_USAGE" -lt 80 ]; then
        log_success "Memory usage is normal (${MEMORY_USAGE}%)"
        return 0
    elif [ "$MEMORY_USAGE" -lt 90 ]; then
        log_warning "Memory usage is high (${MEMORY_USAGE}%)"
        return 0
    else
        log_error "Memory usage is critically high (${MEMORY_USAGE}%)"
        ((FAILED_CHECKS++))
        OVERALL_STATUS="UNHEALTHY"
        return 1
    fi
}

# Function to check SSL certificates
check_ssl_certificates() {
    log_info "Checking SSL certificates"
    
    if [ -f "nginx/ssl/cert.pem" ] && [ -f "nginx/ssl/key.pem" ]; then
        # Check certificate expiration
        if openssl x509 -in nginx/ssl/cert.pem -noout -checkend 86400 &> /dev/null; then
            log_success "SSL certificates are valid"
            return 0
        else
            log_warning "SSL certificates are expiring soon"
            return 0
        fi
    else
        log_warning "SSL certificates not found (HTTP mode)"
        return 0
    fi
}

# Function to check environment variables
check_environment_variables() {
    log_info "Checking critical environment variables"
    
    local critical_vars=("SECRET_KEY" "JWT_SECRET_KEY" "POSTGRES_PASSWORD" "STRIPE_SECRET_KEY")
    local missing_vars=()
    
    for var in "${critical_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        log_success "All critical environment variables are set"
        return 0
    else
        log_error "Missing environment variables: ${missing_vars[*]}"
        ((FAILED_CHECKS++))
        OVERALL_STATUS="UNHEALTHY"
        return 1
    fi
}

# Function to check recent errors in logs
check_recent_errors() {
    log_info "Checking for recent errors in logs"
    
    local error_count=0
    
    # Check backend logs for recent errors
    if [ -f "logs/backend.log" ]; then
        backend_errors=$(tail -100 logs/backend.log | grep -i "error\|exception\|failed" | wc -l)
        error_count=$((error_count + backend_errors))
    fi
    
    # Check nginx logs for recent errors
    if [ -f "logs/nginx/error.log" ]; then
        nginx_errors=$(tail -100 logs/nginx/error.log | grep -i "error\|failed" | wc -l)
        error_count=$((error_count + nginx_errors))
    fi
    
    if [ "$error_count" -eq 0 ]; then
        log_success "No recent errors found in logs"
        return 0
    elif [ "$error_count" -lt 5 ]; then
        log_warning "Found $error_count recent errors in logs"
        return 0
    else
        log_error "Found $error_count recent errors in logs"
        ((FAILED_CHECKS++))
        OVERALL_STATUS="UNHEALTHY"
        return 1
    fi
}

# Main health check
echo ""
echo "=========================================="
echo "🏥 Artin Smart Trade Health Check"
echo "=========================================="
echo "📅 Date: $(date)"
echo ""

# Load environment variables if .env.prod exists
if [ -f ".env.prod" ]; then
    source .env.prod
    log_info "Loaded environment variables from .env.prod"
else
    log_warning "Environment file .env.prod not found"
fi

# Run all health checks
check_container "Backend" "backend"
check_container "Frontend" "frontend"
check_container "Database" "db"
check_container "Redis" "redis"
check_container "Nginx" "nginx"
check_container "Celery" "celery"
check_container "Celery Beat" "celery-beat"

check_http_endpoint "Backend API" "$BACKEND_URL/health"
check_http_endpoint "Frontend" "$FRONTEND_URL"

# Optional checks for monitoring services
if curl -f -s "$GRAFANA_URL" &> /dev/null; then
    check_http_endpoint "Grafana" "$GRAFANA_URL"
fi

if curl -f -s "$PROMETHEUS_URL" &> /dev/null; then
    check_http_endpoint "Prometheus" "$PROMETHEUS_URL"
fi

check_database
check_redis
check_disk_space
check_memory_usage
check_ssl_certificates
check_environment_variables
check_recent_errors

# Health check summary
echo ""
echo "=========================================="
echo "📊 Health Check Summary"
echo "=========================================="
echo "🏥 Overall Status: $OVERALL_STATUS"
echo "❌ Failed Checks: $FAILED_CHECKS"
echo "📅 Date: $(date)"
echo ""

if [ "$OVERALL_STATUS" = "HEALTHY" ]; then
    log_success "All systems are healthy! 🎉"
    exit 0
else
    log_error "Some systems are unhealthy. Please check the logs above."
    exit 1
fi
