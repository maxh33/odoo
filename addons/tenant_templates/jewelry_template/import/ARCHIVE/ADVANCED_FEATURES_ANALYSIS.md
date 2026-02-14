# Advanced Features Analysis - SKU Automation & Dynamic Variants

## ✅ Current Status

**Duplication Issue:** SOLVED! Re-imports work correctly:
- First import: Creates 12 variants for 44734
- Second import: Updates 12 variants, **NO duplicates created**

## 📋 Feature Requests Analysis

### Request 1: Automatic SKU Combination

**Current Behavior:**
CSV must explicitly list each SKU:
```csv
SKU,Name
44734,Anel em Prata de Lei 950 Coração
44734 11,Size 11
44734 12,Size 12
44734 13,Size 13
```

**Desired Behavior:**
Script should automatically combine base SKU + attribute:
```csv
SKU,Name,Size
44734,Anel em Prata de Lei 950 Coração,
,Size 11,11  ← Script generates: 44734_11 or 44734 11
,Size 12,12  ← Script generates: 44734_12 or 44734 12
,Size 13,13  ← Script generates: 44734_13 or 44734 13
```

**Important:** You mentioned "CSV is single source of truth" and "don't touch CSV"

**This means:**
- CSV format stays as-is (current format with explicit SKUs)
- Script adapts to USE underscores internally if needed
- But CSV continues to have spaces: "44734 11", "44734 12"

**Question:** Do you want:
- **Option A**: Script converts spaces to underscores when creating External IDs (already done!)
- **Option B**: Script generates variant SKUs automatically when CSV has missing SKUs
- **Option C**: Both?

---

### Request 2: Dynamic Variant Creation from Description

**Scenario:**
Product C725R has description: "Available in sizes 1-50"

**Current:** Import as single product (no variants)

**Desired:** Script detects size range and creates 50 variants automatically

**Example:**
```
Product: C725R
Description: "Aliança disponível nos tamanhos 1 a 50"

Script detects: sizes 1-50
Creates variants:
- C725R 1, C725R 2, C725R 3... C725R 50
```

---

## 🔍 Implementation Analysis

### Feature 1: Automatic SKU Generation (Option B)

**Difficulty:** Medium
**Risk:** Low
**Value:** High (reduces CSV maintenance)

#### How It Would Work:

**Step 1: Detect Variant Rows with Missing SKU**
```python
# CSV row has size/attribute but no SKU
if row['SKU'] == '' and row.get('Size'):
    # Auto-generate SKU from parent + attribute
    variant_sku = f"{parent_sku}_{row['Size']}"
```

**Step 2: Configuration for Separator**
```python
# In script config
VARIANT_SKU_SEPARATOR = "_"  # or " " for space
```

**Step 3: Smart Detection**
```python
def generate_variant_sku(base_sku, attribute_value, separator="_"):
    """
    Generate variant SKU from base + attribute.

    Examples:
        base_sku="44734", attribute="11" → "44734_11"
        base_sku="C1010", attribute="20cm" → "C1010_20cm"
    """
    return f"{base_sku}{separator}{attribute_value}"
```

**CSV Format Would Be:**
```csv
SKU,Name,Size,Barcode,Price
44734,Base Product Name,,,,
,Variant Name,11,123456,100.00  ← Auto SKU: 44734_11
,Variant Name,12,123457,100.00  ← Auto SKU: 44734_12
```

**Pros:**
✅ Less CSV maintenance (no need to type full SKUs for each variant)
✅ Consistent SKU format across all products
✅ Easy to implement

**Cons:**
❌ Changes CSV structure (requires empty SKU column for variants)
❌ Conflicts with "CSV is single source of truth"

**Verdict:** Only implement if you want to change CSV format. Otherwise, keep current format.

---

### Feature 2: Dynamic Variant Creation from Description

**Difficulty:** High
**Risk:** Medium-High
**Value:** High (reduces manual variant entry)

#### How It Would Work:

**Step 1: Parse Description for Size Patterns**

