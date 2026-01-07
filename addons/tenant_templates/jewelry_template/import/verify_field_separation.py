# -*- coding: utf-8 -*-
"""
Smart Field Separation Verification for JoiasMax Products

Validates the separation between:
- Internal ERP fields (automation, fiscal, logistics)
- External E-commerce fields (customer-facing display)
- Hybrid fields (both purposes)

Reports critical missing data that breaks automation.
"""

import xmlrpc.client
import csv
from collections import defaultdict

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
print("JOIASMAX FIELD SEPARATION VERIFICATION")
print("=" * 100)

# Get all jewelry products
products = models.execute_kw(
    db, uid, password,
    'product.template', 'search_read',
    [[('create_date', '>=', '2026-01-05'), ('is_jewelry', '=', True)]],
    {'fields': [
        # Identity
        'id', 'default_code', 'name', 'categ_id',
        # Internal ERP Fields (Backend Automation)
        'metal_weight_grams', 'material_type', 'metal_purity',
        'jewelry_pricing_id', 'barcode',
        'weight', 'volume',  # Package logistics
        # External E-commerce Fields (Customer-facing)
        'description_sale', 'list_price',
        # Hybrid
        'is_jewelry'
    ],
     'order': 'categ_id, default_code'}
)

print(f"\n[INFO] Found {len(products)} jewelry products imported today")
print("=" * 100)

# Field classification
INTERNAL_FIELDS = {
    'metal_weight_grams': 'Precious metal weight (for pricing automation)',
    'material_type': 'Material type (gold/silver for pricing)',
    'metal_purity': 'Metal purity (24k/950 for pricing)',
    'jewelry_pricing_id': 'Linked pricing record (automation)',
    'barcode': 'GTIN/EAN (fiscal, inventory tracking)',
    'weight': 'Package weight Kg (shipping calculation)',
    'volume': 'Package volume m3 (shipping calculation)',
}

EXTERNAL_FIELDS = {
    'name': 'Product name (customer display)',
    'description_sale': 'E-commerce description (WooCommerce HTML)',
    'list_price': 'Sales price (customer display)',
}

HYBRID_FIELDS = {
    'is_jewelry': 'Jewelry flag (internal logic + display filter)',
    'categ_id': 'Category (internal organization + customer navigation)',
}

# Analysis by category
category_stats = defaultdict(lambda: {
    'count': 0,
    'with_weight': 0,
    'with_barcode': 0,
    'with_package_weight': 0,
    'with_package_volume': 0,
    'with_pricing_link': 0,
    'with_description_sale': 0,
    'products': []
})

critical_issues = []

for p in products:
    categ_name = p['categ_id'][1] if p.get('categ_id') else 'Uncategorized'

    category_stats[categ_name]['count'] += 1
    category_stats[categ_name]['products'].append(p)

    # Check internal fields
    has_metal_weight = p.get('metal_weight_grams') and p['metal_weight_grams'] > 0
    has_barcode = bool(p.get('barcode'))
    has_package_weight = p.get('weight') and p['weight'] > 0
    has_package_volume = p.get('volume') and p['volume'] > 0
    has_pricing_link = bool(p.get('jewelry_pricing_id'))
    has_description_sale = bool(p.get('description_sale'))

    if has_metal_weight:
        category_stats[categ_name]['with_weight'] += 1
    if has_barcode:
        category_stats[categ_name]['with_barcode'] += 1
    if has_package_weight:
        category_stats[categ_name]['with_package_weight'] += 1
    if has_package_volume:
        category_stats[categ_name]['with_package_volume'] += 1
    if has_pricing_link:
        category_stats[categ_name]['with_pricing_link'] += 1
    if has_description_sale:
        category_stats[categ_name]['with_description_sale'] += 1

    # CRITICAL: Jewelry product claiming gold/silver but no weight = can't automate pricing
    if p.get('material_type') in ['gold', 'silver'] and not has_metal_weight:
        critical_issues.append({
            'sku': p['default_code'],
            'name': p['name'][:60],
            'category': categ_name,
            'material': p['material_type'],
            'issue': 'MISSING METAL WEIGHT - Cannot calculate dynamic pricing',
            'severity': 'CRITICAL'
        })

    # WARNING: No barcode = fiscal/inventory tracking issues
    if not has_barcode:
        critical_issues.append({
            'sku': p['default_code'],
            'name': p['name'][:60],
            'category': categ_name,
            'material': p.get('material_type', 'N/A'),
            'issue': 'MISSING BARCODE - Fiscal/inventory tracking limited',
            'severity': 'WARNING'
        })

# Print Field Classification
print("\n[FIELD CLASSIFICATION]")
print("-" * 100)

print("\n1. INTERNAL ERP FIELDS (Backend Automation):")
for field, description in INTERNAL_FIELDS.items():
    print(f"   - {field:25s} : {description}")

print("\n2. EXTERNAL E-COMMERCE FIELDS (Customer-facing):")
for field, description in EXTERNAL_FIELDS.items():
    print(f"   - {field:25s} : {description}")

print("\n3. HYBRID FIELDS (Both purposes):")
for field, description in HYBRID_FIELDS.items():
    print(f"   - {field:25s} : {description}")

# Print Category Analysis
print("\n\n[CATEGORY ANALYSIS - Field Population]")
print("=" * 100)

