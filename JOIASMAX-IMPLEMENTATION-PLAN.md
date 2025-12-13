# JoiasMax Jewelry Tenant - Implementation Plan
## Dynamic Pricing System for Multi-Tenant Odoo Platform

**Version**: 1.0
**Date**: 2025-12-13
**Status**: 📋 PLANNING - Ready for Implementation
**Client**: JoiasMax E-commerce (First Production Tenant)

---

## 🎯 Executive Summary

### The Challenge
JoiasMax operates a jewelry e-commerce business with **critical operational risks**:

1. **🔴 ZERO Cost Visibility** (CRITICAL)
   - Bling ERP exports ALL products with "Preço de custo" = R$ 0,00 (100% of products)
   - **IMPOSSIBLE to know actual margins or profitability**
   - Operating "blind" without cost control
   - Cannot identify unprofitable products

2. **🔴 Market Volatility** (PROVEN)
   - Gold price: R$ 365/g → R$ 385.50/g (+5.6% in 9 days)
   - ~1500 gold products affected
   - Manual price updates impossible at scale
   - Risk of selling below market cost

3. **🟡 High Return Rate** (REQUIRES INVESTIGATION)
   - 20.69% returns (R$ 110,561.15 over 4 years)
   - vs. 8-10% industry average (2x higher!)
   - Correlation with pricing needs analysis

### The Solution
**Automated Dynamic Pricing + Real Cost Tracking** using:
- **Odoo 18 Multi-Tenant Platform** (already deployed locally)
- **Custom Jewelry Template** (to be implemented)
- **Hybrid Database Architecture** (PostgreSQL custom tables + Odoo ORM)
- **N8N Automation Workflows** (gold price updates, inventory sync)
- **WooCommerce Integration** (bidirectional sync)

### Timeline
- **Local Development & Testing**: 3-4 weeks
- **VPS Production Deployment**: Week 5
- **Cost Data Calibration Period**: 3 months post-launch

---

## 📊 Current State Analysis

### What We Have ✅
1. **Odoo 18 Deployed Locally**
   - HTTP server running on port 8069
   - PostgreSQL database configured
   - Master database (odoo_master) created
   - Multi-tenant core module installed

2. **Multi-Tenant Infrastructure**
   - Tenant configuration management UI
   - Database routing via subdomain
   - API key generation for tenants
   - Docker compose with Traefik labels

3. **Product Data Available**
   - 1500+ products exported from Bling (CSV)
   - Location: `D:\Programacao\Repositorios\joiasmax-ecommerce\doc\products\produtos_2025-12-10-21-34-15.csv`
   - Data quality: 70% have pricing data buried in HTML descriptions
   - **Critical Issue**: ALL costs = R$ 0,00

4. **Documentation Complete**
   - 10 comprehensive planning documents
   - Dynamic pricing strategy defined
   - Data cleanup methodology documented
   - N8N workflow designs ready

### What We Need to Build ❌
1. **Jewelry Template Module**
   - Custom product fields (metal type, karat, weight, gemstones)
   - Certificate tracking
   - Quality metrics
   - Jewelry-specific pricing logic

2. **Dynamic Pricing Module**
   - Gold price API integration (Metals.dev)
   - Automated price calculation engine
   - Price update workflows
   - Audit trail for all changes

3. **N8N Integration**
   - Webhook handlers in Odoo
   - N8N workflow configurations
   - Authentication and security
   - Error handling and logging

4. **WooCommerce Sync**
   - Product synchronization (Odoo → WooCommerce)
   - Inventory updates
   - Price changes
   - Order management (WooCommerce → Odoo)

5. **Custom Cost Tracking**
   - Hybrid database tables for supplier costs
   - Manual cost input interface
   - Cost estimation algorithms
   - Margin calculation dashboard

---

## 🏗️ Technical Architecture

### Hybrid Database Approach (RECOMMENDED)

