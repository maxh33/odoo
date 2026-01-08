# Odoo 18 Multi-Tenant Platform

A comprehensive multi-tenant Odoo 18 Community Edition platform with N8N automation integration, designed for VPS deployment with business-type specific templates.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 2GB+ RAM available
- 5GB+ disk space

### 1. Environment Setup
```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env with your specific settings (passwords, domains, API keys)
```

### 2. Test Locally (Recommended First)
```bash
# For Windows
scripts\testing\test-deployment.bat

# For Linux/Mac
./scripts/testing/test-deployment.sh
```

### 3. Deploy Platform
```bash
# Make scripts executable (if needed)
chmod +x scripts/*.sh

# Deploy the platform
./scripts/deploy.sh
```

### 4. Access Your Platform
- **Local Development**: http://localhost:8069
- **Production**: https://odoo.maxhaider.dev
- **API**: https://api.odoo.maxhaider.dev

## 🏗️ Architecture

### Core Components
- **Odoo 18.0 Community**: Multi-tenant ERP with performance optimization
- **PostgreSQL 15**: Dedicated database with multi-tenant architecture
- **N8N Integration**: Webhook automation for business processes
- **Traefik Integration**: SSL termination and domain routing
- **Monitoring**: Prometheus/Grafana integration for VPS

### Business Type Templates
- **Jewelry Stores**: Gold pricing automation, gemstone tracking
- **Retail Businesses**: Multi-channel inventory, POS integration
- **Manufacturing**: BOM management, production planning
- **Service Companies**: Project management, time tracking

## 📁 Project Structure

```
odoo-multitenant-platform/
├── docker-compose.yml          # Main deployment configuration
├── .env                        # Environment variables
├── configs/                    # Configuration files
│   ├── odoo/odoo.conf         # Odoo server configuration
│   └── postgres/              # Database setup scripts
├── addons/                     # Custom Odoo modules
│   ├── multi_tenant_core/     # Core multi-tenancy functionality
│   ├── n8n_connector/         # N8N webhook integration
│   └── tenant_templates/      # Business-type templates
├── scripts/                    # Management scripts
│   ├── deploy.sh              # Main deployment script
│   ├── create-tenant.sh       # Tenant creation
│   └── health-check.sh        # System health validation
└── tenant_configs/            # Per-tenant configurations
```

## 🔧 Management Commands

### Deployment
```bash
# Full deployment with health checks
./scripts/deploy.sh

# Force rebuild and skip backup
./scripts/deploy.sh --force-rebuild --skip-backup

# Development deployment
./scripts/deploy.sh --env=development
```

### Tenant Management
```bash
# Create a new jewelry store tenant
./scripts/create-tenant.sh --tenant-id=store1 --business-type=jewelry --name="Gold Palace Jewelry"

# Create a retail tenant
./scripts/create-tenant.sh --tenant-id=shop1 --business-type=retail --name="Fashion Boutique"
```

### Health Monitoring
```bash
# Quick health check
./scripts/health-check.sh

# View container status
docker-compose ps

# View logs
docker-compose logs -f odoo
```

## 🌐 Multi-Tenant Features

### Tenant Isolation
- Separate databases per tenant
- Subdomain routing (`tenant-name.odoo.maxhaider.dev`)
- Business-type specific configurations
- Isolated API access with authentication

### Business-Type Templates

#### Jewelry Template
- **Features**: Gold price automation, gemstone tracking, karat management
- **Integrations**: Real-time precious metal pricing APIs
- **Automation**: Dynamic pricing based on market rates

#### Retail Template
- **Features**: Multi-channel inventory, POS integration, customer segmentation
- **Integrations**: WooCommerce, Shopify synchronization
- **Automation**: Inventory alerts, promotional pricing

#### Manufacturing Template
- **Features**: BOM management, production planning, quality control
- **Integrations**: Supplier APIs, capacity planning tools
- **Automation**: Cost tracking, production scheduling

