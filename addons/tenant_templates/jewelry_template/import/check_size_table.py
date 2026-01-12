#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check CPL size adjustment table

Usage:
    python3 check_size_table.py --db tenant_joiasmax --password admin
"""

import argparse
import xmlrpc.client
import sys


def check_size_table(url, db, username, password):
    """Check CPL size adjustment factors"""

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

    print("\n" + "="*70)
    print("CPL SIZE ADJUSTMENT TABLE")
    print("="*70)

    # Get all size adjustments
    size_ids = execute(
        'joiasmax.size.weight.adjustment', 'search',
        [[('size_number', '>=', 6), ('size_number', '<=', 50)]]
    )

    if not size_ids:
        print("❌ No size adjustments found!")
        return False

    sizes = execute(
        'joiasmax.size.weight.adjustment', 'read',
        [size_ids],
        {'fields': ['size_number', 'adjustment_factor']}
    )

    # Sort by size number
    sizes.sort(key=lambda x: x['size_number'])

    print(f"\nTotal entries: {len(sizes)}")
    print("\nSize | Factor  | Expected Weight (7g × 1.15 × factor)")
    print("-" * 70)

    # Test sizes
    test_sizes = [6, 13, 20, 46, 50]

    for size_data in sizes:
        size_num = size_data['size_number']
        factor = size_data['adjustment_factor']
        expected_weight = 7.0 * 1.15 * factor

        marker = " *** TEST CASE ***" if size_num in test_sizes else ""

        print(f"{size_num:4d} | {factor:7.4f} | {expected_weight:7.4f}g{marker}")

    print("="*70)

    # Check specific test cases
    print("\nTEST CASE VERIFICATION:")
    print("-" * 70)

    test_cases = {
        20: 1.0000,
        13: 0.8833,
        6: 0.7666,
        46: 1.4000,
    }

    all_correct = True
    for size_num, expected_factor in test_cases.items():
        size_data = next((s for s in sizes if s['size_number'] == size_num), None)

        if not size_data:
            print(f"❌ Size {size_num}: NOT FOUND in table!")
            all_correct = False
            continue

        actual_factor = size_data['adjustment_factor']

        if abs(actual_factor - expected_factor) < 0.0001:
            print(f"✓ Size {size_num}: {actual_factor} (expected {expected_factor})")
        else:
            print(f"❌ Size {size_num}: {actual_factor} (expected {expected_factor}, MISMATCH!)")
            all_correct = False

    print("="*70)

    if all_correct:
        print("\n✓ All test cases match expected values!")
        return True
    else:
        print("\n❌ Some test cases have incorrect values!")
        return False


def main():
    parser = argparse.ArgumentParser(description='Check CPL size adjustment table')
    parser.add_argument('--url', default='http://localhost:8069', help='Odoo server URL')
    parser.add_argument('--db', default='odoo_master', help='Database name')
    parser.add_argument('--user', default='admin', help='Odoo username')
    parser.add_argument('--password', required=True, help='Odoo password')

    args = parser.parse_args()

    try:
        success = check_size_table(args.url, args.db, args.user, args.password)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
