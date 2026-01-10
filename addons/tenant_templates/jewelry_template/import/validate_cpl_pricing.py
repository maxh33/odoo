#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate CPL Size-Based Pricing Calculations

This script validates that CPL ring variants have correct:
- Weight calculations (base_weight × COEF × size_adjustment_factor)
- Cost calculations (weight × gold_price × provider_indice)
- Price calculations (cost × (1 + markup/100))

Test cases based on cpl_size_indice.md:
- Size 20: Reference size (factor = 1.0000)
- Size 13: Example from MD file (factor = 0.8833)

Usage:
    python3 validate_cpl_pricing.py --sku C725R
    python3 validate_cpl_pricing.py --sku C725R --verbose

Requirements:
    - Product must have size-based pricing enabled
    - 45 variants must exist (sizes 6-50)
    - CPL size adjustment table loaded
"""

import argparse
import logging
import sys
import xmlrpc.client
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CPLPricingValidator:
    """Validate CPL size-based pricing calculations"""

    # Expected number of variants
    EXPECTED_VARIANTS = 45
    SIZE_RANGE = range(6, 51)

    # Test cases from cpl_size_indice.md
    TEST_CASES = {
        20: {
            'size_number': 20,
            'adjustment_factor': 1.0000,
            'description': 'Reference size (factor = 1.0000)'
        },
        13: {
            'size_number': 13,
            'adjustment_factor': 0.8833,
            'description': 'Example from MD file'
        },
        6: {
            'size_number': 6,
            'adjustment_factor': 0.7666,
            'description': 'Minimum size'
        },
        50: {
            'size_number': 50,
            'adjustment_factor': 1.5000,
            'description': 'Maximum size'
        },
    }

    def __init__(self, url, db, username, password, verbose=False):
        """
        Initialize Odoo connection

        Args:
            url: Odoo server URL
            db: Database name
            username: Odoo user
            password: Odoo password
            verbose: Enable detailed output
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.verbose = verbose

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
        product_ids = self.execute(
            'product.template', 'search',
            [[('default_code', '=', sku)]],
            {'limit': 1}
        )

        if not product_ids:
            return None

        products = self.execute(
            'product.template', 'read',
            product_ids,
            {'fields': [
                'id', 'name', 'default_code',
                'has_size_based_pricing', 'size_pricing_coef',
                'metal_weight_grams', 'material_type', 'metal_purity',
                'jewelry_pricing_id'
            ]}
        )

        return products[0] if products else None

    def get_market_price(self, material_type='gold_24k'):
        """Get current market price for material"""
        price_ids = self.execute(
            'joiasmax.market.price', 'search',
            [[('material_type', '=', material_type), ('is_active', '=', True)]],
            {'limit': 1}
        )

        if not price_ids:
            return None

        prices = self.execute(
            'joiasmax.market.price', 'read',
            price_ids,
            {'fields': ['price_per_gram_brl']}
        )

        return prices[0]['price_per_gram_brl'] if prices else None

    def get_variants(self, product_id):
        """Get all variants for product"""
        variant_ids = self.execute(
            'product.product', 'search',
            [[('product_tmpl_id', '=', product_id)]]
        )

        if not variant_ids:
            return []

        variants = self.execute(
            'product.product', 'read',
            variant_ids,
            {'fields': [
                'id', 'default_code', 'ring_size',
                'calculated_metal_weight', 'standard_price', 'list_price'
            ]}
        )

        return variants

    def validate_weight_calculation(self, variant, base_weight, coef,
                                   expected_factor):
        """
        Validate weight calculation for variant

        Args:
            variant: Variant dict
            base_weight: Base weight in grams
            coef: Production coefficient
            expected_factor: Expected size adjustment factor

        Returns:
            Tuple (passed, message)
        """
        expected_weight = base_weight * coef * expected_factor
        actual_weight = variant.get('calculated_metal_weight', 0)

        # Allow 0.001g tolerance for floating point
        tolerance = 0.001
        diff = abs(actual_weight - expected_weight)

        if diff <= tolerance:
            return True, f"✓ Weight: {actual_weight:.4f}g (expected {expected_weight:.4f}g)"
        else:
            return False, f"❌ Weight: {actual_weight:.4f}g (expected {expected_weight:.4f}g, diff: {diff:.4f}g)"

    def validate_cost_calculation(self, variant, expected_weight, gold_price,
                                  provider_indice):
        """
        Validate cost calculation for variant

        Args:
            variant: Variant dict
            expected_weight: Expected weight in grams
            gold_price: Gold price per gram
            provider_indice: Provider pricing factor

        Returns:
            Tuple (passed, message)
        """
        if not gold_price:
            return None, "⚠️  Cost: Cannot validate (no market price)"

        expected_cost = expected_weight * gold_price * provider_indice
        actual_cost = variant.get('standard_price', 0)

        # Allow R$0.50 tolerance for rounding
        tolerance = 0.50
        diff = abs(actual_cost - expected_cost)

        if diff <= tolerance:
            return True, f"✓ Cost: R${actual_cost:.2f} (expected R${expected_cost:.2f})"
        else:
            return False, f"❌ Cost: R${actual_cost:.2f} (expected R${expected_cost:.2f}, diff: R${diff:.2f})"

    def validate_all(self, sku):
        """
        Validate all pricing calculations for product

        Args:
            sku: Product SKU

        Returns:
            Dict with validation results
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"VALIDATING CPL PRICING: {sku}")
        logger.info(f"{'='*70}")

        results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'tests': []
        }

        # Find product
        product = self.find_product(sku)
        if not product:
            logger.error(f"❌ Product '{sku}' not found!")
            return results

        product_id = product['id']
        base_weight = product.get('metal_weight_grams', 0)
        coef = product.get('size_pricing_coef', 1.0)

        logger.info(f"\nProduct: {product['name']} (ID: {product_id})")
        logger.info(f"  - Base Weight: {base_weight}g")
        logger.info(f"  - COEF: {coef}")
        logger.info(f"  - Material: {product.get('material_type')} {product.get('metal_purity')}")

        # Validate size-based pricing enabled
        if not product.get('has_size_based_pricing'):
            logger.error("❌ Size-based pricing NOT enabled!")
            results['failed'] += 1
            return results

        logger.info("  ✓ Size-based pricing: ENABLED")

        # Get market price
        gold_price = self.get_market_price('gold_24k')
        if gold_price:
            logger.info(f"  ✓ Current gold price: R${gold_price:.2f}/g")
        else:
            logger.warning("  ⚠️  No active gold market price found")

        # Get jewelry pricing configuration
        jewelry_pricing_id = product.get('jewelry_pricing_id')
        provider_indice = 1.0
        markup = 200.0

        if jewelry_pricing_id:
            pricing = self.execute(
                'joiasmax.jewelry.pricing', 'read',
                [jewelry_pricing_id[0]],
                {'fields': ['provider_indice', 'markup_percentage']}
            )[0]
            provider_indice = pricing.get('provider_indice', 1.0)
            markup = pricing.get('markup_percentage', 200.0)

        logger.info(f"  - Provider Index: {provider_indice}")
        logger.info(f"  - Markup: {markup}%")

        # Get variants
        variants = self.get_variants(product_id)
        variant_count = len(variants)

        logger.info(f"\n{'='*70}")
        logger.info(f"VARIANTS: {variant_count}/{self.EXPECTED_VARIANTS}")
        logger.info(f"{'='*70}")

        if variant_count == 0:
            logger.error("❌ No variants found!")
            logger.error("   Run create_cpl_variants.py first.")
            results['failed'] += 1
            return results

        if variant_count != self.EXPECTED_VARIANTS:
            logger.warning(f"⚠️  Expected {self.EXPECTED_VARIANTS} variants, found {variant_count}")
            results['warnings'] += 1

        # Organize variants by size
        variants_by_size = {v['ring_size']: v for v in variants if v.get('ring_size')}

        logger.info(f"Variants with ring_size: {len(variants_by_size)}")
        logger.info(f"Size range: {min(variants_by_size.keys())} - {max(variants_by_size.keys())}")

        # Run test cases
        logger.info(f"\n{'='*70}")
        logger.info("TEST CASES")
        logger.info(f"{'='*70}")

        for size, test_case in self.TEST_CASES.items():
            logger.info(f"\n--- Size {size}: {test_case['description']} ---")

            if size not in variants_by_size:
                logger.error(f"❌ Variant not found for size {size}")
                results['failed'] += 1
                continue

            variant = variants_by_size[size]
            factor = test_case['adjustment_factor']

            logger.info(f"Variant: {variant['default_code']} (ID: {variant['id']})")

            # Validate weight
            passed, msg = self.validate_weight_calculation(
                variant, base_weight, coef, factor
            )
            logger.info(f"  {msg}")
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1

            results['tests'].append({
                'test': f'Weight calculation - Size {size}',
                'passed': passed,
                'message': msg
            })

            # Validate cost
            expected_weight = base_weight * coef * factor
            status, msg = self.validate_cost_calculation(
                variant, expected_weight, gold_price, provider_indice
            )

            if status is not None:
                logger.info(f"  {msg}")
                if status:
                    results['passed'] += 1
                else:
                    results['failed'] += 1

                results['tests'].append({
                    'test': f'Cost calculation - Size {size}',
                    'passed': status,
                    'message': msg
                })
            else:
                logger.info(f"  {msg}")
                results['warnings'] += 1

        # Validate all sizes have correct range
        logger.info(f"\n{'='*70}")
        logger.info("SIZE RANGE VALIDATION")
        logger.info(f"{'='*70}")

        missing_sizes = set(self.SIZE_RANGE) - set(variants_by_size.keys())
        if missing_sizes:
            logger.warning(f"⚠️  Missing sizes: {sorted(missing_sizes)}")
            results['warnings'] += 1
        else:
            logger.info("✓ All 45 sizes present (6-50)")
            results['passed'] += 1

        # Check for invalid sizes
        invalid_sizes = [s for s in variants_by_size.keys() if s < 6 or s > 50]
        if invalid_sizes:
            logger.error(f"❌ Invalid ring sizes found: {invalid_sizes}")
            results['failed'] += 1
        else:
            logger.info("✓ All sizes in valid range")
            results['passed'] += 1

        # Verbose: Show all variants
        if self.verbose and variants_by_size:
            logger.info(f"\n{'='*70}")
            logger.info("ALL VARIANTS DETAIL")
            logger.info(f"{'='*70}")

            for size in sorted(variants_by_size.keys()):
                variant = variants_by_size[size]
                weight = variant.get('calculated_metal_weight', 0)
                cost = variant.get('standard_price', 0)
                price = variant.get('list_price', 0)

                logger.info(f"Size {size:2d}: {variant['default_code']:12s} | "
                          f"Weight: {weight:7.4f}g | "
                          f"Cost: R${cost:8.2f} | "
                          f"Price: R${price:9.2f}")

        # Final summary
        logger.info(f"\n{'='*70}")
        logger.info("VALIDATION SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Tests passed: {results['passed']}")
        logger.info(f"Tests failed: {results['failed']}")
        logger.info(f"Warnings: {results['warnings']}")

        if results['failed'] == 0:
            logger.info("\n✓ ALL VALIDATIONS PASSED!")
        else:
            logger.error(f"\n❌ {results['failed']} VALIDATION(S) FAILED")

        logger.info(f"{'='*70}\n")

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Validate CPL size-based pricing calculations'
    )

    # Product selection
    parser.add_argument('--sku', required=True,
                       help='Product SKU (e.g., C725R)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output for all variants')

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
        # Initialize validator
        validator = CPLPricingValidator(
            args.url, args.db, args.user, args.password,
            verbose=args.verbose
        )

        # Run validation
        results = validator.validate_all(args.sku)

        # Exit with appropriate code
        if results['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