#### Services Template
- **Features**: Project management, time tracking, client billing
- **Integrations**: Time tracking APIs, client portals
- **Automation**: Milestone notifications, billing automation

## 🔗 N8N Integration

### Webhook Endpoints
Each tenant gets dedicated webhook endpoints for automation:
- `{tenant-id}-product-sync`: Product synchronization
- `{tenant-id}-inventory-update`: Inventory management
- `{tenant-id}-price-update`: Dynamic pricing updates
- `{tenant-id}-order-notification`: Order processing

### Automation Workflows
- **Product Sync**: Bidirectional sync with e-commerce platforms
- **Inventory Management**: Real-time stock level updates
- **Price Automation**: Market-based pricing for jewelry/retail
- **Notifications**: Business alerts and customer communication

## 🔒 Security Features

### Authentication & Authorization
- Multi-tenant user isolation
- API key authentication for webhooks
- HMAC signature verification
- Rate limiting and throttling

### Infrastructure Security
- SSL/TLS termination via Traefik
- Network isolation with Docker networks
- Secrets management via environment variables
- Database connection encryption

## 📊 Monitoring & Analytics

### Performance Monitoring
- Container resource usage tracking
- Database performance metrics
- Webhook execution statistics
- Business analytics per tenant

### Health Checks
- Automated service health validation
- Database connectivity monitoring
- API endpoint availability checks
- Resource usage alerts

## 🚀 Production Deployment

### VPS Integration
The platform is designed for deployment on shared VPS infrastructure:

1. **Network Integration**: Uses `monitoring_shared_monitoring_network`
2. **SSL Termination**: Integrates with existing Traefik setup
3. **Resource Limits**: Optimized for shared hosting environment
4. **Monitoring**: Connects to existing Prometheus/Grafana stack

### Configuration Steps
1. Configure DNS records for `odoo.maxhaider.dev`
2. Update Traefik configuration for SSL certificates
3. Set up monitoring dashboards
4. Configure backup automation
5. Set up N8N workflow templates

## 🛠️ Development

### Local Development
```bash
# Start in development mode
./scripts/deploy.sh --env=development

# Create test tenant
./scripts/create-tenant.sh --tenant-id=test1 --business-type=jewelry --name="Test Store"

# Run health checks
./scripts/health-check.sh
```

### Custom Module Development
1. Create module in appropriate `addons/` subdirectory
2. Follow Odoo 18 development standards
3. Include tenant isolation in all functionality
4. Test with multiple business types

### Adding New Business Types
1. Create template in `addons/tenant_templates/`
2. Update business type configuration
3. Create N8N workflow templates
4. Document business-specific features

## 🐛 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs odoo

# Verify configuration
docker-compose config

# Check resource usage
docker stats
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose exec odoo_postgres pg_isready -U odoo

# Check database logs
docker-compose logs odoo_postgres
```

#### Webhook Integration Problems
```bash
# Check N8N connectivity
curl -I https://automation.maxhaider.dev/webhook/health

# View webhook logs
docker-compose exec odoo tail -f /var/log/odoo/odoo.log
```

### Performance Optimization
- Monitor memory usage with `docker stats`
- Adjust worker processes in `odoo.conf`
- Optimize PostgreSQL settings for your workload
- Use connection pooling for high-traffic scenarios

## 📚 Documentation

- **[CLAUDE.md](./CLAUDE.md)**: Complete development guide for Claude Code
- **[Project Structure](./docs/PROJECT_STRUCTURE.md)**: Complete project organization
- **[Directory Details](./docs/DIRECTORY_STRUCTURE.md)**: Detailed structure guide
- **[Implementation Guide](./docs/context/2_odoo_implementation_guide.md)**: Technical implementation details

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs`
3. Validate configuration: `docker-compose config`
4. Run health checks: `./scripts/health-check.sh`

## 📄 License

This project is licensed under LGPL-3 for Odoo components and appropriate licenses for other components.

---

**Built with ❤️ for multi-tenant business automation**