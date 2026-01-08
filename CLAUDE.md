# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Multi-Tenant Odoo 18 Community Platform** that serves as a foundational base for deploying Odoo 18.0 Community Edition across multiple business types and industries. The platform provides configurable tenant templates, automated business process integration, and scalable infrastructure for serving diverse client needs including retail, manufacturing, services, and specialized industries like jewelry.

## Architecture

### Core Components
- **Odoo 18.0 Community**: Multi-tenant ERP platform with configurable tenant templates
- **N8N Integration**: Automated business process workflows and external system synchronization
- **E-commerce Sync**: Bidirectional inventory, pricing, and order management with multiple platforms
- **Multi-Tenant Database**: PostgreSQL with tenant isolation via database sharding
- **Tenant Templates**: Pre-configured business modules for different industries (jewelry, retail, manufacturing, services)

### Key Integration Points
- **Automated Business Processes**: N8N workflows for industry-specific automation (pricing, inventory, notifications)
- **Tenant-Specific Configurations**: Custom business rules, pricing strategies, and workflows per client
- **Real-time Synchronization**: Odoo ↔ E-commerce platforms (WooCommerce, Shopify, etc.)
- **VPS Infrastructure**: Leverages existing monitoring stack (Prometheus, Grafana, Traefik)
- **Scalable Architecture**: Easy onboarding of new tenants with pre-built templates

## Directory Structure

```
odoo-multitenant-platform/
├── context/                              # Project documentation
│   ├── 1_odoo_project_guide.md         # Strategic project overview
│   └── 2_odoo_implementation_guide.md  # Technical implementation details
├── docker-compose.yml                   # Multi-tenant Odoo deployment
├── configs/                             # Configuration files
│   ├── odoo/odoo.conf                  # Odoo server configuration
│   └── postgres/                       # Database initialization
├── scripts/                            # Deployment and migration scripts
├── addons/                             # Custom Odoo modules
│   ├── multi_tenant_core/              # Core multi-tenancy functionality
│   ├── n8n_connector/                  # N8N integration module
│   ├── tenant_templates/               # Industry-specific tenant templates
│   │   ├── base_template/              # Base tenant configuration
│   │   ├── jewelry_template/           # Jewelry store template
│   │   ├── retail_template/            # General retail template
│   │   ├── manufacturing_template/     # Manufacturing template
│   │   └── services_template/          # Service business template
│   ├── automation_workflows/           # Industry-specific automation
│   │   ├── pricing_automation/         # Dynamic pricing (gold, market-based)
│   │   ├── inventory_sync/             # Multi-platform inventory sync
│   │   └── notification_systems/      # Automated alerts and notifications
│   └── integration_modules/            # External system connectors
│       ├── woocommerce_connector/      # WooCommerce integration
│       ├── shopify_connector/          # Shopify integration
│       └── api_gateway/                # Unified API access
├── tenant_configs/                     # Per-tenant configurations
│   ├── tenant_jewelry_store_1/         # Example jewelry store config
│   └── tenant_retail_shop_1/           # Example retail shop config
└── exports/                           # Data migration and backup files
```

## 🚀 Quick Start (Minimal Configuration)

### Prerequisites
- Docker and Docker Compose installed
- Git for cloning the repository
- 4GB+ RAM available for containers

### Step-by-Step Deployment

#### 1. Clone and Setup
```bash
git clone <repository-url> odoo-platform
cd odoo-platform
cp .env.example .env  # Configure environment variables
```

#### 2. Start with Minimal Configuration (Recommended)
The project includes both full production configuration and a proven minimal configuration for quick setup:

```bash
# Quick deployment using minimal configuration (default)
docker-compose up -d

# Check deployment status
docker ps
docker logs odoo_community_18 | grep "HTTP service"
```

#### 3. Verify Installation
```bash
# Test HTTP connectivity (should return HTTP 303 redirect)
curl -I http://localhost:8069

# Expected success indicators:
# ✅ Container shows "HTTP service (werkzeug) running on :8069"
# ✅ curl returns "HTTP/1.1 303 SEE OTHER"
# ✅ Web interface accessible at http://localhost:8069
```

#### 4. Access Odoo Database Manager
1. Open browser: http://localhost:8069
2. You'll see master password generation (this is normal):
   ```
   Warning, your Odoo database manager is not protected.
   To secure it, we have generated the following master password: [generated-password]
   ```
3. **Save this password** - it's required for database operations
4. Create your first database or tenant

