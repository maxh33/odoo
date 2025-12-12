#!/bin/bash
# Odoo Multi-Tenant Health Check Script

set -e

echo "========================================="
echo "Odoo Multi-Tenant Health Check"
echo "========================================="

# Check if containers are running
echo "Checking container status..."
if docker ps | grep -q "odoo_community_18"; then
    echo "✓ Odoo container is running"
else
    echo "✗ Odoo container is NOT running"
    exit 1
fi

if docker ps | grep -q "odoo_postgres"; then
    echo "✓ PostgreSQL container is running"
else
    echo "✗ PostgreSQL container is NOT running"
    exit 1
fi

# Check HTTP service
echo ""
echo "Checking HTTP service..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8069 || echo "000")
if [ "$HTTP_STATUS" -eq 303 ] || [ "$HTTP_STATUS" -eq 200 ]; then
    echo "✓ HTTP service is responding (Status: $HTTP_STATUS)"
else
    echo "✗ HTTP service check failed (Status: $HTTP_STATUS)"
    exit 1
fi

# Check database connectivity
echo ""
echo "Checking database connectivity..."
if docker exec odoo_postgres pg_isready -U odoo -d odoo_master > /dev/null 2>&1; then
    echo "✓ Database is accepting connections"
else
    echo "✗ Database connection failed"
    exit 1
fi

# Check disk space
echo ""
echo "Checking disk space..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    echo "✓ Disk usage is healthy ($DISK_USAGE%)"
else
    echo "⚠ Warning: Disk usage is high ($DISK_USAGE%)"
fi

echo ""
echo "========================================="
echo "Health check complete!"
echo "========================================="
