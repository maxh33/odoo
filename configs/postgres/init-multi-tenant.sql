-- Odoo Multi-Tenant Database Initialization Script
-- This script creates the master database and configures PostgreSQL for multi-tenancy

-- Create master database if not exists
SELECT 'CREATE DATABASE odoo_master'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'odoo_master')\gexec

-- Connect to master database
\c odoo_master

-- Create extensions for better performance
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Grant permissions to odoo user
GRANT ALL PRIVILEGES ON DATABASE odoo_master TO odoo;

-- Performance optimization settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '512MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '2GB';

-- Reload configuration
SELECT pg_reload_conf();

-- Log completion
\echo 'Odoo multi-tenant database initialization complete'