#### 5. Configuration Files Used
- **Development**: `configs/odoo/odoo-minimal.conf` (default, proven working)
- **Production**: `configs/odoo/odoo.conf` (full configuration, use after validation)

### Troubleshooting Quick Start
If HTTP server doesn't start:
1. Check logs: `docker logs odoo_community_18`
2. Ensure using minimal configuration (default setup)
3. Verify no port conflicts: `netstat -tlnp | grep 8069`
4. Emergency recovery: `docker-compose down && docker-compose up -d`

### Next Steps
- Create tenant databases via web interface
- Configure business-specific templates
- Set up N8N automation workflows
- Deploy to production VPS (see VPS Integration section)

## 🐳 Docker Compose Best Practices

### Environment-Specific Deployments

#### Development Environment
```bash
# Use development configuration with debugging features
docker-compose -f docker-compose.yml -f docker-compose.development.yml up -d

# Features enabled:
# - Auto-reload for code changes
# - Debug mode and detailed logging
# - Permissive database filtering
# - Demo data included
# - Read-write volume mounts for development
```

#### Staging Environment
```bash
# Use staging configuration for pre-production testing
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Features:
# - Production-like performance settings (reduced resources)
# - Worker processes enabled for performance testing
# - Security settings active
# - No demo data
# - Basic Traefik routing for staging domain
```

#### Production Environment
```bash
# Use base docker-compose.yml with production configuration
docker-compose up -d

# Automatically uses:
# - configs/odoo/odoo.conf (minimal, proven configuration)
# - Full Traefik labels for multi-tenant routing
# - Optimized resource limits
# - Security headers and SSL configuration
```

### Configuration File Management

#### Switching Configurations
```bash
# Method 1: Use environment-specific docker-compose files (recommended)
docker-compose -f docker-compose.yml -f docker-compose.development.yml up -d

# Method 2: Manual configuration switching
docker-compose down
# Edit docker-compose.yml to change config file path
# - ./configs/odoo/odoo-development.conf:/etc/odoo/odoo.conf:ro
docker-compose up -d
```

#### Configuration Validation
```bash
# Before deploying, validate configuration syntax
docker-compose config

# Test with minimal config first (reduces troubleshooting)
# Then gradually switch to more complex configurations

# Verify HTTP server startup
docker logs odoo_community_18 | grep "HTTP service"
```

### Volume Management Best Practices

#### Development Volumes (Read-Write)
```yaml
volumes:
  # Allow real-time code changes
  - ./addons/custom_module:/mnt/extra-addons/custom_module
  - ./configs/odoo/odoo-development.conf:/etc/odoo/odoo.conf:ro
```

#### Production Volumes (Read-Only)
```yaml
volumes:
  # Prevent accidental modifications
  - ./addons/multi_tenant_core:/mnt/extra-addons/multi_tenant_core:ro
  - ./configs/odoo/odoo.conf:/etc/odoo/odoo.conf:ro
```

### Essential Docker Commands

#### Container Management
```bash
# Start services
docker-compose up -d

# View all containers status
docker-compose ps

# Check resource usage
docker stats

# View logs with timestamps
docker-compose logs -f --timestamps odoo

# Restart specific service
docker-compose restart odoo

# Stop all services
docker-compose down
```

#### Debugging and Maintenance
```bash
# Execute commands inside container
docker exec -it odoo_community_18 bash

# Check Odoo process inside container
docker exec odoo_community_18 ps aux

# Database operations
docker exec -it odoo_postgres psql -U odoo -d odoo_master

# Copy files to/from container
docker cp odoo_community_18:/var/lib/odoo/filestore ./backups/

# Inspect container configuration
docker inspect odoo_community_18
```

### Network Configuration

#### Local Development
```yaml
networks:
  # Override external network for local testing
  monitoring_shared_monitoring_network:
    external: false
    driver: bridge
```

#### Production Integration
```yaml
networks:
  # Use shared VPS monitoring network
  monitoring_shared_monitoring_network:
    external: true
    name: monitoring_shared_monitoring_network
```

### Security Best Practices

#### Secrets Management
```bash
# Use .env file for sensitive data
echo "ODOO_DB_PASSWORD=secure_password" >> .env
echo "ODOO_ADMIN_PASSWORD=admin_secure_password" >> .env

# Never commit passwords to version control
echo ".env" >> .gitignore
```

