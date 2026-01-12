#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upgrade jewelry_template Module

This script upgrades the jewelry_template module to apply model changes.

Usage:
    python3 upgrade_module.py --db tenant_joiasmax --password admin
"""

import argparse
import xmlrpc.client
import sys
import time


def upgrade_module(url, db, username, password, module_name='jewelry_template'):
    """Upgrade module via XML-RPC"""

    print(f"\n{'='*70}")
    print(f"UPGRADING MODULE: {module_name}")
    print(f"{'='*70}\n")

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

    try:
        # Find the module
        module_ids = execute(
            'ir.module.module', 'search',
            [[('name', '=', module_name)]],
            {'limit': 1}
        )

        if not module_ids:
            print(f"ERROR: Module '{module_name}' not found!")
            return False

        module = execute(
            'ir.module.module', 'read',
            [module_ids],
            {'fields': ['name', 'state', 'latest_version']}
        )[0]

        print(f"Found module: {module['name']}")
        print(f"  Current state: {module['state']}")
        print(f"  Version: {module.get('latest_version', 'N/A')}")

        if module['state'] != 'installed':
            print(f"\nERROR: Module is not installed (state: {module['state']})")
            return False

        print("\nInitiating upgrade...")

        # Trigger upgrade
        execute(
            'ir.module.module', 'button_immediate_upgrade',
            [module_ids]
        )

        print("OK - Upgrade initiated successfully!")
        print("\nNote: Odoo is processing the upgrade. This may take a moment.")
        print("Wait for the upgrade to complete before running validation.")

        # Wait a moment
        time.sleep(3)

        # Check if upgrade completed
        module_after = execute(
            'ir.module.module', 'read',
            [module_ids],
            {'fields': ['state']}
        )[0]

        print(f"\nModule state after upgrade: {module_after['state']}")

        if module_after['state'] == 'installed':
            print("\nSUCCESS - Module upgrade completed!")
            return True
        else:
            print(f"\nWARNING: Module state is '{module_after['state']}' (expected 'installed')")
            print("The upgrade may still be processing. Check Odoo logs if issues persist.")
            return True

    except Exception as e:
        print(f"\nERROR during upgrade: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description='Upgrade jewelry_template module')
    parser.add_argument('--url', default='http://localhost:8069', help='Odoo server URL')
    parser.add_argument('--db', default='odoo_master', help='Database name')
    parser.add_argument('--user', default='admin', help='Odoo username')
    parser.add_argument('--password', required=True, help='Odoo password')
    parser.add_argument('--module', default='jewelry_template', help='Module name to upgrade')

    args = parser.parse_args()

    try:
        success = upgrade_module(args.url, args.db, args.user, args.password, args.module)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
