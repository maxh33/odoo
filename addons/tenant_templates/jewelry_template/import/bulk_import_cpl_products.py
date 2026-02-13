#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bulk Import CPL Products with Size-Based Pricing

This script processes multiple CPL products from a CSV file and:
1. Configures each product for size-based pricing
2. Creates 41 size variants per product
3. Validates all calculations

CSV Format:
SKU,Name,Base Weight (g),COEF,Material,Purity,Provider Index,Markup
C725R,Wedding Ring C725R,7.0,1.15,gold,24k,1.0,200.0
C790RZ,Wedding Ring C790RZ,7.0,1.10,gold,24k,1.0,200.0

Usage:
    python3 bulk_import_cpl_products.py --csv cpl_products.csv --db tenant_joiasmax --password admin
    python3 bulk_import_cpl_products.py --csv cpl_products.csv --db tenant_joiasmax --password admin --dry-run
"""

import argparse
import os
import csv
import logging
import sys
import time
import xmlrpc.client
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BulkCPLImporter:
    """Bulk import CPL products with size-based pricing"""

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
        """Find product template by SKU"""
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

    def configure_product(self, sku, base_weight, coef, material='gold',
                         purity='24k', provider_indice=1.0, markup=200.0):
        """Configure product for CPL size-based pricing"""
        product_id = self.find_product(sku)
        if not product_id:
            logger.error(f"Product '{sku}' not found!")
            return False

        try:
            # Update product template
            update_vals = {
                'is_jewelry': True,
                'material_type': material,
                'metal_purity': purity,
                'metal_weight_grams': base_weight,
                'has_size_based_pricing': True,
                'size_pricing_coef': coef,
            }

            self.execute('product.template', 'write', [[product_id], update_vals])

            # Read product to get jewelry pricing
            product = self.execute(
                'product.template', 'read',
                [product_id],
                {'fields': ['jewelry_pricing_id']}
            )[0]

            pricing_vals = {
                'provider_indice': provider_indice,
                'markup_percentage': markup,
            }

            pricing_id = product.get('jewelry_pricing_id')
            if pricing_id:
                self.execute('joiasmax.jewelry.pricing', 'write',
                            [[pricing_id[0]], pricing_vals])
            else:
                pricing_vals['product_id'] = product_id
                pricing_id = self.execute('joiasmax.jewelry.pricing', 'create',
                                         [pricing_vals])
                self.execute('product.template', 'write',
                            [[product_id], {'jewelry_pricing_id': pricing_id}])

            logger.info(f"  ✓ Configuration: OK")
            return True

        except Exception as e:
            logger.error(f"  ❌ Configuration failed: {e}")
            return False

    def create_variants(self, sku):
        """Create 41 size variants using Odoo attributes"""
        try:
            # Get or create Ring Size attribute
            attr_ids = self.execute(
                'product.attribute', 'search',
                [[('name', '=', 'Ring Size')]],
                {'limit': 1}
            )

            if not attr_ids:
                logger.error(f"  ❌ Ring Size attribute not found!")
                return False

            attribute_id = attr_ids[0]

            # Get size values (6-46)
            value_ids = self.execute(
                'product.attribute.value', 'search',
                [[('attribute_id', '=', attribute_id)]]
            )

            if len(value_ids) < 41:
                logger.error(f"  ❌ Not enough size values (found {len(value_ids)}, need 41)")
                return False

            # Filter to sizes 6-46
            all_values = self.execute(
                'product.attribute.value', 'read',
                [value_ids],
                {'fields': ['name', 'id']}
            )

            size_values = [v for v in all_values if v['name'].isdigit() and 6 <= int(v['name']) <= 46]
            if len(size_values) < 41:
                logger.error(f"  ❌ Not enough size values in range 6-46")
                return False

            size_value_ids = [v['id'] for v in sorted(size_values, key=lambda x: int(x['name']))]

            # Get product
            product_id = self.find_product(sku)
            if not product_id:
                logger.error(f"  ❌ Product not found!")
                return False

            # Check for existing attribute line
            existing_line_ids = self.execute(
                'product.template.attribute.line', 'search',
                [[('product_tmpl_id', '=', product_id), ('attribute_id', '=', attribute_id)]],
                {'limit': 1}
            )

            if existing_line_ids:
                # Update existing line
                self.execute(
                    'product.template.attribute.line', 'write',
                    [[existing_line_ids[0]], {'value_ids': [(6, 0, size_value_ids)]}]
                )
            else:
                # Create new line
                self.execute(
                    'product.template.attribute.line', 'create',
                    [{
                        'product_tmpl_id': product_id,
                        'attribute_id': attribute_id,
                        'value_ids': [(6, 0, size_value_ids)],
                    }]
                )

            # Wait for Odoo to create variants
            time.sleep(2)

            # Verify variants created
            variant_ids = self.execute(
                'product.product', 'search',
                [[('product_tmpl_id', '=', product_id)]]
            )

            if len(variant_ids) != 41:
                logger.warning(f"  ⚠️  Created {len(variant_ids)} variants (expected 41)")

            # Update variant SKUs and ring_size
            variants = self.execute(
                'product.product', 'read',
                [variant_ids],
                {'fields': ['id', 'product_template_attribute_value_ids']}
            )

            updated = 0
            for variant in variants:
                ptav_ids = variant.get('product_template_attribute_value_ids', [])
                if not ptav_ids:
                    continue

                ptav = self.execute(
                    'product.template.attribute.value', 'read',
                    [ptav_ids],
                    {'fields': ['name']}
                )

                if not ptav:
                    continue

                size_name = ptav[0]['name']
                if not size_name.isdigit():
                    continue

                size_number = int(size_name)
                variant_sku = f"{sku}_{size_number}"

                self.execute(
                    'product.product', 'write',
                    [[variant['id']], {
                        'default_code': variant_sku,
                        'ring_size': size_number,
                    }]
                )
                updated += 1

            logger.info(f"  ✓ Variants: {updated} created and configured")
            return updated == 41

        except Exception as e:
            logger.error(f"  ❌ Variant creation failed: {e}")
            return False

    def validate_product(self, sku):
        """Quick validation of product pricing"""
        try:
            product_id = self.find_product(sku)
            if not product_id:
                return False

            # Get variants
            variant_ids = self.execute(
                'product.product', 'search',
                [[('product_tmpl_id', '=', product_id)]]
            )

            if len(variant_ids) != 41:
                logger.error(f"  ❌ Validation: Expected 41 variants, found {len(variant_ids)}")
                return False

            # Sample check: size 20
            variants = self.execute(
                'product.product', 'read',
                [variant_ids],
                {'fields': ['ring_size', 'calculated_metal_weight', 'standard_price']}
            )

            size_20 = next((v for v in variants if v.get('ring_size') == 20), None)
            if not size_20:
                logger.error(f"  ❌ Validation: Size 20 variant not found")
                return False

            weight = size_20.get('calculated_metal_weight', 0)
            cost = size_20.get('standard_price', 0)

            if weight == 0:
                logger.error(f"  ❌ Validation: Weight not calculated")
                return False

            if cost == 0:
                logger.error(f"  ❌ Validation: Cost not calculated")
                return False

            logger.info(f"  ✓ Validation: PASSED (Size 20: {weight:.4f}g, R${cost:.2f})")
            return True

        except Exception as e:
            logger.error(f"  ❌ Validation failed: {e}")
            return False

    def process_product(self, row, dry_run=False):
        """Process a single product from CSV row"""
        sku = row['SKU'].strip()
        name = row.get('Name', sku).strip()
        base_weight = float(row['Base Weight (g)'])
        coef = float(row['COEF'])
        material = row.get('Material', 'gold').strip().lower()
        purity = row.get('Purity', '24k').strip()
        provider_indice = float(row.get('Provider Index', 1.0))
        markup = float(row.get('Markup', 200.0))

        logger.info(f"\nProcessing: {sku} ({name})")
        logger.info(f"  Base Weight: {base_weight}g, COEF: {coef}")

        if dry_run:
            logger.info(f"  [DRY RUN] Would configure and create 41 variants")
            return True

        # Step 1: Configure
        if not self.configure_product(sku, base_weight, coef, material, purity,
                                      provider_indice, markup):
            return False

        # Step 2: Create variants
        if not self.create_variants(sku):
            return False

        # Step 3: Validate
        if not self.validate_product(sku):
            return False

        return True

    def import_from_csv(self, csv_file, dry_run=False):
        """Import all products from CSV file"""
        if not Path(csv_file).exists():
            logger.error(f"CSV file not found: {csv_file}")
            return False

        logger.info(f"\n{'='*70}")
        logger.info(f"BULK CPL PRODUCT IMPORT")
        logger.info(f"{'='*70}")
        logger.info(f"CSV File: {csv_file}")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE IMPORT'}")
        logger.info(f"{'='*70}\n")

        results = {
            'success': [],
            'failed': [],
            'total': 0
        }

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                results['total'] += 1
                sku = row['SKU'].strip()

                try:
                    if self.process_product(row, dry_run):
                        results['success'].append(sku)
                    else:
                        results['failed'].append(sku)
                except Exception as e:
                    logger.error(f"  ❌ Error processing {sku}: {e}")
                    results['failed'].append(sku)

        # Summary
        logger.info(f"\n{'='*70}")
        logger.info("IMPORT SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Total products: {results['total']}")
        logger.info(f"✓ Successful: {len(results['success'])}")
        logger.info(f"❌ Failed: {len(results['failed'])}")

        if results['success']:
            logger.info(f"\nSuccessful imports:")
            for sku in results['success']:
                logger.info(f"  ✓ {sku}")

        if results['failed']:
            logger.info(f"\nFailed imports:")
            for sku in results['failed']:
                logger.info(f"  ❌ {sku}")

        logger.info(f"{'='*70}\n")

        return len(results['failed']) == 0


def main():
    parser = argparse.ArgumentParser(
        description='Bulk import CPL products with size-based pricing'
    )

    parser.add_argument('--csv', required=True, help='CSV file path')
    parser.add_argument('--url', default='http://localhost:8069', help='Odoo server URL')
    parser.add_argument('--db', default='odoo_master', help='Database name')
    parser.add_argument('--user', default='admin', help='Odoo username')
    parser.add_argument('--password', default=os.environ.get('ODOO_PASSWORD'),
                       help='Odoo password (or set ODOO_PASSWORD env var)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no actual changes)')

    args = parser.parse_args()
    if not args.password:
        parser.error("--password is required (or set ODOO_PASSWORD environment variable)")

    try:
        importer = BulkCPLImporter(args.url, args.db, args.user, args.password)
        success = importer.import_from_csv(args.csv, args.dry_run)
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
