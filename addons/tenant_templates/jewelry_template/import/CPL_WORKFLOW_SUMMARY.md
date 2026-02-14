# CPL Supplier Product Import - Workflow Summary

## Current Status: ✅ Ready for Bulk Import

### What's Been Validated
- ✅ 2 test products successfully validated (C725R, C790RZ)
- ✅ 82 variants created (41 per product, sizes 6-46)
- ✅ Weight calculations confirmed accurate (formula: base × COEF × size_factor)
- ✅ Cost calculations working automatically (formula: weight × gold_price × purity × provider_index)
- ✅ Price calculations correct (formula: cost × (1 + markup%))
- ✅ Different COEFs tested (1.10, 1.15) - system handles variations perfectly
- ✅ Automatic computation working - no manual triggers needed for new products

### System is Production-Ready For:
- Bulk import of entire CPL product catalog
- Automatic cost/price calculation for all variants
- Real-time gold price updates via N8N webhooks
- WooCommerce synchronization

---

## Next Step: Prepare Your Product Catalog

### What You Need to Provide

A CSV file with your complete CPL product catalog containing these columns:

| Column | Description | Example |
|--------|-------------|---------|
| SKU | Product code | C725R |
| Name | Product name | Wedding Ring C725R |
| Base Weight (g) | Weight at size 20 in grams | 7.0 |
| COEF | CPL production coefficient | 1.15 |
| Material | Metal type | gold |
| Purity | Metal purity | 24k |
| Provider Index | Supplier pricing factor | 1.0 |
| Markup | Markup percentage | 200.0 |

### Template File Location
```
addons/tenant_templates/jewelry_template/import/cpl_products_template.csv
```

This file already contains your two validated products as examples. Add all additional CPL products below these rows.

---

## Import Process (Once You Provide the CSV)

### Step 1: Dry Run Test (Preview Mode)
```bash
cd addons/tenant_templates/jewelry_template/import

python3 bulk_import_cpl_products.py \
  --csv cpl_products.csv \
  --db tenant_joiasmax \
  --password admin \
  --dry-run
```

**What This Does**:
- ✓ Reads CSV file and validates format
- ✓ Shows which products will be processed
- ✓ Checks for existing products
- ✓ **Does NOT modify database** (safe preview)
- ✓ Reports any issues before actual import

### Step 2: Actual Bulk Import
```bash
python3 bulk_import_cpl_products.py \
  --csv cpl_products.csv \
  --db tenant_joiasmax \
  --password admin
```

**What This Does**:
- ✓ Configures each product (base weight, COEF, material, pricing)
- ✓ Creates 41 variants per product (sizes 6-46)
- ✓ Validates weight calculations for size 20 (reference check)
- ✓ Reports success/failure for each product
- ✓ Provides detailed summary at end

**Expected Duration**: ~2-3 minutes per product (configuring + creating 41 variants + validation)

### Step 3: Full Validation (Optional but Recommended)
After bulk import, validate a sample of products:

```bash
# Validate first product
python3 validate_cpl_pricing.py --sku C725R --db tenant_joiasmax --password admin --verbose

# Validate last product
python3 validate_cpl_pricing.py --sku [LAST_SKU] --db tenant_joiasmax --password admin --verbose

# Validate random middle product
python3 validate_cpl_pricing.py --sku [RANDOM_SKU] --db tenant_joiasmax --password admin --verbose
```

**What to Check**:
- ✓ All 41 variants exist
- ✓ Weights calculated correctly
- ✓ Costs > R$0.00 (not zero)
- ✓ Prices > R$0.00 (not zero)

---

## Data Collection Guide

### Where to Find Your COEF Values

The COEF (production coefficient) should come from your CPL supplier documentation or price tables. This represents their manufacturing complexity/cost multiplier.

**Common COEF Patterns** (based on validated examples):
- Simple wedding bands: 1.10 - 1.15
- Detailed rings: 1.20 - 1.30
- Complex designs: 1.35+

**Important**: Each SKU may have a different COEF based on design complexity.

### Base Weight Determination

Base weight is the metal weight at **size 20** (reference size, factor = 1.0000).

**How to Calculate**:
1. If you have size 20 actual weight: `base_weight = actual_weight ÷ COEF`
2. If you have size 13 weight: `base_weight = size_13_weight ÷ (COEF × 0.8833)`
3. If you have any size: Use the size's adjustment factor from CPL table

**Example**:
- Size 20 weighs 8.05g with COEF 1.15
- Base weight = 8.05 ÷ 1.15 = 7.0g ✓

---

## Expected Results After Import

### Per Product (Example: 10 Products)
- 10 product templates configured
- 410 variants created (10 × 41)
- 410 weights calculated automatically
- 410 costs calculated automatically (based on current gold price)
- 410 prices calculated automatically (cost × markup)

### Database Impact
- Minimal additional storage (~50 KB per product with 41 variants)
- Fast query performance (indexed on ring_size)
- Automatic updates when gold price changes via N8N

### E-commerce Integration
- All 410 variants sync to WooCommerce
- Size selector dropdown automatically populated
- Prices update in real-time with gold market

---

## Troubleshooting Common Issues

### Issue: CSV Format Error
**Error**: `Error reading CSV file`
**Solution**: Ensure CSV uses comma separators, not semicolons. Check column headers match exactly.

### Issue: Product Already Exists
**Warning**: `Product C725R already configured`
**Action**: This is normal. Script will skip already-configured products. Use `--force` flag to reconfigure.

