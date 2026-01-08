# -*- coding: utf-8 -*-
"""
Verify new field extractions (barcode, weight, volume, description_sale)
"""

import csv
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

# Test 1: Check CSV data extraction
print("\n[TEST 1] CSV Field Extraction")
print("-"*80)

csv_path = r"d:\Programacao\Repositorios\odoo\addons\tenant_templates\products\produtos_2026-01-05-08-46-50.csv"

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')

    # Get first product (C790RZ from your screenshot)
    for row in reader:
        if row.get('Código', '').strip() == 'C790RZ':
            print(f"\nProduct SKU: {row.get('Código')}")
            print(f"   Name: {row.get('Descrição')}")
            print(f"\nExtracted CSV Fields:")
            print(f"   GTIN/EAN (Barcode): {row.get('GTIN/EAN', 'N/A')}")
            print(f"   Peso liquido (Kg): {row.get('Peso líquido (Kg)', 'N/A')}")
            print(f"   Largura (cm): {row.get('Largura do Produto (cm)', 'N/A')}")
            print(f"   Altura (cm): {row.get('Altura do Produto (cm)', 'N/A')}")
            print(f"   Profundidade (cm): {row.get('Profundidade do Produto (cm)', 'N/A')}")

            # Calculate volume
            try:
                w = float(row.get('Largura do Produto (cm)', '0').replace(',', '.'))
                h = float(row.get('Altura do Produto (cm)', '0').replace(',', '.'))
                d = float(row.get('Profundidade do Produto (cm)', '0').replace(',', '.'))
                volume_m3 = (w * h * d) / 1000000.0 if (w and h and d) else 0.0
                print(f"\nCalculated Volume: {volume_m3:.6f} m3")
            except:
                print(f"\nVolume calculation failed")

            break

# Test 2: Check existing product in Odoo
print("\n\n[TEST 2] Check Existing Product in Odoo")
print("-"*80)

products = models.execute_kw(
    db, uid, password,
    'product.template', 'search_read',
    [[('default_code', '=', 'C790RZ')]],
    {'fields': ['default_code', 'name', 'barcode', 'weight', 'volume',
                'description_sale', 'is_jewelry', 'metal_weight_grams',
                'jewelry_pricing_id'],
     'limit': 1}
)

if products:
    p = products[0]
    print(f"\nProduct: {p.get('default_code')} - {p.get('name')}")
    print(f"\nStandard Odoo Fields:")
    print(f"   Barcode: {p.get('barcode') or 'NOT SET'}")
    print(f"   Weight (Kg): {p.get('weight', 0):.3f} {'[OK]' if p.get('weight') else '[MISSING]'}")
    print(f"   Volume (m3): {p.get('volume', 0):.6f} {'[OK]' if p.get('volume') else '[MISSING]'}")
    print(f"   Description Sale: {'SET' if p.get('description_sale') else 'NOT SET'}")

    print(f"\nJewelry Fields:")
    print(f"   Is Jewelry: {p.get('is_jewelry')}")
    print(f"   Metal Weight (g): {p.get('metal_weight_grams', 0):.3f}")
    print(f"   Pricing Record ID: {p.get('jewelry_pricing_id') or 'NOT LINKED'}")

    # If pricing record exists, check it
    if p.get('jewelry_pricing_id'):
        pricing_id = p['jewelry_pricing_id'][0] if isinstance(p['jewelry_pricing_id'], list) else p['jewelry_pricing_id']

        pricing = models.execute_kw(
            db, uid, password,
            'joiasmax.jewelry.pricing', 'read',
            [pricing_id],
            {'fields': ['provider_indice', 'material_cost_brl', 'calculated_price_brl']}
        )

        if pricing:
            pr = pricing[0]
            print(f"\nPricing Record (ID: {pricing_id}):")
            print(f"   Provider Indice: {pr.get('provider_indice', 0):.2f}")
            print(f"   Material Cost: R$ {pr.get('material_cost_brl', 0):.2f}")
            print(f"   Calculated Price: R$ {pr.get('calculated_price_brl', 0):.2f}")
else:
    print("[ERROR] Product C790RZ not found in Odoo!")

print("\n" + "="*80)
print("\n[VERIFICATION COMPLETE]")
print("\nNote: Existing products may not have new fields populated.")
print("      Delete and re-import to test full integration, or check a newly created product.")
