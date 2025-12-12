# -*- coding: utf-8 -*-
from odoo import models
from odoo.http import request

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_db_from_hostname(cls, hostname):
        """
        Extract database name from hostname for multi-tenant routing
        Format: {tenant}.odoo.maxhaider.dev -> tenant database
        """
        # Get base domain from config
        try:
            base_domain = request.env['ir.config_parameter'].sudo().get_param(
                'multi_tenant.base_domain', 'odoo.maxhaider.dev'
            )
        except:
            # Fallback if config parameter not available
            base_domain = 'odoo.maxhaider.dev'

        if hostname.endswith(base_domain):
            # Extract subdomain
            subdomain = hostname.replace(f'.{base_domain}', '')

            # Convert subdomain to database name (replace hyphens with underscores)
            db_name = f"tenant_{subdomain.replace('-', '_')}"

            return db_name

        # Default to master database
        return 'odoo_master'
