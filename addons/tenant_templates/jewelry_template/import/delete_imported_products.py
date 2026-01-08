# -*- coding: utf-8 -*-
"""
Delete all imported products for clean re-import testing
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
print("="*80)

# Get all products from the import (created recently)
print("\nSearching for imported products...")

products = models.execute_kw(
    db, uid, password,
    'product.template', 'search_read',
    [[('create_date', '>=', '2026-01-05')]],  # Products created today
    {'fields': ['id', 'default_code', 'name', 'create_date'],
     'order': 'create_date desc'}
)

print(f"Found {len(products)} products created today")

if not products:
    print("\nNo products to delete!")
    exit(0)

# Show sample products
print("\nSample products to be deleted:")
for p in products[:5]:
    print(f"  - {p['default_code']}: {p['name'][:50]}...")

# Confirm deletion (auto-confirm for testing)
print(f"\n{'='*80}")
print(f"[WARNING] This will delete {len(products)} products!")
print(f"{'='*80}")
print("\nAuto-confirming deletion for testing...")
# response = input("\nType 'DELETE' to confirm: ")
# if response != 'DELETE':
#     print("\n[CANCELLED] Deletion cancelled")
#     exit(0)

# Delete pricing records first (to avoid foreign key constraints)
print("\n[DELETING] Pricing records...")

product_ids = [p['id'] for p in products]

pricing_records = models.execute_kw(
    db, uid, password,
    'joiasmax.jewelry.pricing', 'search',
    [[('product_id', 'in', product_ids)]]
)

if pricing_records:
    models.execute_kw(
        db, uid, password,
        'joiasmax.jewelry.pricing', 'unlink',
        [pricing_records]
    )
    print(f"   [OK] Deleted {len(pricing_records)} pricing records")
else:
    print(f"   [INFO] No pricing records found")

# Delete products
print(f"\n[DELETING] {len(products)} products...")

try:
    models.execute_kw(
        db, uid, password,
        'product.template', 'unlink',
        [product_ids]
    )
    print(f"   [OK] Successfully deleted {len(products)} products")
except Exception as e:
    print(f"   [ERROR] Error deleting products: {e}")
    exit(1)

print(f"\n{'='*80}")
print(f"[SUCCESS] Deletion complete!")
print(f"{'='*80}")
print(f"\nYou can now re-run the import to test new fields:")
print(f"  python import_products.py --csv path/to/csv")
