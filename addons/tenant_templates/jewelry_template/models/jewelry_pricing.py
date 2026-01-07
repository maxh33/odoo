# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class JewelryPricing(models.Model):
    _name = 'joiasmax.jewelry.pricing'
    _description = 'Jewelry Pricing Calculator'
    _table = 'joiasmax_product_pricing'
    _rec_name = 'product_id'

    # Core relationships
    product_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        help='Product this pricing record applies to'
    )

    tenant_id = fields.Integer(
        string='Tenant ID',
        help='Multi-tenant isolation field'
    )

    # Material information (copied from product for calculation)
    material_type = fields.Selection(
        related='product_id.material_type',
        string='Material Type',
        store=True,
        readonly=True
    )

    metal_weight_grams = fields.Float(
        related='product_id.metal_weight_grams',
        string='Metal Weight (g)',
        store=True,
        readonly=True
    )

    metal_purity = fields.Selection(
        related='product_id.metal_purity',
        string='Metal Purity',
        store=True,
        readonly=True
    )

    # Cost components
    material_cost_brl = fields.Float(
        string='Material Cost (R$)',
        compute='_compute_material_cost',
        store=True,
        digits=(10, 2),
        help='Calculated cost of precious metal based on current market price'
    )

    total_cost_brl = fields.Float(
        string='Total Cost (R$)',
        compute='_compute_total_cost',
        store=True,
        digits=(10, 2),
        help='Material cost (provider indice includes production costs)'
    )

    # Pricing strategy
    markup_percentage = fields.Float(
        string='Markup Percentage (%)',
        digits=(5, 2),
        default=200.0,
        help='Markup percentage to apply to total cost'
    )

    calculated_price_brl = fields.Float(
        string='Calculated Price (R$)',
        compute='_compute_calculated_price',
        store=True,
        digits=(10, 2),
        help='Calculated selling price based on costs and markup'
    )

    manual_override_price_brl = fields.Float(
        string='Manual Override Price (R$)',
        digits=(10, 2),
        default=0.0,
        help='Override calculated price with manual value'
    )

    use_manual_override = fields.Boolean(
        string='Use Manual Override',
        default=False,
        help='If checked, manual price will be used instead of calculated'
    )

    # Provider pricing factor
    provider_indice = fields.Float(
        string='Provider Index Factor',
        digits=(5, 2),
        default=1.0,
        help='Provider-specific pricing factor that adjusts for production costs and rarity. '
             'Default 1.0. User provides real values per product type.'
    )

    final_price_brl = fields.Float(
        string='Final Price (R$)',
        compute='_compute_final_price',
        store=True,
        digits=(10, 2),
        help='Final selling price (calculated or manual override)'
    )

    # Market price tracking
    gold_price_at_calculation = fields.Float(
        string='Gold Price at Calculation (R$/g)',
        digits=(10, 2),
        help='Gold market price when cost was calculated'
    )

    silver_price_at_calculation = fields.Float(
        string='Silver Price at Calculation (R$/g)',
        digits=(10, 2),
        help='Silver market price when cost was calculated'
    )

    # Audit fields
    last_cost_update = fields.Datetime(
        string='Last Cost Update',
        help='When costs were last recalculated'
    )

    last_sync_to_product = fields.Datetime(
        string='Last Sync to Product',
        help='When price was last synced to product'
    )

    notes = fields.Text(string='Pricing Notes')

    # Purity factor mapping (metal purity to decimal factor)
    # NOTE: Provider's "indice" already includes production costs
    PURITY_FACTORS = {
        '24k': 1.0,     # Gold 24k (pure)
        '950': 0.95,    # Silver 950
    }

    @api.depends('metal_weight_grams', 'metal_purity', 'material_type', 'provider_indice')
    def _compute_material_cost(self):
        """Calculate material cost based on weight, purity, market price, and provider indice"""
        for record in self:
            if not record.metal_weight_grams or not record.metal_purity or not record.material_type:
                record.material_cost_brl = 0.0
                continue

            # Get market price (always 24k for gold, 950 for silver)
            market_price = record._get_market_price(record.material_type, record.metal_purity)

            if not market_price:
                _logger.warning(
                    f"No market price found for {record.material_type} with purity {record.metal_purity}"
                )
                record.material_cost_brl = 0.0
                continue

            # Get purity factor
            purity_factor = record._get_purity_factor(record.metal_purity)

            # Get provider indice (default 1.0)
            indice = record.provider_indice or 1.0

            # Calculate: weight × market_price × purity_factor × provider_indice
            # Note: For gold, purity_factor is 1.0 (always use 24k price)
            # Provider indice adjusts for production costs and product type (e.g., 1.10 for 18k products)
            material_cost = record.metal_weight_grams * market_price * purity_factor * indice

            record.material_cost_brl = material_cost

            # Auto-sync material cost to product's standard_price field
            if record.product_id and material_cost > 0:
                record.product_id.write({'standard_price': material_cost})

            # Store market prices for audit trail
            if record.material_type == 'gold':
                record.gold_price_at_calculation = market_price
            elif record.material_type == 'silver':
                record.silver_price_at_calculation = market_price

            record.last_cost_update = fields.Datetime.now()

    @api.depends('material_cost_brl')
    def _compute_total_cost(self):
        """Calculate total cost - provider's indice already includes production costs"""
        for record in self:
            # Total cost = material cost (indice from provider includes production)
            record.total_cost_brl = record.material_cost_brl

    @api.depends('total_cost_brl', 'markup_percentage')
    def _compute_calculated_price(self):
        """Calculate selling price based on total cost and markup"""
        for record in self:
            if record.total_cost_brl > 0 and record.markup_percentage > 0:
                record.calculated_price_brl = record.total_cost_brl * (1 + record.markup_percentage / 100)
            else:
                record.calculated_price_brl = 0.0

    @api.depends('calculated_price_brl', 'manual_override_price_brl', 'use_manual_override')
    def _compute_final_price(self):
        """Determine final price (calculated or manual override)"""
        for record in self:
            if record.use_manual_override and record.manual_override_price_brl > 0:
                record.final_price_brl = record.manual_override_price_brl
            else:
                record.final_price_brl = record.calculated_price_brl

    def _get_market_price(self, material_type, purity):
        """
        Query market price from joiasmax_market_price table
        Returns price per gram in BRL
        """
        # Map material type to market price type
        market_type_map = {
            'gold': 'gold_24k',
            'silver': 'silver_950',
        }

        market_type = market_type_map.get(material_type)
        if not market_type:
            return 0.0

        # Query active market price
        market_price_record = self.env['joiasmax.market.price'].search([
            ('material_type', '=', market_type),
            ('is_active', '=', True)
        ], limit=1)

        if market_price_record:
            return market_price_record.price_per_gram_brl
        else:
            _logger.warning(f"No active market price found for {market_type}")
            return 0.0

    def _get_purity_factor(self, purity):
        """Get purity factor for calculation"""
        return self.PURITY_FACTORS.get(purity, 1.0)

    def sync_to_product(self):
        """
        Sync calculated price to product.template.list_price
        Log price change to price_history
        """
        for record in self:
            if not record.product_id:
                continue

            old_price = record.product_id.list_price
            new_price = record.final_price_brl
            new_cost = record.material_cost_brl  # Material cost for product Cost field

            # Update product price and cost
            record.product_id.write({
                'list_price': new_price,
                'standard_price': new_cost,  # Sync material cost to product Cost field
            })

            # Log to price history if price changed
            if abs(old_price - new_price) > 0.01:  # Avoid logging tiny differences
                self.env['joiasmax.price.history'].create({
                    'product_id': record.product_id.id,
                    'old_price_brl': old_price,
                    'new_price_brl': new_price,
                    'change_reason': 'cost_change',
                    'changed_by_user_id': self.env.user.id,
                    'gold_price_at_change': record.gold_price_at_calculation,
                })

                _logger.info(
                    f"Synced price for {record.product_id.name}: "
                    f"R$ {old_price:.2f} → R$ {new_price:.2f}"
                )

            record.last_sync_to_product = fields.Datetime.now()

        return True

    def action_recalculate_costs(self):
        """Manual action to recalculate all costs"""
        self._compute_material_cost()
        self._compute_total_cost()
        self._compute_calculated_price()
        self._compute_final_price()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Costs Recalculated'),
                'message': _('All cost components have been recalculated.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_sync_to_product(self):
        """Manual action to sync price to product"""
        self.sync_to_product()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Price Synced'),
                'message': _('Price has been synced to product.'),
                'type': 'success',
                'sticky': False,
            }
        }

    @api.constrains('markup_percentage')
    def _check_markup_percentage(self):
        """Validate markup percentage"""
        for record in self:
            if record.markup_percentage < 0:
                raise ValidationError(_('Markup percentage cannot be negative.'))

    def action_view_product(self):
        """Open the linked product record"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product',
            'res_model': 'product.template',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        """Set tenant_id on create"""
        # TODO: Implement proper tenant isolation
        # For now, use company_id as a proxy
        if 'tenant_id' not in vals:
            vals['tenant_id'] = 1  # Default tenant

        return super(JewelryPricing, self).create(vals)
