# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class JoiasmaxMarketPrice(models.Model):
    _name = 'joiasmax.market.price'
    _description = 'JoiasMax Market Prices for Precious Metals'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Audit trail
    _order = 'fetched_at desc'

    material_type = fields.Selection([
        ('gold_24k', 'Gold 24K (999.9)'),
        ('silver_950', 'Silver 950 (95%)'),
    ], string='Material Type', required=True, index=True, tracking=True)

    price_per_gram_brl = fields.Float(
        string='Price per Gram (BRL)',
        required=True,
        digits=(10, 2),
        tracking=True,
        help='Current market price in Brazilian Reais per gram'
    )

    source_api = fields.Char(
        string='Source',
        default='n8n_automation',
        tracking=True,
        help='Data source identifier'
    )

    fetched_at = fields.Datetime(
        string='Fetched At',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )

    is_active = fields.Boolean(
        string='Active Price',
        default=True,
        tracking=True,
        help='Only one active price per material type'
    )

    exchange_rate = fields.Float(
        string='USD/BRL Exchange Rate',
        digits=(10, 4),
        tracking=True
    )

    _sql_constraints = [
        ('unique_active_material',
         'UNIQUE(material_type) WHERE is_active = TRUE',
         'Only one active price allowed per material type')
    ]

    @api.model
    def update_from_n8n(self, gold_24k_brl, silver_950_brl, exchange_rate, source='n8n_automation'):
        """
        Update market prices from N8N webhook
        Called via XML-RPC from N8N workflow
        """
        _logger.info(f"Updating market prices: Gold 24k={gold_24k_brl}, Silver 950={silver_950_brl}")

        # Validate inputs
        if gold_24k_brl <= 0 or silver_950_brl <= 0:
            raise ValidationError("Prices must be positive values")

        # Update Gold 24k
        gold_24k = self.search([('material_type', '=', 'gold_24k'), ('is_active', '=', True)])
        if gold_24k:
            gold_24k.write({
                'price_per_gram_brl': gold_24k_brl,
                'exchange_rate': exchange_rate,
                'fetched_at': fields.Datetime.now(),
                'source_api': source
            })
        else:
            self.create({
                'material_type': 'gold_24k',
                'price_per_gram_brl': gold_24k_brl,
                'exchange_rate': exchange_rate,
                'source_api': source,
                'is_active': True
            })

        # Update Silver 950
        silver_950 = self.search([('material_type', '=', 'silver_950'), ('is_active', '=', True)])
        if silver_950:
            silver_950.write({
                'price_per_gram_brl': silver_950_brl,
                'exchange_rate': exchange_rate,
                'fetched_at': fields.Datetime.now(),
                'source_api': source
            })
        else:
            self.create({
                'material_type': 'silver_950',
                'price_per_gram_brl': silver_950_brl,
                'exchange_rate': exchange_rate,
                'source_api': source,
                'is_active': True
            })

        return {
            'status': 'success',
            'updated': ['gold_24k', 'silver_950'],
            'timestamp': fields.Datetime.now().isoformat()
        }

    def action_activate(self):
        """Activate this market price (deactivates others of the same type)"""
        self.ensure_one()
        # Deactivate all other prices of the same material type
        self.search([('material_type', '=', self.material_type), ('id', '!=', self.id)]).write({'is_active': False})
        # Activate this price
        self.write({'is_active': True})
        return True

    def action_deactivate(self):
        """Deactivate this market price"""
        self.ensure_one()
        self.write({'is_active': False})
        return True

    def action_fetch_current_price(self):
        """Placeholder for fetching current market price from external API"""
        self.ensure_one()
        # TODO: Implement actual API integration in future
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Fetch Price'),
                'message': _('Manual price fetch is not yet implemented. Prices are updated via N8N automation.'),
                'type': 'info',
                'sticky': False,
            }
        }