#### Container Security
```yaml
# Run containers as non-root user
services:
  odoo:
    user: odoo  # Default Odoo user

  # Limit container resources
  deploy:
    resources:
      limits:
        cpus: '0.7'
        memory: 1024M
```

### Performance Optimization

#### Resource Allocation Strategy
- **Development**: Generous resources for debugging (2GB RAM, 1 CPU)
- **Staging**: Production-like but reduced (1.5GB RAM, 0.8 CPU)
- **Production**: Optimized for VPS constraints (1GB RAM, 0.7 CPU)

#### Monitoring Container Health
```bash
# Check container resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Monitor container restarts
docker-compose ps

# Check container logs for errors
docker-compose logs --tail=50 odoo | grep -i error
```

### Backup and Recovery

#### Data Backup
```bash
# Backup PostgreSQL data
docker exec odoo_postgres pg_dumpall -U odoo > backup_all_$(date +%Y%m%d).sql

# Backup Odoo file storage
docker run --rm -v odoo_platform_data:/data -v $(pwd):/backup busybox tar czf /backup/odoo_files_$(date +%Y%m%d).tar.gz /data

# Backup custom addons
tar czf addons_backup_$(date +%Y%m%d).tar.gz ./addons/
```

#### Emergency Recovery
```bash
# Complete reset (CAREFUL: destroys all data)
docker-compose down -v
docker system prune -f
docker-compose up -d

# Restore from backup
docker exec -i odoo_postgres psql -U odoo < backup_all_20231201.sql
```

## Development Commands

### Docker Deployment
```bash
# Deploy Odoo platform
cd ~/odoo-platform
docker-compose up -d

# View logs
docker-compose logs -f odoo

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up --build -d
```

### Database Management
```bash
# Connect to Odoo PostgreSQL
docker exec -it odoo_postgres psql -U odoo -d odoo_master

# Create new tenant database
docker exec -it odoo_postgres psql -U odoo -c "CREATE DATABASE tenant_new_store;"

# Backup tenant database
docker exec odoo_postgres pg_dump -U odoo tenant_store_1 > backup_store_1.sql
```

### Data Migration
```bash
# Export WooCommerce data
cd ~/odoo-platform/scripts
python3 export_woocommerce.py

# Transform data for Odoo
python3 transform_data.py

# Import data to Odoo (via web interface or API)
```

### Monitoring
```bash
# Check container health
docker ps
docker stats

# View Odoo health endpoint
curl https://odoo.maxhaider.dev/web/health

# Monitor N8N integration
curl https://n8n.maxhaider.dev/webhook/health
```

## Key Configuration Files

### Environment Variables (.env)
- `ODOO_DB_PASSWORD`: PostgreSQL password for Odoo
- `ODOO_ADMIN_PASSWORD`: Odoo admin interface password
- `N8N_WEBHOOK_URL`: N8N webhook endpoint for integrations
- `WOOCOMMERCE_*`: WooCommerce API credentials for synchronization
- `GOLD_PRICE_API_KEY`: API key for gold price monitoring

### Odoo Configuration (configs/odoo/odoo.conf)
- Multi-tenant database configuration
- Performance settings for VPS resource constraints
- N8N integration endpoints
- Brazilian localization settings

## Multi-Tenant Architecture

### Tenant Management
- Each client business has a separate database (`tenant_{business_type}_{name}`)
- Tenant routing via subdomain: `tenant-name.odoo.maxhaider.dev`
- API access: `api.odoo.maxhaider.dev/tenant/{tenant-id}`
- Isolated data, configurations, and business rules per tenant
- Template-based tenant creation for rapid onboarding

### Database Structure
- Master database: `odoo_master` (tenant management, shared configurations, templates)
- Tenant databases: `tenant_{business_type}_{name}` (isolated client data)
- Template databases: `template_{business_type}` (template configurations for quick tenant creation)
- Shared PostgreSQL instance on port 5433 (separate from existing services)

### Tenant Templates
- **Base Template**: Core Odoo functionality for any business type
- **Jewelry Template**: Specialized for jewelry stores (gold pricing, gemstone management)
- **Retail Template**: General retail operations (inventory, POS, e-commerce)
- **Manufacturing Template**: Production workflows, BOM, quality control
- **Services Template**: Service-based businesses, project management, time tracking

## N8N Integration Workflows

