#!/bin/bash
# Odoo Multi-Tenant Database Creation Script
# Automatically creates tenant databases based on ODOO_TENANT_DATABASES environment variable

set -e

# Parse tenant databases from environment variable
IFS=',' read -ra TENANT_DBS <<< "$POSTGRES_MULTIPLE_DATABASES"

if [ ${#TENANT_DBS[@]} -eq 0 ]; then
    echo "No tenant databases specified in POSTGRES_MULTIPLE_DATABASES"
    exit 0
fi

echo "Creating tenant databases: ${TENANT_DBS[@]}"

for db in "${TENANT_DBS[@]}"; do
    # Trim whitespace
    db=$(echo "$db" | xargs)

    if [ -z "$db" ]; then
        continue
    fi

    echo "Creating database: $db"

    # Create database if not exists
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        SELECT 'CREATE DATABASE $db'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
        GRANT ALL PRIVILEGES ON DATABASE $db TO $POSTGRES_USER;
EOSQL

    # Connect to tenant database and create extensions
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db" <<-EOSQL
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        CREATE EXTENSION IF NOT EXISTS unaccent;
EOSQL

    echo "Database $db created successfully"
done

echo "Tenant database creation complete"
