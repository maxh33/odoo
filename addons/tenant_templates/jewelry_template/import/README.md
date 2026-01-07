# JoiasMax Product Import Guide

Complete guide for importing product catalogs into the Jewelry Template for Odoo 18.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [CSV Format Requirements](#csv-format-requirements)
- [Import Process](#import-process)
- [Python Scripts Reference](#python-scripts-reference)
- [Troubleshooting](#troubleshooting)
- [Advanced Features](#advanced-features)

---

## 🚀 Quick Start

**For impatient users who just want to import products:**

```bash
# 1. Navigate to import directory
cd addons/tenant_templates/jewelry_template/import

# 2. Run import (replace with your actual values)
python import_products.py \
  --csv /path/to/your/produtos_bling.csv \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_password

# 3. Verify results
python verify_import_results.py \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_password

# 4. Check the generated report
cat VALIDATION_SUMMARY.md
```

**Expected Result:**
- ✅ Products imported with categories, barcodes, weights
- ✅ Product variants created for sizes/lengths
- ✅ Jewelry pricing linked for material cost tracking
- ✅ Validation report generated

---

## 📦 Prerequisites

### System Requirements

1. **Odoo 18.0 Community Edition** installed and running
2. **Python 3.8+** with required packages:
   ```bash
   # No external packages required - uses Python standard library only!
   # Built-in modules: csv, argparse, logging, xmlrpc.client, datetime
   ```

3. **Database access credentials**
   - Odoo URL (e.g., `http://localhost:8069`)
   - Database name (e.g., `tenant_joiasmax`)
   - Admin username and password

4. **Jewelry Template Module installed** in your Odoo database
   ```
   Go to: Apps → Search "jewelry_template" → Install
   ```

### Verify Template Installation

```bash
# Check if jewelry template is installed
# Open Odoo UI → Apps → Remove "Apps" filter → Search "jewelry_template"
# Should show as "Installed"

# Or via database:
docker exec -it odoo_postgres psql -U odoo -d tenant_joiasmax -c \
  "SELECT name, state FROM ir_module_module WHERE name = 'jewelry_template';"
```

---

## 📊 CSV Format Requirements

### Required CSV Columns

Your CSV export from Bling ERP should include these columns:

| Column Name (Portuguese) | English | Required | Description |
|--------------------------|---------|----------|-------------|
| `Código` | SKU/Code | ✅ YES | Product reference (e.g., "C1010", "44734") |
| `Nome` | Name | ✅ YES | Product name |
| `Código de barras GTIN/EAN` | Barcode | ⚠️ Recommended | Product barcode (extracted from field) |
| `Descrição` | Description | ⚠️ Recommended | Short description |
| `Descrição HTML` | HTML Description | ⚠️ Recommended | Full description with HTML |
| `Peso líquido (Kg)` | Net Weight | ⚠️ Recommended | Product weight in kg |
| `Largura do Produto (cm)` | Width | Optional | Product width |
| `Altura do Produto (cm)` | Height | Optional | Product height |
| `Profundidade do Produto (cm)` | Depth | Optional | Product depth |

### CSV Encoding

**CRITICAL**: CSV must be UTF-8 encoded!

```bash
# Check CSV encoding
file -i produtos_bling.csv

# Convert from Windows-1252 to UTF-8 if needed
iconv -f WINDOWS-1252 -t UTF-8 produtos_bling.csv > produtos_utf8.csv

# Or on Windows using PowerShell:
Get-Content produtos_bling.csv | Out-File -Encoding UTF8 produtos_utf8.csv
```

### Sample CSV Format

```csv
Código,Nome,Código de barras GTIN/EAN,Descrição,Descrição HTML,Peso líquido (Kg)
C1010,"Pulseira Groumet 3x1 Diamantada","7895476485955","Pulseira em ouro","<p><strong>Peso:</strong> 32,000 g</p>",0.100
44734 11,"Anel Solitário","7895476123456","Anel tamanho 11","<p>Anel solitário tamanho 11</p>",0.100
B043,"Brinco Argola","7895475945511","Brinco argola","<p>Brinco em ouro 18k</p>",0.100
```

---

## 🔧 Import Process

### Step 1: Prepare Your CSV File

1. **Export from Bling ERP:**
   ```
   Bling → Products → Export → CSV (UTF-8)
   ```

2. **Verify CSV file:**
   ```bash
   # Check file exists
   ls -lh /path/to/produtos_bling.csv

   # Verify encoding
   file -i produtos_bling.csv

   # Preview first 5 lines
   head -5 produtos_bling.csv
   ```

3. **Optional: Test with sample data first**
   ```bash
   # Create test CSV with 5 products
   head -6 produtos_bling.csv > test_sample.csv
   ```

### Step 2: Run Import Script

```bash
# Navigate to import directory
cd addons/tenant_templates/jewelry_template/import

# Basic import
python import_products.py \
  --csv /path/to/produtos_bling.csv \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_password

# With options
python import_products.py \
  --csv /path/to/produtos_bling.csv \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_password \
  --batch-size 25 \
  --dry-run
```

**Import Script Options:**
- `--csv` - Path to your CSV file (required)
- `--url` - Odoo server URL (required)
- `--db` - Database name (required)
- `--username` - Odoo username (required)
- `--password` - Odoo password (required)
- `--batch-size` - Products per batch (default: 50)
- `--dry-run` - Test mode, no actual import

### Step 3: Monitor Import Progress

The import script will show real-time progress:

```
2026-01-07 10:30:00 - INFO - Connected to Odoo successfully
2026-01-07 10:30:01 - INFO - Reading CSV file: produtos_bling.csv
2026-01-07 10:30:02 - INFO - Found 156 products to import
2026-01-07 10:30:03 - INFO - Processing batch 1/4 (50 products)
2026-01-07 10:30:15 - INFO - Batch 1 completed: 50 products imported
2026-01-07 10:30:16 - INFO - Processing batch 2/4 (50 products)
...
2026-01-07 10:31:45 - INFO - Import completed: 156 products imported successfully
2026-01-07 10:31:45 - INFO - Creating product variants...
2026-01-07 10:31:50 - INFO - Created 24 variants for 6 products
```

### Step 4: Verify Import Results

```bash
# Run validation script
python verify_import_results.py \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password your_password

# This generates: VALIDATION_SUMMARY.md
```

### Step 5: Review Validation Report

```bash
# Read the generated report
cat VALIDATION_SUMMARY.md

# Or open in your editor
code VALIDATION_SUMMARY.md
```

**Report Includes:**
- ✅ Field population statistics (barcode, weight, categories)
- ✅ Product variant creation results
- ✅ Category mapping accuracy
- ✅ Test product validation
- ✅ Recommendations and next steps

---

## 📚 Python Scripts Reference

### 1. `import_products.py` - Main Import Script

**Purpose:** Import products from Bling CSV export to Odoo

**Features:**
- ✅ HTML description parsing and cleaning
- ✅ Automatic category detection from product names
- ✅ Barcode extraction from description fields
- ✅ Metal weight extraction for jewelry items
- ✅ Product variant detection and creation
- ✅ Batch processing for large catalogs
- ✅ Dry-run mode for testing

**Usage:**
```bash
python import_products.py \
  --csv produtos_bling.csv \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password admin123

# Dry run (test without importing)
python import_products.py --csv produtos.csv --url http://localhost:8069 \
  --db tenant_joiasmax --username admin --password admin123 --dry-run

# Small batches for slower systems
python import_products.py --csv produtos.csv --url http://localhost:8069 \
  --db tenant_joiasmax --username admin --password admin123 --batch-size 10
```

**What It Does:**
1. Connects to Odoo via XML-RPC
2. Reads CSV file and validates data
3. Cleans HTML descriptions
4. Extracts categories from product names
5. Creates/updates products in batches
6. Detects and creates product variants
7. Links products to jewelry pricing system

### 2. `verify_import_results.py` - Validation Script

**Purpose:** Validate imported products and generate detailed report

**Usage:**
```bash
python verify_import_results.py \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password admin123
```

**Generates:** `VALIDATION_SUMMARY.md` with:
- Field population statistics
- Category accuracy check
- Variant creation verification
- Test product validation
- Recommendations

### 3. `delete_imported_products.py` - Cleanup Script

**Purpose:** Remove all imported products (for testing/re-import)

**⚠️ WARNING:** This permanently deletes products!

**Usage:**
```bash
# Delete all jewelry products
python delete_imported_products.py \
  --url http://localhost:8069 \
  --db tenant_joiasmax \
  --username admin \
  --password admin123

# You will be prompted to confirm:
# "This will delete all imported products. Are you sure? (yes/no): "
```

**Use Cases:**
- ✅ Testing import with different CSV formats
- ✅ Re-importing after data cleanup
- ✅ Development and testing

**What It Deletes:**
- All products in "Joias" category and subcategories
- Associated jewelry pricing records
- Product variants
- Price history entries

### 4. `test_variant_creation.py` - Variant Testing

**Purpose:** Test variant creation for a specific product

**Usage:**
```bash
# Test creating variants for product C1010
python test_variant_creation.py

# Edit the script to test different products:
# Change: test_sku = "C1010"
# To:     test_sku = "44734"
```

**Use Cases:**
- ✅ Debug variant creation issues
- ✅ Test variant logic for specific product
- ✅ Validate size/length detection

### 5. `test_single_product.py` - Single Product Import

**Purpose:** Import a single product for testing

**Usage:**
```bash
# Import only product C775R
python test_single_product.py

# Edit the script to test different products:
# Change: test_sku = "C775R"
# To:     test_sku = "B043"
```

**Use Cases:**
- ✅ Test import logic for specific product
- ✅ Debug data extraction issues
- ✅ Validate category mapping

### 6. Helper Modules (Not Run Directly)

**`html_parser.py`**
- Cleans HTML descriptions from Bling
- Extracts metal weight from HTML
- Extracts barcode from description
- Removes unnecessary HTML tags

**`category_mapper.py`**
- Maps product names to Odoo categories
- Creates category hierarchy
- Supports Portuguese jewelry categories
- Fallback to generic "Joias" category

**`data_validator.py`**
- Validates product data
- Cleans and normalizes values
- Ensures required fields are present
- Handles encoding issues

**`report_generator.py`**
- Generates VALIDATION_SUMMARY.md
- Calculates field population statistics
- Formats markdown reports
- Provides recommendations

---

## 🎯 Advanced Features

### Product Variant Detection

The import script automatically detects and creates variants for products with sizes or lengths:

**Supported Variant Patterns:**
- Ring sizes: `"44734 11"`, `"44734 12"`, `"44734 16"`
- Chain lengths: `"C1010 20cm"`, `"C1010 50cm"`, `"C1010 60cm"`
- Custom sizes: `"C1010 C"`, `"PC0510 c"` (Customizado)

**How It Works:**
1. Detects SKU pattern with size suffix
2. Extracts base SKU (e.g., "C1010" from "C1010 20cm")
3. Groups variants by base SKU
4. Creates Odoo product template for base
5. Creates product variants with size attribute

**Example:**
```
Input CSV:
- C1010 20cm - Pulseira Groumet 20cm
- C1010 50cm - Pulseira Groumet 50cm
- C1010 60cm - Pulseira Groumet 60cm

Result in Odoo:
Product Template: "Pulseira Groumet"
- Variant 1: 20cm
- Variant 2: 50cm
- Variant 3: 60cm
```

### Category Mapping Logic

**Automatic Category Detection:**
```python
Product Name → Category
"Anel Solitário" → Joias / Anéis / Solitário
"Pulseira Groumet" → Joias / Pulseiras
"Colar Veneziana" → Joias / Colares
"Brinco Argola" → Joias / Brincos
"Pingente Coração" → Joias / Pingentes
"Aliança Lisa" → Joias / Alianças
"Aparador" → Joias / Aparadores
```

**Keyword Matching:**
- Anel/Ring → Anéis
- Pulseira/Bracelet → Pulseiras
- Colar/Necklace → Colares
- Brinco/Earring → Brincos
- Pingente/Pendant → Pingentes
- Aliança/Wedding Band → Alianças
- Aparador/Extender → Aparadores

### Metal Weight Extraction

**Extracts weight from HTML descriptions:**
```html
Input: <p><strong>Peso:</strong> 32,000 g</p>
Result: metal_weight = 32.0 (grams)

Input: <p>Peso do metal: 5,1g</p>
Result: metal_weight = 5.1 (grams)
```

**Patterns Detected:**
- `Peso: 32,000 g`
- `Peso do metal: 5,1 g`
- `32,0 gramas`
- `Weight: 32.0g`

### Barcode Extraction

**Extracts GTIN/EAN from HTML descriptions:**
```html
Input: <p>Código de barras GTIN: 7895476485955</p>
Result: barcode = "7895476485955"

Input: <p>EAN: 6015032975961</p>
Result: barcode = "6015032975961"
```

**Patterns Detected:**
- `Código de barras GTIN: {barcode}`
- `EAN: {barcode}`
- `Barcode: {barcode}`
- 13-digit numbers in description

---

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. Authentication Failed

**Error:**
```
ERROR - Authentication failed: Invalid username or password
```

**Solutions:**
```bash
# Verify Odoo is running
docker ps | grep odoo
curl -I http://localhost:8069

# Test database access
docker exec -it odoo_postgres psql -U odoo -d tenant_joiasmax -c "SELECT 1;"

# Verify credentials
# Open Odoo UI → Login with username/password
# If login works, credentials are correct

# Check database name
docker exec -it odoo_postgres psql -U odoo -c "\l" | grep tenant
```

#### 2. CSV Encoding Error

**Error:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```

**Solution:**
```bash
# Check file encoding
file -i produtos_bling.csv

# Convert to UTF-8
iconv -f WINDOWS-1252 -t UTF-8 produtos_bling.csv > produtos_utf8.csv

# Re-run import with UTF-8 file
python import_products.py --csv produtos_utf8.csv ...
```

#### 3. Module Not Installed

**Error:**
```
ERROR - Jewelry template module not installed
```

**Solution:**
```bash
# Install via Odoo UI:
# 1. Go to Apps
# 2. Remove "Apps" filter
# 3. Search "jewelry_template"
# 4. Click Install

# Or via command line:
docker exec -it odoo_community_18 odoo -d tenant_joiasmax \
  -i jewelry_template --stop-after-init
```

#### 4. Missing CSV Columns

**Error:**
```
KeyError: 'Código'
```

**Solution:**
```bash
# Check CSV headers
head -1 produtos_bling.csv

# Verify column names match expected format:
# Required: Código, Nome
# Recommended: Descrição, Descrição HTML, Peso líquido (Kg)

# If columns are different, edit CSV headers to match
```

#### 5. Products Imported But Missing Data

**Issue:** Products created but barcode, weight, or categories missing

**Solution:**
```bash
# Run validation to identify issues
python verify_import_results.py ...

# Check VALIDATION_SUMMARY.md for details
cat VALIDATION_SUMMARY.md

# Common causes:
# - HTML description empty → No barcode/weight extracted
# - Product name doesn't match category keywords → Generic "Joias" category
# - CSV columns empty → No data to import

# Fix CSV and re-import:
python delete_imported_products.py ...
python import_products.py ...
```

#### 6. Variants Not Created

**Issue:** Size variants imported as separate products

**Solution:**
```bash
# Check variant detection logic
python test_variant_creation.py

# Expected SKU patterns:
# - "C1010 20cm" → variant detected
# - "44734 11" → variant detected
# - "C1010C" → NOT detected (missing space)

# Fix SKU format in CSV:
# Change: "C1010C" to "C1010 C"
# Change: "4473411" to "44734 11"

# Re-import after fixing CSV
```

#### 7. Slow Import Performance

**Issue:** Import takes very long for large catalogs

**Solutions:**
```bash
# Reduce batch size
python import_products.py --batch-size 10 ...

# Check Odoo server resources
docker stats odoo_community_18

# Increase Odoo worker processes (in odoo.conf):
workers = 2

# Disable variant creation temporarily
# Edit import_products.py:
# Comment out: create_product_variants()
```

---

## 📊 Import Best Practices

### Before Import

✅ **DO:**
1. Backup your database
   ```bash
   docker exec odoo_postgres pg_dump -U odoo tenant_joiasmax > backup_$(date +%Y%m%d).sql
   ```
2. Test with sample data first
   ```bash
   head -11 produtos.csv > test_sample.csv
   python import_products.py --csv test_sample.csv --dry-run ...
   ```
3. Verify CSV encoding (UTF-8)
4. Check CSV column headers match expected format
5. Install jewelry_template module first

❌ **DON'T:**
- Import without database backup
- Skip dry-run testing
- Use non-UTF-8 encoded CSV
- Import into wrong database

### During Import

✅ **DO:**
- Monitor import logs for errors
- Watch for duplicate product warnings
- Check batch completion messages
- Note any skipped products

❌ **DON'T:**
- Interrupt import mid-process
- Run multiple imports simultaneously
- Modify products in Odoo during import

### After Import

✅ **DO:**
1. Run validation script
2. Review VALIDATION_SUMMARY.md
3. Check products in Odoo UI
4. Verify categories are correct
5. Test pricing automation
6. Configure market prices

❌ **DON'T:**
- Skip validation step
- Assume all data imported correctly
- Forget to set up market prices

---

## 🔗 Related Documentation

- [Tenant Templates Overview](../../README.md)
- [Jewelry Template Operation Guide](../README.md)
- [Odoo XML-RPC API Documentation](https://www.odoo.com/documentation/18.0/developer/misc/api/odoo.html)
- [Project CLAUDE.md](../../../../../CLAUDE.md)

---

## 🆘 Getting Help

**Issues with Import:**
1. Check this README first
2. Review VALIDATION_SUMMARY.md
3. Check import logs for errors
4. Open GitHub issue with error details

**Contact:**
- Email: support@maxhaider.dev
- GitHub Issues: [odoo-platform/issues](https://github.com/your-org/odoo-platform/issues)

---

**Last Updated**: 2026-01-07
**Script Version**: 1.1.0
**Compatible With**: Odoo 18.0 Community, Jewelry Template 18.0.1.1.0