for categ_name in sorted(category_stats.keys()):
    stats = category_stats[categ_name]
    total = stats['count']

    print(f"\n{categ_name} ({total} products)")
    print("-" * 100)
    print(f"  Internal Fields (Automation):")
    print(f"    - Metal Weight (pricing):        {stats['with_weight']:2d}/{total} ({stats['with_weight']/total*100:5.1f}%)")
    print(f"    - Pricing Link (automation):     {stats['with_pricing_link']:2d}/{total} ({stats['with_pricing_link']/total*100:5.1f}%)")
    print(f"    - Barcode (fiscal/inventory):    {stats['with_barcode']:2d}/{total} ({stats['with_barcode']/total*100:5.1f}%)")
    print(f"    - Package Weight (shipping):     {stats['with_package_weight']:2d}/{total} ({stats['with_package_weight']/total*100:5.1f}%)")
    print(f"    - Package Volume (shipping):     {stats['with_package_volume']:2d}/{total} ({stats['with_package_volume']/total*100:5.1f}%)")
    print(f"  External Fields (E-commerce):")
    print(f"    - Description Sale (WooCommerce): {stats['with_description_sale']:2d}/{total} ({stats['with_description_sale']/total*100:5.1f}%)")

# Print Critical Issues
print("\n\n[CRITICAL MISSING DATA REPORT]")
print("=" * 100)

if critical_issues:
    critical_count = sum(1 for i in critical_issues if i['severity'] == 'CRITICAL')
    warning_count = sum(1 for i in critical_issues if i['severity'] == 'WARNING')

    print(f"\n[SUMMARY] {critical_count} CRITICAL issues, {warning_count} WARNINGS")
    print("-" * 100)

    # Group by severity
    for severity in ['CRITICAL', 'WARNING']:
        issues = [i for i in critical_issues if i['severity'] == severity]
        if issues:
            print(f"\n[{severity}] {len(issues)} issues:")
            print(f"{'SKU':<15} {'Category':<20} {'Material':<10} {'Issue':<60}")
            print("-" * 100)
            for issue in issues[:10]:  # Show first 10
                print(f"{issue['sku']:<15} {issue['category']:<20} {issue['material']:<10} {issue['issue']:<60}")
            if len(issues) > 10:
                print(f"\n   ...and {len(issues) - 10} more {severity} issues")
else:
    print("\n[SUCCESS] No critical issues found!")

# Suggest ONE representative product per category for focused testing
print("\n\n[RECOMMENDED TEST PRODUCTS - One per Category]")
print("=" * 100)
print("\nFor focused validation testing, use these representative products:")
print("-" * 100)
print(f"{'Category':<25} {'SKU':<15} {'Name':<45} {'Fields Status'}")
print("-" * 100)

for categ_name in sorted(category_stats.keys()):
    stats = category_stats[categ_name]
    products_in_cat = stats['products']

    # Pick best representative: has most fields populated
    best_product = None
    best_score = -1

    for p in products_in_cat:
        score = 0
        if p.get('metal_weight_grams') and p['metal_weight_grams'] > 0: score += 3  # Most important
        if p.get('barcode'): score += 2
        if p.get('weight') and p['weight'] > 0: score += 1
        if p.get('jewelry_pricing_id'): score += 2
        if p.get('description_sale'): score += 1

        if score > best_score:
            best_score = score
            best_product = p

    if best_product:
        status_parts = []
        if best_product.get('metal_weight_grams') and best_product['metal_weight_grams'] > 0:
            status_parts.append("Weight")
        if best_product.get('barcode'):
            status_parts.append("Barcode")
        if best_product.get('jewelry_pricing_id'):
            status_parts.append("Pricing")

        status = ", ".join(status_parts) if status_parts else "Minimal data"

        print(f"{categ_name:<25} {best_product['default_code']:<15} {best_product['name'][:45]:<45} {status}")

# Export detailed field separation report
print("\n\n[EXPORTING DETAILED REPORT]")
print("=" * 100)

csv_path = 'reports/field_separation_report.csv'
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'SKU', 'Name', 'Category', 'Material',
        'Metal_Weight_g', 'Barcode', 'Package_Weight_kg', 'Package_Volume_m3',
        'Pricing_Linked', 'Description_Sale_Set',
        'Critical_Issues'
    ])
    writer.writeheader()

    for p in products:
        categ_name = p['categ_id'][1] if p.get('categ_id') else 'Uncategorized'

        # Find critical issues for this product
        product_issues = [i['issue'] for i in critical_issues if i['sku'] == p['default_code'] and i['severity'] == 'CRITICAL']

        writer.writerow({
            'SKU': p['default_code'],
            'Name': p['name'],
            'Category': categ_name,
            'Material': p.get('material_type', ''),
            'Metal_Weight_g': p.get('metal_weight_grams', 0),
            'Barcode': p.get('barcode', ''),
            'Package_Weight_kg': p.get('weight', 0),
            'Package_Volume_m3': p.get('volume', 0),
            'Pricing_Linked': 'YES' if p.get('jewelry_pricing_id') else 'NO',
            'Description_Sale_Set': 'YES' if p.get('description_sale') else 'NO',
            'Critical_Issues': '; '.join(product_issues) if product_issues else ''
        })

print(f"\n[SUCCESS] Detailed report exported to: {csv_path}")

print("\n" + "=" * 100)
print("[VERIFICATION COMPLETE]")
print("=" * 100)
print("\nKey Findings:")
print(f"  - {len(products)} jewelry products analyzed")
print(f"  - {critical_count if critical_issues else 0} products with CRITICAL missing data (breaks automation)")
print(f"  - {warning_count if critical_issues else 0} products with WARNINGS (limited functionality)")
print(f"  - {len(category_stats)} categories validated")
print(f"\nRecommendation: Focus testing on {len(category_stats)} representative products (one per category)")
print("=" * 100)
