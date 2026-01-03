# -*- coding: utf-8 -*-
{
    'name': 'Jewelry Template - JoiasMax',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Jewelry store template with dynamic pricing for gold/silver products',
    'description': """
        Jewelry Template Module for JoiasMax
        =====================================

        Features:
        ---------
        * Custom product fields for jewelry (metal type, weight, purity, gemstones)
        * Dynamic pricing based on market gold/silver prices
        * Supplier cost tracking and management
        * Complete price change audit trail
        * Integration ready for N8N automation workflows
        * WooCommerce synchronization support

        Custom Database Tables:
        -----------------------
        * joiasmax_product_pricing - Material and pricing data
        * joiasmax_market_prices - Current market rates
        * joiasmax_supplier_costs - Historical supplier costs
        * joiasmax_price_history - Complete price change log

        Use Case:
        ---------
        Designed for jewelry e-commerce businesses that need:
        - Automated price updates based on precious metal market rates
        - Real cost tracking (solving Bling ERP limitation of R$ 0.00 costs)
        - Margin visibility and profitability analysis
        - Integration with e-commerce platforms
    """,
    'author': 'Max Haider',
    'website': 'https://joiasmax.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'sale_management',
        'stock',
    ],
    'data': [
        # Security - Load first
        'security/jewelry_security.xml',
        'security/ir.model.access.csv',

        # Views - Load in logical order
        'views/product_template_views.xml',
        'views/jewelry_pricing_views.xml',
        'views/market_price_views.xml',
        'views/supplier_cost_views.xml',
        'views/price_history_views.xml',

        # Menu - Load last
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
