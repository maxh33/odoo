# Odoo Tenant Templates

Multi-tenant business templates for Odoo 18.0 Community Edition, providing pre-configured modules for different industries and business types.

## 📋 Available Templates

### 1. Jewelry Template (`jewelry_template/`)
Specialized template for jewelry e-commerce businesses with dynamic pricing based on precious metal market rates.

**Key Features:**
- ✅ Dynamic gold/silver pricing automation
- ✅ Product catalog import from Bling ERP exports
- ✅ Real cost tracking and margin analysis
- ✅ WooCommerce/E-commerce synchronization
- ✅ Material weight and purity tracking
- ✅ Automated price updates via N8N webhooks

**Ideal For:** Jewelry stores, precious metals dealers, gemstone retailers

---

## 🚀 Quick Start Guide

### Prerequisites

1. **Odoo 18.0 Community** running with Docker or local installation
2. **Python 3.8+** for running import scripts
3. **Database access** via Odoo XML-RPC API
4. **CSV export** from your source system (Bling, WooCommerce, etc.)

### Installation

#### Method 1: Docker Deployment (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd odoo-platform

# 2. Start Odoo with tenant templates
docker-compose up -d

# 3. Access Odoo
# Open browser: http://localhost:8069
# Create database: tenant_jewelry_store_1
```

#### Method 2: Local Development

```bash
# 1. Add templates to Odoo addons path
ln -s /path/to/tenant_templates /path/to/odoo/addons/tenant_templates

# 2. Update Odoo configuration
# Edit odoo.conf:
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/path/to/tenant_templates

# 3. Restart Odoo
./odoo-bin -c odoo.conf
```

### Activating a Template

1. **Create Tenant Database**
   ```
   Database Name: tenant_jewelry_store_1
   Admin Email: admin@yourstore.com
   Password: [secure_password]
   Country: Brazil
   Language: Portuguese (Brazil)
   ```

2. **Install Template Module**
   - Navigate to: **Apps** menu
   - Remove "Apps" filter
   - Search: `jewelry_template`
   - Click **Install**

3. **Configure Template**
   - Go to: **Jewelry → Configuration**
   - Set up market prices (gold, silver)
   - Configure supplier costs
   - Verify product pricing automation

---

## 📦 Importing Product Catalogs

### Jewelry Template Import Process

The jewelry template includes powerful import scripts for migrating product catalogs from Bling ERP or WooCommerce.

#### Step 1: Prepare CSV Export

**From Bling ERP:**
1. Navigate to: **Products → Export**
2. Select format: **CSV (UTF-8)**
3. Include fields: SKU, Name, Barcode, Weight, Dimensions, Description, HTML Description
4. Save as: `produtos_bling.csv`

**Required CSV Columns:**
- `Código` - Product SKU/Reference
- `Nome` - Product name
- `Código de barras GTIN/EAN` - Barcode
- `Descrição` - Short description
- `Descrição HTML` - Full HTML description
- `Peso líquido (Kg)` - Product weight
- `Largura do Produto (cm)` - Width
- `Altura do Produto (cm)` - Height
- `Profundidade do Produto (cm)` - Depth

#### Step 2: Run Import Script

```bash
# Navigate to import directory
cd addons/tenant_templates/jewelry_template/import

# Run import with your CSV
python import_products.py \
  --csv /path/to/produtos_bling.csv \
  --url http://localhost:8069 \
  --db tenant_jewelry_store_1 \
  --username admin \
  --password your_password

# Optional: Dry run mode (test without importing)
python import_products.py \
  --csv produtos_bling.csv \
  --url http://localhost:8069 \
  --db tenant_jewelry_store_1 \
  --username admin \
  --password your_password \
  --dry-run
```

#### Step 3: Verify Import

```bash
# Validate imported products
python verify_import_results.py \
  --url http://localhost:8069 \
  --db tenant_jewelry_store_1 \
  --username admin \
  --password your_password

