# SKU Import Fix for Composed Products - Summary

## 🐛 Bug Identified

**Issue:** When importing composed products (products with variants like different sizes), the Internal Reference (SKU) field was not being stored in the individual variant records (`product.product`).

**Symptoms:**
- Base products showed SKU correctly (e.g., "C1010")
- Variant products showed empty SKU field in Odoo UI
- Only happened with composed products (rings with sizes, chains with lengths, etc.)

**Root Cause:**
In [import_products.py:865-876](import_products.py#L865-L876), when updating variant-specific data, the code was only updating:
- `barcode`
- `weight`
- `list_price`

But the full variant SKU (e.g., "C1010 20cm", "44734 11") was available in `variant_dict['sku']` but was NOT being written to the `default_code` field of the `product.product` record.

---

## ✅ Fix Applied

**File Modified:** `addons/tenant_templates/jewelry_template/import/import_products.py`

**Lines Changed:** 865-880

**Change Summary:**
```python
# BEFORE (missing SKU assignment)
update_vals = {}
if variant_dict.get('barcode'):
    update_vals['barcode'] = variant_dict['barcode']
if variant_dict.get('weight'):
    update_vals['weight'] = variant_dict['weight']
if variant_dict.get('price'):
    update_vals['list_price'] = variant_dict['price']

# AFTER (now includes SKU)
update_vals = {}

# Set the full variant SKU as default_code (Internal Reference)
if variant_dict.get('sku'):
    update_vals['default_code'] = variant_dict['sku']

if variant_dict.get('barcode'):
    update_vals['barcode'] = variant_dict['barcode']
if variant_dict.get('weight'):
    update_vals['weight'] = variant_dict['weight']
if variant_dict.get('price'):
    update_vals['list_price'] = variant_dict['price']
```

**Result:** Now when variants are created, each `product.product` record will have its complete SKU stored in `default_code`:
- Variant 1: `default_code` = "C1010 20cm"
- Variant 2: `default_code` = "C1010 50cm"
- Variant 3: `default_code` = "C1010 60cm"

---

## 🧪 Testing the Fix

### Test Current Database State

A test script has been created to check if existing products have SKU set correctly:

**File:** `test_sku_fix.py`

**Run the test:**
```bash
cd d:\Programacao\Repositorios\odoo\addons\tenant_templates\jewelry_template\import
python test_sku_fix.py
```

**What it checks:**
- Finds products with variants (C1010, 44734, etc.)
- Reads all variant records
- Verifies each variant has `default_code` (SKU) set
- Reports which variants are missing SKU

**Expected Output (BEFORE re-import):**
```
TEST: Validate SKU (default_code) Fix for Product Variants
================================================================================
Testing: C1010
  Variant ID 123: Pulseira Groumet (20cm)
    SKU (default_code): [MISSING ❌]
    ❌ SKU is MISSING - This is the bug!

[FAILURE] X variants are missing SKU - Re-import needed!
```

**Expected Output (AFTER re-import with fix):**
```
TEST: Validate SKU (default_code) Fix for Product Variants
================================================================================
Testing: C1010
  Variant ID 123: Pulseira Groumet (20cm)
    SKU (default_code): C1010 20cm
    ✅ SKU is set
    ✅ SKU matches expected format: C1010 20cm

[SUCCESS] All variants have SKU (default_code) set! 🎉
```

---

## 🔄 Re-Import Procedure

To apply the fix to existing products, you need to re-import your product data.

### Option 1: Full Re-Import (Recommended)

**Prerequisites:**
1. Ensure Odoo is running: `docker ps | grep odoo`
2. Have your original Bling export CSV file ready
3. Backup your database first (optional but recommended)

**Steps:**

1. **Delete existing products** (optional - only if you want clean import):
```bash
cd d:\Programacao\Repositorios\odoo\addons\tenant_templates\jewelry_template\import
python delete_imported_products.py
```

2. **Run the import with the fixed script:**
```bash
python import_products.py --csv /path/to/your/bling_export.csv
```

**Example with specific file:**
```bash
python import_products.py --csv "C:\Users\MaxHaider\Downloads\bling_products_2024.csv"
```

3. **Verify the import:**
```bash
python test_sku_fix.py
```

**Expected console output during import:**
```
Creating product variants for 15 base products...
  C1010: Creating 3 variants (attribute: Comprimento)
    ✓ Linked 3 attribute values to template
    ✓ Updated 3 variant products
      Updated variant 20cm: SKU, barcode, weight, price
      Updated variant 50cm: SKU, barcode, weight, price
      Updated variant 60cm: SKU, barcode, weight, price
```

Note the new "SKU" in the log message!

---

### Option 2: Manual Update via Odoo UI

If you prefer not to re-import:

1. Go to **Products > Products** in Odoo
2. Filter for products with variants
3. Open each product
4. Click **Variants** smart button
5. For each variant, manually set the **Internal Reference** field to the full SKU

**Example:**
- Product: Pulseira Groumet
- Base SKU: C1010
- Variants:
  - Variant 1 (20cm): Set Internal Reference = "C1010 20cm"
  - Variant 2 (50cm): Set Internal Reference = "C1010 50cm"
  - Variant 3 (60cm): Set Internal Reference = "C1010 60cm"

---

## 📊 Verifying the Fix in Odoo UI

After re-import, verify in the web interface:

1. Navigate to: http://localhost:8069
2. Go to **Products > Products**
3. Open a product with variants (e.g., search for "C1010" or "44734")
4. Click the **Variants** smart button
5. In the variants list, check the **Internal Reference** column
6. Each variant should show its complete SKU:
   - ✅ C1010 20cm
   - ✅ C1010 50cm
   - ✅ C1010 60cm

**Before Fix:**
- Internal Reference column would be empty or show only base SKU

**After Fix:**
- Each variant has its unique SKU with size suffix

---

## 🎯 Impact of the Fix

### What Now Works:
1. **Unique SKU per variant** - Each size has its own searchable SKU
2. **Better inventory tracking** - Can track stock by specific size SKU
3. **E-commerce sync** - WooCommerce/Shopify integration can use variant SKUs
4. **Barcode scanning** - POS and warehouse can identify exact variant
5. **Reporting** - Sales reports can show SKU at variant level

### Data Integrity:
- **Base product.template**: Keeps base SKU (e.g., "C1010")
- **Variant product.product**: Each has full SKU (e.g., "C1010 20cm", "C1010 50cm")
- **Hierarchical structure**: Maintained correctly

---

## 📋 Checklist for User

- [ ] Run `test_sku_fix.py` to confirm the bug exists in current database
- [ ] Backup database (optional): `docker exec odoo_postgres pg_dump -U odoo tenant_joiasmax > backup.sql`
- [ ] Locate your original Bling CSV export file
- [ ] Run import with fixed script: `python import_products.py --csv your_file.csv`
- [ ] Run `test_sku_fix.py` again to verify fix applied
- [ ] Check Odoo UI to visually confirm SKUs are visible
- [ ] Test a few products manually to ensure data integrity

---

## 🚨 Troubleshooting

### Issue: "Base product not found" during variant creation
**Cause:** Base product SKU doesn't exist in database
**Solution:** Ensure base products are created before variants

### Issue: "Attribute already linked" error
**Cause:** Product already has attribute defined
**Solution:** This is normal - import will skip and continue

### Issue: Variants created but SKU still empty
**Cause:** Fix not applied or CSV missing SKU data
**Solution:**
1. Verify you're using the updated `import_products.py`
2. Check CSV file has SKU column with variant SKUs
3. Check import logs for errors

### Issue: Duplicate variants created
**Cause:** Running import multiple times without cleanup
**Solution:** Use `delete_imported_products.py` before re-importing

---

## 📝 Notes

- The fix is **backward compatible** - won't break existing imports
- **No database migration needed** - just re-import data
- **Works with all product types** - rings, chains, bracelets, etc.
- **Preserves all other data** - categories, prices, weights, etc.

---

## ✨ Summary

**Bug:** Variant products missing SKU (Internal Reference)
**Fixed in:** `import_products.py` line 867-869
**Action required:** Re-import products using updated script
**Validation:** Run `test_sku_fix.py` before and after
**Impact:** All variants will have complete, searchable SKUs

---

**Fix Applied:** 2024-01-10
**Tested:** Ready for validation
**Status:** ✅ Fix complete, awaiting re-import
