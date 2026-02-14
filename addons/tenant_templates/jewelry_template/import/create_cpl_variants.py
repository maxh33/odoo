#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create CPL Size Variants for Ring Products

This script creates 45 size variants (sizes 6-50) for CPL supplier ring products.
Each variant will have:
- Unique SKU: {BASE_SKU}-{SIZE}
- ring_size field populated
- Auto-calculated weight (base_weight × COEF × size_adjustment_factor)
- Auto-calculated cost and price

Usage:
    python3 create_cpl_variants.py --sku C725R --dry-run
    python3 create_cpl_variants.py --sku C725R

Requirements:
    - Product must be configured with has_size_based_pricing=True
    - CPL size adjustment table must be loaded (sizes 6-50)
    - Odoo XML-RPC connection configured
"""

import argparse
import os
import logging
import sys
import time
import xmlrpc.client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CPLVariantCreator:
    """Create size variants for CPL ring products"""

    # CPL size range: 6-50 (45 sizes)
    SIZE_RANGE = range(6, 51)

    def __init__(self, url, db, username, password):
        """
        Initialize Odoo connection

        Args:
            url: Odoo server URL (e.g., http://localhost:8069)
            db: Database name
            username: Odoo user
            password: Odoo password
        """
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
        """
        Find product template by SKU

        Args:
            sku: Product SKU (default_code)

        Returns:
            Product dict or None
        """
        product_ids = self.execute(
            'product.template', 'search',
            [[('default_code', '=', sku)]],
            {'limit': 1}
        )

        if not product_ids:
            logger.error(f"Product with SKU '{sku}' not found!")
            return None

        # Read product data
        products = self.execute(
            'product.template', 'read',
            product_ids,
            {'fields': [
                'id', 'name', 'default_code',
                'has_size_based_pricing', 'size_pricing_coef',
                'metal_weight_grams', 'material_type', 'metal_purity'
            ]}
        )

        return products[0] if products else None

    def get_existing_variants(self, product_id):
        """
        Get existing variants for product

        Args:
            product_id: Product template ID

        Returns:
            List of variant dicts
        """
        variant_ids = self.execute(
            'product.product', 'search',
            [[('product_tmpl_id', '=', product_id)]]
        )

        if not variant_ids:
            return []

        variants = self.execute(
            'product.product', 'read',
            variant_ids,
            {'fields': ['default_code', 'ring_size', 'calculated_metal_weight']}
        )

        return variants

    def verify_size_table(self):
        """
        Verify CPL size adjustment table exists

        Returns:
            Number of size records found
        """
        size_ids = self.execute(
            'joiasmax.size.weight.adjustment', 'search',
            [[('size_number', '>=', 6), ('size_number', '<=', 50)]]
        )

        return len(size_ids)

    def create_variants(self, sku, dry_run=False):
        """
        Create 45 size variants for CPL product

        Args:
            sku: Product SKU
            dry_run: If True, only validate without creating

        Returns:
            Number of variants created
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Creating CPL Size Variants for: {sku}")
        logger.info(f"{'='*70}")

        # Find product
        product = self.find_product(sku)
        if not product:
            return 0

        product_id = product['id']
        logger.info(f"\nProduct: {product['name']} (ID: {product_id})")

        # Validate size-based pricing is enabled
        if not product.get('has_size_based_pricing'):
            logger.error("❌ Size-based pricing NOT enabled!")
            logger.error("   Run configure_cpl_product.py first.")
            return 0

        logger.info(f"✓ Size-based pricing: ENABLED")
        logger.info(f"  - Base Weight: {product.get('metal_weight_grams', 0)}g")
        logger.info(f"  - COEF: {product.get('size_pricing_coef', 1.0)}")
        logger.info(f"  - Material: {product.get('material_type')} {product.get('metal_purity')}")

        # Verify CPL size table
        size_count = self.verify_size_table()
        if size_count < 45:
            logger.error(f"❌ CPL size table incomplete! Found {size_count}/45 sizes")
            logger.error("   Load size_weight_adjustments.xml first.")
            return 0

        logger.info(f"✓ CPL size table: {size_count}/45 sizes loaded")

        # Check existing variants
        existing_variants = self.get_existing_variants(product_id)
        existing_sizes = {v.get('ring_size') for v in existing_variants if v.get('ring_size')}

        logger.info(f"\nExisting variants: {len(existing_variants)}")
        if existing_sizes:
            logger.info(f"  Sizes already created: {sorted(existing_sizes)}")

        # Determine sizes to create
        sizes_to_create = [s for s in self.SIZE_RANGE if s not in existing_sizes]

        if not sizes_to_create:
            logger.info("✓ All 45 variants already exist!")
            return 0

        logger.info(f"\n{'='*70}")
        logger.info(f"Variants to create: {len(sizes_to_create)} sizes")
        logger.info(f"Sizes: {sizes_to_create}")
        logger.info(f"{'='*70}")

        if dry_run:
            logger.info("\n⚠️  DRY RUN MODE - No variants will be created")
            logger.info("Remove --dry-run flag to create variants")
            return 0

        # Create variants
        created_count = 0
        errors = []

        for size in sizes_to_create:
            try:
                variant_sku = f"{sku}-{size}"
                barcode = f"{sku}{size:02d}"

                logger.info(f"\nCreating variant: {variant_sku} (Size {size})")

                variant_vals = {
                    'product_tmpl_id': product_id,
                    'default_code': variant_sku,
                    'ring_size': size,
                    'barcode': barcode,
                }

                variant_id = self.execute(
                    'product.product', 'create',
                    [variant_vals]
                )

                # Read back calculated values
                variant = self.execute(
                    'product.product', 'read',
                    [variant_id],
                    {'fields': [
                        'default_code', 'ring_size',
                        'calculated_metal_weight', 'standard_price'
                    ]}
                )[0]

                weight = variant.get('calculated_metal_weight', 0)
                cost = variant.get('standard_price', 0)

                logger.info(f"  ✓ Created ID: {variant_id}")
                logger.info(f"    - SKU: {variant_sku}")
                logger.info(f"    - Barcode: {barcode}")
                logger.info(f"    - Calculated Weight: {weight:.4f}g")
                logger.info(f"    - Cost: R${cost:.2f}")

                created_count += 1

                # Small delay to avoid overwhelming server
                time.sleep(0.1)

            except Exception as e:
                error_msg = f"Size {size}: {str(e)}"
                logger.error(f"  ❌ Error: {error_msg}")
                errors.append(error_msg)

        # Summary
        logger.info(f"\n{'='*70}")
        logger.info("VARIANT CREATION SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Variants created: {created_count}/{len(sizes_to_create)}")

        if errors:
            logger.warning(f"Errors: {len(errors)}")
            for error in errors:
                logger.warning(f"  - {error}")
        else:
            logger.info("✓ All variants created successfully!")

        # Verify final count
        all_variants = self.get_existing_variants(product_id)
        all_sizes = [v.get('ring_size') for v in all_variants if v.get('ring_size')]

        logger.info(f"\nTotal variants: {len(all_variants)}")
        logger.info(f"Variants with ring_size: {len(all_sizes)}/45")

        if len(all_sizes) == 45:
            logger.info("✓ COMPLETE: All 45 size variants created!")
        else:
            missing = set(self.SIZE_RANGE) - set(all_sizes)
            logger.warning(f"Missing sizes: {sorted(missing)}")

        logger.info(f"\n{'='*70}\n")

        return created_count


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Create CPL size variants (6-50) for ring products'
    )

    # Product selection
    parser.add_argument('--sku', required=True,
                       help='Product SKU (e.g., C725R)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Validate without creating variants')

    # Odoo connection
    parser.add_argument('--url', default='http://localhost:8069',
                       help='Odoo server URL')
    parser.add_argument('--db', default='odoo_master',
                       help='Database name')
    parser.add_argument('--user', default='admin',
                       help='Odoo username')
    parser.add_argument('--password', default=os.environ.get('ODOO_PASSWORD'),
                       help='Odoo password (or set ODOO_PASSWORD env var)')

    args = parser.parse_args()
    if not args.password:
        parser.error("--password is required (or set ODOO_PASSWORD environment variable)")

    try:
        # Initialize creator
        creator = CPLVariantCreator(
            args.url, args.db, args.user, args.password
        )

        # Create variants
        created = creator.create_variants(args.sku, dry_run=args.dry_run)

        if created > 0:
            logger.info("Next steps:")
            logger.info("1. Run validate_cpl_pricing.py to verify calculations")
            logger.info("2. Check Odoo UI: Sales > Products > Search for SKU")
            logger.info("3. Open product > Variants tab > Verify all 45 sizes")
            sys.exit(0)
        elif args.dry_run:
            logger.info("Dry run completed. Remove --dry-run to create variants.")
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
