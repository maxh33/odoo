# -*- coding: utf-8 -*-
"""
Test importing single product C790RZ to Odoo with all fields
"""

import xmlrpc.client
import csv

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

# Delete existing C790RZ if exists
existing = models.execute_kw(
    db, uid, password,
    'product.template', 'search',
    [[('default_code', '=', 'C790RZ')]]
)

if existing:
    print(f"Deleting existing product C790RZ (ID: {existing[0]})")
    # Delete pricing record first
    pricing_ids = models.execute_kw(
        db, uid, password,
        'joiasmax.jewelry.pricing', 'search',
        [[('product_id', '=', existing[0])]]
    )
    if pricing_ids:
        models.execute_kw(db, uid, password, 'joiasmax.jewelry.pricing', 'unlink', [pricing_ids])
        print(f"  Deleted pricing record ID: {pricing_ids}")

    models.execute_kw(db, uid, password, 'product.template', 'unlink', [existing])
    print(f"  Deleted product")

# Extract from CSV
csv_path = r"d:\Programacao\Repositorios\odoo\addons\tenant_templates\products\produtos_2026-01-05-08-46-50.csv"

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')

    for row in reader:
        sku = row.get('Código', '').strip().replace('\t', '').strip()

        if sku == 'C790RZ':
            # Extract barcode
            barcode = row.get('GTIN/EAN', '').strip().replace('\t', '').strip()

            # Extract weight
            weight_str = row.get('Peso líquido (Kg)', '0').strip().replace('\t', '')
            weight = float(weight_str.replace(',', '.')) if weight_str and weight_str != '0' else 0.0

            # Create product
            print(f"\nCreating product C790RZ with:")
            print(f"  Barcode: '{barcode}'")
            print(f"  Weight: {weight} kg")

            product_vals = {
                'name': 'Test Product C790RZ',
                'default_code': 'C790RZ',
                'list_price': 100.0,
            }

            # Add barcode
            if barcode:
                product_vals['barcode'] = barcode
                print(f"  Adding barcode to product_vals: '{barcode}'")

            # Add weight
            if weight:
                product_vals['weight'] = weight
                print(f"  Adding weight to product_vals: {weight} kg")

            print(f"\nCreating product with vals:")
            for k, v in product_vals.items():
                print(f"  {k}: {v}")

            product_id = models.execute_kw(
                db, uid, password,
                'product.template', 'create',
                [product_vals]
            )

            print(f"\nProduct created with ID: {product_id}")

            # Verify the fields were set
            product = models.execute_kw(
                db, uid, password,
                'product.template', 'read',
                [product_id],
                {'fields': ['default_code', 'name', 'barcode', 'weight', 'volume']}
            )

            p = product[0]
            print(f"\nVerification - Product fields in Odoo:")
            print(f"  SKU: {p.get('default_code')}")
            print(f"  Name: {p.get('name')}")
            print(f"  Barcode: {p.get('barcode') or '[NOT SET]'}")
            print(f"  Weight: {p.get('weight', 0):.3f} kg")
            print(f"  Volume: {p.get('volume', 0):.6f} m³")

            print("\n" + "=" * 80)
            print("[SUCCESS] Product created with barcode and weight!")
            print("=" * 80)
            break
