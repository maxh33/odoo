# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging
import json
from datetime import datetime

_logger = logging.getLogger(__name__)

class MarketPriceWebhook(http.Controller):

    @http.route('/api/v1/jewelry/market_prices/update', type='json', auth='public', methods=['POST'], csrf=False)
    def update_market_prices(self, **kwargs):
        """
        Webhook endpoint to receive gold/silver price updates from N8N

        Expected payload:
        {
            "gold_24k_brl": 750.00,
            "silver_950_brl": 10.30,
            "exchange_rate": 5.42,
            "timestamp": "2025-12-17T11:00:00",
            "source": "n8n_automation"
        }
        """
        try:
            data = request.jsonrequest
            _logger.info(f"Received market price update: {data}")

            # Validate required fields
            required_fields = ['gold_24k_brl', 'silver_950_brl', 'exchange_rate']
            if not all(field in data for field in required_fields):
                return {'status': 'error', 'message': 'Missing required fields'}

            # Get database connection
            env = request.env(su=True)  # Bypass authentication for webhook

            # Update gold 24k price
            env.cr.execute("""
                INSERT INTO joiasmax_market_prices (material_type, price_per_gram_brl, source_api, is_active)
                VALUES ('gold_24k', %s, %s, TRUE)
                ON CONFLICT (material_type) DO UPDATE
                SET price_per_gram_brl = EXCLUDED.price_per_gram_brl,
                    fetched_at = CURRENT_TIMESTAMP,
                    source_api = EXCLUDED.source_api
            """, (data['gold_24k_brl'], data.get('source', 'n8n_webhook')))

            # Calculate and update gold 18k (75% of 24k)
            gold_18k_price = data['gold_24k_brl'] * 0.75
            env.cr.execute("""
                INSERT INTO joiasmax_market_prices (material_type, price_per_gram_brl, source_api, is_active)
                VALUES ('gold_18k', %s, 'calculated_from_24k', TRUE)
                ON CONFLICT (material_type) DO UPDATE
                SET price_per_gram_brl = EXCLUDED.price_per_gram_brl,
                    fetched_at = CURRENT_TIMESTAMP
            """, (gold_18k_price,))

            # Update silver 950 price
            env.cr.execute("""
                INSERT INTO joiasmax_market_prices (material_type, price_per_gram_brl, source_api, is_active)
                VALUES ('silver_950', %s, %s, TRUE)
                ON CONFLICT (material_type) DO UPDATE
                SET price_per_gram_brl = EXCLUDED.price_per_gram_brl,
                    fetched_at = CURRENT_TIMESTAMP,
                    source_api = EXCLUDED.source_api
            """, (data['silver_950_brl'], data.get('source', 'n8n_webhook')))

            env.cr.commit()

            _logger.info(f"Market prices updated successfully: Gold 24k={data['gold_24k_brl']}, Silver 950={data['silver_950_brl']}")

            return {
                'status': 'success',
                'message': 'Market prices updated successfully',
                'timestamp': datetime.now().isoformat(),
                'updated_materials': ['gold_24k', 'gold_18k', 'silver_950']
            }

        except Exception as e:
            _logger.error(f"Error updating market prices: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
