# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyPenalty(models.Model):
    """Penalty configuration for overdue / late rental payments."""
    _name = 'property.penalty'
    _description = 'Property Rental Penalty'
    _order = 'name asc, id desc'

    name = fields.Char(
        string='Name',
        required=True,
        help='Name of the penalty rule (e.g. Late Payment 5%, Overdue Grace 3 Days)'
    )
    tolerance_days = fields.Integer(
        string='Tolerance Days',
        default=0,
        required=True,
        help='Grace period / number of days allowed past due date before penalty applies'
    )
    amount_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage'),
    ], string='Amount Type', required=True, default='percentage',
       help='Calculation method: Fixed amount or percentage of rent')
    amount = fields.Float(
        string='Amount',
        required=True,
        digits=(16, 2),
        help='Penalty value (fixed monetary amount or percentage rate)'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id'
    )
    description = fields.Text(
        string='Description',
        help='Details and terms of the penalty'
    )
    active = fields.Boolean(default=True, string='Active')

    _sql_constraints = [
        ('tolerance_days_non_negative', 'CHECK(tolerance_days >= 0)', 'Tolerance days must be 0 or positive!'),
        ('amount_non_negative', 'CHECK(amount >= 0)', 'Penalty amount must be 0 or positive!'),
    ]