### Automated Business Process Workflows
- **Industry-Specific Automation**: Configurable workflows per business type
- **Price Management**: Dynamic pricing based on market data, cost changes, competitive analysis
- **Inventory Synchronization**: Multi-platform inventory management across e-commerce channels
- **Order Processing**: Automated order routing and fulfillment workflows
- **Notification Systems**: Business alerts, low stock warnings, performance metrics

### E-commerce Platform Synchronization
- **Supported Platforms**: WooCommerce, Shopify, custom APIs
- **Bidirectional Sync**: Products, inventory levels, orders, customer data
- **Tenant Routing**: Intelligent routing based on business rules and configurations
- **Real-time Updates**: Webhook-based instant synchronization

### Example Workflows by Template:
- **Jewelry Template**: Gold price automation, gemstone inventory tracking
- **Retail Template**: Multi-channel inventory sync, promotional price updates
- **Manufacturing Template**: Raw material cost tracking, production scheduling
- **Services Template**: Project milestone notifications, time tracking integration

## Industry-Specific Features by Template

### Jewelry Template Features
- **Product Attributes**: Metal type/karat, weight, gemstone tracking, craftsmanship levels
- **Pricing Logic**: Automated precious metal price updates, material cost calculations
- **Inventory Management**: Certificate tracking, quality metrics, custom piece workflows

### Retail Template Features
- **Product Variants**: Size, color, style management across multiple channels
- **Pricing Strategies**: Competitive pricing, promotional campaigns, bulk discounts
- **Multi-channel Operations**: POS integration, e-commerce sync, marketplace management

### Manufacturing Template Features
- **BOM Management**: Bill of materials, component tracking, cost analysis
- **Production Planning**: Workflow automation, capacity planning, quality control
- **Supply Chain**: Vendor management, procurement automation, lead time optimization

### Services Template Features
- **Project Management**: Task tracking, milestone management, time billing
- **Resource Planning**: Staff allocation, capacity management, service delivery
- **Client Management**: Service contracts, recurring billing, performance tracking

### Configurable Business Rules
- Per-tenant pricing strategies and markup rules
- Industry-specific automation workflows
- Custom notification and alert systems
- Compliance and reporting requirements per business type

## Development Guidelines

### Adding New Tenants
1. Choose appropriate business template (jewelry, retail, manufacturing, services)
2. Create tenant database: `CREATE DATABASE tenant_{business_type}_{name};`
3. Initialize with template: `./scripts/create-tenant.sh --template=jewelry --name=store1`
4. Configure subdomain routing in Traefik
5. Set up tenant-specific N8N workflow endpoints
6. Configure business-specific rules and automation

### Creating New Business Templates
1. Create template directory: `addons/tenant_templates/{new_template}/`
2. Define template modules and configurations
3. Create template database with pre-configured data
4. Document template-specific features and requirements
5. Add template to deployment scripts

### Custom Module Development
- Place modules in appropriate template directories or core addons
- Follow Odoo 18 development standards and multi-tenant best practices
- Include tenant isolation in all custom functionality
- Design for template reusability across different business types
- Integrate with N8N webhook framework for automation

### Testing
- Test multi-tenant isolation thoroughly
- Verify N8N workflow integrations
- Validate gold price calculation accuracy
- Test WooCommerce bidirectional sync

## Integration Endpoints

### Odoo APIs
- Products: `https://odoo.maxhaider.dev/api/v1/products`
- Tenants: `https://api.odoo.maxhaider.dev/tenant/{tenant-id}`
- Health: `https://odoo.maxhaider.dev/web/health`

### N8N Webhooks
- Gold price updates: `https://n8n.maxhaider.dev/webhook/gold-price-update`
- WooCommerce sync: `https://n8n.maxhaider.dev/webhook/woocommerce-sync`
- Tenant notifications: `https://n8n.maxhaider.dev/webhook/tenant/{tenant-id}`

## VPS Infrastructure Integration

### Shared Services
- **Monitoring**: Integrated with existing Prometheus/Grafana stack
- **SSL**: Automated via Traefik reverse proxy
- **Networking**: Uses monitoring_shared_monitoring_network (172.18.0.0/16)
- **Backups**: Extends existing VPS backup procedures

### Resource Allocation
- **Odoo Container**: 512MB RAM, 0.5 CPU cores
- **PostgreSQL**: 256MB RAM, 0.2 CPU cores
- **Port Usage**: 8069 (Odoo), 5433 (PostgreSQL)

## Troubleshooting

### Container Deployment Issues (Critical Lessons Learned)

#### ✅ HTTP Server Not Starting
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

