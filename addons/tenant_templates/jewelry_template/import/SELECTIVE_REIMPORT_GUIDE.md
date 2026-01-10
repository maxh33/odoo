# Selective Re-Import Guide - Fix Only Products with SKU Issues

## ✅ YES - The Script is Smart Enough to Skip Existing Products!

**Good news:** You can delete ONLY the problematic products and re-import them without affecting your entire product catalog.

---

## 🔍 How the Import Script Handles Duplicates

### Duplicate Detection Logic (Lines 546-554)

```python
# Check for duplicates
existing = self.execute('product.template', 'search', [
    ('default_code', '=', sku)
])

if existing:
    _logger.info(f"  {sku}: Already exists, skipping")
    self.stats['duplicates'] += 1
    return False  # ← SKIPS the product
```

**What this means:**
- ✅ Before creating any product, the script searches by SKU (`default_code`)
- ✅ If a product with that SKU exists → **SKIPS IT**
- ✅ If a product doesn't exist → **CREATES IT**
- ✅ You'll see "Already exists, skipping" in the logs

---

## 🎯 Your Strategy: Delete Only Problematic Products

### Step 1: Identify Products to Delete

**Products with variant SKU issues:**
- **44734** - Anel em Prata (Silver Ring with sizes)
- **C1010** - Pulseira de Ouro (Gold Bracelet with lengths)
- **CP3009** - Corrente de Prata (Silver Chain with lengths)
- **PC0510** - Pulseira de Ouro Chapa (Gold Bracelet)

### Step 2: Delete Products in Odoo

**Option A: Via Odoo UI (Safest)**

1. Go to **Products → Products**
2. Search for SKU: `44734` → Open product
3. Click **Action** → **Delete**
4. Confirm deletion (Odoo will ask for confirmation)
5. Repeat for `C1010`, `CP3009`, `PC0510`

**What Gets Deleted:**
- ✅ Base product template
- ✅ ALL variants (automatic cascade delete in Odoo)
- ✅ Attribute links
- ✅ Related pricing records (if any)

**Option B: Via Python Script (Faster for multiple products)**

Create a quick deletion script:

```python
# delete_problematic_products.py
import xmlrpc.client

url = 'http://localhost:8069'
db = 'tenant_joiasmax'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Products to delete
problem_skus = ['44734', 'C1010', 'CP3009', 'PC0510']

for sku in problem_skus:
    template_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('default_code', '=', sku)]]
    )

    if template_ids:
        models.execute_kw(
            db, uid, password,
            'product.template', 'unlink',
            [template_ids]
        )
        print(f"✓ Deleted product: {sku}")
    else:
        print(f"⚠ Product not found: {sku}")

print("\n✓ All problematic products deleted!")
```

### Step 3: Re-Import from CSV

```bash
cd d:\Programacao\Repositorios\odoo\addons\tenant_templates\jewelry_template\import

python import_products.py --csv "d:\Programacao\Repositorios\odoo\addons\tenant_templates\products\produtos_2026-01-05-08-46-50.csv"
```

**What Will Happen:**

```
Reading CSV...
Processing 250 products...

  B191: Already exists, skipping          ← Existing product kept
  B199: Already exists, skipping          ← Existing product kept
  44734: Importing...                     ← DELETED product - will create
    ✓ 44734: Imported successfully
  C1010: Importing...                     ← DELETED product - will create
    ✓ C1010: Imported successfully
  Pl003: Already exists, skipping         ← Existing product kept

Creating product variants...
  44734: Creating 12 variants (attribute: Tamanho)
    ✓ Linked 12 attribute values to template
    ✓ Updated 12 variant products
      Updated variant 11: SKU, barcode, weight, price  ← NOW WITH SKU!
      Updated variant 12: SKU, barcode, weight, price  ← NOW WITH SKU!
      ...
  C1010: Creating 4 variants (attribute: Comprimento)
    ✓ Linked 4 attribute values to template
    ✓ Updated 4 variant products
      Updated variant 20cm: SKU, barcode, weight, price  ← NOW WITH SKU!
      Updated variant 50cm: SKU, barcode, weight, price  ← NOW WITH SKU!
      ...

Import Summary:
  Total products in CSV: 250
  Imported: 4              ← Only the deleted ones
  Duplicates (skipped): 246  ← All your existing products
  Variants created: 22     ← Fixed variants with SKU
```

### Step 4: Verify the Fix

```bash
python test_sku_fix.py
```

**Expected Output:**

```
Testing: 44734
  Variant ID 123: Anel em Prata (Tamanho:11)
    SKU (default_code): 44734 11  ✅
    ✅ SKU is set
    ✅ SKU matches expected format

Testing: C1010
  Variant ID 456: Pulseira de Ouro (Comprimento:20cm)
    SKU (default_code): C1010 20cm  ✅
    ✅ SKU is set
    ✅ SKU matches expected format

[SUCCESS] All variants have SKU (default_code) set! 🎉
```

