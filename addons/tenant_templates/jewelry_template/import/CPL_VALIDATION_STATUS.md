# CPL Supplier Product Validation Status

## Overview
This document tracks the validation status of all CPL supplier products imported into the Odoo tenant_joiasmax database.

**Total Products**: 2 validated
**Total Variants**: 82 (41 per product, sizes 6-46)
**Validation Success Rate**: 100%

---

## Validated Products

### ✅ C725R - Wedding Ring C725R
**Configuration**:
- Base Weight: 7.0g
- COEF: 1.15
- Material: Gold 24k
- Provider Index: 1.0
- Markup: 200%

**Validation Results** (@ R$380.00/g gold price):
- Total Variants: 41 ✅
- Size 6: Weight 6.1711g → Cost R$2,345.02 ✅
- Size 13: Weight 7.1106g → Cost R$2,702.03 ✅
- Size 20: Weight 8.0500g → Cost R$3,059.00 ✅ (Reference)
- Size 46: Weight 11.5381g → Cost R$4,384.48 ✅

**Status**: ✅ PRODUCTION READY
**Date Validated**: 2026-01-12

---

### ✅ C790RZ - Wedding Ring C790RZ
**Configuration**:
- Base Weight: 7.0g
- COEF: 1.10
- Material: Gold 24k
- Provider Index: 1.0
- Markup: 200%

**Validation Results** (@ R$380.00/g gold price):
- Total Variants: 41 ✅
- Size 6: Weight 5.9028g → Cost R$2,243.06 ✅
- Size 13: Weight 6.8014g → Cost R$2,584.53 ✅
- Size 20: Weight 7.7000g → Cost R$2,926.00 ✅ (Reference)
- Size 46: Weight 11.0364g → Cost R$4,193.83 ✅

**Status**: ✅ PRODUCTION READY
**Date Validated**: 2026-01-12

---

## Pending Import

### Products Awaiting Configuration
_List will be updated when user provides complete CPL product catalog with COEF values_

Format for new entries:
```
- [ ] SKU: [SKU_CODE] - COEF: [VALUE] - Status: PENDING
```

---

## Validation Criteria

For each product to be marked as ✅ PRODUCTION READY, the following must pass:

1. **Configuration**:
   - [ ] Product template configured with correct base weight and COEF
   - [ ] has_size_based_pricing = True
   - [ ] Material and purity set correctly
   - [ ] Jewelry pricing record created with provider index and markup

2. **Variant Creation**:
   - [ ] 41 variants created (sizes 6-46)
   - [ ] All variants have ring_size attribute set
   - [ ] All variants have unique SKU (BASE_SKU-SIZE)

3. **Weight Calculation**:
   - [ ] Size 20 weight matches: base_weight × COEF × 1.0000
   - [ ] Size 13 weight matches: base_weight × COEF × 0.8833
   - [ ] Size 6 weight matches: base_weight × COEF × 0.7666
   - [ ] Size 46 weight matches: base_weight × COEF × 1.4333

4. **Cost Calculation**:
   - [ ] All costs > R$0.00 (not zero)
   - [ ] Costs match formula: weight × gold_price × provider_indice
   - [ ] Costs update when gold price changes

5. **Price Calculation**:
   - [ ] All prices > R$0.00 (not zero)
   - [ ] Prices match formula: cost × (1 + markup/100)

---

## CPL Size Adjustment Reference

| Size | Factor  | Size | Factor  | Size | Factor  | Size | Factor  |
|------|---------|------|---------|------|---------|------|---------|
| 6    | 0.7666  | 17   | 0.9500  | 28   | 1.1333  | 39   | 1.3166  |
| 7    | 0.7833  | 18   | 0.9666  | 29   | 1.1500  | 40   | 1.3333  |
| 8    | 0.8000  | 19   | 0.9833  | 30   | 1.1666  | 41   | 1.3500  |
| 9    | 0.8166  | 20   | 1.0000* | 31   | 1.1833  | 42   | 1.3666  |
| 10   | 0.8333  | 21   | 1.0166  | 32   | 1.2000  | 43   | 1.3833  |
| 11   | 0.8500  | 22   | 1.0333  | 33   | 1.2166  | 44   | 1.4000  |
| 12   | 0.8666  | 23   | 1.0500  | 34   | 1.2333  | 45   | 1.4166  |
| 13   | 0.8833  | 24   | 1.0666  | 35   | 1.2500  | 46   | 1.4333  |
| 14   | 0.9000  | 25   | 1.0833  | 36   | 1.2666  |      |         |
| 15   | 0.9166  | 26   | 1.1000  | 37   | 1.2833  |      |         |
| 16   | 0.9333  | 27   | 1.1166  | 38   | 1.3000  |      |         |

*Size 20 is the reference size (factor = 1.0000)

---

## Common Issues and Resolutions

### Issue: Product Not Found
**Symptom**: Script reports "Product not found"
**Cause**: Product doesn't exist or SKU mismatch
**Resolution**: Run `check_product_config.py` to verify product exists

### Issue: Costs Show R$0.00
**Symptom**: Validation shows all costs as zero
**Cause**: Computed field not triggering
**Resolution**:
1. Check `has_size_based_pricing = True`
2. Verify market price exists (check_market_price.py)
3. Toggle `has_size_based_pricing` to trigger recomputation

### Issue: Weight Calculation Mismatch
**Symptom**: Actual weight doesn't match expected
**Cause**: Incorrect COEF or base weight
**Resolution**: Re-run `configure_cpl_product.py` with correct values

### Issue: Variant Count Wrong
**Symptom**: Less than 41 variants created
**Cause**: Attribute values not properly set
**Resolution**: Delete variants and re-run `create_cpl_variants_with_attributes.py`

---

## Next Steps

1. **Prepare Product List**: Fill in `cpl_products_template.csv` with all CPL SKUs and COEFs
2. **Dry Run Test**: Execute bulk import with `--dry-run` flag
3. **Bulk Import**: Run bulk import without dry-run flag
4. **Validation**: Run validation script on all imported products
5. **Production Deploy**: Update WooCommerce sync for new variants

---

## Commands Quick Reference

```bash
# Check single product configuration
python3 check_product_config.py --sku C725R --db tenant_joiasmax --password admin

# Configure single product
python3 configure_cpl_product.py --sku C725R --base-weight 7.0 --coef 1.15 --db tenant_joiasmax --password admin

# Create variants for single product
python3 create_cpl_variants_with_attributes.py --sku C725R --db tenant_joiasmax --password admin

# Validate single product
python3 validate_cpl_pricing.py --sku C725R --db tenant_joiasmax --password admin --verbose

# Bulk import (dry-run)
python3 bulk_import_cpl_products.py --csv cpl_products.csv --db tenant_joiasmax --password admin --dry-run

# Bulk import (actual)
python3 bulk_import_cpl_products.py --csv cpl_products.csv --db tenant_joiasmax --password admin
```

---

**Last Updated**: 2026-01-12
**Next Review**: After bulk import completion