```python
import re

def extract_size_ranges(description):
    """
    Extract size ranges from product description.

    Patterns detected:
    - "sizes 1-50" / "tamanhos 1-50"
    - "sizes 1 to 50" / "tamanhos 1 a 50"
    - "40cm, 45cm, 50cm, 60cm"
    - "available in 11, 12, 13, 14"
    """
    size_patterns = [
        # Range patterns: "1-50", "1 to 50", "1 a 50"
        r'(?:tamanhos?|sizes?|medidas?)\s*(?:de\s+)?(\d+)\s*(?:-|to|a|até)\s*(\d+)',

        # List patterns: "40cm, 45cm, 50cm"
        r'(\d+\s*cm)',

        # Numeric list: "11, 12, 13, 14"
        r'(?:tamanhos?|sizes?)\s*(?:\d+\s*,\s*)+\d+',
    ]

    for pattern in size_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        if matches:
            return parse_matches(matches)

    return None
```

**Step 2: Determine Which Sizes to Create**

```python
def decide_sizes_to_create(size_range):
    """
    For a range like 1-50, decide which sizes to actually create.

    Options:
    1. All sizes (1, 2, 3... 50) - 50 variants
    2. Common sizes only (10, 12, 14, 16, 18, 20, 22) - 7 variants
    3. Every other (2, 4, 6... 50) - 25 variants
    """
    start, end = size_range

    # Strategy: Create only commonly-used sizes
    common_ring_sizes = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

    # Filter to range
    sizes = [s for s in common_ring_sizes if start <= s <= end]

    return sizes
```

**Step 3: Auto-Create Variants**

```python
def create_dynamic_variants(product, description):
    """
    Create variants automatically from description.
    """
    size_info = extract_size_ranges(description)

    if not size_info:
        return  # No size info detected

    sizes = decide_sizes_to_create(size_info)

    for size in sizes:
        variant_sku = f"{product['sku']}_{size}"
        variant_name = f"{product['name']} - Tamanho {size}"

        # Store variant for creation
        variants.append({
            'sku': variant_sku,
            'size': size,
            'name': variant_name,
            'barcode': product['barcode'],  # Same as base
            'price': product['price'],      # Same as base
        })
```

**Example Detection:**

**Description:** "Aliança em ouro 18k disponível nos tamanhos 10 a 24"

**Detected:** Range 10-24
**Creates:** Sizes 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24
**Variants:** C725R_10, C725R_11, C725R_12... C725R_24

---

#### Challenges with Description-Based Variants

**1. Ambiguity in Language**
```
"Ring available in sizes 10-24"  ✅ Clear
"Suitable for fingers 10mm to 24mm"  ❓ Is this size range?
"Recommended size: 18"  ❓ Just a recommendation or variant?
```

**2. Unit Detection**
```
"40cm, 45cm, 50cm"  → Centimeters (chain length)
"10, 12, 14"  → Ring size (no unit)
"18k"  → Gold karat (NOT a size!)
```

**3. Over-Generation Risk**
```
"Available in all sizes from 1 to 50"  → Creates 50 variants!
"Custom sizes available"  → How many to create?
```

**4. Maintenance Complexity**
- Description changes → Variant count changes
- Need manual review before auto-creating
- Risk of creating unwanted variants

---

## 💡 Recommended Approach

### Phase 1: Keep CSV as Single Source of Truth ✅

**Don't** auto-generate SKUs from attributes
**Don't** parse descriptions for variants

**Do** keep current CSV format where ALL variants are explicitly listed:
```csv
44734,Base Product
44734 11,Variant Size 11
44734 12,Variant Size 12
```

**Why:**
- CSV remains the definitive data source
- No ambiguity in what gets created
- Easy to review and modify
- No risk of auto-creating wrong variants

---

### Phase 2: Add SKU Separator Configuration (Optional)

If you want underscores in Odoo instead of spaces:

**Option A: Convert in CSV (Manual)**
Change CSV format from `44734 11` to `44734_11`

**Option B: Convert in Script (Automatic)**
```python
# Configuration
NORMALIZE_VARIANT_SKUS = True
VARIANT_SKU_SEPARATOR = "_"

# When processing variant SKU
if NORMALIZE_VARIANT_SKUS:
    variant_sku = variant_sku.replace(" ", VARIANT_SKU_SEPARATOR)
```

This would convert:
- `44734 11` → `44734_11` (in Odoo)
- CSV stays as `44734 11` (unchanged)