**Why Hybrid?**
- Odoo ORM is excellent for standard ERP data (products, customers, orders)
- Custom PostgreSQL tables give us flexibility for complex pricing logic
- Separation of concerns: ERP data vs. pricing intelligence
- Easier to test and maintain pricing algorithms independently

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    ODOO 18 (Multi-Tenant)                       │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │           Odoo ORM (Standard Tables)                      │ │
│  │  - product.template (products)                            │ │
│  │  - res.partner (customers, suppliers)                     │ │
│  │  - sale.order (orders)                                    │ │
│  │  - stock.quant (inventory)                                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            ▲                                    │
│                            │ References                         │
│                            ▼                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │     Custom Tables (Pricing Intelligence)                  │ │
│  │                                                            │ │
│  │  joiasmax_product_pricing:                                │ │
│  │    - product_id (FK to product.template)                  │ │
│  │    - material_type (gold, silver, diamond)                │ │
│  │    - metal_weight_grams                                   │ │
│  │    - metal_purity (18k, 24k, etc.)                        │ │
│  │    - gemstone_type                                        │ │
│  │    - gemstone_carats                                      │ │
│  │    - labor_cost_estimate                                  │ │
│  │    - markup_percentage                                    │ │
│  │    - calculated_price                                     │ │
│  │    - last_updated                                         │ │
│  │                                                            │ │
│  │  joiasmax_market_prices:                                  │ │
│  │    - material_type                                        │ │
│  │    - price_per_gram_brl                                   │ │
│  │    - timestamp                                            │ │
│  │    - source_api                                           │ │
│  │                                                            │ │
│  │  joiasmax_supplier_costs:                                 │ │
│  │    - product_id                                           │ │
│  │    - supplier_id (FK to res.partner)                      │ │
│  │    - cost_brl                                             │ │
│  │    - last_purchase_date                                   │ │
│  │    - minimum_order_quantity                               │ │
│  │                                                            │ │
│  │  joiasmax_price_history:                                  │ │
│  │    - product_id                                           │ │
│  │    - old_price                                            │ │
│  │    - new_price                                            │ │
│  │    - reason (gold_price_change, manual, cost_update)      │ │
│  │    - changed_by                                           │ │
│  │    - timestamp                                            │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       N8N Automation                            │
│                                                                 │
│  Workflow 1: Gold Price Updater (Every 4 hours)                │
│    1. Fetch current gold price (Metals.dev API)                │
│    2. Compare with joiasmax_market_prices                      │
│    3. Calculate new prices for affected products               │
│    4. Update joiasmax_product_pricing.calculated_price         │
│    5. Sync to product.template.list_price (Odoo)               │
│    6. Log to joiasmax_price_history                            │
│    7. Sync to WooCommerce                                      │
│                                                                 │
│  Workflow 2: WooCommerce Product Sync (On demand)              │
│  Workflow 3: Inventory Alerts (When stock < threshold)         │
│  Workflow 4: Cost Update Alerts (When supplier costs change)   │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WooCommerce (joiasmax.com)                   │
│  - Product catalog synchronized from Odoo                       │
│  - Prices updated automatically                                │
│  - Orders sent back to Odoo                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Approach Works

**Advantages:**
1. **Flexibility**: Custom pricing logic without modifying Odoo core
2. **Performance**: Optimized queries for pricing calculations
3. **Testability**: Can test pricing algorithms independently
4. **Maintainability**: Clear separation of ERP vs. pricing intelligence
5. **Auditability**: Complete price change history in dedicated tables
6. **Scalability**: Easy to add new pricing rules or materials

**Integration Points:**
- Custom tables reference Odoo product IDs (foreign keys)
- Python models bridge Odoo ORM and custom tables
- N8N workflows update both systems atomically
- API endpoints expose pricing data to external systems

---

## 📦 Module Structure

### 1. Jewelry Template Module
**Location**: `addons/tenant_templates/jewelry_template/`

```
jewelry_template/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── product_template.py          # Extends Odoo product model
│   ├── jewelry_pricing.py           # Custom pricing model (hybrid)
│   ├── market_price.py              # Market price tracking
│   ├── supplier_cost.py             # Supplier cost management
│   └── price_history.py             # Audit trail
├── views/
│   ├── product_template_views.xml   # Product form with jewelry fields
│   ├── pricing_dashboard.xml        # Pricing management UI
│   ├── cost_management_views.xml    # Supplier cost input
│   └── price_history_views.xml      # Audit log viewer
├── security/
│   ├── ir.model.access.csv          # Access control
│   └── pricing_security.xml         # Record rules
├── data/
│   ├── material_types.xml           # Pre-defined materials
│   ├── metal_purities.xml           # 18k, 24k, etc.
│   └── markup_rules.xml             # Default markup by category
└── static/
    └── description/
        └── icon.png
```

### 2. Dynamic Pricing Module
**Location**: `addons/automation_workflows/pricing_automation/`

```
pricing_automation/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── pricing_engine.py            # Core calculation logic
│   └── price_calculator.py          # Formula implementations
├── controllers/
│   ├── __init__.py
│   └── api_pricing.py               # REST API endpoints
├── wizards/
│   ├── __init__.py
│   ├── bulk_price_update.py         # Manual bulk updates
│   └── cost_estimation.py           # Help estimate missing costs
├── cron/
│   └── price_sync_jobs.xml          # Scheduled tasks
└── tests/
    ├── __init__.py
    ├── test_pricing_engine.py
    └── test_price_calculations.py
```

### 3. N8N Connector Module
**Location**: `addons/n8n_connector/`

```
n8n_connector/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── n8n_webhook.py               # Webhook registry
│   └── n8n_config.py                # N8N connection settings
├── controllers/
│   ├── __init__.py
│   ├── webhook_receiver.py          # Receive N8N webhooks
│   └── webhook_sender.py            # Send data to N8N
├── security/
│   ├── ir.model.access.csv
│   └── webhook_security.xml
└── data/
    └── webhook_templates.xml         # Pre-defined webhook endpoints
```

### 4. WooCommerce Connector Module
**Location**: `addons/integration_modules/woocommerce_connector/`

```
woocommerce_connector/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── woo_config.py                # WooCommerce credentials
│   ├── woo_product_sync.py          # Product synchronization
│   ├── woo_order_import.py          # Import orders from WooCommerce
│   └── sync_queue.py                # Sync queue management
├── wizards/
│   ├── __init__.py
│   ├── manual_sync.py               # Manual sync wizard
│   └── sync_history.py              # View sync logs
└── cron/
    └── auto_sync_jobs.xml           # Automatic sync schedule
```

