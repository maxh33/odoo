# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class PriceHistory(models.Model):
    _name = 'joiasmax.price.history'
    _description = 'Product Price Change History'
    _table = 'joiasmax_price_history'
    _order = 'changed_at desc, id desc'
    _rec_name = 'product_id'

    # Core relationships
    product_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        readonly=True,
        help='Product whose price changed'
    )

    tenant_id = fields.Integer(
        string='Tenant ID',
        readonly=True,
        help='Multi-tenant isolation field'
    )

    # Price change information
    old_price_brl = fields.Float(
        string='Old Price (R$)',
        required=True,
        readonly=True,
        digits=(10, 2),
        help='Price before the change'
    )

    new_price_brl = fields.Float(
        string='New Price (R$)',
        required=True,
        readonly=True,
        digits=(10, 2),
        help='Price after the change'
    )

    price_difference_brl = fields.Float(
        string='Difference (R$)',
        compute='_compute_price_difference',
        store=True,
        digits=(10, 2),
        help='Difference between new and old price'
    )

    price_change_percentage = fields.Float(
        string='Change (%)',
        compute='_compute_price_difference',
        store=True,
        digits=(5, 2),
        help='Percentage change in price'
    )

    # Change context
    change_reason = fields.Selection([
        ('market_price_update', 'Market Price Update'),
        ('manual_adjustment', 'Manual Price Adjustment'),
        ('cost_change', 'Cost Change'),
        ('promotion', 'Promotional Pricing'),
        ('competitive_adjustment', 'Competitive Adjustment'),
        ('seasonal_adjustment', 'Seasonal Adjustment'),
        ('bulk_update', 'Bulk Price Update'),
        ('other', 'Other'),
    ], string='Change Reason', required=True, readonly=True, default='manual_adjustment')

    change_notes = fields.Text(
        string='Notes',
        readonly=True,
        help='Additional details about the price change'
    )

    # Audit trail
    changed_at = fields.Datetime(
        string='Changed At',
        required=True,
        readonly=True,
        default=fields.Datetime.now,
        help='When the price was changed'
    )

    changed_by_user_id = fields.Many2one(
        'res.users',
        string='Changed By',
        readonly=True,
        help='User who initiated the price change'
    )

    # Market context at time of change
    gold_price_at_change = fields.Float(
        string='Gold Price (R$/g)',
        readonly=True,
        digits=(10, 2),
        help='Gold market price when change occurred'
    )

    silver_price_at_change = fields.Float(
        string='Silver Price (R$/g)',
        readonly=True,
        digits=(10, 2),
        help='Silver market price when change occurred'
    )

    exchange_rate_at_change = fields.Float(
        string='Exchange Rate (USD/BRL)',
        readonly=True,
        digits=(10, 4),
        help='USD to BRL exchange rate when change occurred'
    )

    # Integration tracking
    synced_to_woocommerce = fields.Boolean(
        string='Synced to WooCommerce',
        default=False,
        help='Whether this price change was synced to WooCommerce'
    )

    synced_at = fields.Datetime(
        string='Synced At',
        readonly=True,
        help='When the price was synced to external systems'
    )

    sync_error = fields.Text(
        string='Sync Error',
        readonly=True,
        help='Error message if sync failed'
    )

    @api.depends('old_price_brl', 'new_price_brl')
    def _compute_price_difference(self):
        """Calculate price difference and percentage change"""
        for record in self:
            record.price_difference_brl = record.new_price_brl - record.old_price_brl

            if record.old_price_brl > 0:
                record.price_change_percentage = (
                    (record.new_price_brl - record.old_price_brl) / record.old_price_brl
                ) * 100
            else:
                record.price_change_percentage = 0.0

    @api.model
    def create(self, vals):
        """
        Set tenant_id on create
        This is an audit log - write-only, no updates allowed
        """
        # Set tenant_id
        if 'tenant_id' not in vals:
            vals['tenant_id'] = 1  # Default tenant

        # Set changed_at if not provided
        if 'changed_at' not in vals:
            vals['changed_at'] = fields.Datetime.now()

        # Log the price change
        _logger.info(
            f"Price history created: Product ID {vals.get('product_id')}, "
            f"R$ {vals.get('old_price_brl', 0):.2f} → R$ {vals.get('new_price_brl', 0):.2f}, "
            f"Reason: {vals.get('change_reason', 'unknown')}"
        )

        return super(PriceHistory, self).create(vals)

    def write(self, vals):
        """
        Prevent updates to audit log except for sync status
        """
        # Only allow updating sync-related fields
        allowed_fields = {'synced_to_woocommerce', 'synced_at', 'sync_error'}
        if not set(vals.keys()).issubset(allowed_fields):
            raise UserError(
                _('Price history records are audit logs and cannot be modified. '
                  'Only sync status can be updated.')
            )

        return super(PriceHistory, self).write(vals)

    def unlink(self):
        """Prevent deletion of audit log records"""
        raise UserError(
            _('Price history records are audit logs and cannot be deleted. '
              'They are kept for compliance and tracking purposes.')
        )

    @api.model
    def log_price_change(self, product_id, old_price, new_price, reason='manual_adjustment',
                        notes=None, user_id=None, gold_price=None, silver_price=None):
        """
        Convenience method to create a price history record

        Args:
            product_id: Product template ID
            old_price: Previous price
            new_price: New price
            reason: Change reason (from selection)
            notes: Optional notes
            user_id: User who made the change
            gold_price: Gold price at time of change
            silver_price: Silver price at time of change

        Returns:
            PriceHistory record
        """
        vals = {
            'product_id': product_id,
            'old_price_brl': old_price,
            'new_price_brl': new_price,
            'change_reason': reason,
            'changed_by_user_id': user_id or self.env.user.id,
        }

        if notes:
            vals['change_notes'] = notes

        if gold_price:
            vals['gold_price_at_change'] = gold_price

        if silver_price:
            vals['silver_price_at_change'] = silver_price

        return self.create(vals)

    def action_mark_synced(self):
        """Mark record as synced to WooCommerce"""
        for record in self:
            record.write({
                'synced_to_woocommerce': True,
                'synced_at': fields.Datetime.now(),
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sync Status Updated'),
                'message': _('%s record(s) marked as synced') % len(self),
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

    @api.model
    def get_product_price_trend(self, product_id, days=30):
        """
        Get price trend for a product over last N days

        Args:
            product_id: Product template ID
            days: Number of days to look back

        Returns:
            list: Price history records
        """
        from_date = fields.Datetime.now() - timedelta(days=days)

        return self.search([
            ('product_id', '=', product_id),
            ('changed_at', '>=', from_date),
        ], order='changed_at asc')

    @api.model
    def get_recent_changes(self, limit=50):
        """
        Get recent price changes across all products

        Args:
            limit: Maximum number of records to return

        Returns:
            list: Recent price history records
        """
        return self.search([], order='changed_at desc', limit=limit)
