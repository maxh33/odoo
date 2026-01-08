# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SupplierCost(models.Model):
    _name = 'joiasmax.supplier.cost'
    _description = 'Supplier Cost Tracking'
    _table = 'joiasmax_supplier_costs'
    _order = 'valid_from desc, id desc'

    # Core relationships
    product_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        help='Product this cost record applies to'
    )

    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        domain=[('supplier_rank', '>', 0)],
        required=True,
        ondelete='restrict',
        help='Supplier providing this product'
    )

    tenant_id = fields.Integer(
        string='Tenant ID',
        help='Multi-tenant isolation field'
    )

    # Cost information
    unit_cost_brl = fields.Float(
        string='Unit Cost (R$)',
        required=True,
        digits=(10, 2),
        help='Cost per unit from this supplier'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Currency of the cost'
    )

    # Validity period
    valid_from = fields.Date(
        string='Valid From',
        required=True,
        default=fields.Date.today,
        help='Date when this cost becomes effective'
    )

    valid_until = fields.Date(
        string='Valid Until',
        help='Date when this cost expires (leave empty for indefinite)'
    )

    is_current = fields.Boolean(
        string='Is Current',
        compute='_compute_is_current',
        store=True,
        help='Whether this cost is currently valid'
    )

    # Supplier preference
    is_preferred_supplier = fields.Boolean(
        string='Preferred Supplier',
        default=False,
        help='Mark this as the preferred supplier for this product'
    )

    # Additional terms
    minimum_order_quantity = fields.Float(
        string='Minimum Order Qty',
        digits=(10, 2),
        help='Minimum quantity that must be ordered'
    )

    lead_time_days = fields.Integer(
        string='Lead Time (days)',
        help='Expected delivery time in days'
    )

    payment_terms = fields.Char(
        string='Payment Terms',
        help='Payment terms for this supplier'
    )

    # Audit fields
    notes = fields.Text(string='Notes')

    created_by_user_id = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )

    @api.depends('valid_from', 'valid_until')
    def _compute_is_current(self):
        """Determine if this cost record is currently valid"""
        today = fields.Date.today()
        for record in self:
            if record.valid_from and record.valid_from > today:
                # Not yet valid
                record.is_current = False
            elif record.valid_until and record.valid_until < today:
                # Expired
                record.is_current = False
            else:
                # Valid
                record.is_current = True

    @api.constrains('valid_from', 'valid_until')
    def _check_validity_dates(self):
        """Ensure valid_until is after valid_from"""
        for record in self:
            if record.valid_until and record.valid_from:
                if record.valid_until < record.valid_from:
                    raise ValidationError(
                        _('Valid Until date must be after Valid From date.')
                    )

    @api.constrains('unit_cost_brl')
    def _check_unit_cost(self):
        """Ensure unit cost is positive"""
        for record in self:
            if record.unit_cost_brl <= 0:
                raise ValidationError(
                    _('Unit cost must be greater than zero.')
                )

    @api.constrains('minimum_order_quantity')
    def _check_minimum_order_quantity(self):
        """Ensure minimum order quantity is positive if set"""
        for record in self:
            if record.minimum_order_quantity and record.minimum_order_quantity <= 0:
                raise ValidationError(
                    _('Minimum order quantity must be greater than zero.')
                )

    @api.model
    def get_current_cost(self, product_id, supplier_id=None):
        """
        Get current cost for a product from preferred or specified supplier

        Args:
            product_id: Product template ID
            supplier_id: Optional supplier ID (uses preferred if not specified)

        Returns:
            float: Current unit cost or 0.0 if not found
        """
        domain = [
            ('product_id', '=', product_id),
            ('is_current', '=', True),
        ]

        if supplier_id:
            domain.append(('supplier_id', '=', supplier_id))
        else:
            # Look for preferred supplier first
            domain.append(('is_preferred_supplier', '=', True))

        cost_record = self.search(domain, order='valid_from desc', limit=1)

        if cost_record:
            return cost_record.unit_cost_brl

        # If no preferred supplier found, try any current supplier
        if not supplier_id:
            cost_record = self.search([
                ('product_id', '=', product_id),
                ('is_current', '=', True),
            ], order='valid_from desc', limit=1)

            if cost_record:
                return cost_record.unit_cost_brl

        return 0.0

    @api.model
    def create(self, vals):
        """Set tenant_id on create and handle preferred supplier logic"""
        # Set tenant_id
        if 'tenant_id' not in vals:
            vals['tenant_id'] = 1  # Default tenant

        # If setting as preferred supplier, unset other preferred suppliers for same product
        if vals.get('is_preferred_supplier') and vals.get('product_id'):
            self.search([
                ('product_id', '=', vals['product_id']),
                ('is_preferred_supplier', '=', True),
            ]).write({'is_preferred_supplier': False})

        return super(SupplierCost, self).create(vals)

    def write(self, vals):
        """Handle preferred supplier logic on update"""
        # If setting as preferred supplier, unset other preferred suppliers for same product
        if vals.get('is_preferred_supplier'):
            for record in self:
                self.search([
                    ('product_id', '=', record.product_id.id),
                    ('is_preferred_supplier', '=', True),
                    ('id', '!=', record.id),
                ]).write({'is_preferred_supplier': False})

        return super(SupplierCost, self).write(vals)

    def action_set_as_preferred(self):
        """Action to set this supplier as preferred"""
        self.ensure_one()
        self.write({'is_preferred_supplier': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Preferred Supplier Set'),
                'message': _('This supplier has been set as preferred for %s') % self.product_id.name,
                'type': 'success',
                'sticky': False,
            }
        }

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

    def action_view_supplier(self):
        """Open the linked supplier record"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Supplier',
            'res_model': 'res.partner',
            'res_id': self.supplier_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.onchange('supplier_id')
    def _onchange_supplier_id(self):
        """Auto-populate payment terms from supplier"""
        if self.supplier_id:
            payment_term = self.supplier_id.property_supplier_payment_term_id
            if payment_term:
                self.payment_terms = payment_term.name