---

## 🗄️ Database Schema (Custom Tables)

### Table: joiasmax_product_pricing
**Purpose**: Store jewelry-specific pricing data linked to Odoo products

```sql
CREATE TABLE joiasmax_product_pricing (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES product_template(id) ON DELETE CASCADE,
    tenant_id INTEGER REFERENCES tenant_config(id),

    -- Material Information
    material_type VARCHAR(50) NOT NULL,  -- 'gold', 'silver', 'diamond', 'gemstone'
    metal_weight_grams NUMERIC(10, 3),
    metal_purity VARCHAR(10),            -- '18k', '24k', '950', etc.
    gemstone_type VARCHAR(50),
    gemstone_carats NUMERIC(8, 3),
    gemstone_quality VARCHAR(20),        -- 'VS1', 'VVS', etc.

    -- Cost Components
    material_cost_brl NUMERIC(12, 2),    -- Calculated from weight × market price
    labor_cost_brl NUMERIC(12, 2),       -- Manual input or estimated
    overhead_cost_brl NUMERIC(12, 2),    -- Fixed overhead per piece
    total_cost_brl NUMERIC(12, 2),       -- Sum of above

    -- Pricing Strategy
    markup_percentage NUMERIC(5, 2) DEFAULT 200.00,  -- Default 200% markup
    calculated_price_brl NUMERIC(12, 2), -- Auto-calculated selling price
    manual_override_price NUMERIC(12, 2), -- If manually set
    use_manual_override BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES res_users(id),
    updated_by INTEGER REFERENCES res_users(id),

    -- Constraints
    UNIQUE(product_id, tenant_id),
    CHECK (metal_weight_grams >= 0),
    CHECK (markup_percentage >= 0),
    CHECK (calculated_price_brl >= 0)
);

CREATE INDEX idx_pricing_product ON joiasmax_product_pricing(product_id);
CREATE INDEX idx_pricing_material ON joiasmax_product_pricing(material_type);
CREATE INDEX idx_pricing_tenant ON joiasmax_product_pricing(tenant_id);
```

### Table: joiasmax_market_prices
**Purpose**: Track current market prices for precious materials

```sql
CREATE TABLE joiasmax_market_prices (
    id SERIAL PRIMARY KEY,
    material_type VARCHAR(50) NOT NULL,  -- 'gold_24k', 'gold_18k', 'silver_950', etc.
    price_per_gram_brl NUMERIC(12, 4) NOT NULL,
    price_per_gram_usd NUMERIC(12, 4),

    -- Source Information
    source_api VARCHAR(100),             -- 'metals.dev', 'manual', etc.
    api_response_json JSONB,             -- Raw API response

    -- Timestamps
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,               -- Cache expiration

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,

    CHECK (price_per_gram_brl > 0)
);

CREATE INDEX idx_market_material ON joiasmax_market_prices(material_type);
CREATE INDEX idx_market_active ON joiasmax_market_prices(is_active, fetched_at DESC);
```

### Table: joiasmax_supplier_costs
**Purpose**: Track supplier-specific costs for products

```sql
CREATE TABLE joiasmax_supplier_costs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES product_template(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES res_partner(id) ON DELETE CASCADE,

    -- Cost Data
    unit_cost_brl NUMERIC(12, 2) NOT NULL,
    currency_code VARCHAR(3) DEFAULT 'BRL',

    -- Purchase Information
    last_purchase_date DATE,
    minimum_order_quantity INTEGER DEFAULT 1,
    lead_time_days INTEGER,

    -- Validity
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_until DATE,
    is_preferred_supplier BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,

    UNIQUE(product_id, supplier_id, valid_from),
    CHECK (unit_cost_brl >= 0),
    CHECK (minimum_order_quantity > 0)
);

CREATE INDEX idx_supplier_cost_product ON joiasmax_supplier_costs(product_id);
CREATE INDEX idx_supplier_cost_supplier ON joiasmax_supplier_costs(supplier_id);
CREATE INDEX idx_supplier_cost_preferred ON joiasmax_supplier_costs(is_preferred_supplier, valid_until);
```

### Table: joiasmax_price_history
**Purpose**: Complete audit trail of all price changes

```sql
CREATE TABLE joiasmax_price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES product_template(id) ON DELETE CASCADE,

    -- Price Change
    old_price_brl NUMERIC(12, 2),
    new_price_brl NUMERIC(12, 2) NOT NULL,
    price_difference_brl NUMERIC(12, 2),  -- new - old
    price_difference_percent NUMERIC(8, 4),

    -- Reason
    change_reason VARCHAR(50) NOT NULL,   -- 'gold_price_change', 'manual_update', 'cost_update', 'market_competition'
    change_details TEXT,                  -- Additional context

    -- Attribution
    changed_by_user_id INTEGER REFERENCES res_users(id),
    changed_by_system VARCHAR(50),        -- 'n8n_workflow', 'api', 'manual'

    -- Market Context (at time of change)
    gold_price_at_change NUMERIC(12, 4),
    material_cost_at_change NUMERIC(12, 2),

    -- Timestamps
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_to_woocommerce BOOLEAN DEFAULT FALSE,
    synced_at TIMESTAMP,

    CHECK (new_price_brl >= 0)
);

CREATE INDEX idx_price_history_product ON joiasmax_price_history(product_id);
CREATE INDEX idx_price_history_date ON joiasmax_price_history(changed_at DESC);
CREATE INDEX idx_price_history_reason ON joiasmax_price_history(change_reason);
CREATE INDEX idx_price_history_sync ON joiasmax_price_history(synced_to_woocommerce);
```