# This generates: VALIDATION_SUMMARY.md with detailed results
```

#### Import Features

**✅ Automatic Data Processing:**
- HTML description parsing and cleaning
- Category extraction from product names
- Barcode and weight extraction
- Product variant detection (sizes, lengths)
- Material weight calculation for jewelry items

**✅ Intelligent Variant Handling:**
- Detects size variants: `"C1010 20cm"`, `"44734 11"`, `"Ring 16"`
- Creates Odoo product variants automatically
- Groups variants under base product template
- Supports ring sizes, chain lengths, custom sizes

**✅ Category Mapping:**
- Automatically maps Portuguese categories to Odoo structure
- Supports: Anéis, Pulseiras, Colares, Brincos, Pingentes, Alianças, Aparadores
- Creates category hierarchy: `Joias / Anéis / Solitário`

---

## 🔧 Python Script Reference

### Core Import Scripts

#### `import_products.py`
**Main product import script**

```bash
Usage:
  python import_products.py --csv FILE --url URL --db DB --username USER --password PASS

Options:
  --csv           Path to CSV file
  --url           Odoo URL (e.g., http://localhost:8069)
  --db            Database name
  --username      Odoo username
  --password      Odoo password
  --dry-run       Test mode (no actual import)
  --batch-size    Number of products per batch (default: 50)

Example:
  python import_products.py \
    --csv produtos.csv \
    --url http://localhost:8069 \
    --db tenant_joias \
    --username admin \
    --password admin123
```

#### `verify_import_results.py`
**Validates imported products and generates report**

```bash
Usage:
  python verify_import_results.py --url URL --db DB --username USER --password PASS

Generates:
  - VALIDATION_SUMMARY.md - Detailed validation report
  - Field population statistics
  - Category accuracy check
  - Variant creation verification
  - Test product validation

Example:
  python verify_import_results.py \
    --url http://localhost:8069 \
    --db tenant_joias \
    --username admin \
    --password admin123
```

### Utility Scripts

#### `delete_imported_products.py`
**Remove imported products (for testing)**

```bash
# ⚠️ WARNING: This deletes products permanently!
python delete_imported_products.py \
  --url http://localhost:8069 \
  --db tenant_joias \
  --username admin \
  --password admin123
```

#### `test_variant_creation.py`
**Test variant creation for a specific product**

```bash
# Create variants for product C1010 (sizes: 20cm, 50cm, 60cm)
python test_variant_creation.py
```

#### `test_single_product.py`
**Import a single product for testing**

```bash
# Test import for SKU C775R
python test_single_product.py
```

### Helper Modules

- **`html_parser.py`** - Clean HTML descriptions from Bling
- **`category_mapper.py`** - Map product names to Odoo categories
- **`data_validator.py`** - Validate and clean product data
- **`report_generator.py`** - Generate import validation reports

---

## 🎯 Template Operation Guide

### Jewelry Template Features

#### 1. Dynamic Pricing System

**Market Price Updates:**
```python
# Via Odoo UI:
Jewelry → Configuration → Market Prices

# Via N8N Webhook (automated):
POST https://your-odoo.com/jewelry/webhook/market-price
{
  "metal_type": "gold",
  "purity": "18k",
  "price_per_gram": 350.00
}
```

**Automatic Product Price Recalculation:**
- Updates triggered when market prices change
- Respects markup percentages per product
- Maintains supplier cost history
- Logs all price changes for audit

#### 2. Product Cost Management

**Track Real Costs:**
```
Product → Jewelry Tab:
- Metal Type: Gold, Silver, Platinum
- Metal Weight (g): Actual metal content
- Purity: 18k, 24k, 925, etc.
- Provider Index: Markup multiplier
```

**Cost Calculation:**
```
Real Cost = (Metal Weight × Market Price) + Supplier Cost
Sale Price = Real Cost × Provider Index
Margin = Sale Price - Real Cost
```

#### 3. Size/Weight Adjustments

**Configure size-based weight adjustments:**
```
Jewelry → Configuration → Size/Weight Adjustments

Example:
- Product Type: Ring
- Size: 16
- Weight Adjustment: +0.5g
- Cost Impact: Auto-calculated
```

#### 4. Price History Tracking

**Complete audit trail:**
```
Jewelry → Reports → Price History

Fields tracked:
- Old Price → New Price
- Change Date/Time
- Change Reason (manual, market update, cost change)
- User who made the change
```

### Integration Features

#### WooCommerce Sync
```bash
# Sync products to WooCommerce
Settings → Technical → Automation → WooCommerce Sync

Synced Fields:
- Product name, SKU, barcode
- Sale price (auto-updated)
- Stock quantity
- Images
- Categories
```

#### N8N Workflow Integration
```bash
# Webhook endpoints:
POST /jewelry/webhook/market-price    # Update market prices
POST /jewelry/webhook/supplier-cost   # Update supplier costs
GET  /jewelry/webhook/products        # Export product data
```

---

## 📊 Best Practices

### Product Import

✅ **DO:**
- Test with `--dry-run` first
- Verify CSV encoding is UTF-8
- Backup database before large imports
- Run validation after import
- Review VALIDATION_SUMMARY.md report

❌ **DON'T:**
- Import without testing sample first
- Skip validation step
- Mix different CSV formats
- Import without database backup

### Pricing Configuration

✅ **DO:**
- Set realistic provider indices (1.5-3.0)
- Update market prices regularly
- Track supplier costs accurately
- Monitor margin percentages

❌ **DON'T:**
- Use 0 or negative provider indices
- Forget to update market prices
- Mix currencies in pricing data

### Template Customization

✅ **DO:**
- Create custom fields via UI
- Use Odoo Studio for modifications
- Test in staging environment first
- Document custom changes

❌ **DON'T:**
- Directly modify core template files
- Skip version control
- Make untested production changes

---

## 🛠️ Troubleshooting

### Import Issues

**Problem: "Authentication failed"**
```bash
Solution:
1. Verify username/password
2. Check database name
3. Ensure Odoo is running: docker ps
4. Test URL: curl http://localhost:8069
```

**Problem: "CSV encoding error"**
```bash
Solution:
1. Convert CSV to UTF-8:
   iconv -f WINDOWS-1252 -t UTF-8 input.csv > output.csv
2. Re-run import with UTF-8 file
```

**Problem: "Products imported but missing fields"**
```bash
Solution:
1. Check CSV column names match expected format
2. Run verification: python verify_import_results.py
3. Review VALIDATION_SUMMARY.md for missing fields
```

### Pricing Issues

**Problem: "Prices not updating automatically"**
```bash
Solution:
1. Check market prices: Jewelry → Configuration → Market Prices
2. Verify product has jewelry_pricing_id linked
3. Check provider index is set (>0)
4. Manually trigger: Update Market Prices button
```

**Problem: "Margin calculation incorrect"**
```bash
Solution:
1. Verify supplier cost is set
2. Check metal weight is populated
3. Ensure provider index is correct
4. Review price history for calculation log
```

---

## 📚 Additional Resources

### Documentation
- [Jewelry Template Import Guide](jewelry_template/import/README.md)
- [Odoo XML-RPC API Docs](https://www.odoo.com/documentation/18.0/developer/misc/api/odoo.html)
- [CSV Import Format](jewelry_template/import/CSV_FORMAT.md)

### Example Data
- [Sample CSV Export](jewelry_template/import/examples/sample_produtos.csv)
- [Test Product Data](jewelry_template/import/examples/test_products.csv)

### Support
- **Issues**: [GitHub Issues](https://github.com/your-org/odoo-platform/issues)
- **Documentation**: [Project Wiki](https://github.com/your-org/odoo-platform/wiki)
- **Email**: support@maxhaider.dev

---

## 🔜 Future Templates

Additional templates in development:

- **Retail Template** - General retail operations with POS integration
- **Manufacturing Template** - Production workflows and BOM management
- **Services Template** - Service businesses and project management

---

**Last Updated**: 2026-01-07
**Version**: 1.1.0
**Odoo Compatibility**: 18.0 Community Edition
