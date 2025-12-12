# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    tenant_config_id = fields.Many2one(
        'multi_tenant.config',
        string='Tenant Configuration',
        help='Link to tenant configuration for multi-tenant setup'
    )
    is_tenant = fields.Boolean(
        'Is Tenant',
        default=False,
        help='Indicates if this company is a tenant in a multi-tenant setup'
    )
