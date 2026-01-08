# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
import secrets

class TenantConfig(models.Model):
    _name = 'multi_tenant.config'
    _description = 'Tenant Configuration'
    _order = 'create_date desc'

    name = fields.Char('Tenant Name', required=True)
    database_name = fields.Char('Database Name', required=True, readonly=True)
    subdomain = fields.Char('Subdomain', required=True)
    business_type = fields.Selection([
        ('jewelry', 'Jewelry Store'),
        ('retail', 'Retail Business'),
        ('manufacturing', 'Manufacturing'),
        ('services', 'Service Company'),
    ], string='Business Type', required=True, default='retail')

    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)

    # Configuration
    domain = fields.Char('Full Domain', compute='_compute_domain', store=True)
    api_key = fields.Char('API Key', readonly=True, copy=False)

    # Metadata
    create_date = fields.Datetime('Created On', readonly=True)
    write_date = fields.Datetime('Last Updated', readonly=True)

    @api.depends('subdomain')
    def _compute_domain(self):
        base_domain = self.env['ir.config_parameter'].sudo().get_param(
            'multi_tenant.base_domain', 'odoo.maxhaider.dev'
        )
        for record in self:
            record.domain = f"{record.subdomain}.{base_domain}"

    @api.constrains('subdomain')
    def _check_subdomain(self):
        for record in self:
            if not re.match(r'^[a-z0-9-]+$', record.subdomain):
                raise ValidationError(
                    'Subdomain must contain only lowercase letters, numbers, and hyphens'
                )

            # Check uniqueness
            existing = self.search([
                ('subdomain', '=', record.subdomain),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(f'Subdomain {record.subdomain} is already in use')

    @api.model
    def create(self, vals):
        # Generate API key on creation
        vals['api_key'] = secrets.token_urlsafe(32)
        return super().create(vals)