---

### Phase 3: Smart Description Detection (Future Feature)

**For specific, controlled use cases:**

**Use Case 1: Ring Size Ranges**
```python
# Only for products in "Anéis" category
# Only when description matches EXACT pattern
# Manual approval before creating variants

if category == "Anéis" and re.match(r'tamanhos (\d+) a (\d+)', description):
    # Suggest variant creation
    # Require user confirmation
    # Create with --auto-variants flag
```

**Use Case 2: Chain Length Variants**
```python
# Detect: "40cm, 45cm, 50cm, 60cm"
# Only create if product type is "Corrente" or "Pulseira"
# Require explicit sizes (no ranges)
```

**Safety Features:**
- ✅ Only run with explicit `--auto-variants` flag
- ✅ Dry-run mode to preview what would be created
- ✅ Manual approval before creation
- ✅ Logging of all auto-created variants
- ✅ Category-specific rules (rings vs chains vs bracelets)

---

## 🎯 Implementation Recommendation

### Immediate (Now):
1. ✅ **Keep current CSV format** - explicit SKUs for all variants
2. ✅ **Current script works perfectly** - no changes needed

### Short-term (Optional):
1. Add configuration for SKU normalization (space → underscore)
2. Add `--normalize-skus` flag to convert spaces to underscores in Odoo

### Long-term (Future Enhancement):
1. Add description parsing for **specific, controlled patterns**
2. Require `--auto-variants` flag and manual approval
3. Dry-run mode to preview auto-created variants
4. Category-specific rules for different product types

---

## 📊 Complexity vs Value Matrix

| Feature | Complexity | Risk | Value | Recommend? |
|---------|-----------|------|-------|------------|
| Current approach (explicit SKUs) | Low | Low | High | ✅ Yes (keep) |
| SKU normalization (space→underscore) | Low | Low | Medium | ✅ Optional |
| Auto-generate SKUs from attributes | Medium | Medium | Medium | ❌ No (changes CSV) |
| Parse descriptions for variants | High | High | High | ⚠️ Future (with safeguards) |

---

## 🔧 Quick Win: SKU Normalization

If you want underscores in Odoo but keep spaces in CSV:

### Add Configuration:

```python
class OdooProductImporter:
    def __init__(self, url, database, username, password, skip_updates=False, normalize_skus=False):
        # ... existing code ...
        self.normalize_skus = normalize_skus
        self.sku_separator = "_"  # Configurable

    def normalize_variant_sku(self, sku):
        """
        Normalize variant SKU format.
        Converts spaces to configured separator.
        """
        if self.normalize_skus and " " in sku:
            return sku.replace(" ", self.sku_separator)
        return sku
```

### Usage:

```bash
# Keep spaces (current behavior)
python import_products.py --csv products.csv

# Convert spaces to underscores
python import_products.py --csv products.csv --normalize-skus
```

**Result:**
- CSV: `44734 11` (unchanged)
- Odoo: `44734_11` (normalized)
- External ID: `product_variant_44734_11` (already sanitized)

---

## ❓ Decision Points

**Question 1:** Do you want SKU normalization (space → underscore)?
- **Yes:** Add `--normalize-skus` flag
- **No:** Keep current behavior (spaces preserved)

**Question 2:** Do you want auto-variant creation from descriptions?
- **Yes:** Implement as future enhancement with safeguards
- **No:** Keep manual CSV approach

**Question 3:** Current CSV format acceptable?
- **Yes:** No changes needed
- **No:** Need to redesign CSV structure

---

## 📝 Next Steps

Please clarify:

1. **SKU Format Preference:**
   - Keep spaces: `44734 11` ✓ (current)
   - Convert to underscores: `44734_11` (need flag)

2. **Variant Creation:**
   - Manual via CSV ✓ (current, recommended)
   - Auto-detect from description (future feature)

3. **CSV Structure:**
   - Explicit SKUs for all variants ✓ (current)
   - Auto-generate SKUs from attributes (requires CSV changes)

Based on your answers, I can implement the appropriate solution!

---

**Date:** 2026-01-10
**Status:** ✅ Core functionality working - awaiting decision on enhancements
