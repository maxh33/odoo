#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Market Price Configuration

This script verifies that market price data exists for gold_24k,
which is required for cost calculations.

Usage:
    python3 check_market_price.py --db tenant_joiasmax --password admin
"""

import argparse
import xmlrpc.client
import sys


def check_market_price(url, db, username, password):
    """Check if gold market price exists"""

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
    print("CHECKING MARKET PRICE CONFIGURATION")
    print("="*70)

    # Check if market price model exists
    try:
        # Search for active gold_24k price
        price_ids = execute(
            'joiasmax.market.price', 'search',
            [[('material_type', '=', 'gold_24k'), ('is_active', '=', True)]],
            {'limit': 1}
        )

        if price_ids:
            prices = execute(
                'joiasmax.market.price', 'read',
                [price_ids],
                {'fields': ['material_type', 'price_per_gram_brl', 'is_active']}
            )
            
            price = prices[0]
            print(f"\nOK - Found active gold_24k market price:")
            print(f"  - Price: R${price['price_per_gram_brl']:.2f}/g")
            print(f"  - Is Active: {price['is_active']}")
            
            return True
        else:
            print("\nERROR - No active gold_24k market price found!")
            print("\nYou need to create a market price record:")
            print("  Model: joiasmax.market.price")
            print("  Fields:")
            print("    - material_type: 'gold_24k'")
            print("    - price_per_gram_brl: (e.g., 700.00)")
            print("    - is_active: True")
            
            # Check if any market prices exist (even inactive)
            all_price_ids = execute(
                'joiasmax.market.price', 'search',
                [[]]
            )
            
            if all_price_ids:
                print(f"\n  Found {len(all_price_ids)} market price record(s) total")
                all_prices = execute(
                    'joiasmax.market.price', 'read',
                    [all_price_ids[:5]],  # Show first 5
                    {'fields': ['material_type', 'price_per_gram_brl', 'is_active']}
                )
                
                print("\n  Existing market prices:")
                for p in all_prices:
                    print(f"    - {p['material_type']}: R${p['price_per_gram_brl']:.2f}/g (active: {p['is_active']})")
            
            return False

    except Exception as e:
        print(f"\nERROR - Error checking market price: {e}")
        print("\nPossible issues:")
        print("1. Model joiasmax.market.price doesn't exist")
        print("2. Missing fields: material_type, price_per_gram_brl, is_active")
        print("3. Database connection issue")
        return False

    finally:
        print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Check market price configuration')
    parser.add_argument('--url', default='http://localhost:8069', help='Odoo server URL')
    parser.add_argument('--db', default='odoo_master', help='Database name')
    parser.add_argument('--user', default='admin', help='Odoo username')
    parser.add_argument('--password', required=True, help='Odoo password')

    args = parser.parse_args()

    try:
        success = check_market_price(args.url, args.db, args.user, args.password)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
