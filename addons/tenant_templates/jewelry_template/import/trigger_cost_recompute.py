#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trigger Cost Recomputation by Toggling Dependency

This script forces cost recalculation by toggling has_size_based_pricing flag,
which is a dependency of _compute_variant_cost().

The toggle operation will trigger Odoo's ORM to invalidate the compute cache
and recalculate all dependent fields.

Usage:
    python3 trigger_cost_recompute.py --sku C725R --db tenant_joiasmax --password admin
"""

import argparse
import logging
import sys
import xmlrpc.client
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def trigger_recompute(url, db, username, password, sku):
    """Force recomputation by toggling has_size_based_pricing dependency"""

    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    if not uid:
        logger.error("Authentication failed!")
        return False

    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    def execute(model, method, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        return models.execute_kw(db, uid, password, model, method, args, kwargs)

    logger.info(f"\n{'='*70}")
    logger.info(f"TRIGGER COST RECOMPUTATION: {sku}")
    logger.info(f"{'='*70}")

    # Find product template
    variant_ids = execute(
        'product.product', 'search',
        [[('default_code', '=like', f'{sku}_%')]],
        {'limit': 1}
    )

    if not variant_ids:
        logger.error(f"No variants found for SKU pattern '{sku}_%'!")
        return False

    # Get template from variant
    first_variant = execute(
        'product.product', 'read',
        [[variant_ids[0]]],
        {'fields': ['product_tmpl_id']}
    )[0]

    template_id = first_variant['product_tmpl_id'][0]
    logger.info(f"Found template ID: {template_id}")

    # Get all variants count
    all_variant_ids = execute(
        'product.product', 'search',
        [[('product_tmpl_id', '=', template_id)]]
    )
    logger.info(f"Product has {len(all_variant_ids)} variants")

    # Read before state
    logger.info(f"\n{'='*70}")
    logger.info("BEFORE RECOMPUTATION")
    logger.info(f"{'='*70}")

    before_variants = execute(
        'product.product', 'read',
        [all_variant_ids[:3]],  # Sample first 3
        {'fields': ['default_code', 'calculated_metal_weight', 'standard_price', 'list_price']}
    )

    for v in before_variants:
        logger.info(
            f"  {v['default_code']}: "
            f"Weight {v.get('calculated_metal_weight', 0):.4f}g, "
            f"Cost R${v.get('standard_price', 0):.2f}, "
            f"Price R${v.get('list_price', 0):.2f}"
        )

    # Method 1: Toggle has_size_based_pricing to trigger compute
    logger.info(f"\n{'='*70}")
    logger.info("METHOD 1: Toggle has_size_based_pricing flag")
    logger.info(f"{'='*70}")

    try:
        logger.info("Step 1: Disable size-based pricing...")
        execute(
            'product.template', 'write',
            [[template_id], {'has_size_based_pricing': False}]
        )
        logger.info("OK - Disabled")

        # Small delay to ensure Odoo processes the change
        time.sleep(1)

        logger.info("Step 2: Re-enable size-based pricing...")
        execute(
            'product.template', 'write',
            [[template_id], {'has_size_based_pricing': True}]
        )
        logger.info("OK - Re-enabled (this should trigger _compute_variant_cost)")

        # Small delay to allow compute to complete
        time.sleep(2)

    except Exception as e:
        logger.error(f"Toggle failed: {e}")
        return False

    # Read after state
    logger.info(f"\n{'='*70}")
    logger.info("AFTER RECOMPUTATION")
    logger.info(f"{'='*70}")

    after_variants = execute(
        'product.product', 'read',
        [all_variant_ids[:3]],  # Sample first 3
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
        logger.info("SUCCESS - Costs were updated!")
        logger.info("\nExpected calculation for variants (@ R$380/g gold price):")
        for v in after_variants:
            weight = v.get('calculated_metal_weight', 0)
            cost = v.get('standard_price', 0)
            expected_cost = weight * 380.0 * 1.0 * 1.0  # weight × gold_price × purity × provider
            logger.info(
                f"  {v['default_code']}: "
                f"Weight {weight:.4f}g → "
                f"Cost R${cost:.2f} "
                f"(expected R${expected_cost:.2f})"
            )
    else:
        logger.error("FAILED - Costs are still R$0.00")
        logger.error("\nPossible remaining issues:")
        logger.error("1. Check Odoo server logs for errors in _compute_variant_cost()")
        logger.error("2. Verify template configuration:")
        logger.error("   - has_size_based_pricing = True")
        logger.error("   - material_type = 'gold'")
        logger.error("   - metal_purity = '24k'")
        logger.error("3. Check if _compute_variant_cost is being called at all")

    logger.info(f"{'='*70}\n")

    return costs_updated


def main():
    parser = argparse.ArgumentParser(
        description='Trigger cost recomputation by toggling dependency flag'
    )

    parser.add_argument('--sku', required=True, help='Product SKU (e.g., C725R)')
    parser.add_argument('--url', default='http://localhost:8069', help='Odoo server URL')
    parser.add_argument('--db', default='odoo_master', help='Database name')
    parser.add_argument('--user', default='admin', help='Odoo username')
    parser.add_argument('--password', required=True, help='Odoo password')

    args = parser.parse_args()

    try:
        success = trigger_recompute(args.url, args.db, args.user, args.password, args.sku)
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
