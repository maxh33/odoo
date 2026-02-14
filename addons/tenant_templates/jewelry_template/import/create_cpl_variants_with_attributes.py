#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create CPL Size Variants Using Odoo Product Attributes

This script uses Odoo's built-in product attribute system to create variants.
This properly handles the combination_indices constraint.

Creates 41 ring size variants (sizes 6-46) - practical business range.

Usage:
    python3 create_cpl_variants_with_attributes.py --sku C725R --db tenant_joiasmax --password admin
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


class CPLVariantCreatorWithAttributes:
    """Create size variants using Odoo's product attribute system"""

    SIZE_RANGE = range(6, 47)  # Sizes 6-46 (41 variants) - practical business range

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

    def find_or_create_ring_size_attribute(self):
        """Find or create Ring Size product attribute"""
        logger.info("\n" + "="*70)
        logger.info("Setting up Ring Size Attribute")
        logger.info("="*70)

        # Search for existing attribute
        attr_ids = self.execute(
            'product.attribute', 'search',
            [[('name', '=', 'Ring Size')]],
            {'limit': 1}
        )

        if attr_ids:
            attr_id = attr_ids[0]
            logger.info(f"✓ Ring Size attribute already exists (ID: {attr_id})")
            return attr_id

        # Create new attribute
        attr_id = self.execute(
            'product.attribute', 'create',
            [{
                'name': 'Ring Size',
                'display_type': 'select',
                'create_variant': 'always',
            }]
        )

        logger.info(f"✓ Created Ring Size attribute (ID: {attr_id})")
        return attr_id

    def create_attribute_values(self, attribute_id):
        """Create attribute values for sizes 6-50"""
        logger.info("\nCreating size attribute values...")

        # Check existing values
        existing_value_ids = self.execute(
            'product.attribute.value', 'search',
            [[('attribute_id', '=', attribute_id)]]
        )

        if existing_value_ids:
            existing_values = self.execute(
                'product.attribute.value', 'read',
                [existing_value_ids],
                {'fields': ['name']}
            )
            existing_names = {v['name'] for v in existing_values}
            logger.info(f"Found {len(existing_names)} existing values")
        else:
            existing_names = set()

        # Create missing values
        created = 0
        value_ids = []

        for size in self.SIZE_RANGE:
            size_name = str(size)

            if size_name in existing_names:
                # Find existing
                value_id = self.execute(
                    'product.attribute.value', 'search',
                    [[('attribute_id', '=', attribute_id), ('name', '=', size_name)]],
                    {'limit': 1}
                )[0]
                value_ids.append(value_id)
                continue

            # Create new value
            value_id = self.execute(
                'product.attribute.value', 'create',
                [{
                    'name': size_name,
                    'attribute_id': attribute_id,
                }]
            )
            value_ids.append(value_id)
            created += 1

        logger.info(f"✓ Created {created} new attribute values")
        logger.info(f"✓ Total: {len(value_ids)} size values (6-46)")

        return value_ids

    def configure_product_with_attribute(self, sku, attribute_id, value_ids):
        """Configure product template with Ring Size attribute"""
        logger.info("\n" + "="*70)
        logger.info(f"Configuring Product: {sku}")
        logger.info("="*70)

        # Find product
        product_ids = self.execute(
            'product.template', 'search',
            [[('default_code', '=', sku)]],
            {'limit': 1}
        )

        if not product_ids:
            logger.error(f"Product '{sku}' not found!")
            return False

        product_id = product_ids[0]
        product = self.execute(
            'product.template', 'read',
            [product_id],
            {'fields': ['name', 'attribute_line_ids']}
        )[0]

        logger.info(f"Product: {product['name']} (ID: {product_id})")

        # DO NOT delete variants manually - Odoo will handle this automatically
        # when we update the attribute line values

        # Search for existing Ring Size attribute line directly
        # This is more reliable than reading from product.attribute_line_ids
        existing_line_ids = self.execute(
            'product.template.attribute.line', 'search',
            [[('product_tmpl_id', '=', product_id), ('attribute_id', '=', attribute_id)]],
            {'limit': 1}
        )

        ring_size_line_id = None
        if existing_line_ids:
            ring_size_line_id = existing_line_ids[0]
            logger.info(f"\nFound existing Ring Size attribute line (ID: {ring_size_line_id})")

        if ring_size_line_id:
            # Update existing line with all values
            logger.info(f"Updating Ring Size attribute with {len(value_ids)} values...")

            self.execute(
                'product.template.attribute.line', 'write',
                [[ring_size_line_id], {
                    'value_ids': [(6, 0, value_ids)],  # Replace all values
                }]
            )

            logger.info(f"✓ Attribute line updated (ID: {ring_size_line_id})")
            attribute_line_id = ring_size_line_id
        else:
            # Create new attribute line with all size values
            logger.info(f"\nAdding Ring Size attribute with {len(value_ids)} values...")

            attribute_line_id = self.execute(
                'product.template.attribute.line', 'create',
                [{
                    'product_tmpl_id': product_id,
                    'attribute_id': attribute_id,
                    'value_ids': [(6, 0, value_ids)],  # Set all values
                }]
            )

            logger.info(f"✓ Attribute line created (ID: {attribute_line_id})")

        # Odoo will automatically create variants
        # Wait a moment and check
        import time
        time.sleep(2)

        # Verify variants were created
        variant_ids = self.execute(
            'product.product', 'search',
            [[('product_tmpl_id', '=', product_id)]]
        )

        logger.info(f"\n✓ Odoo created {len(variant_ids)} variants automatically!")

        # Now update each variant with ring_size field
        return self.update_variants_with_ring_size(product_id, sku)

    def update_variants_with_ring_size(self, product_id, base_sku):
        """Update variants with ring_size field and custom SKUs"""
        logger.info("\n" + "="*70)
        logger.info("Updating Variants with Ring Size Data")
        logger.info("="*70)

        # Get all variants
        variant_ids = self.execute(
            'product.product', 'search',
            [[('product_tmpl_id', '=', product_id)]]
        )

        variants = self.execute(
            'product.product', 'read',
            [variant_ids],
            {'fields': ['id', 'product_template_attribute_value_ids', 'default_code']}
        )

        updated = 0
        for variant in variants:
            # Get attribute value name (the size)
            if not variant.get('product_template_attribute_value_ids'):
                continue

            ptav_ids = variant['product_template_attribute_value_ids']

            # Read attribute value
            ptav = self.execute(
                'product.template.attribute.value', 'read',
                [ptav_ids],
                {'fields': ['name', 'product_attribute_value_id']}
            )

            if not ptav:
                continue

            # Get the size number from attribute value name
            size_name = ptav[0]['name']

            try:
                size_number = int(size_name)
            except ValueError:
                logger.warning(f"Could not parse size from: {size_name}")
                continue

            # Update variant
            variant_sku = f"{base_sku}_{size_number}"

            self.execute(
                'product.product', 'write',
                [[variant['id']], {
                    'default_code': variant_sku,
                    'ring_size': size_number,
                    'barcode': f"{base_sku}{size_number:02d}",
                }]
            )

            logger.info(f"  ✓ Size {size_number}: SKU={variant_sku}, ID={variant['id']}")
            updated += 1

        logger.info(f"\n✓ Updated {updated} variants with ring_size and SKUs")

        return True

    def create_variants(self, sku):
        """Main method to create variants"""
        try:
            # Step 1: Create/find Ring Size attribute
            attribute_id = self.find_or_create_ring_size_attribute()

            # Step 2: Create attribute values (sizes 6-50)
            value_ids = self.create_attribute_values(attribute_id)

            # Step 3: Configure product and create variants
            success = self.configure_product_with_attribute(sku, attribute_id, value_ids)

            if success:
                logger.info("\n" + "="*70)
                logger.info("✓ VARIANT CREATION COMPLETE")
                logger.info("="*70)
                logger.info("\nNext steps:")
                logger.info("1. Run validate_cpl_pricing.py to verify calculations")
                logger.info("2. Check Odoo UI: Sales > Products > Search for SKU")
                logger.info("3. Verify all 41 variants show correctly (sizes 6-46)")

            return success

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Create CPL size variants using product attributes'
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
        creator = CPLVariantCreatorWithAttributes(
            args.url, args.db, args.user, args.password
        )

        success = creator.create_variants(args.sku)

        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
