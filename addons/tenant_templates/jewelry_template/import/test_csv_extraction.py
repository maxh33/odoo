# -*- coding: utf-8 -*-
"""
Test CSV extraction for product C790RZ
"""

import csv

csv_path = r"d:\Programacao\Repositorios\odoo\addons\tenant_templates\products\produtos_2026-01-05-08-46-50.csv"

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')

    for row in reader:
        sku = row.get('Código', '').strip().replace('\t', '').strip()

        if sku == 'C790RZ':
            print("=" * 80)
            print(f"Product SKU: {sku}")
            print("=" * 80)

            # Extract barcode (with tab cleaning)
            barcode_raw = row.get('GTIN/EAN', '')
            barcode = barcode_raw.strip().replace('\t', '').strip()
            print(f"\nBarcode:")
            print(f"  Raw: '{barcode_raw}' (len={len(barcode_raw)})")
            print(f"  Cleaned: '{barcode}' (len={len(barcode)})")

            # Extract weight
            weight_raw = row.get('Peso líquido (Kg)', '0')
            weight_clean = weight_raw.strip().replace('\t', '')
            try:
                weight = float(weight_clean.replace(',', '.')) if weight_clean and weight_clean != '0' else 0.0
            except (ValueError, AttributeError):
                weight = 0.0
            print(f"\nWeight:")
            print(f"  Raw: '{weight_raw}'")
            print(f"  Cleaned: '{weight_clean}'")
            print(f"  Float: {weight} kg")

            # Extract dimensions
            width_raw = row.get('Largura do Produto (cm)', '0')
            height_raw = row.get('Altura do Produto (cm)', '0')
            depth_raw = row.get('Profundidade do Produto (cm)', '0')

            width_str = width_raw.strip().replace('\t', '')
            height_str = height_raw.strip().replace('\t', '')
            depth_str = depth_raw.strip().replace('\t', '')

            # Handle 'None' strings
            if width_str == 'None': width_str = '0'
            if height_str == 'None': height_str = '0'
            if depth_str == 'None': depth_str = '0'

            try:
                width = float(width_str.replace(',', '.')) if width_str and width_str != '0' else 0.0
                height = float(height_str.replace(',', '.')) if height_str and height_str != '0' else 0.0
                depth = float(depth_str.replace(',', '.')) if depth_str and depth_str != '0' else 0.0
                volume = (width * height * depth) / 1000000.0 if (width and height and depth) else 0.0
            except (ValueError, AttributeError):
                width = height = depth = volume = 0.0

            print(f"\nDimensions:")
            print(f"  Width raw: '{width_raw}' -> {width} cm")
            print(f"  Height raw: '{height_raw}' -> {height} cm")
            print(f"  Depth raw: '{depth_raw}' -> {depth} cm")
            print(f"  Volume: {volume} m³")

            # Test what would be added to product_data
            product_data = {
                'barcode': barcode if barcode else None,
                'weight': weight,
                'volume': volume,
            }

            print(f"\nWould be added to product_data:")
            print(f"  barcode: {product_data['barcode']}")
            print(f"  weight: {product_data['weight']}")
            print(f"  volume: {product_data['volume']}")

            # Test what would be added to product_vals
            print(f"\nWould be added to Odoo (if checks pass):")
            if product_data.get('barcode'):
                print(f"  barcode: YES -> '{product_data['barcode']}'")
            else:
                print(f"  barcode: NO (value is {product_data.get('barcode')})")

            if product_data.get('weight'):
                print(f"  weight: YES -> {product_data['weight']} kg")
            else:
                print(f"  weight: NO (value is {product_data.get('weight')})")

            if product_data.get('volume'):
                print(f"  volume: YES -> {product_data['volume']} m³")
            else:
                print(f"  volume: NO (value is {product_data.get('volume')})")

            print("=" * 80)
            break
