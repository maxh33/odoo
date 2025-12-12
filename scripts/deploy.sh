#!/bin/bash
# Odoo Multi-Tenant Deployment Script

set -e

ENV=${1:-development}

echo "========================================="
echo "Deploying Odoo Multi-Tenant Platform"
echo "Environment: $ENV"
echo "========================================="

# Check .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Health check before deployment
./scripts/health-check.sh || echo "No existing deployment found"

# Deploy based on environment
if [ "$ENV" = "production" ]; then
    echo "Deploying production environment..."
    docker-compose -f docker-compose.prod.yml up -d
elif [ "$ENV" = "development" ]; then
    echo "Deploying development environment..."
    docker-compose -f docker-compose.yml -f docker-compose.development.yml up -d
else
    echo "Deploying default environment..."
    docker-compose up -d
fi

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 30

# Run health check
./scripts/health-check.sh

echo ""
echo "========================================="
echo "Deployment complete!"
echo "Access Odoo at: http://localhost:8069"
echo "========================================="