---

## 📊 Import Statistics You'll See

The script tracks and reports:

```
Import completed in X seconds

Statistics:
  Total products processed: 250
  Successfully imported: 4        ← Your deleted products
  Duplicates (skipped): 246       ← Your existing products (untouched)
  Validation errors: 0

Product Variants:
  Variant groups created: 4       ← 44734, C1010, CP3009, PC0510
  Total variants created: 22      ← All sizes/lengths

By Material:
  Gold: 2 (C1010, PC0510)
  Silver: 2 (44734, CP3009)
```

---

## ⚠️ Important Notes

### 1. Base Product Must Be Deleted for Variants

**Important:** You must delete the **base product template**, not individual variants.

When you delete a base product in Odoo:
- ✅ Odoo automatically deletes ALL variants (cascade delete)
- ✅ Attribute links are removed
- ✅ Clean slate for re-import

**Wrong Approach:**
- ❌ Deleting individual variants one by one (tedious and unnecessary)
- ❌ Trying to update existing products (script doesn't support updates)

**Right Approach:**
- ✅ Delete base product "44734" → All sizes (11-22) auto-deleted
- ✅ Delete base product "C1010" → All lengths auto-deleted

### 2. Stock Quantities Will Be Reset

**Warning:** When you delete and re-import:
- ❌ Stock quantities will be lost
- ❌ Product images will be lost (unless in CSV)
- ❌ Custom notes/descriptions will be overwritten

**If you have stock:**
1. Export current stock levels first: **Inventory → Reporting → Stock**
2. Delete and re-import products
3. Manually adjust stock levels after re-import

**Or:** If stock is critical, see "Alternative: Manual Fix" below

### 3. Impact on Sales Orders

**If you have pending sales orders:**
- ⚠️ Deleting products might affect draft/pending orders
- ✅ Completed orders are usually safe (historical data)

**Recommendation:**
- Check for pending sales orders for these 4 products first
- Process or cancel them before deletion

### 4. CSV File Must Be Complete

**Ensure your CSV has:**
- ✅ All variant rows for each product
- ✅ "Código Pai" (Parent Code) column populated for variants
- ✅ Complete SKUs like "44734 11", "C1010 20cm"

---

## 🔄 Alternative: Manual Fix (No Deletion Required)

If deletion is risky, you can manually set SKUs:

### Option 1: Via Odoo UI

1. Go to **Products → Products**
2. Open product "44734"
3. Click **Variants** smart button
4. For each variant:
   - Click on variant (e.g., "Tamanho: 11")
   - Set **Internal Reference** = "44734 11"
   - Save
5. Repeat for all 4 products

**Time required:** ~5 minutes per product

### Option 2: Via SQL (Fastest, Advanced)

```sql
-- Run in PostgreSQL directly (CAREFUL!)

-- Update 44734 variants
UPDATE product_product
SET default_code = '44734 11'
WHERE id IN (
    SELECT pp.id FROM product_product pp
    JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE pt.default_code = '44734'
    AND pp.id IN (SELECT product_id FROM product_template_attribute_value_product_product_rel ...)
);

-- Requires knowing variant IDs - complex query
-- Not recommended unless you're SQL expert
```

---

## ✅ Recommended Workflow

### Best Approach for Your Situation:

1. **Backup database** (optional but recommended):
```bash
docker exec odoo_postgres pg_dump -U odoo tenant_joiasmax > backup_before_fix.sql
```

2. **Test current state:**
```bash
python test_sku_fix.py
```

3. **Delete 4 problematic products** via Odoo UI:
   - 44734, C1010, CP3009, PC0510

4. **Re-import:**
```bash
python import_products.py --csv "produtos_2026-01-05-08-46-50.csv"
```

5. **Verify fix:**
```bash
python test_sku_fix.py
```

6. **Check in Odoo UI** - Visual confirmation

---

## 🎯 Summary

| Question | Answer |
|----------|--------|
| **Can I delete only problematic products?** | ✅ YES |
| **Will script skip existing products?** | ✅ YES - checks by SKU |
| **Will my other products be affected?** | ❌ NO - they'll be skipped |
| **Will variants get correct SKUs?** | ✅ YES - with the fix applied |
| **Do I need to delete all products?** | ❌ NO - only the 4 with issues |
| **Is this safe?** | ✅ YES - if you don't have pending orders |

---

**You're good to go!** The import script is smart enough to skip existing products, so you can safely delete just the 4 problematic products and re-import them without affecting your entire catalog. 🎉
