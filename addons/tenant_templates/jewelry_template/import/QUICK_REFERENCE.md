# Quick Reference - Import Script Updates

## 🎯 What's Been Fixed

### ✅ 1. External ID Space Issue - FIXED
**Problem:** SKUs with spaces (e.g., "B143 VERDE OVAL") caused External ID creation errors.

**Solution:** All SKUs are now sanitized automatically - spaces and special characters replaced with underscores.

**No action needed** - works automatically!

---

### ✅ 2. Skip Updates Feature - NEW
**Problem:** Updating existing products slows down debugging when testing new product creation.

**Solution:** New `--skip-updates` flag to skip existing products and only create new ones.

---

## 🚀 How to Use

### Normal Import (Updates Existing Products)
```bash
python import_products.py --csv products.csv
```

**Behavior:**
- Creates new products
- **Updates existing products** with CSV data (CSV always wins)
- Updates existing variants with CSV data
- Registers External IDs for all products

**Use when:** Running production imports, updating prices/inventory

---

### Debug Mode (Skip Existing Products)
```bash
python import_products.py --csv products.csv --skip-updates
```

**Behavior:**
- Creates new products
- **Skips existing products** (no updates)
- Skips existing variants (no updates)
- Still registers External IDs for new products

**Use when:**
- Testing new product creation logic
- Debugging import issues
- Fast iteration during development
- Only want to import new products

---

## 📊 What You'll See in Logs

### Normal Mode
```
Processing product: B143 VERDE OVAL
  B143 VERDE OVAL: Found by External ID, updating
  ✓ Updated product with 8 fields

  C1010: 4 variants exist (updating), 0 need creation
    ✓ Updated 4 existing variants
```

### Skip-Updates Mode
```
Processing product: B143 VERDE OVAL
  B143 VERDE OVAL: Found by External ID, skipping (--skip-updates enabled)

  C1010: 4 variants exist (skipped), 0 need creation
    ✓ Skipped 4 existing variants (--skip-updates enabled)
```

---

## 🔧 What's Changed Internally

1. **SKU Sanitization:**
   - "B143 VERDE OVAL" → External ID: `product_template_B143_VERDE_OVAL`
   - "C1010 20cm" → External ID: `product_variant_C1010_20cm`
   - "PC05/10" → External ID: `product_template_PC05_10`

2. **External ID Creation:**
   - All 5 External ID creation points now sanitize SKUs
   - Consistent naming across all products and variants

3. **Update Behavior:**
   - Controlled by `--skip-updates` flag
   - Applies to both base products and variants
   - Clear logging shows what's happening

---

## 🧪 Test the Fixes

### Test 1: Verify Space Issue is Fixed
```bash
# Import products with spaces in SKU
python import_products.py --csv products.csv

# Should work without errors now!
# Check logs - no "External IDs cannot contain spaces" errors
```

### Test 2: Compare Import Times
```bash
# Time a full import with updates
time python import_products.py --csv products.csv

# Time a fast import without updates (for debugging)
time python import_products.py --csv products.csv --skip-updates

# Skip mode should be significantly faster!
```

### Test 3: Verify External IDs Created
```sql
-- Connect to database and check External IDs
SELECT name, model, res_id
FROM ir_model_data
WHERE module = 'jewelry_import'
  AND name LIKE '%B143%'
ORDER BY id DESC;

-- Should show: product_template_B143_VERDE_OVAL (not spaces!)
```

---

## 📝 Complete Command Reference

```bash
python import_products.py --csv FILEPATH [OPTIONS]

Required:
  --csv FILEPATH                Path to CSV file

Optional:
  --url URL                     Odoo server (default: http://localhost:8069)
  --database DATABASE           Database name (default: tenant_joiasmax)
  --username USERNAME           Odoo username (default: admin)
  --password PASSWORD           Odoo password (default: admin)
  --output-dir DIR              Reports directory (default: reports)
  --skip-updates                Skip existing products (debugging mode)
```

---

## 💡 Tips

**When to use normal mode:**
- Production imports
- Updating prices from CSV
- Syncing inventory levels
- Updating product descriptions

**When to use --skip-updates:**
- Testing new product creation
- Debugging import issues
- Fast iteration during development
- Only importing new products (not updating existing)

**Speed comparison example:**
- Normal import: ~7 minutes for 51 products (with updates)
- Skip mode: ~2 minutes for 51 products (only new products)

---

## 📄 Related Files

- **Latest Fixes Details:** [LATEST_FIXES_SUMMARY.md](./LATEST_FIXES_SUMMARY.md)
- **Implementation Summary:** [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)
- **Import Script:** [import_products.py](./import_products.py)

---

**Last Updated:** 2026-01-10
