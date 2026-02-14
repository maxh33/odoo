#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick diagnostic script to check current C725R configuration

Usage:
    python3 check_product_config.py --sku C725R --db tenant_joiasmax --password admin
"""

import argparse
import os
import xmlrpc.client
import sys


def check_product_config(url, db, username, password, sku):
    """Check current product configuration in database"""

    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("❌ Authentication failed!")
        return False

    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    def execute(model, method, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        return models.execute_kw(db, uid, password, model, method, args, kwargs)

    print(f"\n{'='*70}")
    print(f"CHECKING PRODUCT CONFIGURATION: {sku}")
    print(f"{'='*70}\n")

    # Try to find product template directly
    product_ids = execute(
        'product.template', 'search',
        [[('default_code', '=', sku)]],
        {'limit': 1}
    )

    if product_ids:
        print(f"✓ Found product template directly (ID: {product_ids[0]})")
        template_id = product_ids[0]
    else:
        print(f"⚠️  Template not found by SKU '{sku}', searching variants...")

        # Search by variant pattern
        variant_ids = execute(
            'product.product', 'search',
            [[('default_code', '=like', f'{sku}_%')]],
            {'limit': 1}
        )

        if not variant_ids:
            print(f"❌ No variants found matching '{sku}_%' pattern!")
            return False

        # Get template from variant
        variants = execute(
            'product.product', 'read',
            [variant_ids],
            {'fields': ['product_tmpl_id', 'default_code']}
        )

        template_id = variants[0]['product_tmpl_id'][0]
        print(f"✓ Found via variant '{variants[0]['default_code']}' (Template ID: {template_id})")

    # Read all configuration fields
    products = execute(
        'product.template', 'read',
        [[template_id]],
        {'fields': [
            'id', 'name', 'default_code',
            'is_jewelry', 'material_type', 'metal_purity',
            'metal_weight_grams', 'has_size_based_pricing',
            'size_pricing_coef', 'jewelry_pricing_id'
        ]}
    )

    if not products:
        print(f"❌ Failed to read product template!")
        return False

    product = products[0]

    # Display configuration
    print(f"\nProduct: {product['name']}")
    print(f"  ID: {product['id']}")
    print(f"  SKU (default_code): {product.get('default_code', 'EMPTY (expected for products with variants)')}")
    print(f"\n--- Jewelry Configuration ---")
    print(f"  is_jewelry: {product.get('is_jewelry', False)}")
    print(f"  material_type: {product.get('material_type', 'NOT SET')}")
    print(f"  metal_purity: {product.get('metal_purity', 'NOT SET')}")
    print(f"\n--- Size-Based Pricing ---")
    print(f"  has_size_based_pricing: {product.get('has_size_based_pricing', False)}")
    print(f"  metal_weight_grams (base weight): {product.get('metal_weight_grams', 0.0)}g")
    print(f"  size_pricing_coef (COEF): {product.get('size_pricing_coef', 1.0)}")

    # Check jewelry pricing
    pricing_id = product.get('jewelry_pricing_id')
    if pricing_id:
        pricing = execute(
            'joiasmax.jewelry.pricing', 'read',
            [pricing_id[0]],
            {'fields': ['provider_indice', 'markup_percentage']}
        )[0]
        print(f"\n--- Jewelry Pricing (ID: {pricing_id[0]}) ---")
        print(f"  provider_indice: {pricing.get('provider_indice', 1.0)}")
        print(f"  markup_percentage: {pricing.get('markup_percentage', 0.0)}%")
    else:
        print(f"\n--- Jewelry Pricing ---")
        print(f"  ⚠️  No jewelry pricing record linked!")

    # Check variants
    variant_ids = execute(
        'product.product', 'search',
        [[('product_tmpl_id', '=', template_id)]]
    )

    print(f"\n--- Variants ---")
    print(f"  Total variants: {len(variant_ids)}")

    if variant_ids:
        # Sample first few variants
        sample_variant_ids = variant_ids[:3] if len(variant_ids) >= 3 else variant_ids
        sample_variants = execute(
            'product.product', 'read',
            [sample_variant_ids],
            {'fields': ['default_code', 'ring_size', 'calculated_metal_weight']}
        )

        print(f"  Sample variants:")
        for v in sample_variants:
            print(f"    - {v['default_code']}: Size {v.get('ring_size', 'N/A')}, "
                  f"Weight {v.get('calculated_metal_weight', 0.0):.4f}g")

    print(f"\n{'='*70}")

    # Validation summary
    issues = []
    if not product.get('has_size_based_pricing'):
        issues.append("❌ has_size_based_pricing is False or not set")
    if product.get('size_pricing_coef', 1.0) != 1.15:
        issues.append(f"❌ size_pricing_coef is {product.get('size_pricing_coef', 1.0)} (expected 1.15)")
    if product.get('metal_weight_grams', 0.0) != 7.0:
        issues.append(f"❌ metal_weight_grams is {product.get('metal_weight_grams', 0.0)} (expected 7.0)")

    if issues:
        print("\n⚠️  CONFIGURATION ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print("\nRun configure_cpl_product.py to fix these issues.")
        return False
    else:
        print("\n✓ ALL CONFIGURATION CORRECT!")
        return True


def main():
    parser = argparse.ArgumentParser(description='Check product configuration')
    parser.add_argument('--sku', required=True, help='Product SKU (e.g., C725R)')
    parser.add_argument('--url', default='http://localhost:8069', help='Odoo server URL')
    parser.add_argument('--db', default='odoo_master', help='Database name')
    parser.add_argument('--user', default='admin', help='Odoo username')
    parser.add_argument('--password', default=os.environ.get('ODOO_PASSWORD'),
                       help='Odoo password (or set ODOO_PASSWORD env var)')

    args = parser.parse_args()
    if not args.password:
        parser.error("--password is required (or set ODOO_PASSWORD environment variable)")

    try:
        success = check_product_config(
            args.url, args.db, args.user, args.password, args.sku
        )
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