---

## 🔧 Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal**: Set up basic jewelry template and custom database tables

**Tasks**:
1. ✅ **Create Jewelry Template Module Structure**
   ```bash
   cd D:\Programacao\Repositorios\odoo\addons\tenant_templates
   mkdir -p jewelry_template/{models,views,security,data,static/description}
   ```

2. ✅ **Define Custom Database Tables**
   - Create SQL migration script
   - Test table creation on local PostgreSQL
   - Add foreign key constraints
   - Create indexes

3. ✅ **Create Python ORM Models**
   - `JewelryProductPricing` (bridges Odoo product → custom table)
   - `MarketPrice` (fetches and stores market data)
   - `SupplierCost` (manages supplier cost database)
   - `PriceHistory` (audit logging)

4. ✅ **Build Basic UI Views**
   - Extended product form with jewelry fields
   - Cost management interface
   - Price history viewer

**Deliverables**:
- Functional jewelry template module
- Custom tables created in PostgreSQL
- Basic CRUD operations working
- UI accessible in Odoo backend

**Testing**:
- Create test product with jewelry attributes
- Input supplier cost
- Verify data saved to custom tables
- Check Odoo product linking

---

### Phase 2: Data Migration (Week 2)
**Goal**: Import JoiasMax products from Bling CSV into Odoo

**Tasks**:
1. ✅ **Data Extraction & Cleanup**
   - Read CSV: `produtos_2025-12-10-21-34-15.csv`
   - Parse HTML descriptions for jewelry data (weight, material, karat)
   - Extract structured data using regex patterns
   - Handle missing/malformed data

2. ✅ **Create Migration Script**
   ```python
   # Location: scripts/joiasmax_migration/import_products.py

   import csv
   import re
   import xmlrpc.client

   # Connect to Odoo
   url = 'http://localhost:8069'
   db = 'tenant_joiasmax'
   username = 'admin'
   password = 'admin'

   common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
   uid = common.authenticate(db, username, password, {})
   models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

   # Import products
   # ... (full script in Phase 2 section below)
   ```

3. ✅ **Cost Estimation Workflow**
   - For products with material data → calculate material cost
   - For products without → flag for manual review
   - Create wizard UI for bulk cost estimation

4. ✅ **Quality Validation**
   - Check for duplicate SKUs
   - Validate price > 0
   - Ensure category mapping
   - Verify image URLs

**Deliverables**:
- 1500+ products imported to Odoo
- Jewelry attributes populated where possible
- Cost estimates for gold products
- Import report with statistics

**Testing**:
- Spot-check 20 random products
- Verify gold products have weight/karat
- Check product categories
- Validate images display correctly

---

### Phase 3: Pricing Engine (Week 3)
**Goal**: Implement automated dynamic pricing calculation

**Tasks**:
1. ✅ **Gold Price API Integration**
   ```python
   # models/market_price.py

   import requests
   from odoo import models, fields, api

   class MarketPrice(models.Model):
       _name = 'joiasmax.market.price'
       _description = 'Market Prices for Precious Materials'

       def fetch_gold_price(self):
           """Fetch current gold price from Metals.dev API"""
           api_key = self.env['ir.config_parameter'].sudo().get_param('gold_price_api_key')
           url = f'https://api.metals.dev/v1/latest?api_key={api_key}&currency=BRL&unit=gram'

           response = requests.get(url, timeout=10)
           data = response.json()

           # Store in joiasmax_market_prices table
           self.env.cr.execute("""
               INSERT INTO joiasmax_market_prices
               (material_type, price_per_gram_brl, source_api, fetched_at)
               VALUES (%s, %s, %s, NOW())
           """, ('gold_24k', data['gold'], 'metals.dev'))

           return data['gold']
   ```

2. ✅ **Pricing Calculation Engine**
   ```python
   # models/pricing_engine.py

   def calculate_product_price(self, product_id):
       """Calculate selling price based on current market rates"""

       # Get product pricing data
       pricing = self.env.cr.execute("""
           SELECT metal_weight_grams, metal_purity, labor_cost_brl, markup_percentage
           FROM joiasmax_product_pricing
           WHERE product_id = %s
       """, (product_id,))

       weight, purity, labor, markup = pricing.fetchone()

       # Get current gold price
       gold_price = self._get_latest_market_price('gold_24k')

       # Apply purity factor (18k = 75% of 24k)
       purity_factor = 0.75 if purity == '18k' else 1.0
       material_cost = weight * gold_price * purity_factor

       # Calculate selling price
       total_cost = material_cost + labor
       selling_price = total_cost * (1 + markup / 100)

       return selling_price
   ```

