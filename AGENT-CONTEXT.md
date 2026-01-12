# Odoo Multi-Tenant Platform - Agent Quick Reference

> **For detailed navigation, see [TABLE-OF-CONTENTS.md](TABLE-OF-CONTENTS.md)**

## What This Project Is

Multi-tenant Odoo 18.0 Community Edition platform with industry-specific templates:
- **Jewelry** (✅ Production): Size-based pricing, gold market automation, CPL supplier
- **Retail** (⏳ Planned): Multi-channel inventory, POS integration
- **Manufacturing** (⏳ Planned): BOM, production workflows
- **Services** (⏳ Planned): Project management, time tracking

**Architecture**: PostgreSQL multi-database, Traefik routing, N8N automation, Docker deployment.

---

## Critical Paths

| Purpose | Location |
|---------|----------|
| Custom modules | `addons/tenant_templates/{template}/` |
| Import scripts | `addons/tenant_templates/jewelry_template/import/` |
| Odoo config | `configs/odoo/odoo-minimal.conf` (dev), `configs/odoo/odoo.conf` (prod) |
| Documentation hub | `TABLE-OF-CONTENTS.md` (master index) |
| Deployment | `docker-compose.yml` (local), VPS integration docs |
| N8N integration | `addons/n8n_connector/` |

---

## Current Implementation Status

### Jewelry Template (✅ Complete)

| Feature | Status | Details |
|---------|--------|---------|
| CPL Supplier | ✅ Prod | 41 variants/product, sizes 6-46, validated C725R/C790RZ |
| Bling ERP Import | ✅ Prod | CSV bulk import, 28 category mappings |
| Size-based Pricing | ✅ Prod | Weight = base × COEF × size_factor |
| Market Price Automation | 🔧 Framework | N8N webhook ready, workflows pending |
| Variant Creation | ✅ Prod | Attribute-based system, ring_size field |
| Pricing Models | ✅ Prod | 7 custom models (jewelry_pricing, market_price, etc.) |

### Import Scripts (28 Total)

- **CPL Core** (4): configure, create_variants, bulk_import, validate ✅
- **Diagnostics** (8): check_product_config, check_size_table, etc. ✅
- **Maintenance** (4): recalculate_prices, force_recompute, etc. ✅
- **Bling ERP** (5): import_products + 4 helpers ✅
- **Testing** (4): test_single_product, test_variant_creation, etc. ✅

### Database Tables (joiasmax module)

- `joiasmax.size.weight.adjustment`: 45 entries (sizes 6-50, CPL adjustment factors)
- `joiasmax.market.price`: Gold/silver market prices (N8N webhook updates)
- `joiasmax.jewelry.pricing`: Product pricing config (provider_indice, markup)
- `joiasmax.supplier.cost`: Supplier cost tracking with validity periods
- `joiasmax.price.history`: Immutable audit log of price changes

---

## Business Formulas (CPL Supplier)

```
Weight = Base Weight × COEF × Size Adjustment Factor
Cost = Weight × Gold Price/gram × Purity Factor × Provider Index
Price = Cost × (1 + Markup%)
```

**Example (C725R @ R$700/g gold, size 20)**:
- Weight = 7.0g × 1.15 × 1.0000 = 8.05g
- Cost = 8.05g × R$700 × 1.0 = R$5,635
- Price = R$5,635 × (1 + 200%) = R$16,905

---

## Multi-Tenant Architecture

**Current State**: Hard-coded `tenant_id = 1` in security rules (single tenant)

**Database Routing**: Domain-based via `addons/multi_tenant_core/models/ir_http.py`
- Format: `{tenant}.odoo.maxhaider.dev` → `tenant_{tenant}`
- Master DB: `odoo_master` (template management)
- Tenant DBs: `tenant_{business_type}_{name}` (isolated client data)

**Row-Level Security Pattern**:
```xml
<record id="model_tenant_rule" model="ir.rule">
    <field name="domain_force">[('tenant_id', '=', 1)]</field>
</record>
```

---

## Quick Command Reference

### Local Development

```bash
# Start Odoo (minimal config, proven working)
docker-compose up -d

# Check HTTP server started
docker logs odoo_community_18 | grep "HTTP service"

# Access: http://localhost:8069 (master password on first visit)
```

### Import Scripts (Jewelry Template)

