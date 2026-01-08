# -*- coding: utf-8 -*-
"""
Verify Import Results - Validate all fields populated correctly
Checks: categories, barcode, weight, volume, product variants
"""

import xmlrpc.client

# Odoo connection
url = 'http://localhost:8069'
db = 'tenant_joiasmax'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"Connected as user ID: {uid}")
print("=" * 100)
print("IMPORT RESULTS VALIDATION")
print("=" * 100)

# Get all products imported today
products = models.execute_kw(
    db, uid, password,
    'product.template', 'search_read',
    [[('create_date', '>=', '2026-01-05'), ('is_jewelry', '=', True)]],
    {'fields': [
        'id', 'default_code', 'name', 'categ_id',
        'barcode', 'weight', 'volume',
        'metal_weight_grams', 'material_type', 'metal_purity',
        'jewelry_pricing_id', 'list_price',
        'product_variant_count', 'product_variant_ids',
    ],
     'order': 'default_code'}
)

print(f"\n[INFO] Found {len(products)} jewelry products imported today")
print("=" * 100)

# Validation Statistics
stats = {
    'total_products': len(products),
    'with_barcode': 0,
    'with_weight': 0,
    'with_volume': 0,
    'with_metal_weight': 0,
    'with_pricing_link': 0,
    'category_aparadores': 0,
    'products_with_variants': 0,
    'total_variants': 0,
}

# Test specific products (one per category)
test_products = {
    'C775R': 'Aparadores',
    'C1010': 'Pulseiras (with variants)',
    '44734': 'Anéis (with variants)',
    'B043': 'Brincos',
    'P208': 'Pingentes',
    'C790RZ': 'Test product (barcode validation)',
}

print("\n[TEST PRODUCTS VALIDATION]")
print("=" * 100)

for sku, expected_category in test_products.items():
    product = next((p for p in products if p.get('default_code') == sku), None)

    if not product:
        print(f"\n[X] {sku}: NOT FOUND - Expected category: {expected_category}")
        continue

    print(f"\n[OK] {sku}: {product['name'][:60]}")
    print(f"   Category: {product['categ_id'][1] if product.get('categ_id') else 'None'} (Expected: {expected_category})")
    print(f"   Barcode: {product.get('barcode') or '[NOT SET]'}")
    print(f"   Weight: {product.get('weight', 0):.3f} kg")
    print(f"   Volume: {product.get('volume', 0):.6f} m³")
    print(f"   Metal Weight: {product.get('metal_weight_grams', 0):.3f} g")
    print(f"   Pricing Linked: {'YES' if product.get('jewelry_pricing_id') else 'NO'}")
    print(f"   Variants: {product.get('product_variant_count', 0)} variants")

    # Check if has variants
    if product.get('product_variant_count', 0) > 1:
        print(f"\n   [VARIANT DETAILS]")
        variant_ids = product.get('product_variant_ids', [])

        # Read variant details
        variants = models.execute_kw(
            db, uid, password,
            'product.product', 'search_read',
            [[('id', 'in', variant_ids)]],
            {'fields': [
                'id', 'default_code', 'display_name',
                'barcode', 'weight', 'lst_price',
                'product_template_attribute_value_ids'
            ]}
        )

        for variant in variants:
            attr_values = variant.get('product_template_attribute_value_ids', [])
            print(f"      - {variant['display_name'][:50]}")
            print(f"        Barcode: {variant.get('barcode') or '[NOT SET]'}")
            print(f"        Weight: {variant.get('weight', 0):.3f} kg")
            print(f"        Price: R$ {variant.get('lst_price', 0):.2f}")

print("\n\n[OVERALL STATISTICS]")
print("=" * 100)

# Calculate statistics
for p in products:
    if p.get('barcode'):
        stats['with_barcode'] += 1
    if p.get('weight') and p['weight'] > 0:
        stats['with_weight'] += 1
    if p.get('volume') and p['volume'] > 0:
        stats['with_volume'] += 1
    if p.get('metal_weight_grams') and p['metal_weight_grams'] > 0:
        stats['with_metal_weight'] += 1
    if p.get('jewelry_pricing_id'):
        stats['with_pricing_link'] += 1

    # Check category
    categ_name = p['categ_id'][1] if p.get('categ_id') else ''
    if 'Aparadores' in categ_name:
        stats['category_aparadores'] += 1

    # Check variants
    variant_count = p.get('product_variant_count', 0)
    if variant_count > 1:
        stats['products_with_variants'] += 1
        stats['total_variants'] += variant_count

print(f"\nTotal Products: {stats['total_products']}")
print(f"\nField Population:")
print(f"  - Barcode:        {stats['with_barcode']:2d}/{stats['total_products']} ({stats['with_barcode']/stats['total_products']*100:5.1f}%)")
print(f"  - Weight:         {stats['with_weight']:2d}/{stats['total_products']} ({stats['with_weight']/stats['total_products']*100:5.1f}%)")
print(f"  - Volume:         {stats['with_volume']:2d}/{stats['total_products']} ({stats['with_volume']/stats['total_products']*100:5.1f}%)")
print(f"  - Metal Weight:   {stats['with_metal_weight']:2d}/{stats['total_products']} ({stats['with_metal_weight']/stats['total_products']*100:5.1f}%)")
print(f"  - Pricing Link:   {stats['with_pricing_link']:2d}/{stats['total_products']} ({stats['with_pricing_link']/stats['total_products']*100:5.1f}%)")

print(f"\nCategory Validation:")
print(f"  - 'Aparadores' category: {stats['category_aparadores']} products")

print(f"\nProduct Variants:")
print(f"  - Products with variants: {stats['products_with_variants']}")
print(f"  - Total variant records:  {stats['total_variants']}")

print("\n" + "=" * 100)
print("[VALIDATION COMPLETE]")
print("=" * 100)

# Summary
issues = []
if stats['with_barcode'] < stats['total_products'] * 0.5:
    issues.append("[WARNING] Low barcode population")
if stats['with_weight'] < stats['total_products'] * 0.5:
    issues.append("[WARNING] Low weight population")
if stats['category_aparadores'] == 0:
    issues.append("[WARNING] 'Aparadores' category not created or not assigned")
if stats['products_with_variants'] == 0:
    issues.append("[WARNING] No product variants detected")

if issues:
    print("\n[ISSUES DETECTED]")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\n[SUCCESS] All validations passed!")
