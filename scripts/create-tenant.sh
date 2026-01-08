#!/bin/bash
# Create New Tenant Database

TENANT_ID=$1
BUSINESS_TYPE=${2:-retail}
COMPANY_NAME=$3

if [ -z "$TENANT_ID" ]; then
    echo "Usage: ./create-tenant.sh <tenant-id> [business-type] [company-name]"
    echo "Example: ./create-tenant.sh store1 jewelry 'Gold Palace Jewelry'"
    exit 1
fi

DB_NAME="tenant_${TENANT_ID}"

echo "Creating tenant: $TENANT_ID"
echo "Database: $DB_NAME"
echo "Business Type: $BUSINESS_TYPE"

# Create database
docker exec odoo_postgres psql -U odoo -d postgres -c "CREATE DATABASE $DB_NAME;"
docker exec odoo_postgres psql -U odoo -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
docker exec odoo_postgres psql -U odoo -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS unaccent;"

echo "Tenant database created: $DB_NAME"
echo "Access URL: http://${TENANT_ID}.odoo.maxhaider.dev"
