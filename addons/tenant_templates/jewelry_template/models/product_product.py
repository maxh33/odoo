# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    ring_size = fields.Integer(
        'Ring Size',
        help='Ring size number (1-50) for size-based pricing'
    )

    calculated_metal_weight = fields.Float(
        'Calculated Weight (g)',
        compute='_compute_size_based_weight',
        store=True,
        digits=(8, 4),
        help='Auto-calculated: base_weight × COEF × size_adjustment_factor'
    )

    @api.depends(
        'product_tmpl_id.metal_weight_grams',
        'product_tmpl_id.size_pricing_coef',
        'product_tmpl_id.has_size_based_pricing',
        'ring_size'
    )
    def _compute_size_based_weight(self):
        """Calculate weight based on ring size using CPL adjustment table"""
        for variant in self:
            template = variant.product_tmpl_id

            # Only for products with size-based pricing enabled
            if not template.has_size_based_pricing or not variant.ring_size:
                variant.calculated_metal_weight = template.metal_weight_grams or 0.0
                continue

            # Find size adjustment factor from CPL table
            size_adj = self.env['joiasmax.size.weight.adjustment'].search([
                ('size_number', '=', variant.ring_size)
            ], limit=1)

            if not size_adj:
                _logger.warning(
                    f"No size adjustment factor found for ring size {variant.ring_size}. "
                    f"Using base weight for {variant.display_name}."
                )
                variant.calculated_metal_weight = template.metal_weight_grams or 0.0
                continue

            # Formula: base_weight × COEF × size_adjustment_factor
            base_weight = template.metal_weight_grams or 0.0
            coef = template.size_pricing_coef or 1.0

            variant.calculated_metal_weight = base_weight * coef * size_adj.adjustment_factor

            _logger.debug(
                f"Size-based weight calculated for {variant.display_name} (size {variant.ring_size}): "
                f"{base_weight}g × {coef} × {size_adj.adjustment_factor} = {variant.calculated_metal_weight}g"
            )

    @api.depends(
        'calculated_metal_weight',
        'product_tmpl_id.material_type',
        'product_tmpl_id.metal_purity',
        'product_tmpl_id.has_size_based_pricing',
        'product_tmpl_id.jewelry_pricing_id',
        'product_tmpl_id.jewelry_pricing_id.provider_indice'
    )
    def _compute_variant_cost(self):
        """Calculate cost for variant based on calculated weight"""
        for variant in self:
            template = variant.product_tmpl_id

            # Only apply to products with size-based pricing enabled
            if not template.has_size_based_pricing or not variant.calculated_metal_weight:
                continue

            # Get market price for material type
            market_price_obj = self.env['joiasmax.market.price']
            market_type_map = {
                'gold': 'gold_24k',
                'silver': 'silver_950',
            }

            market_type = market_type_map.get(template.material_type)
            if not market_type:
                continue

            # Query active market price
            market_price_record = market_price_obj.search([
                ('material_type', '=', market_type),
                ('is_active', '=', True)
            ], limit=1)

            if not market_price_record:
                _logger.warning(
                    f"No active market price found for {market_type}. "
                    f"Cannot calculate cost for {variant.display_name}."
                )
                continue

            # Get purity factor
            purity_factors = {
                '24k': 1.0,     # Gold - always 24k price
                '950': 0.95,    # Silver 950
            }
            purity_factor = purity_factors.get(template.metal_purity, 1.0)

            # Get provider indice from jewelry pricing
            provider_indice = 1.0
            if template.jewelry_pricing_id:
                provider_indice = template.jewelry_pricing_id.provider_indice or 1.0

            # Calculate cost: weight × market_price × purity_factor × provider_indice
            variant_cost = (
                variant.calculated_metal_weight *
                market_price_record.price_per_gram_brl *
                purity_factor *
                provider_indice
            )

            # Update variant cost (standard_price)
            variant.standard_price = variant_cost

            _logger.debug(
                f"Size-based cost calculated for {variant.display_name}: "
                f"{variant.calculated_metal_weight}g × R${market_price_record.price_per_gram_brl}/g × "
                f"{purity_factor} × {provider_indice} = R${variant_cost:.2f}"
            )
