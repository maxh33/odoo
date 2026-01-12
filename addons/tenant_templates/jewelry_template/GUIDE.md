# Jewelry Template - Complete Guide

> **Navigation**: [Root TABLE-OF-CONTENTS.md](../../TABLE-OF-CONTENTS.md) | [AGENT-CONTEXT.md](../../../AGENT-CONTEXT.md)

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [CPL Supplier Integration](#cpl-supplier-integration)
4. [Bling ERP Integration](#bling-erp-integration)
5. [Database Schema](#database-schema)
6. [Import Scripts Reference](#import-scripts-reference)
7. [Troubleshooting](#troubleshooting)
8. [Reusable Patterns for New Suppliers](#reusable-patterns-for-new-suppliers)

---

## Overview

The Jewelry Template is a **production-ready** Odoo 18 module specifically designed for jewelry businesses. It provides sophisticated pricing automation, variant management, and supplier integration capabilities.

**Status**: ✅ Production Ready (Validated: 2026-01-12)

**Key Features**:
- Size-based variant pricing (41 variants per product)
- Automated gold/silver market price integration
- Supplier-specific calculation patterns (CPL, Gold Indice, Cronus)
- Bulk import capabilities
- Multi-tenant isolation

**Validated Suppliers**:
- ✅ **CPL**: Complete integration (sizes 6-46, weight/cost/price automation)
- ⏳ **Gold Indice**: Planned
- ⏳ **Cronus**: Planned
- ⏳ **Silver/Steel Suppliers**: Planned

---

## Quick Start

### Prerequisites

- Odoo 18 deployed and running
- PostgreSQL database accessible
- Python 3.8+ for import scripts
- Admin credentials for target database

### Quick CPL Product Import

```bash
cd addons/tenant_templates/jewelry_template/import

# Single product (3-step workflow)
python3 configure_cpl_product.py --sku C725R --base-weight 7.0 --coef 1.15 --db tenant_joiasmax --password admin
python3 create_cpl_variants_with_attributes.py --sku C725R --db tenant_joiasmax --password admin
python3 validate_cpl_pricing.py --sku C725R --db tenant_joiasmax --password admin

# Bulk import from CSV
python3 bulk_import_cpl_products.py --csv cpl_products.csv --db tenant_joiasmax --password admin
```

**For detailed CPL workflow**: See [import/CPL_WORKFLOW_SUMMARY.md](import/CPL_WORKFLOW_SUMMARY.md)

---

## CPL Supplier Integration

### Business Formulas

```
Weight = Base Weight × COEF × Size Adjustment Factor
Cost = Weight × Gold Price/gram × Purity Factor × Provider Index
Price = Cost × (1 + Markup%)
```

**Example Calculation** (C725R @ R$700/g gold, size 20):
- Weight = 7.0g × 1.15 × 1.0000 = 8.05g
- Cost = 8.05g × R$700 × 1.0 = R$5,635
- Price = R$5,635 × (1 + 200%) = R$16,905

### Size Adjustment Table

The CPL supplier uses a 45-entry lookup table for ring sizes 6-50:

| Size | Adjustment Factor | Note |
|------|------------------|------|
| 6 | 0.7666 | Smallest |
| 13 | 0.8833 | Reference -1.0% |
| 20 | 1.0000 | **REFERENCE SIZE** |
| 30 | 1.1666 | |
| 46 | 1.3500 | Largest |

**Database Table**: `joiasmax.size.weight.adjustment` (45 entries total)

### Variant Creation Process

1. **Configure Product** (`configure_cpl_product.py`):
   - Sets base weight, COEF, material type, purity
   - Creates jewelry_pricing record
   - Links pricing to product template

2. **Create Variants** (`create_cpl_variants_with_attributes.py`):
   - Creates attribute "Ring Size" with values 6-46
   - Generates 41 product variants
   - Each variant automatically calculates weight/cost based on size

3. **Validate** (`validate_cpl_pricing.py`):
   - Verifies all 41 variants exist
   - Checks weight calculation accuracy
   - Validates cost and price computations
   - Reports any discrepancies

### CPL Documentation

- **Quick Start**: [import/CPL_WORKFLOW_SUMMARY.md](import/CPL_WORKFLOW_SUMMARY.md)
- **Technical Details**: [import/CPL_SUPPLIER_ONBOARDING.md](import/CPL_SUPPLIER_ONBOARDING.md)
- **Validation Status**: [import/CPL_VALIDATION_STATUS.md](import/CPL_VALIDATION_STATUS.md)
- **CSV Template**: [import/cpl_products_template.csv](import/cpl_products_template.csv)

---

## Bling ERP Integration

### Overview

Import products from Bling ERP CSV exports with automatic category mapping.

### CSV Format

Required columns:
- `codigo`: Product SKU
- `descricao`: Product name
- `preco`: Product price
- `categoria`: Category name
- `estoque`: Stock quantity

### Category Mapping

The importer includes 28 pre-configured category mappings:

| Bling Category | Odoo Category |
|---------------|---------------|
| Anéis | Jewelry / Rings |
| Aliança | Jewelry / Wedding Rings |
| Brincos | Jewelry / Earrings |
| Colares | Jewelry / Necklaces |
| Pulseiras | Jewelry / Bracelets |
| ... | ... |

**Full mapping**: See `import/helpers/category_mapper.py`

### Import Process

```bash
cd addons/tenant_templates/jewelry_template/import

# Import from Bling CSV
python3 import_products.py --csv bling_export.csv --db tenant_joiasmax --password admin --dry-run
python3 import_products.py --csv bling_export.csv --db tenant_joiasmax --password admin
```

---

## Database Schema

### Custom Models (joiasmax module)

#### 1. joiasmax.jewelry.pricing

**Purpose**: Central pricing logic for jewelry products

**Key Fields**:
- `product_id`: Link to product.template
- `tenant_id`: Multi-tenant isolation
- `material_type`: gold_24k / silver_950
- `provider_indice`: Supplier-specific multiplier
- `markup_percentage`: Profit markup
- `material_cost_brl`: Computed cost
- `calculated_price_brl`: Computed price
- `final_price_brl`: Manual override or calculated

**Key Methods**:
- `_compute_material_cost()`: Weight × price × purity × provider
- `action_sync_to_product()`: Updates product.list_price
- `action_recalculate_costs()`: Force recomputation

#### 2. joiasmax.market.price

**Purpose**: Gold/silver market prices (updated via N8N webhook)

**Key Fields**:
- `material_type`: gold_24k / silver_950
- `price_per_gram_brl`: Current market price
- `is_active`: Only one active price per type
- `fetched_at`: Timestamp of last update
- `source_api`: External API identifier

**Webhook Method**:
```python
@api.model
def update_from_n8n(self, gold_24k_brl, silver_950_brl, exchange_rate):
    # Updates prices and cascades to all products
    pass
```

#### 3. joiasmax.size.weight.adjustment

**Purpose**: CPL size adjustment factors (45 entries)

**Key Fields**:
- `size_number`: Ring size (6-50)
- `adjustment_factor`: Weight multiplier
- `reference_size`: Boolean (size 20 = True)

**Usage**: Lookup table for variant weight calculation

#### 4. joiasmax.supplier.cost

**Purpose**: Track supplier costs with validity periods

**Key Fields**:
- `product_id`: Product reference
- `supplier_id`: Supplier (res.partner)
- `unit_cost_brl`: Cost per unit
- `valid_from` / `valid_until`: Date range
- `is_current`: Computed (currently valid?)
- `is_preferred_supplier`: Boolean

#### 5. joiasmax.price.history

**Purpose**: Immutable audit log of price changes

**Key Fields**:
- `product_id`: Product reference
- `old_price_brl` / `new_price_brl`: Price change
- `change_reason`: market_price_update / manual_adjustment / etc.
- `changed_at`: Timestamp
- `changed_by_user_id`: User reference
- `synced_to_woocommerce`: Integration tracking

**Constraints**: Read-only except sync status

### Product Extensions

#### product.template (Extended)

Added jewelry-specific fields:
- `is_jewelry`: Boolean flag
- `material_type`: gold / silver / etc.
- `metal_weight_grams`: Base weight
- `metal_purity`: 24k / 950 / etc.
- `jewelry_pricing_id`: Link to joiasmax.jewelry.pricing
- `has_size_based_pricing`: Enable CPL pricing
- `size_pricing_coef`: COEF multiplier

#### product.product (Extended - Variants)

Added variant-specific fields:
- `ring_size`: Integer (6-50)
- `calculated_metal_weight`: Computed field
- `standard_price`: Computed cost

---

## Import Scripts Reference

### CPL Scripts (4 core scripts)

| Script | Purpose | Usage |
|--------|---------|-------|
| `configure_cpl_product.py` | Set base weight, COEF, material | `--sku --base-weight --coef` |
| `create_cpl_variants_with_attributes.py` | Create 41 size variants | `--sku` |
| `validate_cpl_pricing.py` | Verify calculations | `--sku --verbose` |
| `bulk_import_cpl_products.py` | CSV bulk import | `--csv --dry-run` |

### Diagnostic Scripts (8 scripts)

| Script | Purpose |
|--------|---------|
| `check_product_config.py` | Verify product configuration |
| `check_size_table.py` | Verify size adjustment table loaded |
| `check_market_price.py` | Verify market prices exist |
| `check_variant_costs.py` | Check variant cost calculations |
| `check_jewelry_pricing.py` | Verify pricing records |
| `list_cpl_products.py` | List all size-based products |
| `check_attribute_values.py` | Verify ring size attribute |
| `inspect_product_variants.py` | Detailed variant inspection |

### Maintenance Scripts (4 scripts)

| Script | Purpose |
|--------|---------|
| `recalculate_all_prices.py` | Force price recalculation |
| `trigger_cost_recompute.py` | Trigger cost computation |
| `force_recompute_all.py` | Nuclear option - recompute everything |
| `update_market_price_manual.py` | Manually set market price |

### Bling ERP Scripts (5 scripts)

| Script | Purpose |
|--------|---------|
| `import_products.py` | Main import script |
| `helpers/category_mapper.py` | Category mapping logic |
| `helpers/csv_validator.py` | Validate CSV format |
| `helpers/product_creator.py` | Create products in Odoo |
| `helpers/stock_updater.py` | Update stock quantities |

### Testing Scripts (4 scripts)

| Script | Purpose |
|--------|---------|
| `test_single_product.py` | Test single product import |
| `test_variant_creation.py` | Test variant creation process |
| `test_price_calculation.py` | Test pricing formulas |
| `test_market_price_update.py` | Test webhook integration |

---

## Troubleshooting

### Issue: Variant Costs = 0

**Cause**: No market price in database

**Fix**:
```bash
python3 check_market_price.py --db tenant_joiasmax --password admin

# If no price found, use update script
python3 update_market_price_manual.py --gold-price 700.0 --db tenant_joiasmax --password admin
```

### Issue: Import Fails "Product Not Found"

**Cause**: SKU mismatch between CSV and Odoo

**Fix**:
```bash
# Check product in database
docker exec -it odoo_postgres psql -U odoo -d tenant_joiasmax -c \
  "SELECT id, name, default_code FROM product_template WHERE default_code LIKE '%C725R%';"

# SKU must match exactly (case-sensitive)
```

### Issue: Incorrect Weight Calculation

**Cause**: Size adjustment table not loaded

**Fix**:
```bash
python3 check_size_table.py --db tenant_joiasmax --password admin

# Should show 45 entries
# If missing, reload data: Settings > Technical > Update List > Update Module (jewelry_template)
```

### Issue: Prices Not Updating After Market Price Change

**Cause**: Computed fields not triggering

**Fix**:
```bash
# Force recalculation
python3 force_recompute_all.py --db tenant_joiasmax --password admin
```

**For detailed troubleshooting**: See [Root TROUBLESHOOTING.md](../../../TROUBLESHOOTING.md)

---

## Reusable Patterns for New Suppliers

### Adding Gold Indice / Cronus / Other Suppliers

**Pattern**: Follow CPL implementation as blueprint

#### 1. Configuration Script (`{supplier}_configure_product.py`)

```python
# Set supplier-specific parameters
product.write({
    'metal_weight_grams': base_weight,
    'size_pricing_coef': coef,  # Or supplier-specific field
    'has_size_based_pricing': True
})

# Create pricing record
pricing = env['joiasmax.jewelry.pricing'].create({
    'product_id': product.id,
    'provider_indice': provider_index,
    'markup_percentage': markup
})
```

#### 2. Variant Creation (if size-based)

```python
# Create/get ring size attribute
attribute = env['product.attribute'].search([('name', '=', 'Ring Size')])

# Create variants
for size in range(start_size, end_size + 1):
    variant = env['product.product'].create({
        'product_tmpl_id': product.id,
        'ring_size': size
    })
```

#### 3. Bulk Import Script

```python
# Read CSV
import csv
with open(csv_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # 1. Create/update product template
        # 2. Create pricing record
        # 3. Create variants (if applicable)
        # 4. Validate
        pass
```

#### 4. Validation Script

```python
# Verify:
# 1. Product exists
# 2. Pricing record exists
# 3. Variants exist (if size-based)
# 4. Weight calculations correct
# 5. Cost calculations correct
# 6. Price calculations correct
```

#### 5. Documentation

**Required files**:
- `{SUPPLIER}_WORKFLOW_SUMMARY.md` - Quick reference
- `{SUPPLIER}_SUPPLIER_ONBOARDING.md` - Technical guide
- `{supplier}_products_template.csv` - CSV template

### Supplier-Specific Differences

| Supplier | Variant Type | Calculation Pattern | Special Fields |
|----------|-------------|---------------------|----------------|
| CPL | 41 ring sizes (6-46) | Weight × COEF × Size Factor | `size_pricing_coef` |
| Gold Indice | TBD (likely size-based) | TBD | TBD |
| Cronus | TBD | TBD | TBD |
| Silver/Steel | Potentially non-size | Base price + margin | Different material_type |

---

**Related Documentation**:
- [Root ARCHITECTURE.md](../../../ARCHITECTURE.md) - Template architecture
- [Root DEVELOPMENT.md](../../../DEVELOPMENT.md) - Custom module patterns
- [Root API.md](../../../API.md) - Webhook endpoints
- [import/CPL_WORKFLOW_SUMMARY.md](import/CPL_WORKFLOW_SUMMARY.md) - CPL quick start

**Last Updated**: 2026-01-12