3. ✅ **Price Update Mechanism**
   - Detect price changes > threshold (e.g., 2%)
   - Update product.template.list_price
   - Log to joiasmax_price_history
   - Queue for WooCommerce sync

4. ✅ **Manual Override Support**
   - UI to manually set prices
   - Flag products with manual pricing
   - Don't auto-update flagged products

**Deliverables**:
- Gold price fetched from API
- Automated price calculation working
- Price update mechanism functional
- Manual override system

**Testing**:
- Manually change gold price in DB → verify prices update
- Test with different karats (18k, 24k)
- Verify labor costs included
- Check markup applied correctly

---

### Phase 4: N8N Integration (Week 3-4)
**Goal**: Set up N8N workflows for automation

**Tasks**:
1. ✅ **Deploy N8N Locally**
   ```yaml
   # docker-compose-n8n.yml (add to main docker-compose)

   services:
     n8n:
       image: n8nio/n8n:latest
       ports:
         - "5678:5678"
       environment:
         - N8N_BASIC_AUTH_ACTIVE=true
         - N8N_BASIC_AUTH_USER=admin
         - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
         - WEBHOOK_URL=http://localhost:5678
       volumes:
         - n8n_data:/home/node/.n8n
       networks:
         - odoo_internal

   volumes:
     n8n_data:
   ```

2. ✅ **Create Webhook Endpoints in Odoo**
   ```python
   # controllers/webhook_receiver.py

   from odoo import http
   import json

   class N8NWebhookReceiver(http.Controller):

       @http.route('/api/n8n/gold-price-update', type='json', auth='public', methods=['POST'])
       def receive_gold_price(self, **kw):
           """Receive gold price update from N8N"""
           data = json.loads(request.httprequest.data)

           # Validate webhook signature
           if not self._validate_signature(data.get('signature')):
               return {'error': 'Invalid signature'}

           # Process price update
           gold_price = data.get('gold_price_brl')
           self.env['joiasmax.market.price'].create_from_webhook(gold_price)

           # Trigger price recalculation
           self.env['joiasmax.pricing.engine'].update_all_gold_products()

           return {'status': 'success', 'products_updated': count}
   ```

3. ✅ **Build N8N Workflows**

   **Workflow 1: Gold Price Automation** (See N8N section below for full JSON)
   - Trigger: Cron (every 4 hours)
   - Nodes: HTTP Request → Data Transformation → Odoo Webhook → Telegram Notification

4. ✅ **Testing N8N Integration**
   - Test webhook locally with Postman
   - Verify Odoo receives data correctly
   - Check price calculations triggered
   - Confirm Telegram notifications sent

**Deliverables**:
- N8N running locally
- Gold price workflow active
- Odoo webhooks functional
- End-to-end automation working

---

### Phase 5: WooCommerce Sync (Week 4)
**Goal**: Bidirectional synchronization with WooCommerce

**Tasks**:
1. ✅ **WooCommerce REST API Client**
   ```python
   # models/woo_config.py

   from woocommerce import API

   class WooConfig(models.Model):
       _name = 'woo.config'

       def get_api_client(self):
           return API(
               url=self.woo_url,
               consumer_key=self.woo_consumer_key,
               consumer_secret=self.woo_consumer_secret,
               version="wc/v3",
               timeout=30
           )
   ```

2. ✅ **Product Sync (Odoo → WooCommerce)**
   ```python
   def sync_product_to_woocommerce(self, product_id):
       """Push product updates to WooCommerce"""
       product = self.env['product.template'].browse(product_id)
       wc_api = self.env['woo.config'].get_api_client()

       data = {
           'name': product.name,
           'regular_price': str(product.list_price),
           'description': product.description_sale,
           'short_description': product.description,
           'sku': product.default_code,
           'manage_stock': True,
           'stock_quantity': int(product.qty_available),
           'images': [{'src': img.url} for img in product.image_ids],
       }

       if product.woo_product_id:
           # Update existing
           wc_api.put(f'products/{product.woo_product_id}', data)
       else:
           # Create new
           response = wc_api.post('products', data)
           product.woo_product_id = response.json()['id']
   ```

3. ✅ **Order Import (WooCommerce → Odoo)**
   - Webhook from WooCommerce on order creation
   - Create sale.order in Odoo
   - Update inventory
   - Sync order status changes

4. ✅ **Sync Queue Management**
   - Queue products for sync (avoid rate limits)
   - Retry failed syncs
   - Track sync status per product

**Deliverables**:
- Products sync to WooCommerce
- Prices update automatically
- Orders import from WooCommerce
- Inventory synchronized

**Testing**:
- Create product in Odoo → verify in WooCommerce
- Update price in Odoo → check WooCommerce updated
- Place order in WooCommerce → verify imported to Odoo
- Update stock in Odoo → check WooCommerce reflects

---

### Phase 6: Local Testing & Validation (Week 4)
**Goal**: Comprehensive testing before VPS deployment

**Test Scenarios**:

1. ✅ **Multi-Tenant Isolation**
   - Create second test tenant
   - Verify database filtering works
   - Check no data leakage between tenants
   - Test API authentication per tenant

