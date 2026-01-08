# -*- coding: utf-8 -*-
"""
Verify imported products have correct fields
"""

import xmlrpc.client

# Odoo connection
url = 'http://localhost:8069'
db = 'tenant_joiasmax'
username = 'admin'
password = 'admin'

# Connect
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"Connected as user ID: {uid}")
print("="*60)

# Search for jewelry products
products = models.execute_kw(
    db, uid, password,
    'product.template', 'search_read',
    [[('is_jewelry', '=', True)]],
    {'fields': ['default_code', 'name', 'is_jewelry', 'material_type',
                'metal_weight_grams', 'metal_purity'],
     'limit': 10}
)

print(f"\nFound {len(products)} jewelry products (showing first 10):\n")

for product in products:
    print(f"SKU: {product.get('default_code')}")
    print(f"  Name: {product.get('name')}")
    print(f"  Material: {product.get('material_type')}")
    print(f"  Purity: {product.get('metal_purity')}")
    print(f"  Weight: {product.get('metal_weight_grams')} g")

    # Check pricing record
    pricing = models.execute_kw(
        db, uid, password,
        'joiasmax.jewelry.pricing', 'search_read',
        [[('product_id', '=', product['id'])]],
        {'fields': ['provider_indice', 'material_cost_brl', 'calculated_price_brl',
                    'use_manual_override', 'manual_override_price_brl'],
         'limit': 1}
    )

    if pricing:
        p = pricing[0]
        print(f"  Provider Indice: {p.get('provider_indice')}")
        print(f"  Material Cost: R$ {p.get('material_cost_brl', 0):.2f}")
        print(f"  Calculated Price: R$ {p.get('calculated_price_brl', 0):.2f}")
        if p.get('use_manual_override'):
            print(f"  Manual Override: R$ {p.get('manual_override_price_brl', 0):.2f}")
    else:
        print(f"  WARNING: No pricing record found!")

    print()

print("="*60)
