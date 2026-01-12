# Odoo Multi-Tenant Platform - Development Guide

> **Navigation**: [TABLE-OF-CONTENTS.md](TABLE-OF-CONTENTS.md) | [AGENT-CONTEXT.md](AGENT-CONTEXT.md)

## Table of Contents

1. [Development Commands](#development-commands)
2. [Database Management](#database-management)
3. [Data Migration](#data-migration)
4. [Monitoring](#monitoring)
5. [Development Guidelines](#development-guidelines)
6. [Adding New Tenants](#adding-new-tenants)
7. [Creating New Business Templates](#creating-new-business-templates)
8. [Custom Module Development](#custom-module-development)
9. [Testing](#testing)

---

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

---

## Database Management

### Connection

```bash
# Connect to Odoo PostgreSQL
docker exec -it odoo_postgres psql -U odoo -d odoo_master

# Create new tenant database
docker exec -it odoo_postgres psql -U odoo -c "CREATE DATABASE tenant_new_store;"

# Backup tenant database
docker exec odoo_postgres pg_dump -U odoo tenant_store_1 > backup_store_1.sql
```

### Common Queries

```sql
-- List all databases
\l

-- List joiasmax tables
\dt joiasmax*

-- Check market prices
SELECT * FROM joiasmax_market_price WHERE is_active = TRUE;

-- Check size adjustment table
SELECT * FROM joiasmax_size_weight_adjustment ORDER BY size_number;

-- Check product configuration
SELECT
    pt.default_code,
    pt.name,
    pt.has_size_based_pricing,
    pt.size_pricing_coef,
    pt.metal_weight_grams
FROM product_template pt
WHERE pt.has_size_based_pricing = TRUE;
```

---

## Data Migration

### Export WooCommerce Data

```bash
# Export WooCommerce data
cd ~/odoo-platform/scripts
python3 export_woocommerce.py

# Transform data for Odoo
python3 transform_data.py

# Import data to Odoo (via web interface or API)
```

---

## Monitoring

### Container Health

```bash
# Check container health
docker ps
docker stats

# View Odoo health endpoint
curl https://odoo.maxhaider.dev/web/health

# Monitor N8N integration
curl https://n8n.maxhaider.dev/webhook/health
```

---

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

**Template Structure**:
```
{new_template}/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── product_template.py      # Extend core models
│   ├── custom_model.py          # Custom business logic
│   └── ...
├── controllers/
│   ├── __init__.py
│   └── webhooks.py              # N8N integration
├── views/
│   ├── menu_views.xml
│   ├── product_views.xml
│   └── ...
├── data/
│   └── reference_data.xml       # Initial data
├── security/
│   ├── ir.model.access.csv
│   └── security_rules.xml       # Row-level security
└── import/
    └── import_scripts.py
```

### Custom Module Development

- **Location**: Place modules in appropriate template directories or core addons
- **Standards**: Follow Odoo 18 development standards and multi-tenant best practices
- **Tenant Isolation**: Include tenant isolation in all custom functionality
- **Reusability**: Design for template reusability across different business types
- **Integration**: Integrate with N8N webhook framework for automation

#### Multi-Tenant Pattern (CRITICAL)

**All custom models MUST implement tenant isolation**:

```python
# models/custom_model.py
from odoo import models, fields, api

class CustomModel(models.Model):
    _name = 'namespace.custom.model'
    _description = 'Custom Model'

    # CRITICAL: Tenant isolation field
    tenant_id = fields.Integer('Tenant ID', required=True, default=1)

    # Your business fields
    name = fields.Char('Name', required=True)
    # ...

    @api.model
    def create(self, vals):
        # Ensure tenant_id is set
        if 'tenant_id' not in vals:
            vals['tenant_id'] = 1  # Or get from context
        return super().create(vals)
```

**Row-Level Security (RLS)**:

```xml
<!-- security/security_rules.xml -->
<record id="custom_model_tenant_rule" model="ir.rule">
    <field name="name">Custom Model: Tenant Isolation</field>
    <field name="model_id" ref="model_namespace_custom_model"/>
    <field name="domain_force">[('tenant_id', '=', 1)]</field>
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_create" eval="True"/>
    <field name="perm_unlink" eval="True"/>
</record>
```

#### Computed Fields Pattern

```python
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Dependency-based computation
    calculated_field = fields.Float(
        'Calculated Field',
        compute='_compute_calculated_field',
        store=True  # Store for performance
    )

    @api.depends('base_field', 'multiplier')
    def _compute_calculated_field(self):
        for record in self:
            record.calculated_field = record.base_field * record.multiplier
```

#### Webhook Integration Pattern

```python
# controllers/webhooks.py
from odoo import http
from odoo.http import request

class CustomWebhook(http.Controller):

    @http.route(
        '/api/v1/custom/endpoint',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    def custom_endpoint(self, **kwargs):
        # Validate API key
        api_key = kwargs.get('api_key')
        stored_key = request.env['ir.config_parameter'].sudo().get_param(
            'custom.webhook_api_key'
        )

        if api_key != stored_key:
            return {'error': 'Unauthorized'}

        # Process request
        # ...

        return {'success': True, 'data': result}
```

### CPL Supplier Size-Based Pricing (Jewelry Template)

**Status**: ✅ Production Ready (Validated: 2026-01-12)

The jewelry template includes complete CPL supplier integration for size-based wedding ring pricing:

**Features**:
- 41 ring size variants per product (sizes 6-46)
- Automatic weight/cost/price calculation based on gold market price
- Real-time recalculation when gold price changes (N8N webhook)
- Bulk import capability via CSV
- Complete validation suite

**Documentation**:
- Quick Start: `addons/tenant_templates/jewelry_template/import/CPL_WORKFLOW_SUMMARY.md`
- Technical Guide: `addons/tenant_templates/jewelry_template/import/CPL_SUPPLIER_ONBOARDING.md`
- Status Tracking: `addons/tenant_templates/jewelry_template/import/CPL_VALIDATION_STATUS.md`

**Scripts**:
- `configure_cpl_product.py` - Configure product with base weight and COEF
- `create_cpl_variants_with_attributes.py` - Create 41 size variants
- `validate_cpl_pricing.py` - Comprehensive validation of calculations
- `bulk_import_cpl_products.py` - Bulk import from CSV file

**Usage**:
```bash
# Single product workflow
python3 configure_cpl_product.py --sku C725R --base-weight 7.0 --coef 1.15 --db tenant_joiasmax --password admin
python3 create_cpl_variants_with_attributes.py --sku C725R --db tenant_joiasmax --password admin
python3 validate_cpl_pricing.py --sku C725R --db tenant_joiasmax --password admin

# Bulk import
python3 bulk_import_cpl_products.py --csv cpl_products.csv --db tenant_joiasmax --password admin --dry-run
python3 bulk_import_cpl_products.py --csv cpl_products.csv --db tenant_joiasmax --password admin
```

---

## Testing

### Multi-Tenant Isolation Testing

```bash
# Test Row-Level Security
docker exec -it odoo_postgres psql -U odoo -d tenant_store_1 -c "
SELECT COUNT(*) FROM joiasmax_jewelry_pricing WHERE tenant_id != 1;
"
# Should return 0

# Test cross-tenant data access
docker exec -it odoo_postgres psql -U odoo -d tenant_store_2 -c "
SELECT * FROM joiasmax_jewelry_pricing WHERE tenant_id = 1;
"
# Should return empty
```

### N8N Workflow Integration Testing

```bash
# Test webhook endpoint
curl -X POST https://n8n.maxhaider.dev/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Test gold price update webhook
curl -X POST http://localhost:8069/api/v1/jewelry/update_market_price \
  -H "Content-Type: application/json" \
  -d '{"api_key": "test_key", "gold_24k": 700.0}'
```

### Gold Price Calculation Validation

```bash
cd addons/tenant_templates/jewelry_template/import

# Validate CPL pricing calculations
python3 validate_cpl_pricing.py --sku C725R --db tenant_joiasmax --password admin --verbose

# Expected output:
# ✅ Size 20: Weight calculation correct
# ✅ Size 20: Cost calculation correct
# ✅ Size 20: Price calculation correct
# ...
```

### WooCommerce Bidirectional Sync Testing

```bash
# Test product sync
curl -X POST https://n8n.maxhaider.dev/webhook/woocommerce-sync

# Verify price history
docker exec -it odoo_postgres psql -U odoo -d tenant_store_1 -c "
SELECT * FROM joiasmax_price_history
WHERE synced_to_woocommerce = TRUE
ORDER BY changed_at DESC LIMIT 10;
"
```

---

**Related Documentation**:
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and components
- [jewelry_template/GUIDE.md](addons/tenant_templates/jewelry_template/GUIDE.md) - Jewelry template patterns
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment procedures
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

**Last Updated**: 2026-01-12