#### ✅ Docker Entrypoint Override Issues
**Problem**: Configuration file not being read despite proper mounting
**Solution**: Bypass Docker entrypoint in docker-compose.yml

```yaml
services:
  odoo:
    entrypoint: []
    command: ["python3", "/usr/bin/odoo", "-c", "/etc/odoo/odoo.conf"]
```

#### ✅ Configuration Parameter Conflicts
**Key Settings for Docker Containers**:
- `workers = 0` (Essential - multi-threaded mode for containers)
- `proxy_mode = False` (For local testing - True only for production with reverse proxy)
- Avoid duplicate parameters or complex settings during initial deployment

#### ✅ Database Manager Master Password
**Expected Behavior**: First access shows master password generation
```
Warning, your Odoo database manager is not protected.
To secure it, we have generated the following master password: hb95-qw5c-4j3d
```
**Action**: This is normal security behavior, not an error. Save the password.

### Configuration Strategy

#### Development vs Production Approach
1. **Development/Testing**: Use `odoo-minimal.conf` with essential parameters only
2. **Production**: Use full `odoo.conf` after validating minimal setup works
3. **Staging**: Test with production config in isolated environment

#### Proven Working Configuration Steps
1. Start with minimal configuration
2. Verify HTTP server starts: `docker logs odoo_community_18 | grep "HTTP service"`
3. Test frontend access: `curl -I http://localhost:8069`
4. Expected response: `HTTP/1.1 303 SEE OTHER` redirect to `/odoo`
5. Gradually add advanced configuration parameters

### Common Issues
- **Database Connection**: Check PostgreSQL container health and credentials
- **N8N Integration**: Verify webhook URLs and API authentication
- **Gold Price Updates**: Monitor N8N workflow execution logs
- **Tenant Isolation**: Ensure proper database routing and access controls
- **Configuration Conflicts**: Use minimal config first, then add complexity
- **HTTP Server Startup**: Check for `HTTP service (werkzeug) running` in logs

### Validation Commands

#### Container Health Check
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

#### Expected Success Indicators
- ✅ `HTTP service (werkzeug) running on :8069` in logs
- ✅ `HTTP/1.1 303 SEE OTHER` response from curl
- ✅ Database manager loads at http://localhost:8069
- ✅ Master password generation prompt appears

### Log Locations
- Odoo logs: `docker-compose logs odoo`
- PostgreSQL logs: `docker-compose logs odoo_postgres`
- N8N integration logs: Available in N8N dashboard
- Traefik routing logs: Shared VPS Traefik service

### Emergency Recovery
If deployment fails:
1. Stop containers: `docker-compose down`
2. Switch to minimal config: Update docker-compose.yml to use `odoo-minimal.conf`
3. Clean restart: `docker-compose up -d`
4. Verify with validation commands above

## 📋 Multi-Tenant Setup Checklist

### Initial System Setup

#### ✅ 1. Infrastructure Validation
- [ ] Docker and Docker Compose installed
- [ ] 4GB+ RAM available for containers
- [ ] Port 8069 and 5433 available
- [ ] Network connectivity verified

#### ✅ 2. Basic Deployment
```bash
# Deploy with minimal configuration (proven working)
docker-compose up -d

# Verify success indicators
docker ps  # Both containers running
docker logs odoo_community_18 | grep "HTTP service"  # Should show: "running on :8069"
curl -I http://localhost:8069  # Should return: "HTTP/1.1 303 SEE OTHER"
```

#### ✅ 3. Database Manager Access
- [ ] Navigate to http://localhost:8069
- [ ] **SAVE the generated master password** (appears on first access)
- [ ] Database manager interface loads successfully

### Master Database Setup

#### ✅ 4. Create Master Database
```
Database Name: odoo_master
Admin Email: admin@yourdomain.com
Admin Password: [secure_password]
Country: Brazil
Language: Portuguese (Brazil)
☐ Load demonstration data: UNCHECKED (production)
```

#### ✅ 5. Install Core Multi-Tenant Modules
Navigate to Apps menu and install:
- [ ] `multi_tenant_core` - Core tenant management functionality
- [ ] `tenant_templates` - Business-type specific templates
- [ ] `n8n_connector` - Automation workflow integration (if using N8N)

#### ✅ 6. Configure System Settings
```
Settings > General Settings:
- [ ] Set company information
- [ ] Configure email settings (SMTP)
- [ ] Set timezone: America/Sao_Paulo
- [ ] Set currency: BRL (Brazilian Real)
```

