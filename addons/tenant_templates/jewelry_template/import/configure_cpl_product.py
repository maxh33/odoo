#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configure CPL Product for Size-Based Pricing

This script updates an existing product (e.g., C725R) with CPL supplier configuration:
- Base weight (grams)
- Production coefficient (COEF)
- Material type and purity
- Enable size-based pricing
- Configure jewelry pricing record

Usage:
    python3 configure_cpl_product.py --sku C725R --base-weight 7.0 --coef 1.15

Requirements:
    - Product must already exist in Odoo
    - Odoo XML-RPC connection configured
"""

import argparse
import logging
import sys
import xmlrpc.client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CPLProductConfigurator:
    """Configure CPL products for size-based pricing"""

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

        For products with variants, Odoo clears the template's default_code,
        so we search for a variant with matching SKU pattern instead.

        Args:
            sku: Product SKU (default_code)

        Returns:
            Product ID or None
        """
        # First try: search template directly (for products without variants)
        product_ids = self.execute(
            'product.template', 'search',
            [[('default_code', '=', sku)]],
            {'limit': 1}
        )

        if product_ids:
            logger.info(f"Found product template directly (ID: {product_ids[0]})")
            return product_ids[0]

        # Second try: search variants with SKU pattern (for products with variants)
        logger.info(f"Template not found by SKU '{sku}', searching variants...")
        variant_ids = self.execute(
            'product.product', 'search',
            [[('default_code', '=like', f'{sku}_%')]],
            {'limit': 1}
        )

        if not variant_ids:
            logger.error(f"Product with SKU '{sku}' not found (tried template and variant pattern)!")
            return None

        # Get the product template from the variant
        variants = self.execute(
            'product.product', 'read',
            [variant_ids],
            {'fields': ['product_tmpl_id', 'default_code']}
        )

        if not variants:
            return None

        template_id = variants[0]['product_tmpl_id'][0]
        logger.info(f"Found via variant '{variants[0]['default_code']}' (Template ID: {template_id})")

        return template_id

    def configure_product(self, sku, base_weight, coef, material='gold',
                         purity='24k', provider_indice=1.0, markup=200.0):
        """
        Configure product for CPL size-based pricing

        Args:
            sku: Product SKU
            base_weight: Base weight in grams (at size 20)
            coef: Production coefficient (e.g., 1.15)
            material: Material type ('gold' or 'silver')
            purity: Purity standard ('24k' or '950')
            provider_indice: Provider pricing factor (default 1.0)
            markup: Markup percentage (default 200.0)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Configuring Product: {sku}")
        logger.info(f"{'='*60}")

        # Find product
        product_id = self.find_product(sku)
        if not product_id:
            return False

        # Read current product data
        product = self.execute(
            'product.template', 'read',
            [product_id],
            {'fields': ['name', 'default_code', 'jewelry_pricing_id']}
        )[0]

        logger.info(f"Found product: {product['name']} (ID: {product_id})")

        # Update product template
        update_vals = {
            'is_jewelry': True,
            'material_type': material,
            'metal_purity': purity,
            'metal_weight_grams': base_weight,
            'has_size_based_pricing': True,
            'size_pricing_coef': coef,
        }

        logger.info(f"\nUpdating product template:")
        logger.info(f"  - Material: {material} {purity}")
        logger.info(f"  - Base Weight: {base_weight}g (at size 20)")
        logger.info(f"  - Production COEF: {coef}")
        logger.info(f"  - Size-Based Pricing: ENABLED")

        self.execute('product.template', 'write', [[product_id], update_vals])
        logger.info("✓ Product template updated")

        # Configure jewelry pricing
        pricing_id = product.get('jewelry_pricing_id')

        pricing_vals = {
            'provider_indice': provider_indice,
            'markup_percentage': markup,
        }

        if pricing_id:
            # Update existing pricing record
            pricing_id = pricing_id[0]  # Extract ID from tuple
            logger.info(f"\nUpdating jewelry pricing record (ID: {pricing_id}):")
            logger.info(f"  - Provider Index: {provider_indice}")
            logger.info(f"  - Markup: {markup}% (price = cost × {1 + markup/100})")

            self.execute('joiasmax.jewelry.pricing', 'write',
                        [[pricing_id], pricing_vals])
            logger.info("✓ Jewelry pricing updated")
        else:
            # Create new pricing record
            logger.info(f"\nCreating jewelry pricing record:")
            logger.info(f"  - Provider Index: {provider_indice}")
            logger.info(f"  - Markup: {markup}% (price = cost × {1 + markup/100})")

            pricing_vals['product_id'] = product_id
            pricing_id = self.execute('joiasmax.jewelry.pricing', 'create',
                                     [pricing_vals])

            # Link pricing to product
            self.execute('product.template', 'write',
                        [[product_id], {'jewelry_pricing_id': pricing_id}])
            logger.info(f"✓ Jewelry pricing created (ID: {pricing_id})")

        # Validation calculations
        logger.info(f"\n{'='*60}")
        logger.info("VALIDATION CALCULATIONS")
        logger.info(f"{'='*60}")

        # Size 20 (reference)
        weight_20 = base_weight * coef * 1.0000
        logger.info(f"\nSize 20 (Reference):")
        logger.info(f"  Weight = {base_weight}g × {coef} × 1.0000 = {weight_20:.4f}g")

        # Size 13 (from MD file example)
        weight_13 = base_weight * coef * 0.8833
        logger.info(f"\nSize 13 (CPL Index):")
        logger.info(f"  Weight = {base_weight}g × {coef} × 0.8833 = {weight_13:.6f}g")

        # Example cost calculation (assuming R$700/g gold price)
        gold_price = 700.0
        cost_20 = weight_20 * gold_price * provider_indice
        price_20 = cost_20 * (1 + markup/100)

        logger.info(f"\nExample Pricing @ R${gold_price}/g gold:")
        logger.info(f"  Size 20: Cost = R${cost_20:.2f}, Price = R${price_20:.2f}")

        cost_13 = weight_13 * gold_price * provider_indice
        price_13 = cost_13 * (1 + markup/100)
        logger.info(f"  Size 13: Cost = R${cost_13:.2f}, Price = R${price_13:.2f}")

        logger.info(f"\n{'='*60}")
        logger.info("✓ CONFIGURATION COMPLETE")
        logger.info(f"{'='*60}\n")

        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Configure CPL product for size-based pricing'
    )

    # Product configuration
    parser.add_argument('--sku', required=True, help='Product SKU (e.g., C725R)')
    parser.add_argument('--base-weight', type=float, required=True,
                       help='Base weight in grams at size 20')
    parser.add_argument('--coef', type=float, required=True,
                       help='Production coefficient (e.g., 1.15)')

    # Optional parameters
    parser.add_argument('--material', default='gold',
                       choices=['gold', 'silver'],
                       help='Material type (default: gold)')
    parser.add_argument('--purity', default='24k',
                       choices=['24k', '950'],
                       help='Purity standard (default: 24k)')
    parser.add_argument('--provider-indice', type=float, default=1.0,
                       help='Provider pricing factor (default: 1.0)')
    parser.add_argument('--markup', type=float, default=200.0,
                       help='Markup percentage (default: 200.0)')

    # Odoo connection
    parser.add_argument('--url', default='http://localhost:8069',
                       help='Odoo server URL')
    parser.add_argument('--db', default='odoo_master',
                       help='Database name')
    parser.add_argument('--user', default='admin',
                       help='Odoo username')
    parser.add_argument('--password', required=True,
                       help='Odoo password')

    args = parser.parse_args()

    try:
        # Initialize configurator
        configurator = CPLProductConfigurator(
            args.url, args.db, args.user, args.password
        )

        # Configure product
        success = configurator.configure_product(
            sku=args.sku,
            base_weight=args.base_weight,
            coef=args.coef,
            material=args.material,
            purity=args.purity,
            provider_indice=args.provider_indice,
            markup=args.markup
        )

        if success:
            logger.info("Next steps:")
            logger.info("1. Run create_cpl_variants.py to create 45 size variants")
            logger.info("2. Run validate_cpl_pricing.py to verify calculations")
            logger.info("3. Check Odoo UI: Sales > Products > Search for SKU")
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