2. ✅ **Pricing Automation End-to-End**
   ```
   Test Flow:
   1. Manually set gold price in joiasmax_market_prices
   2. Wait for N8N cron trigger (or trigger manually)
   3. Verify gold products have new calculated prices
   4. Check joiasmax_price_history logged changes
   5. Confirm WooCommerce products updated
   6. Validate Telegram notification sent
   ```

3. ✅ **Data Integrity**
   - Foreign key constraints enforced
   - No orphaned records
   - Audit trail complete
   - Cost calculations accurate

4. ✅ **Performance Testing**
   - Bulk price update (1500 products)
   - Query response times
   - Database index usage
   - API endpoint latency

5. ✅ **Error Handling**
   - API unavailable → graceful degradation
   - Invalid data → validation errors
   - Network timeout → retry logic
   - Database errors → rollback transactions

**Testing Checklist**:
```
☐ Create tenant: tenant_joiasmax
☐ Import 100 sample products
☐ Set gold price manually
☐ Trigger pricing calculation
☐ Verify prices updated in Odoo
☐ Check price history logged
☐ Test WooCommerce sync
☐ Create test order in WooCommerce
☐ Verify order imported to Odoo
☐ Test N8N workflows manually
☐ Check Telegram notifications
☐ Validate multi-tenant isolation
☐ Performance test: 1500 products
☐ Error scenarios: API down, invalid data
☐ Backup and restore test
```

---

### Phase 7: VPS Production Deployment (Week 5)
**Goal**: Deploy to production VPS (maxhaider.dev)

**Prerequisites**:
- ✅ All local tests passing
- ✅ Documentation complete
- ✅ Backup procedures verified
- ✅ Rollback plan documented

**Deployment Steps**:

1. ✅ **VPS Preparation**
   ```bash
   # SSH to VPS
   ssh your_user@maxhaider.dev

   # Clone Odoo repository
   cd ~
   git clone <odoo-repo-url> odoo-platform
   cd odoo-platform

   # Configure environment
   cp .env.example .env
   nano .env  # Set production values
   ```

2. ✅ **Database Setup**
   ```bash
   # Start PostgreSQL
   docker-compose up -d odoo_postgres

   # Create tenant database
   ./scripts/create-tenant.sh joiasmax jewelry "JoiasMax E-commerce"
   ```

3. ✅ **Odoo Deployment**
   ```bash
   # Deploy Odoo with Traefik routing
   docker-compose up -d odoo_community_18

   # Check logs
   docker logs odoo_community_18 | grep "HTTP service"

   # Verify accessible
   curl -I https://odoo.maxhaider.dev
   curl -I https://joiasmax.odoo.maxhaider.dev
   ```

4. ✅ **Module Installation**
   ```bash
   # Install jewelry template via UI
   # https://joiasmax.odoo.maxhaider.dev/web
   # Apps → Update Apps List → Search "Jewelry Template" → Install
   ```

5. ✅ **Data Migration to Production**
   ```bash
   # Run import script on VPS
   cd ~/odoo-platform/scripts/joiasmax_migration
   python3 import_products.py --env production --dry-run

   # If dry-run looks good:
   python3 import_products.py --env production
   ```

6. ✅ **N8N Deployment**
   ```bash
   # Deploy N8N to VPS
   docker-compose -f docker-compose.n8n.yml up -d

   # Access: https://n8n.maxhaider.dev
   # Import workflow JSONs
   # Update webhook URLs to production
   ```

7. ✅ **WooCommerce Configuration**
   - Update joiasmax.com WooCommerce settings
   - Set Odoo webhook URL: `https://joiasmax.odoo.maxhaider.dev/api/woo/order-webhook`
   - Test product sync
   - Test order creation

8. ✅ **Monitoring Setup**
   - Add Odoo to Prometheus scrape targets
   - Create Grafana dashboard for JoiasMax metrics
   - Set up alerts (price update failures, sync errors)
   - Configure Uptime Kuma checks

**Production Validation**:
```
☐ Tenant database created
☐ Odoo accessible via subdomain
☐ SSL certificate active
☐ Jewelry template installed
☐ Products imported successfully
☐ N8N workflows deployed
☐ WooCommerce sync working
☐ Monitoring dashboards showing data
☐ Backups running automatically
☐ Team trained on system usage
```

---

## 📋 N8N Workflow Configurations

### Workflow 1: Gold Price Auto-Update
**File**: `n8n_workflows/gold_price_updater.json`