### Tenant Management Setup

#### ✅ 7. Create Business Templates
For each business type, configure:

**Jewelry Store Template**:
- [ ] Product categories: Gold, Silver, Gemstones, Jewelry
- [ ] Units of measure: Grams, Carats, Pieces
- [ ] Price lists: Gold pricing, Retail pricing
- [ ] Inventory management: Serial numbers, lot tracking

**Retail Store Template**:
- [ ] Standard product categories
- [ ] Point of sale configuration
- [ ] E-commerce integration settings
- [ ] Basic accounting setup

**Manufacturing Template**:
- [ ] Bill of materials (BOM) setup
- [ ] Manufacturing workflows
- [ ] Quality control processes
- [ ] Production planning

#### ✅ 8. Create First Tenant Database
```
Tenant Configuration:
Database Name: tenant_jewelry_store_1
Business Type: Jewelry
Company Name: [Client Company Name]
Admin User: [client_admin@company.com]
Template: jewelry_template
```

#### ✅ 9. Configure Tenant-Specific Settings
- [ ] Upload company logo and branding
- [ ] Configure business-specific workflows
- [ ] Set up user roles and permissions
- [ ] Configure reporting preferences

### Advanced Multi-Tenant Features

#### ✅ 10. Domain-Based Routing (Production)
```yaml
# Configure Traefik labels for tenant subdomains
traefik.http.routers.odoo-tenant.rule=HostRegexp(`{tenant:[a-z0-9-]+}.odoo.maxhaider.dev`)
```

#### ✅ 11. Database Isolation Validation
- [ ] Test tenant database filtering: `dbfilter = ^%d$`
- [ ] Verify tenant data isolation
- [ ] Test backup and restore procedures for individual tenants

#### ✅ 12. Integration Setup (Optional)

**N8N Automation Workflows**:
- [ ] Gold price monitoring (for jewelry stores)
- [ ] Inventory synchronization
- [ ] Customer notifications
- [ ] Automated reporting

**E-commerce Integration**:
- [ ] WooCommerce connector setup
- [ ] Shopify connector setup
- [ ] Product synchronization testing
- [ ] Order management workflow

### Production Deployment Checklist

#### ✅ 13. Security Configuration
- [ ] Change default admin passwords
- [ ] Configure SSL certificates
- [ ] Set up database backup procedures
- [ ] Enable security headers and CORS

#### ✅ 14. Performance Optimization
- [ ] Configure worker processes for production
- [ ] Set memory limits based on VPS resources
- [ ] Monitor container performance
- [ ] Set up log rotation

#### ✅ 15. Monitoring and Maintenance
- [ ] Configure health checks
- [ ] Set up monitoring alerts
- [ ] Document tenant creation procedures
- [ ] Train staff on tenant management

### Tenant Onboarding Process

#### ✅ 16. New Client Onboarding Checklist
1. **Requirement Analysis**:
   - [ ] Identify business type (jewelry, retail, manufacturing, services)
   - [ ] Assess specific customization needs
   - [ ] Plan integration requirements

2. **Tenant Creation**:
   - [ ] Create tenant database using appropriate template
   - [ ] Configure business-specific settings
   - [ ] Set up user accounts and permissions

3. **Data Migration** (if applicable):
   - [ ] Export data from existing systems
   - [ ] Transform data to Odoo format
   - [ ] Import and validate data

4. **Testing and Validation**:
   - [ ] Test all business workflows
   - [ ] Validate integrations (e-commerce, automation)
   - [ ] User acceptance testing

5. **Go-Live**:
   - [ ] Configure production domain
   - [ ] Deploy to production environment
   - [ ] Monitor initial usage and performance

### Troubleshooting Multi-Tenant Issues

#### Common Problems and Solutions:

**Database Access Issues**:
- Check database filtering configuration
- Verify tenant database exists
- Validate user permissions

**Performance Issues**:
- Monitor resource usage per tenant
- Adjust worker processes
- Optimize database queries

**Integration Problems**:
- Verify N8N webhook endpoints
- Check API authentication
- Test data synchronization

### Maintenance Procedures

#### ✅ 17. Regular Maintenance Tasks
- [ ] **Daily**: Monitor container health and logs
- [ ] **Weekly**: Backup tenant databases
- [ ] **Monthly**: Review resource usage and performance
- [ ] **Quarterly**: Update Odoo and security patches

