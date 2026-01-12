#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose Cost Computation Issues

This script checks all conditions that _compute_variant_cost() evaluates
to identify why costs aren't being calculated.

Usage:
    python3 diagnose_cost_compute.py --sku C725R --db tenant_joiasmax --password admin
"""

import argparse
import xmlrpc.client
import sys


def diagnose(url, db, username, password, sku):
    """Diagnose all conditions for cost computation"""

    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("ERROR: Authentication failed!")
        return False

    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    def execute(model, method, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        return models.execute_kw(db, uid, password, model, method, args, kwargs)

    print("\n" + "="*70)
    print(f"DIAGNOSING COST COMPUTATION: {sku}")
    print("="*70)

    # Find product
    variant_ids = execute(
        'product.product', 'search',
        [[('default_code', '=like', f'{sku}_%')]],
        {'limit': 3}
    )

    if not variant_ids:
        print(f"\nERROR: No variants found for SKU pattern '{sku}_%'!")
        return False

    print(f"\nFound {len(variant_ids)} sample variants")

    # Get template from first variant
    first_variant = execute(
        'product.product', 'read',
        [[variant_ids[0]]],
        {'fields': ['product_tmpl_id']}
    )[0]

    template_id = first_variant['product_tmpl_id'][0]

    # Read template configuration
    template = execute(
        'product.template', 'read',
        [[template_id]],
        {'fields': [
            'name', 'has_size_based_pricing', 'material_type', 'metal_purity',
            'metal_weight_grams', 'size_pricing_coef', 'jewelry_pricing_id'
        ]}
    )[0]

    print("\n" + "="*70)
    print("TEMPLATE CONFIGURATION")
    print("="*70)
    print(f"Product: {template['name']} (ID: {template_id})")
    print(f"  has_size_based_pricing: {template.get('has_size_based_pricing')}")
    print(f"  material_type: {template.get('material_type')}")
    print(f"  metal_purity: {template.get('metal_purity')}")
    print(f"  metal_weight_grams: {template.get('metal_weight_grams')}g")
    print(f"  size_pricing_coef: {template.get('size_pricing_coef')}")
    print(f"  jewelry_pricing_id: {template.get('jewelry_pricing_id')}")

    # Check condition 1: has_size_based_pricing
    if not template.get('has_size_based_pricing'):
        print("\nERROR: Condition 1 FAILED - has_size_based_pricing is False!")
        print("  This causes early return in _compute_variant_cost (line 78)")
        return False
    else:
        print("\nOK: Condition 1 PASSED - has_size_based_pricing is True")

    # Check condition 2: material_type mapping
    market_type_map = {
        'gold': 'gold_24k',
        'silver': 'silver_950',
    }
    material_type = template.get('material_type')
    market_type = market_type_map.get(material_type)

    if not market_type:
        print(f"\nERROR: Condition 2 FAILED - material_type '{material_type}' not in map!")
        print("  Valid values: 'gold', 'silver'")
        print("  This causes early return in _compute_variant_cost (line 90)")
        return False
    else:
        print(f"\nOK: Condition 2 PASSED - material_type '{material_type}' maps to '{market_type}'")

    # Check condition 3: market price exists
    price_ids = execute(
        'joiasmax.market.price', 'search',
        [[('material_type', '=', market_type), ('is_active', '=', True)]],
        {'limit': 1}
    )

    if not price_ids:
        print(f"\nERROR: Condition 3 FAILED - No active market price for '{market_type}'!")
        print("  This causes early return in _compute_variant_cost (line 98)")
        return False
    else:
        prices = execute(
            'joiasmax.market.price', 'read',
            [price_ids],
            {'fields': ['price_per_gram_brl']}
        )
        gold_price = prices[0]['price_per_gram_brl']
        print(f"\nOK: Condition 3 PASSED - Active market price found: R${gold_price:.2f}/g")

    # Check purity factor
    purity_factors = {
        '24k': 1.0,
        '950': 0.95,
    }
    metal_purity = template.get('metal_purity')
    purity_factor = purity_factors.get(metal_purity, 1.0)
    print(f"\nPurity factor for '{metal_purity}': {purity_factor}")

    # Check provider indice
    provider_indice = 1.0
    if template.get('jewelry_pricing_id'):
        pricing_id = template['jewelry_pricing_id'][0]
        pricing = execute(
            'joiasmax.jewelry.pricing', 'read',
            [[pricing_id]],
            {'fields': ['provider_indice']}
        )[0]
        provider_indice = pricing.get('provider_indice', 1.0)
        print(f"Provider indice from jewelry_pricing: {provider_indice}")
    else:
        print("No jewelry_pricing_id, using default provider_indice: 1.0")

    # Now check variants
    print("\n" + "="*70)
    print("VARIANT ANALYSIS")
    print("="*70)

    variants = execute(
        'product.product', 'read',
        [variant_ids],
        {'fields': ['default_code', 'calculated_metal_weight', 'standard_price', 'list_price']}
    )

    all_pass = True
    for variant in variants:
        print(f"\nVariant: {variant['default_code']} (ID: {variant['id']})")
        weight = variant.get('calculated_metal_weight', 0)
        cost = variant.get('standard_price', 0)
        price = variant.get('list_price', 0)

        print(f"  calculated_metal_weight: {weight:.4f}g")

        # Check condition 4: calculated_metal_weight exists
        if not weight:
            print("  ERROR: Condition 4 FAILED - calculated_metal_weight is 0!")
            print("  This causes early return in _compute_variant_cost (line 78)")
            all_pass = False
            continue
        else:
            print("  OK: Condition 4 PASSED - calculated_metal_weight exists")

        # Calculate expected cost
        expected_cost = weight * gold_price * purity_factor * provider_indice
        print(f"\n  Expected cost calculation:")
        print(f"    {weight:.4f}g × R${gold_price:.2f}/g × {purity_factor} × {provider_indice}")
        print(f"    = R${expected_cost:.2f}")

        print(f"\n  Actual standard_price: R${cost:.2f}")
        print(f"  Actual list_price: R${price:.2f}")

        if abs(cost - expected_cost) > 0.01:
            print(f"  ERROR: Cost mismatch! Expected R${expected_cost:.2f}, got R${cost:.2f}")
            all_pass = False
        else:
            print("  OK: Cost matches expected value")

    print("\n" + "="*70)
    print("DIAGNOSIS SUMMARY")
    print("="*70)

    if all_pass:
        print("\nALL CONDITIONS PASSED!")
        print("Costs should be calculating correctly.")
        print("\nIf costs are still R$0.00, check:")
        print("1. Odoo server logs for Python exceptions")
        print("2. Whether _compute_variant_cost is actually being called")
        print("3. Database permissions on standard_price field")
    else:
        print("\nSOME CONDITIONS FAILED!")
        print("Review the errors above to identify the issue.")
        print("\nThe compute method has early returns (continue) when conditions fail,")
        print("which prevents cost calculation.")

    print("="*70 + "\n")

    return all_pass


def main():
    parser = argparse.ArgumentParser(description='Diagnose cost computation issues')
    parser.add_argument('--sku', required=True, help='Product SKU (e.g., C725R)')
    parser.add_argument('--url', default='http://localhost:8069', help='Odoo server URL')
    parser.add_argument('--db', default='odoo_master', help='Database name')
    parser.add_argument('--user', default='admin', help='Odoo username')
    parser.add_argument('--password', required=True, help='Odoo password')

    args = parser.parse_args()

    try:
        success = diagnose(args.url, args.db, args.user, args.password, args.sku)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
