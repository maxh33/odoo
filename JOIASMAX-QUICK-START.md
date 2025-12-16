# JoiasMax Implementation - Quick Start Guide
## Get Started in 30 Minutes

**Goal**: Set up the foundation for JoiasMax jewelry tenant with dynamic pricing

---

## ✅ What You Already Have

1. **Odoo 18 Deployed Locally** ✅
   - Running at: http://localhost:8069
   - Database: odoo_master
   - Multi-tenant core installed

2. **Product Data Ready** ✅
   - Location: `D:\Programacao\Repositorios\joiasmax-ecommerce\doc\products\produtos_2025-12-10-21-34-15.csv`
   - 1500+ products from Bling
   - **Issue**: All costs = R$ 0.00 (Bling limitation)

3. **Planning Documentation Complete** ✅
   - Dynamic pricing strategy defined
   - 10 planning documents in joiasmax-ecommerce repo
   - N8N workflows designed
   - Database schema planned

---

## 🚀 Phase 1: Foundation Setup (This Week)

### Step 1: Create Tenant Database (5 minutes)

```bash
# Open terminal in Odoo repository
cd D:\Programacao\Repositorios\odoo

# Create JoiasMax tenant database
docker exec -it odoo_postgres psql -U odoo -c "CREATE DATABASE tenant_joiasmax;"

# Add extensions
docker exec -it odoo_postgres psql -U odoo -d tenant_joiasmax -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
docker exec -it odoo_postgres psql -U odoo -d tenant_joiasmax -c "CREATE EXTENSION IF NOT EXISTS unaccent;"
```

**Verify**:
```bash
docker exec -it odoo_postgres psql -U odoo -c "\l" | grep tenant_joiasmax
```

---

### Step 2: Create Jewelry Template Module Structure (10 minutes)

```bash
# Create module directories
cd D:\Programacao\Repositorios\odoo\addons\tenant_templates\jewelry_template

# Create Python package structure
mkdir -p models views security data static/description wizards controllers

# Create __init__.py files
echo "from . import models" > __init__.py
echo "from . import product_template\nfrom . import jewelry_pricing\nfrom . import market_price\nfrom . import supplier_cost\nfrom . import price_history" > models/__init__.py
```

---

### Step 3: Create Database Migration Script (15 minutes)

Create file: `addons/tenant_templates/jewelry_template/data/custom_tables.sql`

