# Odoo Multi-Tenant Platform - Troubleshooting Guide

> **Navigation**: [TABLE-OF-CONTENTS.md](TABLE-OF-CONTENTS.md) | [AGENT-CONTEXT.md](AGENT-CONTEXT.md)

## Table of Contents

1. [Container Deployment Issues](#container-deployment-issues)
2. [Configuration Strategy](#configuration-strategy)
3. [Validation Commands](#validation-commands)
4. [Common Issues](#common-issues)
5. [Log Locations](#log-locations)
6. [Emergency Recovery](#emergency-recovery)

---

## Container Deployment Issues (Critical Lessons Learned)

### ✅ HTTP Server Not Starting

**Problem**: Odoo loads successfully but HTTP server doesn't start

**Root Cause**: Complex configuration files with conflicting parameters

**Solution**: Use minimal configuration approach

```ini
# Use configs/odoo/odoo-minimal.conf for initial deployment
[options]
db_host = odoo_postgres
db_port = 5432
db_user = odoo
db_password = odoo_test_123
db_name = odoo_master
http_interface = 0.0.0.0
http_port = 8069
workers = 0
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
data_dir = /var/lib/odoo
admin_passwd = admin
dbfilter = ^%d$
list_db = True
lang = pt_BR
```

### ✅ Docker Entrypoint Override Issues

**Problem**: Configuration file not being read despite proper mounting

**Solution**: Bypass Docker entrypoint in docker-compose.yml

```yaml
services:
  odoo:
    entrypoint: []
    command: ["python3", "/usr/bin/odoo", "-c", "/etc/odoo/odoo.conf"]
```

### ✅ Configuration Parameter Conflicts

**Key Settings for Docker Containers**:

- `workers = 0` (Essential - multi-threaded mode for containers)
- `proxy_mode = False` (For local testing - True only for production with reverse proxy)
- Avoid duplicate parameters or complex settings during initial deployment

### ✅ Database Manager Master Password

**Expected Behavior**: First access shows master password generation

```
Warning, your Odoo database manager is not protected.
To secure it, we have generated the following master password: hb95-qw5c-4j3d
```

**Action**: This is normal security behavior, not an error. Save the password.

---

## Configuration Strategy

### Development vs Production Approach

1. **Development/Testing**: Use `odoo-minimal.conf` with essential parameters only
2. **Production**: Use full `odoo.conf` after validating minimal setup works
3. **Staging**: Test with production config in isolated environment

### Proven Working Configuration Steps

1. Start with minimal configuration
2. Verify HTTP server starts: `docker logs odoo_community_18 | grep "HTTP service"`
3. Test frontend access: `curl -I http://localhost:8069`
4. Expected response: `HTTP/1.1 303 SEE OTHER` redirect to `/odoo`
5. Gradually add advanced configuration parameters

---

## Validation Commands

### Container Health Check

```bash
# Check containers are running
docker ps

# Verify HTTP server startup
docker logs odoo_community_18 | grep "HTTP service"

# Test frontend connectivity
curl -I http://localhost:8069

# Check database connectivity
docker exec odoo_postgres pg_isready -U odoo
```

### Expected Success Indicators

- ✅ `HTTP service (werkzeug) running on :8069` in logs
- ✅ `HTTP/1.1 303 SEE OTHER` response from curl
- ✅ Database manager loads at http://localhost:8069
- ✅ Master password generation prompt appears

---

## Common Issues

### Database Connection

**Symptoms**: Odoo can't connect to PostgreSQL

**Diagnosis**:
```bash
# Check PostgreSQL container
docker ps | grep postgres

# Test database connection
docker exec odoo_postgres pg_isready -U odoo

# Check credentials
docker exec -it odoo_postgres psql -U odoo -c "SELECT version();"
```

**Solutions**:
- Verify PostgreSQL container is running
- Check database credentials in `.env` file
- Ensure `db_host` in odoo.conf matches container name
- Wait 10-15 seconds after PostgreSQL starts before starting Odoo

### N8N Integration

**Symptoms**: Webhooks not triggering, automation not working

**Diagnosis**:
```bash
# Test webhook endpoint
curl -X POST https://n8n.maxhaider.dev/webhook/test

# Check N8N logs
docker logs n8n_container
```

**Solutions**:
- Verify N8N_WEBHOOK_URL in `.env` is correct
- Check API key authentication
- Test webhook manually with curl
- Verify network connectivity between containers

### Gold Price Updates (Jewelry Template)

**Symptoms**: Product prices not updating when gold market price changes

**Diagnosis**:
```bash
cd addons/tenant_templates/jewelry_template/import

# Check market price exists
python3 check_market_price.py --db tenant_joiasmax --password admin

# Check product configuration
python3 check_product_config.py --sku C725R --db tenant_joiasmax --password admin
```

**Solutions**:
- Ensure market price record exists in database
- Verify product has `has_size_based_pricing = True`
- Check jewelry_pricing_id is linked
- Force recomputation: `python3 trigger_cost_recompute.py`

### Tenant Isolation

**Symptoms**: Tenants can see each other's data

**Diagnosis**:
```bash
# Check security rules
docker exec -it odoo_postgres psql -U odoo -d odoo_master -c "SELECT * FROM ir_rule WHERE model_id IN (SELECT id FROM ir_model WHERE model LIKE 'joiasmax%');"

# Check tenant_id values
docker exec -it odoo_postgres psql -U odoo -d tenant_store_1 -c "SELECT DISTINCT tenant_id FROM joiasmax_jewelry_pricing;"
```

**Solutions**:
- Verify Row-Level Security (RLS) rules are active
- Check `tenant_id` field exists on all custom models
- Ensure database routing is configured correctly
- Validate `dbfilter` parameter in odoo.conf

### Configuration Conflicts

**Symptoms**: HTTP server won't start, or strange behavior

**Diagnosis**:
```bash
# View active configuration
docker exec odoo_community_18 cat /etc/odoo/odoo.conf

# Check for parameter conflicts
docker exec odoo_community_18 grep -E "(workers|proxy_mode|dbfilter)" /etc/odoo/odoo.conf
```

**Solutions**:
- Use minimal config first (`odoo-minimal.conf`)
- Remove duplicate parameters
- Set `workers = 0` for development
- Avoid complex settings during initial setup

### HTTP Server Startup

**Symptoms**: Container runs but no HTTP service

**Diagnosis**:
```bash
# Check logs for HTTP service
docker logs odoo_community_18 | grep "HTTP service"

# Check if process is running
docker exec odoo_community_18 ps aux | grep odoo

# Check port binding
docker exec odoo_community_18 netstat -tlnp | grep 8069
```

**Solutions**:
- Use `odoo-minimal.conf` configuration
- Bypass Docker entrypoint (see solution above)
- Verify `http_port = 8069` in configuration
- Check for port conflicts on host

---

## Log Locations

### Docker Logs

```bash
# Odoo logs
docker-compose logs odoo

# PostgreSQL logs
docker-compose logs odoo_postgres

# Specific time range
docker-compose logs --since 30m odoo

# Follow logs in real-time
docker-compose logs -f --tail=100 odoo
```

### Container Logs

```bash
# Inside container
docker exec odoo_community_18 cat /var/log/odoo/odoo.log

# Odoo server logs
docker exec odoo_community_18 cat /var/log/odoo/odoo-server.log
```

### N8N Integration Logs

- Available in N8N dashboard
- Workflow execution history shows webhook calls
- Error logs show failed automations

### Traefik Routing Logs

- Shared VPS Traefik service logs
- Shows routing decisions and SSL certificate status

---

## Emergency Recovery

### If Deployment Fails

```bash
# Stop all containers
docker-compose down

# Switch to minimal config
# Edit docker-compose.yml: use odoo-minimal.conf

# Clean restart
docker-compose up -d

# Verify with validation commands
docker ps
docker logs odoo_community_18 | grep "HTTP service"
curl -I http://localhost:8069
```

### Complete System Reset

**⚠️ WARNING: This destroys all data**

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove all Docker images
docker system prune -af

# Start fresh
docker-compose up -d
```

### Database Recovery

```bash
# Stop Odoo
docker-compose stop odoo

# Restore database from backup
docker exec -i odoo_postgres psql -U odoo < backup_all_20260112.sql

# Restart Odoo
docker-compose start odoo
```

### Corrupt Configuration Recovery

```bash
# Copy working minimal config
cp configs/odoo/odoo-minimal.conf configs/odoo/odoo.conf

# Restart containers
docker-compose restart odoo

# Gradually add back custom configuration
```

---

## Import-Specific Troubleshooting

### Variant Costs = 0

**Cause**: No market price in database

**Fix**:
```bash
cd addons/tenant_templates/jewelry_template/import
python3 check_market_price.py --db tenant_joiasmax --password admin

# If no price found, insert one
python3 -c "import xmlrpc.client; models = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/object'); models.execute_kw('tenant_joiasmax', 1, 'admin', 'joiasmax.market.price', 'create', [[{'material_type': 'gold_24k', 'price_per_gram_brl': 700.0, 'is_active': True}]])"
```

### Import Fails "Product Not Found"

**Cause**: SKU mismatch between CSV and Odoo

**Fix**:
```bash
# Check product default_code
docker exec -it odoo_postgres psql -U odoo -d tenant_joiasmax -c "SELECT id, name, default_code FROM product_template WHERE default_code LIKE '%C725R%';"

# Update default_code if needed
docker exec -it odoo_postgres psql -U odoo -d tenant_joiasmax -c "UPDATE product_template SET default_code = 'C725R' WHERE id = 123;"
```

### Duplicate Products on Reimport

**Cause**: No External ID used

**Fix**: Scripts now use External IDs by default. If using old scripts:
```bash
# Use bulk import script (has External ID support)
python3 bulk_import_cpl_products.py --csv products.csv --db tenant_joiasmax --password admin
```

---

**Related Documentation**:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment procedures
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflows
- [MULTI-TENANT-OPERATIONS.md](MULTI-TENANT-OPERATIONS.md) - Tenant management
- [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) - Jewelry-specific troubleshooting

**Last Updated**: 2026-01-12
