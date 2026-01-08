# -*- coding: utf-8 -*-
"""
Test Product Variant Creation - Manual test for C1010
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
print("TEST: Manual Variant Creation for C1010")
print("=" * 80)

# Find C1010 base product
template_ids = models.execute_kw(
    db, uid, password,
    'product.template', 'search',
    [[('default_code', '=', 'C1010')]]
)

if not template_ids:
    print("[ERROR] C1010 product not found")
    exit(1)

template_id = template_ids[0]
print(f"\n[OK] Found C1010 template ID: {template_id}")

# Read current state
template = models.execute_kw(
    db, uid, password,
    'product.template', 'read',
    [template_id],
    {'fields': ['default_code', 'name', 'product_variant_count', 'product_variant_ids', 'attribute_line_ids']}
)[0]

print(f"\nCurrent State:")
print(f"  Name: {template['name']}")
print(f"  Variant Count: {template['product_variant_count']}")
print(f"  Variant IDs: {template['product_variant_ids']}")
print(f"  Attribute Lines: {template['attribute_line_ids']}")

# Create "Comprimento" attribute
print(f"\n[STEP 1] Creating 'Comprimento' attribute...")
existing_attr = models.execute_kw(
    db, uid, password,
    'product.attribute', 'search',
    [[('name', '=', 'Comprimento')]]
)

if existing_attr:
    attr_id = existing_attr[0]
    print(f"  [OK] Attribute already exists: {attr_id}")
else:
    attr_id = models.execute_kw(
        db, uid, password,
        'product.attribute', 'create',
        [{
            'name': 'Comprimento',
            'create_variant': 'always',
            'display_type': 'radio',
        }]
    )
    print(f"  [OK] Created attribute: {attr_id}")

# Create attribute values (20cm, 50cm, 60cm)
print(f"\n[STEP 2] Creating attribute values...")
sizes = ['20cm', '50cm', '60cm']
value_ids = []

for size in sizes:
    existing_value = models.execute_kw(
        db, uid, password,
        'product.attribute.value', 'search',
        [[('attribute_id', '=', attr_id), ('name', '=', size)]]
    )

    if existing_value:
        value_id = existing_value[0]
        print(f"  [OK] Value '{size}' already exists: {value_id}")
    else:
        value_id = models.execute_kw(
            db, uid, password,
            'product.attribute.value', 'create',
            [{
                'name': size,
                'attribute_id': attr_id,
            }]
        )
        print(f"  [OK] Created value '{size}': {value_id}")

    value_ids.append(value_id)

# Link attribute to template
print(f"\n[STEP 3] Linking attribute to template...")
try:
    models.execute_kw(
        db, uid, password,
        'product.template', 'write',
        [[template_id], {
            'attribute_line_ids': [(0, 0, {
                'attribute_id': attr_id,
                'value_ids': [(6, 0, value_ids)],
            })]
        }]
    )
    print(f"  [OK] Attribute linked to template")
except Exception as e:
    print(f"  [ERROR] Failed to link attribute: {e}")
    exit(1)

# Verify variants were created
print(f"\n[STEP 4] Verifying variant creation...")
template_after = models.execute_kw(
    db, uid, password,
    'product.template', 'read',
    [template_id],
    {'fields': ['product_variant_count', 'product_variant_ids']}
)[0]

print(f"  Variant Count AFTER: {template_after['product_variant_count']}")
print(f"  Variant IDs AFTER: {template_after['product_variant_ids']}")

if template_after['product_variant_count'] > 1:
    print(f"\n[SUCCESS] {template_after['product_variant_count']} variants created!")

    # Read variant details
    variants = models.execute_kw(
        db, uid, password,
        'product.product', 'search_read',
        [[('id', 'in', template_after['product_variant_ids'])]],
        {'fields': ['id', 'display_name', 'barcode', 'weight', 'lst_price']}
    )

    print(f"\n[VARIANT DETAILS]")
    for variant in variants:
        print(f"  - {variant['display_name']}")
        print(f"    ID: {variant['id']}")
        print(f"    Barcode: {variant.get('barcode', '[NOT SET]')}")
        print(f"    Weight: {variant.get('weight', 0):.3f} kg")
        print(f"    Price: R$ {variant.get('lst_price', 0):.2f}")
else:
    print(f"\n[ERROR] Variants not created (still only {template_after['product_variant_count']} variant)")

print("\n" + "=" * 80)
print("[TEST COMPLETE]")
print("=" * 80)
