# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Jewelry identification and classification
    is_jewelry = fields.Boolean(
        string='Is Jewelry Product',
        default=False,
        help='Check this if the product is a jewelry item that requires special pricing calculations'
    )

    material_type = fields.Selection([
        ('gold', 'Gold'),
        ('silver', 'Silver'),
    ], string='Material Type', help='Material type (gold or silver)')

    # Metal attributes
    metal_weight_grams = fields.Float(
        string='Metal Weight (grams)',
        digits=(10, 3),
        help='Total weight of precious metal in grams'
    )

    metal_purity = fields.Selection([
        ('24k', 'Gold 24k'),
        ('950', 'Silver 950'),
    ], string='Purity', help='Purity standard (24k gold or 950 silver)')

    # Relationship to pricing model
    jewelry_pricing_id = fields.Many2one(
        'joiasmax.jewelry.pricing',
        string='Jewelry Pricing',
        ondelete='cascade',
        help='Link to detailed pricing calculations'
    )

    # Computed cost and margin fields (delegated to jewelry_pricing)
    material_cost_brl = fields.Float(
        string='Material Cost (R$)',
        compute='_compute_jewelry_costs',
        store=True,
        digits=(10, 2),
        help='Calculated cost of materials based on market prices'
    )

    total_cost_brl = fields.Float(
        string='Total Cost (R$)',
        compute='_compute_jewelry_costs',
        store=True,
        digits=(10, 2),
        help='Total cost including material, labor, and overhead'
    )

    margin_percentage = fields.Float(
        string='Profit Margin (%)',
        compute='_compute_jewelry_costs',
        store=True,
        digits=(5, 2),
        help='Profit margin percentage'
    )

    @api.depends('jewelry_pricing_id', 'jewelry_pricing_id.material_cost_brl', 'jewelry_pricing_id.total_cost_brl', 'list_price')
    def _compute_jewelry_costs(self):
        """Compute jewelry costs from linked pricing record"""
        for product in self:
            if product.jewelry_pricing_id:
                product.material_cost_brl = product.jewelry_pricing_id.material_cost_brl
                product.total_cost_brl = product.jewelry_pricing_id.total_cost_brl

                # Calculate margin percentage
                if product.total_cost_brl > 0 and product.list_price > 0:
                    product.margin_percentage = ((product.list_price - product.total_cost_brl) / product.list_price) * 100
                else:
                    product.margin_percentage = 0.0
            else:
                product.material_cost_brl = 0.0
                product.total_cost_brl = 0.0
                product.margin_percentage = 0.0

    def action_open_jewelry_pricing(self):
        """Open the linked jewelry pricing record"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Jewelry Pricing',
            'res_model': 'joiasmax.jewelry.pricing',
            'res_id': self.jewelry_pricing_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_jewelry_pricing(self):
        """Create a new jewelry pricing record for this product"""
        self.ensure_one()
        pricing = self.env['joiasmax.jewelry.pricing'].create({
            'product_id': self.id,
        })
        self.jewelry_pricing_id = pricing.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Jewelry Pricing',
            'res_model': 'joiasmax.jewelry.pricing',
            'res_id': pricing.id,
            'view_mode': 'form',
            'target': 'current',
        }