```json
{
  "name": "JoiasMax - Gold Price Auto-Update",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "hoursInterval": 4
            }
          ]
        }
      },
      "name": "Every 4 Hours",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300]
    },
    {
      "parameters": {
        "url": "https://api.metals.dev/v1/latest",
        "queryParameters": {
          "parameters": [
            {
              "name": "api_key",
              "value": "={{$env.METALS_API_KEY}}"
            },
            {
              "name": "currency",
              "value": "BRL"
            },
            {
              "name": "unit",
              "value": "gram"
            }
          ]
        }
      },
      "name": "Fetch Gold Price API",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "functionCode": "// Extract gold price from API response\nconst goldPrice = items[0].json.metals.gold;\nconst timestamp = new Date().toISOString();\n\n// Calculate 18k price (75% of 24k)\nconst gold18k = goldPrice * 0.75;\n\nreturn [\n  {\n    json: {\n      gold_24k_brl: goldPrice,\n      gold_18k_brl: gold18k,\n      timestamp: timestamp,\n      source: 'metals.dev'\n    }\n  }\n];"
      },
      "name": "Transform Data",
      "type": "n8n-nodes-base.function",
      "position": [650, 300]
    },
    {
      "parameters": {
        "url": "https://joiasmax.odoo.maxhaider.dev/api/n8n/gold-price-update",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "method": "POST",
        "jsonParameters": true,
        "bodyParametersJson": "={\n  \"gold_24k\": {{$json[\"gold_24k_brl\"]}},\n  \"gold_18k\": {{$json[\"gold_18k_brl\"]}},\n  \"timestamp\": \"{{$json[\"timestamp\"]}}\",\n  \"signature\": \"{{$env.WEBHOOK_SECRET}}\"\n}"
      },
      "name": "Update Odoo Prices",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 300]
    },
    {
      "parameters": {
        "chatId": "={{$env.TELEGRAM_CHAT_ID}}",
        "text": "=🏅 Gold Price Updated!\n\n24K: R$ {{$json[\"gold_24k_brl\"]}} /g\n18K: R$ {{$json[\"gold_18k_brl\"]}} /g\n\nProducts updated: {{$node[\"Update Odoo Prices\"].json[\"products_updated\"]}}\n\nTime: {{$json[\"timestamp\"]}}"
      },
      "name": "Send Telegram Notification",
      "type": "n8n-nodes-base.telegram",
      "position": [1050, 300]
    }
  ],
  "connections": {
    "Every 4 Hours": {
      "main": [[{"node": "Fetch Gold Price API", "type": "main", "index": 0}]]
    },
    "Fetch Gold Price API": {
      "main": [[{"node": "Transform Data", "type": "main", "index": 0}]]
    },
    "Transform Data": {
      "main": [[{"node": "Update Odoo Prices", "type": "main", "index": 0}]]
    },
    "Update Odoo Prices": {
      "main": [[{"node": "Send Telegram Notification", "type": "main", "index": 0}]]
    }
  }
}
```

### Workflow 2: WooCommerce Product Sync
**Trigger**: Manual or on Odoo product update

```json
{
  "name": "JoiasMax - Sync Product to WooCommerce",
  "nodes": [
    {
      "parameters": {
        "path": "product-sync",
        "options": {}
      },
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "webhookId": "joiasmax-product-sync",
      "position": [250, 300]
    },
    {
      "parameters": {
        "url": "https://joiasmax.odoo.maxhaider.dev/api/products/={{$json[\"product_id\"]}}",
        "authentication": "genericCredentialType"
      },
      "name": "Fetch Product from Odoo",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "resource": "product",
        "operation": "update",
        "productId": "={{$json[\"woo_product_id\"]}}",
        "updateFields": {
          "name": "={{$json[\"name\"]}}",
          "regularPrice": "={{$json[\"list_price\"]}}",
          "stockQuantity": "={{$json[\"qty_available\"]}}"
        }
      },
      "name": "Update WooCommerce Product",
      "type": "n8n-nodes-base.wooCommerce",
      "position": [650, 300]
    }
  ],
  "connections": {
    "Webhook Trigger": {
      "main": [[{"node": "Fetch Product from Odoo", "type": "main", "index": 0}]]
    },
    "Fetch Product from Odoo": {
      "main": [[{"node": "Update WooCommerce Product", "type": "main", "index": 0}]]
    }
  }
}
```

---

## 🧪 Testing Strategy

### Local Testing Environment
**Setup**:
```bash
# Use local docker-compose with test data
docker-compose -f docker-compose.test.yml up -d

# Create test tenant
./scripts/create-tenant.sh test_jewelry jewelry "Test Store"

# Import sample products (100 items)
python3 scripts/import_products.py --limit 100 --tenant test_jewelry
```

### Test Data
**Sample Products** (from Bling CSV):
1. Gold earrings (18k, weight data in description)
2. Silver bracelet (925, no weight → needs manual cost)
3. Diamond pendant (price only, no material data)
4. Wedding rings (blend gold+silver)
5. Children's jewelry (lighter weight)

### Manual Testing Scenarios

**Scenario 1: Gold Price Change Impact**
```
1. Set initial gold price: R$ 365/g
2. Create/import 10 gold products with weights
3. Verify calculated prices match expected
4. Change gold price to R$ 385.50/g (+5.6%)
5. Trigger price recalculation
6. Verify all 10 products updated proportionally
7. Check price_history table has 10 entries
8. Confirm WooCommerce prices updated
```

**Scenario 2: Multi-Tenant Isolation**
```
1. Create tenant_a with product X
2. Create tenant_b with product Y
3. Login as tenant_a admin
4. Verify cannot see tenant_b products
5. Check database: product X has tenant_a_id
6. API call to tenant_b → should be unauthorized
```

