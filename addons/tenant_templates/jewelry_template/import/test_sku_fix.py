# -*- coding: utf-8 -*-
"""
Test SKU Fix for Product Variants - Validates that default_code is set correctly
"""

import xmlrpc.client
import logging

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

# Odoo connection
url = 'http://localhost:8069'
db = 'tenant_joiasmax'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"Connected as user ID: {uid}")
print("=" * 80)
print("TEST: Validate SKU (default_code) Fix for Product Variants")
print("=" * 80)

# Test products with known variants (from your actual CSV data)
test_products = [
    {'base_sku': '44734', 'expected_variants': ['44734 11', '44734 12', '44734 13', '44734 14', '44734 15', '44734 16', '44734 17', '44734 18', '44734 19', '44734 20', '44734 21', '44734 22']},
    {'base_sku': 'C1010', 'expected_variants': ['C1010 20cm', 'C1010 50cm', 'C1010 60cm', 'C1010 C']},
    {'base_sku': 'CP3009', 'expected_variants': ['CP3009 40cm', 'CP3009 45cm', 'CP3009 50cm', 'CP3009 60cm']},
    {'base_sku': 'PC0510', 'expected_variants': ['PC0510 20cm', 'PC0510 c']},
]

total_tests = 0
passed_tests = 0
failed_tests = 0

for test_product in test_products:
    base_sku = test_product['base_sku']
    expected_variants = test_product['expected_variants']

    print(f"\n{'='*80}")
    print(f"Testing: {base_sku}")
    print(f"{'='*80}")

    # Find base product template
    template_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('default_code', '=', base_sku)]]
    )

    if not template_ids:
        print(f"[SKIP] Base product {base_sku} not found in database")
        continue

    template_id = template_ids[0]
    print(f"\n[OK] Found base template ID: {template_id}")

    # Read template to get variant IDs
    template = models.execute_kw(
        db, uid, password,
        'product.template', 'read',
        [template_id],
        {'fields': ['name', 'default_code', 'product_variant_count', 'product_variant_ids']}
    )[0]

    print(f"  Template Name: {template['name']}")
    print(f"  Template SKU: {template.get('default_code', '[NOT SET]')}")
    print(f"  Variant Count: {template['product_variant_count']}")

    if template['product_variant_count'] <= 1:
        print(f"[WARNING] Product has no variants (only base product exists)")
        continue

    # Read all variants with SKU field explicitly
    variant_ids = template['product_variant_ids']
    variants = models.execute_kw(
        db, uid, password,
        'product.product', 'read',
        [variant_ids],
        {'fields': ['id', 'display_name', 'default_code', 'barcode', 'weight', 'list_price', 'product_template_attribute_value_ids']}
    )

    print(f"\n[VARIANT DETAILS]")
    for variant in variants:
        total_tests += 1
        variant_sku = variant.get('default_code', '')

        print(f"\n  Variant ID {variant['id']}: {variant['display_name']}")
        print(f"    SKU (default_code): {variant_sku if variant_sku else '[MISSING ❌]'}")
        print(f"    Barcode: {variant.get('barcode', '[NOT SET]')}")
        print(f"    Weight: {variant.get('weight', 0):.3f} kg")
        print(f"    Price: R$ {variant.get('list_price', 0):.2f}")

        # Check if SKU is set
        if variant_sku:
            print(f"    ✅ SKU is set")
            passed_tests += 1

            # Check if it matches expected format
            if variant_sku in expected_variants:
                print(f"    ✅ SKU matches expected format: {variant_sku}")
            elif variant_sku == base_sku:
                print(f"    ⚠️  SKU is base SKU (not variant-specific)")
            else:
                print(f"    ⚠️  SKU doesn't match expected variants: {expected_variants}")
        else:
            print(f"    ❌ SKU is MISSING - This is the bug!")
            failed_tests += 1

# Print summary
print(f"\n{'='*80}")
print(f"TEST SUMMARY")
print(f"{'='*80}")
print(f"Total variants tested: {total_tests}")
print(f"Variants with SKU: {passed_tests} ✅")
print(f"Variants WITHOUT SKU: {failed_tests} ❌")

if failed_tests == 0:
    print(f"\n[SUCCESS] All variants have SKU (default_code) set! 🎉")
else:
    print(f"\n[FAILURE] {failed_tests} variants are missing SKU - Re-import needed!")
    print(f"\nTo fix:")
    print(f"  1. Run the import script with the updated code")
    print(f"  2. Or manually update using Odoo UI")

print(f"{'='*80}")