```sql
-- Custom tables for JoiasMax dynamic pricing

-- Table 1: Product Pricing Intelligence
CREATE TABLE IF NOT EXISTS joiasmax_product_pricing (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    tenant_id INTEGER,

    -- Material Information
    material_type VARCHAR(50) NOT NULL,
    metal_weight_grams NUMERIC(10, 3),
    metal_purity VARCHAR(10),
    gemstone_type VARCHAR(50),
    gemstone_carats NUMERIC(8, 3),

    -- Cost Components
    material_cost_brl NUMERIC(12, 2),
    labor_cost_brl NUMERIC(12, 2),
    overhead_cost_brl NUMERIC(12, 2),
    total_cost_brl NUMERIC(12, 2),

    -- Pricing Strategy
    markup_percentage NUMERIC(5, 2) DEFAULT 200.00,
    calculated_price_brl NUMERIC(12, 2),
    manual_override_price NUMERIC(12, 2),
    use_manual_override BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(product_id, tenant_id)
);

-- Table 2: Market Prices (Gold, Silver, etc.)
CREATE TABLE IF NOT EXISTS joiasmax_market_prices (
    id SERIAL PRIMARY KEY,
    material_type VARCHAR(50) NOT NULL,
    price_per_gram_brl NUMERIC(12, 4) NOT NULL,
    source_api VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Table 3: Supplier Costs
CREATE TABLE IF NOT EXISTS joiasmax_supplier_costs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    unit_cost_brl NUMERIC(12, 2) NOT NULL,
    last_purchase_date DATE,
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_until DATE,
    is_preferred_supplier BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 4: Price Change History (Audit Trail)
CREATE TABLE IF NOT EXISTS joiasmax_price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    old_price_brl NUMERIC(12, 2),
    new_price_brl NUMERIC(12, 2) NOT NULL,
    price_difference_brl NUMERIC(12, 2),
    change_reason VARCHAR(50) NOT NULL,
    change_details TEXT,
    changed_by_user_id INTEGER,
    gold_price_at_change NUMERIC(12, 4),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_to_woocommerce BOOLEAN DEFAULT FALSE
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_pricing_product ON joiasmax_product_pricing(product_id);
CREATE INDEX IF NOT EXISTS idx_pricing_material ON joiasmax_product_pricing(material_type);
CREATE INDEX IF NOT EXISTS idx_market_active ON joiasmax_market_prices(is_active, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_supplier_product ON joiasmax_supplier_costs(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON joiasmax_price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON joiasmax_price_history(changed_at DESC);

-- Sample Market Price Data (Initial Values)
INSERT INTO joiasmax_market_prices (material_type, price_per_gram_brl, source_api) VALUES
('gold_24k', 385.50, 'manual_initial'),
('gold_18k', 289.13, 'manual_initial'),
('silver_950', 4.50, 'manual_initial'),
('diamond_1ct_vs1', 35000.00, 'manual_initial')
ON CONFLICT DO NOTHING;

COMMENT ON TABLE joiasmax_product_pricing IS 'Jewelry-specific pricing data with material breakdown';
COMMENT ON TABLE joiasmax_market_prices IS 'Current market prices for precious materials';
COMMENT ON TABLE joiasmax_supplier_costs IS 'Historical supplier cost tracking';
COMMENT ON TABLE joiasmax_price_history IS 'Complete audit trail of all price changes';
```

**Run Migration**:
```bash
docker exec -i odoo_postgres psql -U odoo -d tenant_joiasmax < addons/tenant_templates/jewelry_template/data/custom_tables.sql
```

**Verify Tables Created**:
```bash
docker exec -it odoo_postgres psql -U odoo -d tenant_joiasmax -c "\dt joiasmax_*"
```

---

### Step 4: Create Module Manifest

Create file: `addons/tenant_templates/jewelry_template/__manifest__.py`

```python
# -*- coding: utf-8 -*-
{
    'name': 'Jewelry Template - JoiasMax',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Jewelry store template with dynamic pricing for gold/silver products',
    'description': """
        Jewelry Template Module for JoiasMax
        =====================================

        Features:
        ---------
        * Custom product fields for jewelry (metal type, weight, purity, gemstones)
        * Dynamic pricing based on market gold/silver prices
        * Supplier cost tracking and management
        * Complete price change audit trail
        * Integration ready for N8N automation workflows
        * WooCommerce synchronization support

        Custom Database Tables:
        -----------------------
        * joiasmax_product_pricing - Material and pricing data
        * joiasmax_market_prices - Current market rates
        * joiasmax_supplier_costs - Historical supplier costs
        * joiasmax_price_history - Complete price change log

        Use Case:
        ---------
        Designed for jewelry e-commerce businesses that need:
        - Automated price updates based on precious metal market rates
        - Real cost tracking (solving Bling ERP limitation of R$ 0.00 costs)
        - Margin visibility and profitability analysis
        - Integration with e-commerce platforms
    """,
    'author': 'Max Haider',
    'website': 'https://joiasmax.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'sale_management',
        'stock',
        'multi_tenant_core',
    ],
    'data': [
        # Security
        'security/jewelry_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/material_types.xml',
        'data/metal_purities.xml',
        'data/markup_rules.xml',

        # Views
        'views/product_template_views.xml',
        'views/jewelry_pricing_views.xml',
        'views/market_price_views.xml',
        'views/supplier_cost_views.xml',
        'views/price_history_views.xml',
        'views/pricing_dashboard.xml',

        # Menus
        'views/menu_views.xml',

        # Wizards
        'wizards/bulk_price_update_views.xml',
        'wizards/cost_estimation_views.xml',
    ],
    'demo': [
        'demo/demo_products.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
```

