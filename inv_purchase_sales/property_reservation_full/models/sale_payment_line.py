# -*- coding: utf-8 -*-
##############################################################################
#    Ahadubit Technologies
#    Copyright (C) 2024-TODAY Ahadubit Technologies(<https://ahadubit.com>).
#    Author: Ahadubit Technologies (<https://ahadubit.com>)
##############################################################################
from odoo import fields, models


class PropertyPaymentLine(models.Model):
    """Installment line generated on a property sale from the payment
    term selected on the property (property.payment.term)."""
    _name = 'property.payment.line'
    _description = 'Property Sale Payment Line'
    _order = 'sequence, id'

    sale_id = fields.Many2one('property.sale', string="Sale", required=True, ondelete='cascade')
    term_line_id = fields.Many2one('property.payment.term.line', string="Payment Term Line")
    sequence = fields.Integer(related='term_line_id.sequence', store=True)
    name = fields.Char(related='term_line_id.name', string="Installment")
    amount = fields.Float(string="Amount")
    is_paid = fields.Boolean(string="Paid", default=False)
