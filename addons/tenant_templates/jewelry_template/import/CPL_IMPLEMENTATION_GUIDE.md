# CPL Supplier Size-Based Pricing - Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing size-based pricing for CPL supplier products (wedding rings). The system automatically calculates weight and prices for 45 ring sizes (6-50) based on the CPL weight adjustment table.

**Business Formula:**
```
Final Weight = Base Weight × COEF × Size Adjustment Factor
Cost = Final Weight × Gold Price/gram × Provider Index
Price = Cost × (1 + Markup%)
```

**Example (C725R, 7g base, COEF 1.15):**
- Size 20: 7g × 1.15 × 1.0000 = 8.05g
- Size 13: 7g × 1.15 × 0.8833 = 7.11g

---

## Prerequisites

### System Requirements
- Odoo 18 Community with jewelry_template module installed
- CPL size adjustment table loaded (45 sizes from 6-50)
- Python 3.7+ for running scripts
- XML-RPC access to Odoo server

### Database Setup
1. **Verify CPL Size Table Loaded:**
   ```sql
   SELECT COUNT(*) FROM joiasmax_size_weight_adjustment
   WHERE size_number BETWEEN 6 AND 50;
   -- Expected: 45 records
   ```

2. **Check Market Price Setup:**
   ```sql
   SELECT * FROM joiasmax_market_price
   WHERE material_type = 'gold_24k' AND is_active = true;
   -- Should return active gold price
   ```

---

## Quick Start: C725R Example

### Step 1: Configure Product

**Option A: Using Script (Recommended)**

```bash
cd addons/tenant_templates/jewelry_template/import

python3 configure_cpl_product.py \
  --sku C725R \
  --base-weight 7.0 \
  --coef 1.15 \
  --password YOUR_ODOO_PASSWORD
```

**Parameters:**
- `--sku`: Product SKU (must exist in database)
- `--base-weight`: Base weight in grams at size 20
- `--coef`: Production coefficient (e.g., 1.15 for CPL)
- `--password`: Odoo admin password (required)

