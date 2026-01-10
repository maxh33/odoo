# -*- coding: utf-8 -*-
"""
Delete Problematic Products with Missing Variant SKUs

This script deletes only the products that have variant SKU issues:
- 44734 (Anel em Prata)
- C1010 (Pulseira de Ouro)
- CP3009 (Corrente de Prata)
- PC0510 (Pulseira de Ouro Chapa)

After deletion, you can re-import these products with the fixed script.
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

print("=" * 80)
print("DELETE PROBLEMATIC PRODUCTS - SKU Variant Fix")
print("=" * 80)
print("\nThis will delete the following products and ALL their variants:")
print("  - 44734 (Anel em Prata - Ring with sizes 11-22)")
print("  - C1010 (Pulseira de Ouro - Bracelet with lengths)")
print("  - CP3009 (Corrente de Prata - Chain with lengths)")
print("  - PC0510 (Pulseira de Ouro Chapa - Bracelet)")
print("\n⚠️  WARNING: This action cannot be undone!")
print("=" * 80)

# Confirm deletion
confirmation = input("\nType 'DELETE' to confirm deletion: ")

if confirmation != 'DELETE':
    print("\n❌ Deletion cancelled. No products were deleted.")
    exit(0)

print("\n✓ Confirmed. Proceeding with deletion...\n")

# Connect to Odoo
try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    print(f"✓ Connected to Odoo as user ID: {uid}\n")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# Products to delete
problem_skus = [
    {'sku': '44734', 'name': 'Anel em Prata de Lei 950'},
    {'sku': 'C1010', 'name': 'Pulseira de Ouro Masculina'},
    {'sku': 'CP3009', 'name': 'Corrente de Prata Singapura'},
    {'sku': 'PC0510', 'name': 'Pulseira de Ouro Chapa'},
]

deleted_count = 0
not_found_count = 0

for product in problem_skus:
    sku = product['sku']
    name = product['name']

    try:
        # Search for product by SKU
        template_ids = models.execute_kw(
            db, uid, password,
            'product.template', 'search',
            [[('default_code', '=', sku)]]
        )

        if template_ids:
            template_id = template_ids[0]

            # Get product details before deletion
            template_data = models.execute_kw(
                db, uid, password,
                'product.template', 'read',
                [template_id],
                {'fields': ['name', 'product_variant_count']}
            )[0]

            variant_count = template_data.get('product_variant_count', 0)
            product_name = template_data.get('name', '')

            # Delete the product (variants will be auto-deleted)
            models.execute_kw(
                db, uid, password,
                'product.template', 'unlink',
                [template_ids]
            )

            print(f"✓ Deleted: {sku}")
            print(f"  Name: {product_name}")
            print(f"  Variants deleted: {variant_count}")
            print()

            deleted_count += 1
        else:
            print(f"⚠  Not found: {sku} ({name})")
            print(f"  Product may have been already deleted or SKU is different")
            print()
            not_found_count += 1

    except Exception as e:
        print(f"❌ Error deleting {sku}: {e}")
        print()

# Summary
print("=" * 80)
print("DELETION SUMMARY")
print("=" * 80)
print(f"Products deleted: {deleted_count}")
print(f"Products not found: {not_found_count}")
print(f"Total processed: {len(problem_skus)}")

if deleted_count > 0:
    print("\n✅ Deletion completed successfully!")
    print("\nNext steps:")
    print("  1. Run the import script to re-create these products:")
    print("     python import_products.py --csv produtos_2026-01-05-08-46-50.csv")
    print()
    print("  2. Verify the fix:")
    print("     python test_sku_fix.py")
    print()
else:
    print("\n⚠️  No products were deleted.")
    print("   Products may have already been deleted or SKUs are different.")

print("=" * 80)
