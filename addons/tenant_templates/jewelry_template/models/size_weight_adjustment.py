# -*- coding: utf-8 -*-
from odoo import models, fields

class SizeWeightAdjustment(models.Model):
    _name = 'joiasmax.size.weight.adjustment'
    _description = 'Ring Size Weight Adjustment Table (CPL)'
    _order = 'size_number'

    size_number = fields.Integer(
        'Ring Size',
        required=True,
        index=True,
        help='Ring size number (1-50)'
    )

    adjustment_factor = fields.Float(
        'Weight Adjustment Factor',
        required=True,
        digits=(6, 4),
        help='Multiplier for base weight based on ring size. '
             'Size 20 = 1.0000 (reference). Formula: final_weight = base_weight × COEF × adjustment_factor'
    )

    _sql_constraints = [
        ('size_unique', 'unique(size_number)', 'Ring size must be unique!')
    ]