**Optional Parameters:**
- `--material gold|silver`: Material type (default: gold)
- `--purity 24k|950`: Purity standard (default: 24k)
- `--provider-indice 1.0`: Provider pricing factor (default: 1.0)
- `--markup 200.0`: Markup percentage (default: 200.0)
- `--url`: Odoo URL (default: http://localhost:8069)
- `--db`: Database name (default: odoo_master)
- `--user`: Odoo username (default: admin)

**Option B: Manual Configuration via Odoo UI**

1. Navigate to: **Sales → Products → Search "C725R"**
2. Edit product and set:
   - Is Jewelry Product: ✓ Checked
   - Material Type: Gold
   - Metal Purity: 24k
   - Metal Weight (grams): 7.0
   - Use Size-Based Pricing: ✓ Checked
   - Size Pricing Coefficient: 1.15

3. Open **Jewelry Pricing** tab:
   - Provider Index Factor: 1.0
   - Markup Percentage: 200.0

### Step 2: Create Size Variants

**Dry Run (Validation):**
```bash
python3 create_cpl_variants.py \
  --sku C725R \
  --dry-run \
  --password YOUR_ODOO_PASSWORD
```

**Create Variants:**
```bash
python3 create_cpl_variants.py \
  --sku C725R \
  --password YOUR_ODOO_PASSWORD
```

**What This Does:**
- Creates 45 variants (C725R-6, C725R-7, ..., C725R-50)
- Sets `ring_size` field for each variant
- Auto-calculates weight using CPL table
- Auto-calculates cost based on current gold price
- Generates unique barcodes (C725R06, C725R07, etc.)

**Expected Output:**
```
Creating CPL Size Variants for: C725R
======================================================================
Product: Aliança C725R - CPL (ID: 123)
✓ Size-based pricing: ENABLED
  - Base Weight: 7.0g
  - COEF: 1.15
  - Material: gold 24k
✓ CPL size table: 45/45 sizes loaded

Creating variant: C725R-20 (Size 20)
  ✓ Created ID: 456
    - SKU: C725R-20
    - Barcode: C725R20
    - Calculated Weight: 8.0500g
    - Cost: R$5635.00

... (44 more variants)

VARIANT CREATION SUMMARY
======================================================================
Variants created: 45/45
✓ All variants created successfully!
Total variants: 45
Variants with ring_size: 45/45
✓ COMPLETE: All 45 size variants created!
```

### Step 3: Validate Calculations

```bash
python3 validate_cpl_pricing.py \
  --sku C725R \
  --password YOUR_ODOO_PASSWORD

# Optional: Show all variants in detail
python3 validate_cpl_pricing.py \
  --sku C725R \
  --verbose \
  --password YOUR_ODOO_PASSWORD
```

**What This Validates:**
- Weight calculation for test cases (sizes 20, 13, 6, 50)
- Cost calculation based on current gold price
- All 45 sizes present
- No invalid sizes outside 6-50 range

**Expected Output:**
```
VALIDATING CPL PRICING: C725R
======================================================================
Product: Aliança C725R - CPL (ID: 123)
  - Base Weight: 7.0g
  - COEF: 1.15
  - Material: gold 24k
  ✓ Size-based pricing: ENABLED
  ✓ Current gold price: R$700.00/g
  - Provider Index: 1.0
  - Markup: 200.0%

VARIANTS: 45/45
======================================================================
Variants with ring_size: 45
Size range: 6 - 50

TEST CASES
======================================================================

--- Size 20: Reference size (factor = 1.0000) ---
Variant: C725R-20 (ID: 456)
  ✓ Weight: 8.0500g (expected 8.0500g)
  ✓ Cost: R$5635.00 (expected R$5635.00)

--- Size 13: Example from MD file ---
Variant: C725R-13 (ID: 449)
  ✓ Weight: 7.1106g (expected 7.1106g)
  ✓ Cost: R$4977.40 (expected R$4977.40)

--- Size 6: Minimum size ---
Variant: C725R-6 (ID: 443)
  ✓ Weight: 6.1713g (expected 6.1713g)
  ✓ Cost: R$4319.90 (expected R$4319.90)

--- Size 50: Maximum size ---
Variant: C725R-50 (ID: 487)
  ✓ Weight: 12.0750g (expected 12.0750g)
  ✓ Cost: R$8452.50 (expected R$8452.50)

SIZE RANGE VALIDATION
======================================================================
✓ All 45 sizes present (6-50)
✓ All sizes in valid range

VALIDATION SUMMARY
======================================================================
Tests passed: 10
Tests failed: 0
Warnings: 0

✓ ALL VALIDATIONS PASSED!
```

### Step 4: Verify in Odoo UI

1. **Open Odoo:** http://localhost:8069
2. **Navigate:** Sales → Products → Search "C725R"
3. **Open Product:** Click on C725R
4. **Check Variants Tab:**
   - Should show 45 variants
   - Each with unique SKU (C725R-6 through C725R-50)
5. **Open a Variant (e.g., C725R-20):**
   - Ring Size: 20
   - Calculated Weight: ~8.05g
   - Cost (standard_price): Matches weight × current gold price
   - Sales Price (list_price): Cost × 3.0 (200% markup)

6. **Test Price Recalculation:**
   - Navigate to: **Joias Max → Market Prices**
   - Update gold_24k price (e.g., from R$700 to R$750)
   - Go back to C725R variants
   - Verify costs and prices updated automatically

---

## Scaling to Multiple CPL Products

### Bulk Configuration

Create a CSV file with CPL product parameters:

**File:** `cpl_products.csv`
```csv
SKU,Name,Base Weight (g),COEF,Material,Purity,Provider Index,Markup
C725R,Wedding Ring C725R,7.0,1.15,gold,24k,1.0,200.0
C810R,Wedding Ring C810R,8.5,1.15,gold,24k,1.0,200.0
C920R,Wedding Ring C920R,9.2,1.15,gold,24k,1.0,200.0
```

**Bulk Processing Script:**
```bash
#!/bin/bash
# bulk_configure_cpl.sh

PASSWORD="YOUR_ODOO_PASSWORD"

while IFS=, read -r sku name base_weight coef material purity provider_indice markup; do
    # Skip header
    if [ "$sku" = "SKU" ]; then
        continue
    fi

    echo "Processing: $sku"

    # Configure product
    python3 configure_cpl_product.py \
        --sku "$sku" \
        --base-weight "$base_weight" \
        --coef "$coef" \
        --material "$material" \
        --purity "$purity" \
        --provider-indice "$provider_indice" \
        --markup "$markup" \
        --password "$PASSWORD"

    # Create variants
    python3 create_cpl_variants.py \
        --sku "$sku" \
        --password "$PASSWORD"

    # Validate
    python3 validate_cpl_pricing.py \
        --sku "$sku" \
        --password "$PASSWORD"

    echo "Completed: $sku"
    echo "---"
done < cpl_products.csv
```

**Usage:**
```bash
chmod +x bulk_configure_cpl.sh
./bulk_configure_cpl.sh
```

---

## Troubleshooting

### Common Issues

#### 1. "Product not found!"
**Problem:** SKU doesn't exist in database

**Solution:**
- Verify SKU: `SELECT default_code FROM product_template WHERE default_code LIKE '%C725R%';`
- Create product first via Odoo UI or import script
- Check for typos in SKU

#### 2. "CPL size table incomplete! Found X/45 sizes"
**Problem:** Size adjustment table not loaded

**Solution:**
```bash
# Check if module data is loaded
cd addons/tenant_templates/jewelry_template
grep -r "size_weight_adjustments.xml" __manifest__.py

# Reinstall module to load data
# Via Odoo UI: Apps → jewelry_template → Upgrade
# Or via command line:
odoo-bin -u jewelry_template -d odoo_master
```

#### 3. "No active market price found"
**Problem:** Gold price not set

**Solution:**
- Navigate to: **Joias Max → Market Prices**
- Create new record:
  - Material Type: gold_24k
  - Price per Gram (R$): 700.00
  - Is Active: ✓ Checked
- Or set via N8N webhook (production)

#### 4. "Weight calculation incorrect"
**Problem:** Calculated weight doesn't match expected

**Solution:**
- Verify base weight is correct (at size 20, not raw weight)
- Check COEF value (should be 1.15 for CPL)
- Ensure size adjustment factor is from CPL table
- Run validation with `--verbose` to see all calculations

#### 5. "Variants already exist"
**Problem:** Running create script multiple times

**Solution:**
- Script automatically skips existing sizes
- To recreate: Delete variants manually first
- Check existing: `SELECT COUNT(*) FROM product_product WHERE product_tmpl_id = X;`

---

## Database Queries for Verification

### Check Product Configuration
```sql
SELECT
    pt.id,
    pt.default_code AS sku,
    pt.name,
    pt.has_size_based_pricing,
    pt.metal_weight_grams AS base_weight,
    pt.size_pricing_coef AS coef,
    pt.material_type,
    pt.metal_purity
FROM product_template pt
WHERE pt.default_code = 'C725R';
```

### Check Variant Count
```sql
SELECT
    pt.default_code AS base_sku,
    COUNT(pp.id) AS variant_count,
    MIN(pp.ring_size) AS min_size,
    MAX(pp.ring_size) AS max_size
FROM product_product pp
JOIN product_template pt ON pp.product_tmpl_id = pt.id
WHERE pt.default_code = 'C725R'
GROUP BY pt.default_code;
```

### Check Variant Weights and Costs
```sql
SELECT
    pp.default_code AS variant_sku,
    pp.ring_size,
    pp.calculated_metal_weight AS weight_g,
    pp.standard_price AS cost_brl,
    pp.list_price AS price_brl,
    swa.adjustment_factor
FROM product_product pp
LEFT JOIN joiasmax_size_weight_adjustment swa
    ON pp.ring_size = swa.size_number
JOIN product_template pt ON pp.product_tmpl_id = pt.id
WHERE pt.default_code = 'C725R'
ORDER BY pp.ring_size;
```

### Verify CPL Size Table
```sql
SELECT
    size_number,
    adjustment_factor,
    CASE
        WHEN size_number = 20 THEN '← Reference'
        ELSE ''
    END AS note
FROM joiasmax_size_weight_adjustment
WHERE size_number BETWEEN 6 AND 50
ORDER BY size_number;
```

---

## Performance Considerations

### Single Product (45 variants)
- Configuration time: ~1 second
- Variant creation time: ~5 seconds (0.1s per variant)
- Validation time: ~2 seconds

### 100 Products (4,500 variants)
- Total configuration time: ~8 minutes
- Database size impact: ~2-3 MB
- Price recalculation (all): ~30 seconds

### 10,000 Products (450,000 variants)
- Estimated total time: ~12 hours (can parallelize)
- Database size impact: ~200-300 MB
- Daily price update: ~5-10 minutes
- Recommended: Use batch processing, off-peak hours

### Optimization Tips
1. **Batch Processing:** Process 100 products at a time
2. **Scheduled Updates:** Run price updates during low-traffic hours
3. **Database Indexes:** Already optimized (ring_size, product_tmpl_id)
4. **Monitoring:** Track PostgreSQL query performance via Grafana

---

## Integration with E-commerce

### WooCommerce Sync
- Each variant has unique SKU (C725R-6, C725R-7, etc.)
- Variants sync as separate WooCommerce products
- Price updates propagate automatically
- Inventory tracked per size

### Customer Selection
- Size selector: Dropdown showing "Size 6" through "Size 50"
- Stock status per size
- Price displays variant-specific cost

---

## Production Deployment Checklist

### Pre-Deployment
- [ ] Test on staging with 10 sample products
- [ ] Validate calculations match business requirements
- [ ] Verify PostgreSQL performance (query time < 500ms)
- [ ] Check VPS resource availability (CPU, RAM, disk)

### Deployment
- [ ] Schedule maintenance window (off-peak hours)
- [ ] Backup database before bulk import
- [ ] Process products in batches (100-1000 per batch)
- [ ] Monitor system resources during processing
- [ ] Validate sample products after import

### Post-Deployment
- [ ] Verify WooCommerce sync working
- [ ] Test customer ordering flow
- [ ] Set up N8N gold price webhook
- [ ] Schedule daily price update job
- [ ] Monitor error logs for 1 week

---

## Support and Maintenance

### Daily Monitoring
- Gold price update successful (N8N webhook log)
- Variant price recalculation (check price_history)
- No errors in Odoo server logs

### Weekly Tasks
- Validate pricing accuracy (sample 10 random products)
- Check PostgreSQL slow query log
- Review customer orders by size

### Monthly Tasks
- Audit price history trends
- Review VPS resource usage (Grafana)
- Update documentation if business rules change

---

## Appendix: Calculation Examples

### Example 1: C725R Size 20 (Reference)
```
Base Weight: 7.0g
COEF: 1.15
Size Adjustment Factor: 1.0000 (reference)

Weight = 7.0 × 1.15 × 1.0000 = 8.05g

Gold Price: R$700/g
Provider Index: 1.0
Cost = 8.05 × 700 × 1.0 = R$5,635.00

Markup: 200%
Price = 5,635 × (1 + 200/100) = 5,635 × 3.0 = R$16,905.00
```

### Example 2: C725R Size 13
```
Base Weight: 7.0g
COEF: 1.15
Size Adjustment Factor: 0.8833

Weight = 7.0 × 1.15 × 0.8833 = 7.110565g

Gold Price: R$700/g
Provider Index: 1.0
Cost = 7.110565 × 700 × 1.0 = R$4,977.40

Markup: 200%
Price = 4,977.40 × 3.0 = R$14,932.20
```

### Example 3: C725R Size 50 (Maximum)
```
Base Weight: 7.0g
COEF: 1.15
Size Adjustment Factor: 1.5000

Weight = 7.0 × 1.15 × 1.5000 = 12.075g

Gold Price: R$700/g
Provider Index: 1.0
Cost = 12.075 × 700 × 1.0 = R$8,452.50

Markup: 200%
Price = 8,452.50 × 3.0 = R$25,357.50
```

---

## References

- **Business Specification:** [cpl_size_indice.md](../supplier/cpl_size_indice.md)
- **Implementation Plan:** [golden-wishing-waffle.md](C:\Users\Admin\.claude\plans\golden-wishing-waffle.md)
- **CPL Size Table:** [size_weight_adjustments.xml](../data/size_weight_adjustments.xml)
- **Product Model:** [product_product.py](../models/product_product.py)
- **Pricing Model:** [jewelry_pricing.py](../models/jewelry_pricing.py)