### Issue: Variant Creation Fails
**Error**: `Failed to create variants for C725R`
**Solution**:
1. Check if Ring Size attribute exists
2. Verify attribute has values 6-46
3. Run `create_cpl_variants_with_attributes.py` individually for troubleshooting

### Issue: Costs Still R$0.00 After Import
**Symptom**: Validation shows zero costs
**Solution**:
1. Check gold market price exists: `python3 check_market_price.py`
2. Verify `has_size_based_pricing = True`: `python3 check_product_config.py --sku [SKU]`
3. Trigger recomputation: `python3 trigger_cost_recompute.py --sku [SKU]`

---

## Validation Metrics (Success Criteria)

After bulk import, your validation should show:

✅ **Configuration Success Rate**: 100%
- All products configured with correct base weight, COEF, material
- All products have `has_size_based_pricing = True`
- All products linked to jewelry pricing records

✅ **Variant Creation Success Rate**: 100%
- Every product has exactly 41 variants
- All variants have ring_size set (6-46)
- All variants have unique SKU (BASE-SIZE format)

✅ **Calculation Success Rate**: 100%
- All variants have calculated_metal_weight > 0
- All variants have standard_price (cost) > R$0.00
- All variants have list_price (selling price) > R$0.00

✅ **Formula Accuracy**: 100%
- Sample validation of size 20 (reference) matches expected weight
- Sample validation of size 13 matches expected weight
- Costs match formula: weight × gold_price × purity × provider_index

---

## Post-Import Actions

### 1. Update Documentation
Update `CPL_VALIDATION_STATUS.md` with:
- Total products imported
- Any products that failed (if applicable)
- Date of bulk import

### 2. Configure WooCommerce Sync
Ensure N8N workflow includes new products:
- Product sync workflow
- Inventory sync workflow
- Price update workflow

### 3. Test Customer Experience
1. Navigate to WooCommerce storefront
2. Select a CPL product
3. Verify size dropdown shows sizes 6-46
4. Verify prices update based on selected size
5. Place test order to confirm checkout flow

### 4. Monitor Gold Price Updates
When gold price changes (N8N webhook):
- Verify all CPL product costs update
- Verify all prices recalculate based on markup
- Check price history logs

---

## Support Scripts

### Diagnostic Scripts (troubleshooting)
- `check_product_config.py` - View current product configuration
- `check_size_table.py` - Verify CPL size adjustment factors loaded
- `check_market_price.py` - Verify gold price exists and active
- `diagnose_cost_compute.py` - Debug cost calculation issues

### Configuration Scripts (setup)
- `configure_cpl_product.py` - Configure single product
- `create_cpl_variants_with_attributes.py` - Create variants for single product

### Maintenance Scripts (ongoing)
- `recalculate_variant_prices.py` - Force recalculation of existing variants
- `trigger_cost_recompute.py` - Trigger cost recomputation via toggle

### Validation Scripts (quality assurance)
- `validate_cpl_pricing.py` - Comprehensive validation of calculations
- `bulk_import_cpl_products.py` - Includes built-in quick validation

---

## Documentation References

### Comprehensive Guides
- **[CPL_SUPPLIER_ONBOARDING.md](CPL_SUPPLIER_ONBOARDING.md)** - Complete onboarding guide with detailed explanations
- **[CPL_VALIDATION_STATUS.md](CPL_VALIDATION_STATUS.md)** - Tracking document for all imported products
- **[COST_COMPUTATION_ISSUE.md](COST_COMPUTATION_ISSUE.md)** - Technical details of cost calculation fix

### Specification Documents
- **[cpl_size_indice.md](../../supplier/cpl_size_indice.md)** - CPL size adjustment table specification

### Sample Data
- **[cpl_products_template.csv](cpl_products_template.csv)** - CSV template with validated examples

---

## Timeline Estimate

### For 50 CPL Products:
- **Data Preparation**: 2-3 hours (gathering COEF values, base weights)
- **CSV File Creation**: 30 minutes (using template)
- **Dry Run Test**: 5 minutes (validation and preview)
- **Actual Import**: 100-150 minutes (~2 minutes per product)
- **Validation Sampling**: 15 minutes (test 3-5 random products)
- **Total**: ~4-5 hours

### For 200 CPL Products:
- **Data Preparation**: 6-8 hours
- **CSV File Creation**: 1-2 hours
- **Dry Run Test**: 10 minutes
- **Actual Import**: 400-600 minutes (~7-10 hours, can run overnight)
- **Validation Sampling**: 30 minutes
- **Total**: ~15-20 hours spread over 2-3 days

---

## Contact & Support

If you encounter any issues during bulk import:

1. Check this workflow summary first
2. Review CPL_SUPPLIER_ONBOARDING.md for detailed explanations
3. Run diagnostic scripts to identify specific issues
4. Review COST_COMPUTATION_ISSUE.md for technical troubleshooting

---

## Ready to Start?

### Your Action Items:
1. ✅ Review validated products (C725R, C790RZ) as examples
2. 📋 Gather COEF values for all CPL products from supplier
3. 📝 Fill in `cpl_products_template.csv` with your product data
4. 🧪 Run bulk import with `--dry-run` flag first
5. 🚀 Execute actual import
6. ✓ Validate sample products
7. 🌐 Enable WooCommerce sync

**Current System Status**: All infrastructure ready. Waiting for your product catalog CSV file.

---

**Document Version**: 1.0
**Last Updated**: 2026-01-12
**System Status**: ✅ Production Ready