---

## 🧪 Testing Your Setup

### Test 1: Database Connection

```bash
# Connect to tenant database
docker exec -it odoo_postgres psql -U odoo -d tenant_joiasmax

# List custom tables
\dt joiasmax_*

# Check sample market prices
SELECT * FROM joiasmax_market_prices;

# Exit
\q
```

**Expected Output**:
```
                        List of relations
 Schema |           Name              | Type  | Owner
--------+-----------------------------+-------+-------
 public | joiasmax_market_prices      | table | odoo
 public | joiasmax_price_history      | table | odoo
 public | joiasmax_product_pricing    | table | odoo
 public | joiasmax_supplier_costs     | table | odoo
```

### Test 2: Odoo Access

1. Open browser: http://localhost:8069
2. Select database: `tenant_joiasmax`
3. Create admin user if prompted
4. Login and verify Odoo dashboard loads

---

## 📋 What's Next (Week 1 Tasks)

### Day 1-2: Python Models (Core Logic)
- [ ] Create `product_template.py` (extends Odoo product model)
- [ ] Create `jewelry_pricing.py` (pricing intelligence model)
- [ ] Create `market_price.py` (market data fetching)
- [ ] Test: Create product via Python console

### Day 3-4: UI Views (User Interface)
- [ ] Create product form with jewelry fields
- [ ] Create pricing dashboard
- [ ] Create supplier cost management UI
- [ ] Test: Add product via UI

### Day 5: Security & Validation
- [ ] Create access control rules
- [ ] Add data validation
- [ ] Create unit tests
- [ ] Test: Multi-user access

---

## 📁 File Checklist

After completing Quick Start, you should have:

```
odoo/addons/tenant_templates/jewelry_template/
├── __init__.py                          ✅ Created
├── __manifest__.py                      ✅ Created
├── models/
│   └── __init__.py                      ✅ Created
├── data/
│   └── custom_tables.sql                ✅ Created
└── [other directories for later]
```

**Database**:
- ✅ tenant_joiasmax database created
- ✅ 4 custom tables created
- ✅ Indexes created
- ✅ Sample market data inserted

---

## 🆘 Troubleshooting

### Issue: "Database already exists"
```bash
# Drop and recreate
docker exec -it odoo_postgres psql -U odoo -c "DROP DATABASE IF EXISTS tenant_joiasmax;"
# Then run Step 1 again
```

### Issue: "Permission denied on table"
```bash
# Grant permissions
docker exec -it odoo_postgres psql -U odoo -d tenant_joiasmax -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO odoo;"
```

### Issue: "Odoo module not found"
- Restart Odoo to detect new modules:
  ```bash
  docker-compose restart odoo_community_18
  ```
- Update apps list in Odoo: Settings → Apps → Update Apps List

---

## 📞 Need Help?

- **Implementation Plan**: See `JOIASMAX-IMPLEMENTATION-PLAN.md` (full technical details)
- **Dynamic Pricing Docs**: See `D:\Programacao\Repositorios\joiasmax-ecommerce\doc\dynamicPricing\`
- **Odoo Documentation**: https://www.odoo.com/documentation/18.0/

---

## ✅ Success Criteria

You'll know this phase is complete when:
- ✅ tenant_joiasmax database exists and accessible
- ✅ 4 custom tables created with correct schema
- ✅ jewelry_template module structure created
- ✅ Module manifest file complete
- ✅ Can connect to database via psql
- ✅ Ready to build Python models

**Estimated Time**: 30-60 minutes
**Next Phase**: Week 1 - Python Models & UI Development

---

Let's build this! 🚀

**Created**: 2025-12-13
**Status**: Ready to Execute
