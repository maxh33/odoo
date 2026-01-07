# Tenant Management Guide

Complete guide for managing tenant databases in the Multi-Tenant Odoo 18 Platform.

## 📋 Table of Contents

- [Tenant Overview](#tenant-overview)
- [Creating New Tenants](#creating-new-tenants)
- [Managing Existing Tenants](#managing-existing-tenants)
- [Importing Product Catalogs](#importing-product-catalogs)
- [Tenant Maintenance](#tenant-maintenance)
- [Troubleshooting](#troubleshooting)

---

## 🏢 Tenant Overview

### What is a Tenant?

In this Odoo platform, each **tenant** represents a separate business or client with:
- ✅ **Isolated database** - Complete data separation
- ✅ **Custom configuration** - Business-specific settings
- ✅ **Template-based setup** - Pre-configured modules (jewelry, retail, etc.)
- ✅ **Independent operations** - No data sharing between tenants

### Current Tenants

| Tenant Database | Business Type | Template | Status |
|----------------|---------------|----------|--------|
| `tenant_joiasmax` | Jewelry Store | jewelry_template | ✅ Active |
| `odoo_master` | Platform Management | base | ✅ Active |

### Tenant Naming Convention

```
Database Name Format: tenant_{business_type}_{name}

Examples:
- tenant_jewelry_store1
- tenant_retail_shop2
- tenant_manufacturing_factory1
- tenant_service_company1
```

---

## 🆕 Creating New Tenants

### Method 1: Via Odoo Web Interface (Recommended)

1. **Access Database Manager**
   ```
   URL: http://localhost:8069/web/database/manager
   Master Password: [check Docker logs or .env file]
   ```

2. **Create New Database**
   ```
   Database Name: tenant_jewelry_newstore
   Email: admin@newstore.com
   Password: [secure_password]
   Phone: +55 11 98765-4321
   Language: Portuguese (BR) / Português (BR)
   Country: Brazil
   ☐ Demo data: UNCHECKED (for production)
   ```

3. **Install Template Module**
   ```
   Navigate to: Apps
   Remove filter: "Apps"
   Search: "jewelry_template"
   Click: Install
   ```

4. **Configure Tenant**
   ```
   Settings → General Settings:
   - Company Name: New Store Name
   - Currency: BRL (Brazilian Real)
   - Timezone: America/Sao_Paulo

   Settings → Users & Companies → Companies:
   - Logo: Upload company logo
   - Address: Fill in complete address
   - Tax ID: CNPJ
   ```

### Method 2: Via Docker Command Line

```bash
# 1. Access Odoo container
docker exec -it odoo_community_18 bash

# 2. Create database with Odoo CLI
odoo -d tenant_jewelry_newstore \
  --db_user=odoo \
  --db_password=odoo_test_123 \
  --db_host=odoo_postgres \
  --without-demo=all \
  --stop-after-init

# 3. Install jewelry template
odoo -d tenant_jewelry_newstore \
  -i jewelry_template \
  --stop-after-init

# 4. Exit container
exit
```

### Method 3: Via PostgreSQL Backup Restore

```bash
# Clone an existing tenant database
docker exec odoo_postgres pg_dump -U odoo tenant_joiasmax > tenant_backup.sql

# Create new database
docker exec odoo_postgres psql -U odoo -c "CREATE DATABASE tenant_jewelry_newstore;"

# Restore backup to new database
cat tenant_backup.sql | docker exec -i odoo_postgres psql -U odoo tenant_jewelry_newstore

# Update company information in new database (via Odoo UI)
```

---

## 📊 Managing Existing Tenants

### Accessing a Tenant

```bash
# Via web interface
URL: http://localhost:8069
# You'll be prompted to select database if multiple exist

# Specify database in URL
URL: http://localhost:8069/web?db=tenant_joiasmax

# Via database manager
URL: http://localhost:8069/web/database/manager
```

### Switching Between Tenants

```bash
# Method 1: Logout and login to different database
# Odoo UI → User Menu → Logout
# Login page will show database selector

# Method 2: Direct database URL
http://localhost:8069/web?db=tenant_jewelry_store1
http://localhost:8069/web?db=tenant_retail_shop1

# Method 3: Database manager
http://localhost:8069/web/database/manager
```

### Tenant Database Operations

#### Backup Tenant Database

```bash
# Backup specific tenant
docker exec odoo_postgres pg_dump -U odoo tenant_joiasmax > \
  backup_joiasmax_$(date +%Y%m%d_%H%M%S).sql

# Backup all tenant databases
docker exec odoo_postgres pg_dumpall -U odoo > \
  backup_all_tenants_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker exec odoo_postgres pg_dump -U odoo tenant_joiasmax | \
  gzip > backup_joiasmax_$(date +%Y%m%d).sql.gz
```

#### Restore Tenant Database

```bash
# Restore from backup
cat backup_joiasmax_20260107.sql | \
  docker exec -i odoo_postgres psql -U odoo tenant_joiasmax

# Restore compressed backup
gunzip -c backup_joiasmax_20260107.sql.gz | \
  docker exec -i odoo_postgres psql -U odoo tenant_joiasmax
```

#### Delete Tenant Database

```bash
# ⚠️ WARNING: This permanently deletes all tenant data!

# Via database manager (recommended)
# http://localhost:8069/web/database/manager
# Select database → Delete → Confirm master password

# Via PostgreSQL command
docker exec odoo_postgres psql -U odoo -c \
  "DROP DATABASE tenant_joiasmax;"
```

---

## 📦 Importing Product Catalogs

### For JoiasMax Jewelry Tenant

#### Quick Re-Import Process

**Scenario:** You deleted sample products and want to reimport them

```bash
# 1. Navigate to import directory
cd addons/tenant_templates/jewelry_template/import

# 2. Verify you have the CSV file
ls -lh /path/to/produtos_bling.csv

# 3. Run import
python import_products.py \
  --csv /path/to/produtos_bling.csv \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_admin_password

# 4. Verify import
python verify_import_results.py \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_admin_password

# 5. Check validation report
cat VALIDATION_SUMMARY.md
```

#### Full Import Guide

See detailed documentation:
- [Jewelry Template Import Guide](../../addons/tenant_templates/jewelry_template/import/README.md)
- [Tenant Templates Overview](../../addons/tenant_templates/README.md)

#### CSV File Location

```bash
# Check if you have the original Bling export
find /d/Programacao -name "*bling*.csv" -o -name "*produtos*.csv"

# Common locations:
# - Downloads folder
# - Export folder in project
# - Backup directory
```

#### Re-Import After Deleting Products

**Step-by-Step:**

```bash
# 1. Delete existing products (if needed)
cd addons/tenant_templates/jewelry_template/import
python delete_imported_products.py \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_password

# Confirm deletion when prompted:
# "This will delete all imported products. Are you sure? (yes/no): yes"

# 2. Re-import from CSV
python import_products.py \
  --csv /path/to/produtos_bling.csv \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_password

# 3. Validate results
python verify_import_results.py \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_password
```

---

## 🔧 Tenant Maintenance

### Regular Maintenance Tasks

#### Daily Tasks
```bash
# Check container health
docker ps | grep odoo

# Monitor disk usage
docker exec odoo_postgres psql -U odoo -c \
  "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname))
   FROM pg_database WHERE datname LIKE 'tenant_%';"

# View recent logs
docker logs --tail=50 odoo_community_18
```

#### Weekly Tasks
```bash
# Backup all tenant databases
./scripts/backup_tenants.sh

# Update Odoo modules
docker exec odoo_community_18 odoo -d tenant_joiasmax \
  -u jewelry_template --stop-after-init

# Vacuum database for performance
docker exec odoo_postgres psql -U odoo -c \
  "VACUUM ANALYZE;" tenant_joiasmax
```

#### Monthly Tasks
```bash
# Review and clean old log files
docker logs odoo_community_18 > odoo_logs_$(date +%Y%m).log
docker logs odoo_postgres > postgres_logs_$(date +%Y%m).log

# Update market prices (for jewelry tenants)
# Via Odoo UI: Jewelry → Configuration → Market Prices → Update

# Review user access and permissions
# Via Odoo UI: Settings → Users & Companies → Users
```

### Performance Optimization

#### Database Maintenance
```bash
# Reindex database
docker exec odoo_postgres psql -U odoo tenant_joiasmax -c "REINDEX DATABASE tenant_joiasmax;"

# Analyze database statistics
docker exec odoo_postgres psql -U odoo tenant_joiasmax -c "ANALYZE;"

# Check database size
docker exec odoo_postgres psql -U odoo -c \
  "SELECT pg_size_pretty(pg_database_size('tenant_joiasmax'));"
```

#### Clear Odoo Cache
```bash
# Restart Odoo to clear cache
docker restart odoo_community_18

# Or via Odoo UI:
# Settings → Technical → Database Structure → Clear Cache
```

### Module Updates

```bash
# Update specific module
docker exec odoo_community_18 odoo -d tenant_joiasmax \
  -u jewelry_template --stop-after-init

# Update all modules
docker exec odoo_community_18 odoo -d tenant_joiasmax \
  -u all --stop-after-init
```

---

## 🛠️ Troubleshooting

### Common Tenant Issues

#### 1. Cannot Access Tenant Database

**Symptoms:**
- Login page doesn't show database
- "Database not found" error
- Redirect to database manager

**Solutions:**
```bash
# Check database exists
docker exec odoo_postgres psql -U odoo -c "\l" | grep tenant

# Check Odoo can see database
docker logs odoo_community_18 | grep "available databases"

# Verify database filtering (in odoo.conf)
dbfilter = ^%d$
list_db = True

# Restart Odoo
docker restart odoo_community_18
```

#### 2. Template Module Not Working

**Symptoms:**
- Missing jewelry menu items
- Product fields not showing
- Pricing automation not working

**Solutions:**
```bash
# Check module is installed
docker exec odoo_postgres psql -U odoo tenant_joiasmax -c \
  "SELECT name, state FROM ir_module_module WHERE name = 'jewelry_template';"

# Reinstall module
docker exec odoo_community_18 odoo -d tenant_joiasmax \
  -i jewelry_template --stop-after-init

# Update module
docker exec odoo_community_18 odoo -d tenant_joiasmax \
  -u jewelry_template --stop-after-init
```

#### 3. Import Script Fails

**Symptoms:**
- "Authentication failed"
- "Module not found"
- "Database not accessible"

**Solutions:**
```bash
# Verify Odoo is running
docker ps | grep odoo
curl -I http://localhost:8069

# Test database connection
docker exec odoo_postgres psql -U odoo tenant_joiasmax -c "SELECT 1;"

# Verify credentials
# Login to Odoo UI with same username/password

# Check import script is in correct directory
cd addons/tenant_templates/jewelry_template/import
ls -lh import_products.py

# See detailed troubleshooting:
# addons/tenant_templates/jewelry_template/import/README.md
```

#### 4. Products Not Showing After Import

**Symptoms:**
- Import completes but products not visible
- Empty product list in Odoo

**Solutions:**
```bash
# Check products in database
docker exec odoo_postgres psql -U odoo tenant_joiasmax -c \
  "SELECT COUNT(*) FROM product_template;"

# Verify category filter
# Odoo UI: Products → Remove all filters

# Run validation script
cd addons/tenant_templates/jewelry_template/import
python verify_import_results.py \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_password

# Check VALIDATION_SUMMARY.md for details
cat VALIDATION_SUMMARY.md
```

#### 5. Pricing Automation Not Working

**Symptoms:**
- Prices not updating when market prices change
- Cost calculations incorrect
- Margin shows as 0%

**Solutions:**
```bash
# Check market prices are set
# Odoo UI: Jewelry → Configuration → Market Prices

# Verify jewelry pricing records exist
docker exec odoo_postgres psql -U odoo tenant_joiasmax -c \
  "SELECT COUNT(*) FROM joiasmax_product_pricing;"

# Check product has pricing link
# Odoo UI: Product → Jewelry tab → Pricing record should be set

# Manually trigger price update
# Odoo UI: Jewelry → Configuration → Market Prices → Update Market Prices

# Check provider indices are set
# Odoo UI: Products → Jewelry tab → Provider Index should be > 0
```

---

## 📚 Related Documentation

### Essential Reading

1. **[Project Overview (CLAUDE.md)](../../CLAUDE.md)**
   - Project architecture and structure
   - Docker deployment guide
   - Troubleshooting and best practices

2. **[Tenant Templates Guide](../../addons/tenant_templates/README.md)**
   - Available business templates
   - Installation and configuration
   - Template features overview

3. **[Jewelry Template Import Guide](../../addons/tenant_templates/jewelry_template/import/README.md)**
   - Detailed CSV import instructions
   - Python script reference
   - Advanced import features

### Quick Reference Links

| Topic | Documentation |
|-------|--------------|
| **Docker Operations** | [CLAUDE.md - Docker Compose Best Practices](../../CLAUDE.md#docker-compose-best-practices) |
| **Product Import** | [Jewelry Import README](../../addons/tenant_templates/jewelry_template/import/README.md) |
| **Template Features** | [Tenant Templates README](../../addons/tenant_templates/README.md) |
| **Troubleshooting** | [CLAUDE.md - Troubleshooting](../../CLAUDE.md#troubleshooting) |

---

## 🆘 Getting Help

### Self-Service Resources

1. **Check Documentation**
   - Read CLAUDE.md for project overview
   - Review template README files
   - Check import guide for CSV issues

2. **Run Diagnostics**
   ```bash
   # Check system status
   docker ps
   docker stats

   # Verify database
   docker exec odoo_postgres psql -U odoo -c "\l"

   # Check logs
   docker logs odoo_community_18 | tail -50
   docker logs odoo_postgres | tail -50
   ```

3. **Validation Scripts**
   ```bash
   # Verify import results
   cd addons/tenant_templates/jewelry_template/import
   python verify_import_results.py ...

   # Check VALIDATION_SUMMARY.md
   cat VALIDATION_SUMMARY.md
   ```

### Getting Support

**For Import Issues:**
- Check: [Import README Troubleshooting](../../addons/tenant_templates/jewelry_template/import/README.md#troubleshooting)
- Include: Error messages, CSV sample, validation report

**For Tenant Issues:**
- Check: [CLAUDE.md Troubleshooting](../../CLAUDE.md#troubleshooting)
- Include: Docker logs, database name, steps to reproduce

**Contact:**
- Email: support@maxhaider.dev
- GitHub Issues: [odoo-platform/issues](https://github.com/your-org/odoo-platform/issues)

---

## 📝 Tenant Operations Cheat Sheet

```bash
# === CREATE TENANT ===
# Via UI: http://localhost:8069/web/database/manager
# Database: tenant_newstore, Install: jewelry_template

# === BACKUP TENANT ===
docker exec odoo_postgres pg_dump -U odoo tenant_joiasmax > backup_$(date +%Y%m%d).sql

# === RESTORE TENANT ===
cat backup.sql | docker exec -i odoo_postgres psql -U odoo tenant_joiasmax

# === IMPORT PRODUCTS ===
cd addons/tenant_templates/jewelry_template/import
python import_products.py --csv produtos.csv --url http://localhost:8069 \
  --db tenant_joiasmax --username admin --password admin123

# === VERIFY IMPORT ===
python verify_import_results.py --url http://localhost:8069 \
  --db tenant_joiasmax --username admin --password admin123

# === DELETE PRODUCTS ===
python delete_imported_products.py --url http://localhost:8069 \
  --db tenant_joiasmax --username admin --password admin123

# === CHECK DATABASE SIZE ===
docker exec odoo_postgres psql -U odoo -c \
  "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname))
   FROM pg_database WHERE datname LIKE 'tenant_%';"

# === RESTART ODOO ===
docker restart odoo_community_18

# === VIEW LOGS ===
docker logs --tail=100 -f odoo_community_18
```

---

**Last Updated**: 2026-01-07
**Platform Version**: 18.0.1.0
**Multi-Tenant Support**: Active
