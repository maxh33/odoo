#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Force Recalculation of Variant Prices

This script forces Odoo to recalculate computed fields for all variants
by touching the ring_size field, which triggers the dependency chain:
- ring_size → calculated_metal_weight → standard_price → list_price

Usage:
    python3 recalculate_variant_prices.py --sku C725R --db tenant_joiasmax --password admin
"""

import argparse
import logging
import sys
import xmlrpc.client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VariantPriceRecalculator:
    """Force recalculation of variant prices"""

    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password

        # Connect to Odoo
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.uid = common.authenticate(db, username, password, {})

        if not self.uid:
            raise ValueError("Authentication failed! Check credentials.")

        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        logger.info(f"Connected to Odoo as user ID: {self.uid}")

    def execute(self, model, method, args=None, kwargs=None):
        """Execute Odoo model method"""
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, method, args, kwargs
        )

    def find_product(self, sku):
        """Find product template by SKU (handles products with variants)"""
        # Try template first
        product_ids = self.execute(
            'product.template', 'search',
            [[('default_code', '=', sku)]],
            {'limit': 1}
        )

        if product_ids:
            return product_ids[0]

        # Try variant pattern
        variant_ids = self.execute(
            'product.product', 'search',
            [[('default_code', '=like', f'{sku}_%')]],
            {'limit': 1}
        )

        if not variant_ids:
            return None

        variants = self.execute(
            'product.product', 'read',
            [variant_ids],
            {'fields': ['product_tmpl_id']}
        )

        return variants[0]['product_tmpl_id'][0] if variants else None

    def recalculate_variants(self, sku):
        """Force recalculation of all variant prices"""
        logger.info(f"\n{'='*70}")
        logger.info(f"RECALCULATING VARIANT PRICES: {sku}")
        logger.info(f"{'='*70}")

        # Find product
        product_id = self.find_product(sku)
        if not product_id:
            logger.error(f"❌ Product '{sku}' not found!")
            return False

        logger.info(f"Found product template ID: {product_id}")

        # Get all variants
        variant_ids = self.execute(
            'product.product', 'search',
            [[('product_tmpl_id', '=', product_id)]]
        )

        if not variant_ids:
            logger.error("❌ No variants found!")
            return False

        logger.info(f"Found {len(variant_ids)} variants")

        # Read current state
        variants = self.execute(
            'product.product', 'read',
            [variant_ids],
            {'fields': [
                'id', 'default_code', 'ring_size',
                'calculated_metal_weight', 'standard_price', 'list_price'
            ]}
        )

        logger.info(f"\n{'='*70}")
        logger.info("BEFORE RECALCULATION")
        logger.info(f"{'='*70}")

        # Show first few variants before
        for v in variants[:3]:
            logger.info(
                f"  {v['default_code']}: Size {v.get('ring_size', 'N/A')}, "
                f"Weight {v.get('calculated_metal_weight', 0):.4f}g, "
                f"Cost R${v.get('standard_price', 0):.2f}, "
                f"Price R${v.get('list_price', 0):.2f}"
            )

        logger.info(f"\n{'='*70}")
        logger.info("FORCING RECALCULATION")
        logger.info(f"{'='*70}")
        logger.info("Method: Touching ring_size field to trigger computed field chain")

        # Force recalculation by "touching" the ring_size field
        # This triggers: ring_size → calculated_metal_weight → standard_price → list_price
        recalculated = 0
        errors = []

        for variant in variants:
            try:
                variant_id = variant['id']
                ring_size = variant.get('ring_size')

                if not ring_size:
                    logger.warning(f"  Skipping {variant['default_code']}: no ring_size")
                    continue

                # Update ring_size to itself to trigger recomputation
                self.execute(
                    'product.product', 'write',
                    [[variant_id], {'ring_size': ring_size}]
                )

                recalculated += 1

            except Exception as e:
                error_msg = f"{variant['default_code']}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"  ❌ Error: {error_msg}")

        logger.info(f"\n✓ Triggered recalculation for {recalculated}/{len(variants)} variants")

        if errors:
            logger.warning(f"⚠️  {len(errors)} errors occurred")

        # Read updated state
        logger.info(f"\n{'='*70}")
        logger.info("AFTER RECALCULATION")
        logger.info(f"{'='*70}")

        updated_variants = self.execute(
            'product.product', 'read',
            [variant_ids],
            {'fields': [
                'id', 'default_code', 'ring_size',
                'calculated_metal_weight', 'standard_price', 'list_price'
            ]}
        )

        # Show first few variants after
        for v in updated_variants[:3]:
            logger.info(
                f"  {v['default_code']}: Size {v.get('ring_size', 'N/A')}, "
                f"Weight {v.get('calculated_metal_weight', 0):.4f}g, "
                f"Cost R${v.get('standard_price', 0):.2f}, "
                f"Price R${v.get('list_price', 0):.2f}"
            )

        # Summary
        logger.info(f"\n{'='*70}")
        logger.info("RECALCULATION SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Variants processed: {recalculated}/{len(variants)}")

        if errors:
            logger.warning(f"Errors: {len(errors)}")
        else:
            logger.info("✓ All variants recalculated successfully!")

        logger.info(f"\n{'='*70}")
        logger.info("Next steps:")
        logger.info("1. Run validate_cpl_pricing.py to verify calculations")
        logger.info("2. Check Odoo UI to verify prices are correct")
        logger.info(f"{'='*70}\n")

        return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(
        description='Force recalculation of variant prices'
    )

    parser.add_argument('--sku', required=True, help='Product SKU (e.g., C725R)')
    parser.add_argument('--url', default='http://localhost:8069', help='Odoo server URL')
    parser.add_argument('--db', default='odoo_master', help='Database name')
    parser.add_argument('--user', default='admin', help='Odoo username')
    parser.add_argument('--password', required=True, help='Odoo password')

    args = parser.parse_args()

    try:
        recalculator = VariantPriceRecalculator(
            args.url, args.db, args.user, args.password
        )

        success = recalculator.recalculate_variants(args.sku)

        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