```bash
cd addons/tenant_templates/jewelry_template/import

# Single CPL product
python3 configure_cpl_product.py --sku C725R --base-weight 7.0 --coef 1.15 --db tenant_joiasmax --password admin
python3 create_cpl_variants_with_attributes.py --sku C725R --db tenant_joiasmax --password admin
python3 validate_cpl_pricing.py --sku C725R --db tenant_joiasmax --password admin

# Bulk CPL import
python3 bulk_import_cpl_products.py --csv cpl_products.csv --db tenant_joiasmax --password admin --dry-run
python3 bulk_import_cpl_products.py --csv cpl_products.csv --db tenant_joiasmax --password admin
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it odoo_postgres psql -U odoo -d odoo_master

# Common queries
\dt joiasmax*  # List joiasmax tables
SELECT * FROM joiasmax_size_weight_adjustment LIMIT 5;
SELECT * FROM joiasmax_market_price WHERE is_active = TRUE;
```

---

## Common Issues & Quick Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| HTTP server won't start | Complex config file | Use `odoo-minimal.conf` |
| Variant costs = 0 | No market price | `check_market_price.py`, insert gold price |
| Import fails "product not found" | SKU mismatch | Check product.default_code field |
| Duplicate products on reimport | No External ID | Scripts use External IDs (fixed) |
| Docker entrypoint issues | Override not set | Use `entrypoint: []` + explicit command |

---

## Documentation Navigation

| Need | Document | Location |
|------|----------|----------|
| **Master Index** | TABLE-OF-CONTENTS.md | Root |
| **Deployment** | DEPLOYMENT.md | Root |
| **Architecture** | ARCHITECTURE.md | Root |
| **Multi-Tenant Ops** | MULTI-TENANT-OPERATIONS.md | Root |
| **Troubleshooting** | TROUBLESHOOTING.md | Root |
| **Jewelry Guide** | GUIDE.md | jewelry_template/ |
| **CPL Supplier** | CPL_SUPPLIER_ONBOARDING.md | jewelry_template/import/ |
| **API Reference** | API.md | Root |

---

## Integration Endpoints

### N8N Webhooks (Framework Ready)

- Market price update: `POST /api/v1/jewelry/update_market_price`
- Price recalculation: `POST /api/v1/jewelry/recalculate_prices`
- Health check: `GET /api/v1/jewelry/recalculate_prices/health`

### WooCommerce (Partial)

- Price sync via `joiasmax.price.history.synced_to_woocommerce` flag
- N8N polls price_history for changes to sync

---

## Next Suppliers (Planned)

| Supplier | Status | Pattern | Notes |
|----------|--------|---------|-------|
| CPL | ✅ Complete | Size-based COEF | 41 variants, production-ready |
| Gold Indice | ⏳ Planned | TBD (likely COEF) | Awaiting spec |
| Cronus | ⏳ Planned | TBD | Awaiting spec |
| Silver/Steel | ⏳ Planned | TBD | Different material type |

---

## Key Odoo Models

### Product Extensions

- `product.template`: Core product + jewelry fields (is_jewelry, material_type, metal_weight_grams, has_size_based_pricing, size_pricing_coef)
- `product.product`: Variant-specific (ring_size, calculated_metal_weight, computed costs)

### Custom Models (joiasmax module)

- `joiasmax.jewelry.pricing`: Central pricing logic (provider_indice, markup, computed costs)
- `joiasmax.market.price`: Market prices (gold_24k, silver_950, updated via webhook)
- `joiasmax.size.weight.adjustment`: CPL size factors (45 entries, sizes 6-50)
- `joiasmax.supplier.cost`: Supplier cost tracking with validity periods
- `joiasmax.price.history`: Immutable audit log

---

## Reusable Patterns for New Suppliers

1. **Configuration Script**: `{supplier}_configure_product.py`
2. **Variant Creation**: `create_{supplier}_variants.py` (if applicable)
3. **Bulk Import**: `bulk_import_{supplier}_products.py`
4. **Validation**: `validate_{supplier}_pricing.py`
5. **Diagnostics**: `check_{supplier}_config.py`
6. **Documentation**: `{SUPPLIER}_WORKFLOW_SUMMARY.md`, `{SUPPLIER}_SUPPLIER_ONBOARDING.md`
7. **CSV Template**: `{supplier}_products_template.csv`

---

## Development Standards

- **Odoo 18 Standards**: Follow community guidelines
- **Multi-tenant Isolation**: All custom models MUST have `tenant_id` field + RLS rules
- **External IDs**: Use for idempotent imports (`product_template_{SANITIZED_SKU}`)
- **Computed Fields**: Use `@api.depends()` decorator
- **Audit Trails**: Log all price/cost changes to history models
- **API Keys**: Validate webhook calls via `ir.config_parameter`

---

**Last Updated**: 2026-01-12
**Agent Version**: 1.0
**Project**: Odoo Multi-Tenant Platform
