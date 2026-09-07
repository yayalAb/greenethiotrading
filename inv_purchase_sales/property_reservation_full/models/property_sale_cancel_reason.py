# -*- coding: utf-8 -*-
##############################################################################
#    Ahadubit Technologies
#    Copyright (C) 2024-TODAY Ahadubit Technologies(<https://ahadubit.com>).
#    Author: Ahadubit Technologies (<https://ahadubit.com>)
##############################################################################
from odoo import fields, models


class PropertySaleCancelReason(models.Model):
    _name = 'property.sale.cancel.reason'
    _description = 'Property Sale Cancellation Reason'
    _rec_name = 'name'

    name = fields.Char(string="Reason", required=True)
