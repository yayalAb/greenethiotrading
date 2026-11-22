# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyPaymentModality(models.Model):
    """Payment modality configuration defining billing frequency / periods (e.g., Monthly, Quarterly, Annual)."""
    _name = 'property.payment.modality'
    _description = 'Payment Modality'
    _order = 'modality asc, number asc, id desc'

    name = fields.Char(
        string='Name',
        required=True,
        help='Name of the payment modality (e.g. Monthly, Quarterly, Semi-Annual, Annual)'
    )
    modality = fields.Selection([
        ('days', 'Days'),
        ('months', 'Months'),
        ('years', 'Years'),
    ], string='Modality', required=True, default='months', help='Unit of period (days, months, years)')
    number = fields.Integer(
        string='Number',
        required=True,
        default=1,
        help='Number of days, months, or years for this modality'
    )
    description = fields.Text(
        string='Description',
        help='Details and notes regarding this payment modality'
    )
    active = fields.Boolean(default=True, string='Active')

    _sql_constraints = [
        ('number_positive_check', 'CHECK(number > 0)', 'The number must be greater than zero!'),
    ]

    @api.onchange('number', 'modality')
    def _onchange_number_modality(self):
        """Auto-suggest name if name is empty"""
        if not self.name and self.number and self.modality:
            mod_labels = dict(self._fields['modality'].selection)
            unit_label = mod_labels.get(self.modality, self.modality)
            if self.number == 1 and unit_label.endswith('s'):
                unit_label = unit_label[:-1]
            self.name = f"{self.number} {unit_label}"