**Scenario 3: Manual Cost Override**
```
1. Product has calculated cost R$ 500
2. User manually sets cost to R$ 600
3. Set manual_override flag = true
4. Gold price changes
5. Verify product price NOT updated (override active)
6. User removes override
7. Next price update → product uses calculated cost
```

---

## 📊 Success Metrics

### Post-Implementation (Month 1)
- ✅ **100% products** have real cost data (not R$ 0.00)
- ✅ **Gold prices** updated 3-6x daily automatically
- ✅ **<5% products** require manual review
- ✅ **95%+ data quality** score
- ✅ **<5 minutes** Odoo → WooCommerce sync time
- ✅ **Zero price gaps** >2% from market

### Month 2-3 (Calibration Period)
- 📊 Refine supplier cost estimates
- 📊 Adjust markup percentages per category
- 📊 Analyze correlation: pricing vs. returns
- 📊 Identify profitable product lines
- 📊 Optimize inventory based on margins

### Long-Term (6+ months)
- 💰 **Time savings**: 10h/week → <1h/week (520 hours/year saved)
- 💰 **Prevented losses**: First prevented loss pays for system
- 💰 **Margin optimization**: Data-driven pricing decisions
- 💰 **Reduced returns**: Investigate if pricing correlation exists

---

## 🔐 Security Considerations

### API Authentication
- JWT tokens for tenant API access
- Webhook signature validation (HMAC-SHA256)
- Rate limiting on public endpoints
- IP whitelisting for N8N webhooks

### Database Security
- Row-level security for multi-tenant
- Encrypted connections (SSL/TLS)
- Regular automated backups
- Separate database users per service

### Odoo Security
- Two-factor authentication enabled
- Password policies enforced
- Session timeout configured
- Audit logging active

---

## 📝 Documentation Deliverables

1. ✅ **This Implementation Plan**
2. **User Manual** (for JoiasMax team):
   - How to add new products
   - How to set supplier costs
   - How to view pricing dashboard
   - How to handle price alerts
3. **Technical Documentation**:
   - Database schema reference
   - API endpoint documentation
   - N8N workflow guide
   - Troubleshooting common issues
4. **Operational Runbook**:
   - Daily checks
   - Weekly maintenance
   - Backup verification
   - Incident response procedures

---

## 🚨 Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Gold API unavailable | Price updates fail | Medium | Cache last known price, retry logic, manual override |
| Data migration errors | Wrong product data | Low | Extensive validation, manual review flagged items |
| Performance issues | Slow price updates | Medium | Database indexing, query optimization, batch processing |
| WooCommerce sync fails | Price mismatch | Medium | Sync queue with retry, monitoring alerts, manual sync UI |
| Cost estimation inaccurate | Wrong margins | High (initial) | 3-month calibration period, supplier verification, gradual refinement |
| Multi-tenant data leak | Security breach | Very Low | Row-level security, extensive testing, audit logging |

---

## 💼 Team Responsibilities

### During Implementation
- **Developer**: Build modules, write tests, deploy to VPS
- **JoiasMax Team**: Provide supplier cost data, validate migrated products, test UI
- **DevOps**: VPS setup, monitoring configuration, backup verification

### Post-Launch
- **JoiasMax Admin**: Daily: Check price alerts, review flagged products
- **JoiasMax Admin**: Weekly: Update supplier costs, validate margins
- **Developer**: Monthly: Review performance metrics, optimize queries
- **Developer**: Quarterly: Update dependencies, security patches

---

## 📞 Support & Escalation

### Issues During Implementation
- Development questions → Check documentation first
- Bugs/errors → Create GitHub issue with logs
- Urgent blockers → Direct communication

### Post-Launch Support
- **Tier 1** (User errors): Self-service via user manual
- **Tier 2** (Data issues): JoiasMax admin reviews
- **Tier 3** (System bugs): Developer investigation

---

## ✅ Next Steps

### Immediate (This Week)
1. Review this implementation plan
2. Approve architecture approach
3. Set up development environment
4. Create jewelry_template module structure

### Week 1
1. Implement custom database tables
2. Build Python ORM models
3. Create basic UI views
4. Test on sample products

### Week 2
1. Data extraction from Bling CSV
2. Migration script development
3. Import to local Odoo
4. Validation and cleanup

### Week 3
1. Pricing engine implementation
2. Gold API integration
3. N8N deployment and workflows
4. End-to-end testing

### Week 4
1. WooCommerce connector
2. Comprehensive testing
3. Performance optimization
4. Documentation finalization

### Week 5
1. VPS production deployment
2. Real data migration
3. Team training
4. Go live! 🚀

---

## 📚 Reference Links

- **Odoo 18 Documentation**: https://www.odoo.com/documentation/18.0/
- **N8N Documentation**: https://docs.n8n.io/
- **Metals.dev API**: https://metals.dev/
- **WooCommerce REST API**: https://woocommerce.github.io/woocommerce-rest-api-docs/
- **PostgreSQL 15 Docs**: https://www.postgresql.org/docs/15/

---

**Status**: ✅ Ready for Review and Implementation
**Last Updated**: 2025-12-13
**Next Review**: After Phase 1 completion

---

Let's build this! 🚀
