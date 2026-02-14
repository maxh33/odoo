#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Force Cost Recomputation via Direct Method Call

This script directly invokes the _compute_variant_cost method on all variants
using Odoo's execute_kw with method invocation.

Usage:
    python3 force_cost_recompute.py --sku C725R --db tenant_joiasmax --password admin
"""

import argparse
import os
import logging
import sys
import xmlrpc.client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def force_recompute(url, db, username, password, sku):
    """Force recomputation by calling compute method directly"""

    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    if not uid:
        logger.error("❌ Authentication failed!")
        return False

    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    def execute(model, method, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        return models.execute_kw(db, uid, password, model, method, args, kwargs)

    logger.info(f"\n{'='*70}")
    logger.info(f"FORCE COST RECOMPUTATION: {sku}")
    logger.info(f"{'='*70}")

    # Find product
    variant_ids = execute(
        'product.product', 'search',
        [[('default_code', '=like', f'{sku}_%')]]
    )

    if not variant_ids:
        logger.error(f"❌ No variants found for SKU pattern '{sku}_%'!")
        return False

    logger.info(f"Found {len(variant_ids)} variants")

    # Read before state
    logger.info(f"\n{'='*70}")
    logger.info("BEFORE RECOMPUTATION")
    logger.info(f"{'='*70}")

    before_variants = execute(
        'product.product', 'read',
        [variant_ids[:3]],  # Sample first 3
        {'fields': ['default_code', 'calculated_metal_weight', 'standard_price', 'list_price']}
    )

    for v in before_variants:
        logger.info(
            f"  {v['default_code']}: "
            f"Weight {v.get('calculated_metal_weight', 0):.4f}g, "
            f"Cost R${v.get('standard_price', 0):.2f}, "
            f"Price R${v.get('list_price', 0):.2f}"
        )

    # Try to call _compute_variant_cost directly
    logger.info(f"\n{'='*70}")
    logger.info("CALLING _compute_variant_cost()")
    logger.info(f"{'='*70}")

    try:
        # Note: Private methods can't be called via XML-RPC
        # We need to use a workaround
        logger.info("Method 1: Trying direct method call...")
        execute(
            'product.product', '_compute_variant_cost',
            [variant_ids]
        )
        logger.info("✓ Method call succeeded")
    except Exception as e:
        logger.warning(f"⚠️  Direct method call failed: {e}")
        logger.info("\nMethod 2: Force recomputation via field invalidation...")

        # Alternative: Force recomputation by updating a dependent field
        # We'll update metal_weight_grams on the template to trigger cascade
        try:
            # Get template ID from first variant
            first_variant = execute(
                'product.product', 'read',
                [[variant_ids[0]]],
                {'fields': ['product_tmpl_id']}
            )[0]

            template_id = first_variant['product_tmpl_id'][0]

            # Read current base weight
            template = execute(
                'product.template', 'read',
                [[template_id]],
                {'fields': ['metal_weight_grams']}
            )[0]

            base_weight = template['metal_weight_grams']

            logger.info(f"Updating template {template_id} metal_weight_grams to trigger cascade...")

            # Update to same value - this should trigger recomputation
            execute(
                'product.template', 'write',
                [[template_id], {'metal_weight_grams': base_weight}]
            )

            logger.info("✓ Template updated")

        except Exception as e2:
            logger.error(f"❌ Cascade trigger failed: {e2}")
            return False

    # Read after state
    logger.info(f"\n{'='*70}")
    logger.info("AFTER RECOMPUTATION")
    logger.info(f"{'='*70}")

    after_variants = execute(
        'product.product', 'read',
        [variant_ids[:3]],  # Sample first 3
        {'fields': ['default_code', 'calculated_metal_weight', 'standard_price', 'list_price']}
    )

    for v in after_variants:
        logger.info(
            f"  {v['default_code']}: "
            f"Weight {v.get('calculated_metal_weight', 0):.4f}g, "
            f"Cost R${v.get('standard_price', 0):.2f}, "
            f"Price R${v.get('list_price', 0):.2f}"
        )

    # Check if costs were updated
    costs_updated = any(v.get('standard_price', 0) > 0 for v in after_variants)

    logger.info(f"\n{'='*70}")
    if costs_updated:
        logger.info("✓ Costs were updated!")
    else:
        logger.error("❌ Costs are still R$0.00")
        logger.error("\nThis indicates the computed field dependencies aren't working.")
        logger.error("You may need to:")
        logger.error("1. Check Odoo logs for errors in _compute_variant_cost()")
        logger.error("2. Verify market price exists: joiasmax.market.price with material_type='gold_24k'")
        logger.error("3. Manually trigger recomputation from Odoo UI")

    logger.info(f"{'='*70}\n")

    return costs_updated


def main():
    parser = argparse.ArgumentParser(
        description='Force cost recomputation via direct method call'
    )

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
        success = force_recompute(args.url, args.db, args.user, args.password, args.sku)
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
