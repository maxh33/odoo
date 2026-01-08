# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class PricingWebhook(http.Controller):

    @http.route(
        '/api/v1/jewelry/recalculate_prices',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    def recalculate_all_prices(self, **kwargs):
        """
        N8N webhook endpoint to recalculate all variant prices
        Called when gold/silver market prices update

        Expected POST data:
        {
            "api_key": "your_webhook_api_key",
            "template_ids": [1, 2, 3],  # Optional: specific templates
            "material_type": "gold"     # Optional: filter by material
        }

        Returns:
        {
            "success": True,
            "templates_processed": 5,
            "variants_recalculated": 42
        }
        """
        try:
            # Verify API key
            api_key = kwargs.get('api_key')
            stored_api_key = request.env['ir.config_parameter'].sudo().get_param(
                'jewelry.webhook_api_key'
            )

            if not stored_api_key:
                _logger.warning(
                    "Jewelry webhook API key not configured. "
                    "Set 'jewelry.webhook_api_key' in System Parameters."
                )
                return {
                    'error': 'Webhook not configured',
                    'message': 'Contact administrator to configure webhook API key'
                }

            if api_key != stored_api_key:
                _logger.warning(f"Invalid API key attempt for jewelry price recalculation")
                return {'error': 'Unauthorized', 'message': 'Invalid API key'}

            # Get optional filters
            template_ids = kwargs.get('template_ids', [])
            material_type = kwargs.get('material_type')

            # Build search domain
            domain = [('has_size_based_pricing', '=', True)]

            if template_ids:
                domain.append(('id', 'in', template_ids))

            if material_type:
                domain.append(('material_type', '=', material_type))

            # Find all templates with size-based pricing
            templates = request.env['product.template'].sudo().search(domain)

            _logger.info(
                f"Recalculating prices for {len(templates)} templates with size-based pricing"
            )

            recalculated_count = 0

            for template in templates:
                _logger.debug(f"Processing template: {template.name}")

                for variant in template.product_variant_ids:
                    try:
                        # Trigger recomputation
                        variant._compute_size_based_weight()
                        variant._compute_variant_cost()
                        recalculated_count += 1

                        _logger.debug(
                            f"  Recalculated variant {variant.display_name}: "
                            f"Weight={variant.calculated_metal_weight}g, Cost=R${variant.standard_price:.2f}"
                        )
                    except Exception as e:
                        _logger.error(
                            f"Failed to recalculate variant {variant.display_name}: {e}"
                        )
                        continue

            _logger.info(
                f"Successfully recalculated {recalculated_count} variants "
                f"across {len(templates)} templates"
            )

            return {
                'success': True,
                'templates_processed': len(templates),
                'variants_recalculated': recalculated_count,
                'timestamp': str(request.env.cr.now())
            }

        except Exception as e:
            _logger.error(f"Error in jewelry price recalculation webhook: {e}", exc_info=True)
            return {
                'error': 'Internal server error',
                'message': str(e)
            }

    @http.route(
        '/api/v1/jewelry/recalculate_prices/health',
        type='json',
        auth='public',
        methods=['GET', 'POST'],
        csrf=False
    )
    def webhook_health_check(self, **kwargs):
        """
        Health check endpoint for N8N monitoring
        """
        try:
            # Check if size adjustment table has data
            size_count = request.env['joiasmax.size.weight.adjustment'].sudo().search_count([])

            # Check if any templates use size-based pricing
            template_count = request.env['product.template'].sudo().search_count([
                ('has_size_based_pricing', '=', True)
            ])

            return {
                'status': 'healthy',
                'size_adjustments_loaded': size_count,
                'size_based_templates': template_count,
                'timestamp': str(request.env.cr.now())
            }
        except Exception as e:
            _logger.error(f"Webhook health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