#### ✅ 18. Tenant Management Tasks
- [ ] Regular tenant database backups
- [ ] Performance monitoring per tenant
- [ ] User access reviews
- [ ] Template updates and improvements

This checklist ensures systematic setup and management of the multi-tenant Odoo platform, based on our proven deployment experience.

## 🚀 VPS Production Deployment

### Prerequisites

Before deploying on the shared VPS, **MUST READ** these critical infrastructure documents in order:

### 🚀 IMMEDIATE PRIORITY (Required Reading)
1. **[Core Infrastructure Guide](D:\Programacao\Repositorios\my-portfolio\CLAUDE.md)** - Essential commands, architecture overview, and safety protocols
2. **[File Structure Guide](D:\Programacao\Repositorios\my-portfolio\FILE-STRUCTURE.md)** - Understanding where everything goes and what not to touch
3. **[VPS Compatibility Notes](D:\Programacao\Repositorios\my-portfolio\VPS-COMPATIBILITY-NOTES.md)** - Critical constraints and files you cannot modify

### 📋 HIGH PRIORITY (Read Before Deployment)
4. **[Script Usage Guide](D:\Programacao\Repositorios\my-portfolio\SCRIPT-USAGE-GUIDE.md)** - How to use management scripts for deployments
5. **[Infrastructure Overview](D:\Programacao\Repositorios\my-portfolio\INFRASTRUCTURE.md)** - Complete architecture understanding for integration
6. **[Security Guidelines](D:\Programacao\Repositorios\my-portfolio\SECURITY.md)** - Security requirements and compliance

### 🛠️ OPERATIONAL PRIORITY (During Setup)
7. **[Disaster Recovery Plan](D:\Programacao\Repositorios\my-portfolio\DISASTER-RECOVERY-PLAN.md)** - Backup procedures for integration
8. **[Monitoring Configuration](D:\Programacao\Repositorios\my-portfolio\MONITORING-SECURITY-README.md)** - How to configure monitoring for new services

### ⚡ Quick Start Path for VPS Integration:
1. Read infrastructure CLAUDE.md sections on "Essential Commands" and "Directory Structure"
2. Check VPS-COMPATIBILITY-NOTES.md for deployment constraints and files you cannot touch
3. Use SCRIPT-USAGE-GUIDE.md to understand `./server-manager.sh` for deployment
4. Follow SECURITY.md guidelines for secure project configuration
5. Integrate with existing monitoring stack via monitoring_shared_monitoring_network

**⚠️ WARNING**: This VPS hosts multiple production services. The first 3 infrastructure files will give you the foundation to safely deploy without breaking existing systems.

### 🔧 VPS Deployment Steps

#### 1. GitHub Repository Setup
```bash
# 1. Push your Odoo project to GitHub
git add .
git commit -m "feat: Add VPS deployment configuration"
git push origin main

# 2. Set up GitHub Container Registry access
# Go to GitHub Settings > Developer Settings > Personal Access Tokens
# Create token with packages:write permissions
```

#### 2. Configure GitHub Secrets
In your GitHub repository, go to Settings > Secrets and Variables > Actions and add:

**Required Secrets:**
```bash
# VPS Access
VPS_HOST=maxhaider.dev  # Your VPS IP/domain
VPS_USER=your_username
VPS_KEY=your_private_ssh_key
VPS_PASSPHRASE=your_key_passphrase  # if applicable

# Container Registry
GHCR_TOKEN=your_github_token  # Token with packages:write permission

# Odoo Configuration
ODOO_DB_PASSWORD=secure_database_password
ODOO_DB_USER=odoo
ODOO_DB_NAME=odoo_master
ODOO_ADMIN_PASSWORD=secure_admin_password

# Email Configuration
EMAIL_HOST=smtp.zoho.com
EMAIL_USER=your_email@domain.com
EMAIL_PASS=your_email_password
EMAIL_FROM=noreply@maxhaider.dev

# Integration APIs (Optional)
N8N_WEBHOOK_URL=https://n8n.maxhaider.dev/webhook/odoo
N8N_API_KEY=your_n8n_api_key
WOOCOMMERCE_API_KEY=your_woocommerce_key
WOOCOMMERCE_API_SECRET=your_woocommerce_secret
GOLD_PRICE_API_KEY=your_gold_price_api_key
```

#### 3. Automatic Deployment
Once secrets are configured, deployment is automatic:

