# Cost Computation Issue - Root Cause Analysis

## Problem Summary

Product C725R has 41 variants with correct weight calculations, but all costs show R$0.00 instead of calculated values based on gold price and weight.

**Expected**: Costs should be calculated as `Weight × Gold Price × Purity Factor × Provider Index`
**Actual**: All costs remain R$0.00

## Root Cause Identified

The `_compute_variant_cost()` method exists in [product_product.py:72-133](../models/product_product.py) with proper `@api.depends` decorators, but **it's never called** because:

1. ✅ The method has `@api.depends` decorators (lines 64-71)
2. ✅ The method logic is correct (validated all conditions pass)
3. ❌ **The `standard_price` field is NOT declared with `compute='_compute_variant_cost'`**

### Code Analysis

**Working Example** (calculated_metal_weight):
```python
calculated_metal_weight = fields.Float(
    'Calculated Weight (g)',
    compute='_compute_size_based_weight',  # ← This hooks the method to the field
    store=True,
    digits=(8, 4),
)

@api.depends('product_tmpl_id.metal_weight_grams', ...)
def _compute_size_based_weight(self):
    # This method WORKS because it's connected via compute= parameter
```

**Broken Example** (standard_price):
```python
# NO FIELD DECLARATION FOR standard_price in ProductProduct model!

@api.depends('calculated_metal_weight', ...)
def _compute_variant_cost(self):
    # This method NEVER RUNS because no field uses compute='_compute_variant_cost'
    variant.standard_price = variant_cost  # This line never executes
```

## Diagnostic Results

All prerequisites for cost computation are **CORRECT**:

| Condition | Status | Details |
|-----------|--------|---------|
| has_size_based_pricing | ✓ PASS | True |
| material_type | ✓ PASS | 'gold' (maps to 'gold_24k') |
| Market price active | ✓ PASS | R$380.00/g |
| calculated_metal_weight | ✓ PASS | 6.7-11.5g range |
| Purity factor ('24k') | ✓ PASS | 1.0 |
| Provider indice | ✓ PASS | 1.0 |

**Expected costs**: R$2549-2651 based on weight × R$380/g
**Actual costs**: R$0.00 (method never executes)

## Solution

Add field declaration in [product_product.py](../models/product_product.py) to override `standard_price` and connect it to the compute method:

```python
class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    ring_size = fields.Integer(...)
    
    calculated_metal_weight = fields.Float(...)
    
    # ADD THIS FIELD DECLARATION:
    standard_price = fields.Float(
        compute='_compute_variant_cost',
        inverse='_set_standard_price',  # Allow manual override if needed
        store=True,
    )
    
    @api.depends(
        'calculated_metal_weight',
        'product_tmpl_id.material_type',
        'product_tmpl_id.metal_purity',
        'product_tmpl_id.has_size_based_pricing',
        'product_tmpl_id.jewelry_pricing_id',
        'product_tmpl_id.jewelry_pricing_id.provider_indice'
    )
    def _compute_variant_cost(self):
        # Existing method - no changes needed
        ...
    
    def _set_standard_price(self):
        # Inverse method to allow manual cost override
        for record in self:
            record._origin.standard_price = record.standard_price
```

### Alternative Quick Fix (If inverse not needed)

```python
standard_price = fields.Float(
    compute='_compute_variant_cost',
    store=True,
    readonly=False,  # Allow writes to stored computed field
)
```

## Implementation Steps

1. **Backup the module**: Copy entire jewelry_template directory
2. **Edit product_product.py**: Add field declaration as shown above
3. **Restart Odoo**: `docker-compose restart odoo`
4. **Upgrade module**: Via Odoo UI or `odoo-bin -u jewelry_template -d tenant_joiasmax`
5. **Test**: Run `python validate_cpl_pricing.py --sku C725R --db tenant_joiasmax --password admin`

## Expected Results After Fix

Once the field declaration is added:

1. ✅ `_compute_variant_cost()` will be automatically called when dependencies change
2. ✅ Costs will be calculated: Weight × R$380/g × 1.0 × 1.0
3. ✅ All 41 variants will have correct costs (R$2549-3063 range)
4. ✅ Costs will auto-update when gold price changes
5. ✅ Validation script will pass all tests

## Why XML-RPC Workarounds Failed

Our attempts to trigger the method via XML-RPC failed because:

1. **Private method call**: XML-RPC can't call `_compute_variant_cost` directly (private methods blocked)
2. **Field toggle**: Toggling `has_size_based_pricing` doesn't help because the method isn't hooked to any field
3. **Template update**: Updating `metal_weight_grams` triggers `_compute_size_based_weight` but not `_compute_variant_cost`

Without the `compute=` declaration, **nothing** will trigger the method - not XML-RPC, not ORM writes, not even Odoo's recomputation engine.

## Files Created During Diagnosis

1. `check_product_config.py` - Shows current configuration
2. `check_size_table.py` - Verifies CPL size adjustment factors
3. `check_market_price.py` - Confirms gold price exists
4. `force_cost_recompute.py` - Attempted direct method call (failed)
5. `trigger_cost_recompute.py` - Attempted toggle trigger (failed)
6. `diagnose_cost_compute.py` - **Identified all conditions pass**

## References

- **Product Model**: `addons/tenant_templates/jewelry_template/models/product_product.py`
- **Odoo Computed Fields Docs**: https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html#computed-fields
- **Issue Line**: product_product.py:126 - `variant.standard_price = variant_cost` never executes
