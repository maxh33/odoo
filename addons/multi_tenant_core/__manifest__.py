# -*- coding: utf-8 -*-
{
    'name': 'Multi-Tenant Core',
    'version': '18.0.1.0.0',
    'category': 'Administration',
    'summary': 'Core multi-tenancy functionality for Odoo 18',
    'description': """
Multi-Tenant Core Module
========================
Provides core functionality for multi-tenant Odoo deployment:
- Database-level tenant isolation
- Domain-based routing (subdomain per tenant)
- Tenant configuration management
- Cross-tenant security enforcement
- API authentication per tenant

Supports multiple business types via tenant templates.
    """,
    'author': 'Max Haider',
    'website': 'https://maxhaider.dev',
    'depends': ['base', 'web'],
    'data': [
        'security/multi_tenant_security.xml',
        'security/ir.model.access.csv',
        'views/tenant_config_views.xml',
        'data/tenant_default_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