```bash
# 1. Push to main branch triggers production deployment
git push origin main

# 2. GitHub Actions will:
#    - Build Docker image
#    - Push to GitHub Container Registry
#    - Deploy to VPS via SSH
#    - Configure Traefik routing
#    - Start services with health checks
```

#### 4. Manual VPS Deployment (Alternative)
If you prefer manual deployment:

```bash
# 1. SSH to VPS
ssh your_username@maxhaider.dev

# 2. Clone repository
git clone https://github.com/your_username/odoo-platform.git
cd odoo-platform

# 3. Create environment file
cp .env.example .env
# Edit .env with your production configuration

# 4. Ensure monitoring stack is running
docker ps | grep traefik  # Should show Traefik running

# 5. Deploy Odoo
docker-compose -f docker-compose.prod.yml up -d

# 6. Verify deployment
curl -I https://odoo.maxhaider.dev
```

#### 5. DNS Configuration
Configure your domain DNS to point to the VPS:

```bash
# A Records (point to your VPS IP)
odoo.maxhaider.dev -> YOUR_VPS_IP
*.odoo.maxhaider.dev -> YOUR_VPS_IP  # For tenant subdomains

# CNAME Records (if using domain)
odoo.yourdomain.com -> maxhaider.dev
*.odoo.yourdomain.com -> maxhaider.dev
```

#### 6. SSL Certificate Setup
Traefik automatically handles SSL certificates via Let's Encrypt:

```yaml
# Traefik labels in docker-compose.prod.yml handle this automatically
traefik.http.routers.odoo-prod.tls=true
traefik.http.routers.odoo-prod.tls.certresolver=myresolver
```

### 🔍 Deployment Verification

#### Check Services
```bash
# SSH to VPS and verify
ssh your_username@maxhaider.dev
cd ~/odoo-platform

# Check containers
docker ps | grep odoo

# Check logs
docker logs odoo_community_18_prod

# Verify HTTP server
docker logs odoo_community_18_prod | grep "HTTP service"
```

#### Test Endpoints
```bash
# Main platform
curl -I https://odoo.maxhaider.dev

# Database manager
curl -I https://odoo.maxhaider.dev/web/database/manager

# Health check
curl https://odoo.maxhaider.dev/web/health
```

#### Monitor Resources
```bash
# Container resource usage
docker stats

# VPS resource usage
htop

# Check available disk space
df -h
```

### 🔧 Maintenance and Updates

#### Automatic Updates via Watchtower
The deployment includes Watchtower for automatic updates:

```yaml
# Enabled in docker-compose.prod.yml
labels:
  - "com.centurylinklabs.watchtower.enable=true"
```

#### Manual Updates
```bash
# 1. SSH to VPS
ssh your_username@maxhaider.dev
cd ~/odoo-platform

# 2. Pull latest changes
git pull origin main

# 3. Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

#### Backup Procedures
```bash
# Database backup
docker exec odoo_postgres_prod pg_dumpall -U odoo > backup_$(date +%Y%m%d).sql

# File storage backup
docker run --rm -v odoo_data_prod:/data -v $(pwd):/backup busybox tar czf /backup/odoo_files_$(date +%Y%m%d).tar.gz /data

# Configuration backup
tar czf config_backup_$(date +%Y%m%d).tar.gz configs/ .env
```

### 🚨 Troubleshooting VPS Deployment

#### Common Issues

**Deployment Fails:**
```bash
# Check GitHub Actions logs
# Verify all secrets are set correctly
# Ensure VPS has enough resources (4GB+ RAM recommended)
```

**Traefik SSL Issues:**
```bash
# Check Traefik logs
docker logs traefik

# Verify DNS propagation
nslookup odoo.maxhaider.dev

# Check certificate status
curl -vI https://odoo.maxhaider.dev 2>&1 | grep -i certificate
```

**Database Connection Issues:**
```bash
# Check PostgreSQL logs
docker logs odoo_postgres_prod

# Verify database password
docker exec odoo_postgres_prod psql -U odoo -c "SELECT version();"
```

**Memory/Performance Issues:**
```bash
# Check resource limits in docker-compose.prod.yml
# Monitor with: docker stats
# Adjust worker processes in odoo-production.conf
```

## Documentation References

For Odoo-specific technical implementation guidance, refer to:
- `context/1_odoo_project_guide.md` - Strategic overview and business requirements
- `context/2_odoo_implementation_guide.md` - Detailed technical implementation steps