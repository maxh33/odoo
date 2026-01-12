# Odoo Multi-Tenant Platform - Architecture

> **Navigation**: [TABLE-OF-CONTENTS.md](TABLE-OF-CONTENTS.md) | [AGENT-CONTEXT.md](AGENT-CONTEXT.md)

## Table of Contents

1. [Project Overview](#project-overview)
2. [Core Components](#core-components)
3. [Key Integration Points](#key-integration-points)
4. [Directory Structure](#directory-structure)
5. [Multi-Tenant Architecture](#multi-tenant-architecture)
6. [N8N Integration Workflows](#n8n-integration-workflows)
7. [Industry-Specific Features by Template](#industry-specific-features-by-template)
8. [Integration Endpoints](#integration-endpoints)
9. [VPS Infrastructure Integration](#vps-infrastructure-integration)
10. [Key Configuration Files](#key-configuration-files)

---

## Project Overview

This is a **Multi-Tenant Odoo 18 Community Platform** that serves as a foundational base for deploying Odoo 18.0 Community Edition across multiple business types and industries. The platform provides configurable tenant templates, automated business process integration, and scalable infrastructure for serving diverse client needs including retail, manufacturing, services, and specialized industries like jewelry.

---

## Core Components

- **Odoo 18.0 Community**: Multi-tenant ERP platform with configurable tenant templates
- **N8N Integration**: Automated business process workflows and external system synchronization
- **E-commerce Sync**: Bidirectional inventory, pricing, and order management with multiple platforms
- **Multi-Tenant Database**: PostgreSQL with tenant isolation via database sharding
- **Tenant Templates**: Pre-configured business modules for different industries (jewelry, retail, manufacturing, services)

---

## Key Integration Points

- **Automated Business Processes**: N8N workflows for industry-specific automation (pricing, inventory, notifications)
- **Tenant-Specific Configurations**: Custom business rules, pricing strategies, and workflows per client
- **Real-time Synchronization**: Odoo ↔ E-commerce platforms (WooCommerce, Shopify, etc.)
- **VPS Infrastructure**: Leverages existing monitoring stack (Prometheus, Grafana, Traefik)
- **Scalable Architecture**: Easy onboarding of new tenants with pre-built templates

---

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
│   │   │   ├── models/                 # Odoo models (product, pricing, etc.)
│   │   │   ├── data/                   # Data files (size_weight_adjustments.xml)
│   │   │   ├── import/                 # Import scripts (CPL supplier, Bling ERP)
│   │   │   │   ├── CPL_WORKFLOW_SUMMARY.md        # CPL quick start guide
│   │   │   │   ├── CPL_SUPPLIER_ONBOARDING.md     # CPL technical guide
│   │   │   │   ├── CPL_VALIDATION_STATUS.md       # CPL import tracking
│   │   │   │   ├── cpl_products_template.csv      # CPL CSV template
│   │   │   │   └── bulk_import_cpl_products.py    # CPL bulk import script
│   │   │   └── supplier/               # Supplier specifications (cpl_size_indice.md)
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

---

## Multi-Tenant Architecture

### Tenant Management

- Each client business has a separate database (`tenant_{business_type}_{name}`)
- Tenant routing via subdomain: `tenant-name.odoo.maxhaider.dev`
- API access: `api.odoo.maxhaider.dev/tenant/{tenant-id}`
- Isolated data, configurations, and business rules per tenant
- Template-based tenant creation for rapid onboarding

### Database Structure

- **Master database**: `odoo_master` (tenant management, shared configurations, templates)
- **Tenant databases**: `tenant_{business_type}_{name}` (isolated client data)
- **Template databases**: `template_{business_type}` (template configurations for quick tenant creation)
- **Shared PostgreSQL instance** on port 5433 (separate from existing services)

### Tenant Templates

- **Base Template**: Core Odoo functionality for any business type
- **Jewelry Template**: Specialized for jewelry stores (gold pricing, gemstone management)
- **Retail Template**: General retail operations (inventory, POS, e-commerce)
- **Manufacturing Template**: Production workflows, BOM, quality control
- **Services Template**: Service-based businesses, project management, time tracking

---

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

### Example Workflows by Template

- **Jewelry Template**:
  - Gold price automation (CPL supplier size-based pricing - Production Ready ✅)
  - Gemstone inventory tracking
  - Automatic cost recalculation when gold market price updates
- **Retail Template**: Multi-channel inventory sync, promotional price updates
- **Manufacturing Template**: Raw material cost tracking, production scheduling
- **Services Template**: Project milestone notifications, time tracking integration

---

## Industry-Specific Features by Template

### Jewelry Template Features

- **Product Attributes**: Metal type/karat, weight, gemstone tracking, craftsmanship levels
- **Pricing Logic**: Automated precious metal price updates, material cost calculations
- **CPL Supplier Integration**: Size-based pricing for wedding rings (41 variants per product, sizes 6-46)
  - Automatic weight calculation: `base_weight × COEF × size_adjustment_factor`
  - Automatic cost calculation: `weight × gold_price × purity × provider_index`
  - Automatic price calculation: `cost × (1 + markup%)`
  - Real-time updates when gold market price changes
  - Bulk import capability for entire supplier catalogs
- **Inventory Management**: Certificate tracking, quality metrics, custom piece workflows

**CPL Supplier Status**: ✅ Production Ready (Validated: 2026-01-12)

**Documentation**:
- Quick Start: `addons/tenant_templates/jewelry_template/import/CPL_WORKFLOW_SUMMARY.md`
- Technical Guide: `addons/tenant_templates/jewelry_template/import/CPL_SUPPLIER_ONBOARDING.md`
- Status Tracking: `addons/tenant_templates/jewelry_template/import/CPL_VALIDATION_STATUS.md`

**Database Tables**:
- `joiasmax.size.weight.adjustment` - CPL size adjustment factors (45 entries, sizes 6-50)
- `joiasmax.market.price` - Gold market prices (updated via N8N webhook)
- `joiasmax.jewelry.pricing` - Jewelry pricing configuration per product

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

---

## Integration Endpoints

### Odoo APIs

- Products: `https://odoo.maxhaider.dev/api/v1/products`
- Tenants: `https://api.odoo.maxhaider.dev/tenant/{tenant-id}`
- Health: `https://odoo.maxhaider.dev/web/health`

### N8N Webhooks

- Gold price updates: `https://n8n.maxhaider.dev/webhook/gold-price-update`
- WooCommerce sync: `https://n8n.maxhaider.dev/webhook/woocommerce-sync`
- Tenant notifications: `https://n8n.maxhaider.dev/webhook/tenant/{tenant-id}`

**See [API.md](API.md) for detailed webhook specifications and authentication.**

---

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

---

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

---

**Related Documentation**:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment procedures and Docker management
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflows and guidelines
- [MULTI-TENANT-OPERATIONS.md](MULTI-TENANT-OPERATIONS.md) - Tenant management operations
- [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) - Jewelry template details

**Last Updated**: 2026-01-12
