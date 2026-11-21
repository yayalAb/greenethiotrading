# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    """A class that inherits the already existing model account move to add
    the related property sale and rental records"""
    _inherit = 'account.move'

    property_order_id = fields.Many2one('property.sale',
                                        string="Property Order ID",
                                        help='The corresponding property '
                                             'sale order')
    property_rental_id = fields.Many2one('property.rental',
                                         string='Property Rental ID',
                                         help='The corresponding property '
                                              'rental order')
    rental_invoice_start_date = fields.Date(
        string='Payment Period Start',
        help='Start date of the payment/rental period covered by this invoice')
    rental_invoice_end_date = fields.Date(
        string='Payment Period End',
        help='End date of the payment/rental period covered by this invoice')

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if move.property_rental_id:
                rental = move.property_rental_id
                rental.invoice_date = fields.Date.today()
                if rental.state == 'draft':
                    rental.property_id.state = 'rented'
                    rental.state = 'in_contract'
        return moves

    @api.onchange('rental_invoice_start_date', 'rental_invoice_end_date')
    def _onchange_rental_invoice_dates(self):
        """Update line quantity based on number of months in the selected period."""
        for move in self:
            if not move.property_rental_id or not move.rental_invoice_start_date or not move.rental_invoice_end_date:
                continue
            if move.rental_invoice_start_date > move.rental_invoice_end_date:
                continue
            months = move._calculate_rental_months(move.rental_invoice_start_date, move.rental_invoice_end_date)
            for line in move.invoice_line_ids:
                line.quantity = months

    @staticmethod
    def _calculate_rental_months(start_date, end_date):
        """Calculate the number of months between start_date and end_date (inclusive)."""
        if not start_date or not end_date or end_date < start_date:
            return 1.0
        end_incl = end_date + relativedelta(days=1)
        d = relativedelta(end_incl, start_date)
        full_months = d.years * 12 + d.months
        if full_months >= 1 and d.days == 0:
            return float(full_months)
        total = full_months + (d.days / 30.0)
        return max(1.0, round(total, 2)) if total > 1.0 else 1.0

    @api.constrains('rental_invoice_start_date', 'rental_invoice_end_date',
                    'property_rental_id')
    def _check_rental_period_overlap(self):
        """Prevent saving an invoice without mandatory payment period
        or whose rental period overlaps with any other invoice linked to the same rental contract."""
        for move in self:
            if not move.property_rental_id:
                continue
            if not move.rental_invoice_start_date or not move.rental_invoice_end_date:
                raise ValidationError(
                    _('Payment Period Start and End dates are mandatory for rental invoices.'))
            if move.rental_invoice_start_date > move.rental_invoice_end_date:
                raise ValidationError(
                    _('Rental Period Start must be before Rental Period End.'))
            rental = move.property_rental_id
            if move.rental_invoice_start_date < rental.start_date:
                raise ValidationError(
                    _('Rental Period Start (%s) cannot be before the rental '
                      'contract Start Date (%s).')
                    % (move.rental_invoice_start_date, rental.start_date))
            if move.rental_invoice_end_date > rental.end_date:
                raise ValidationError(
                    _('Rental Period End (%s) cannot exceed the rental '
                      'contract End Date (%s).')
                    % (move.rental_invoice_end_date, rental.end_date))
            # Overlap check against sibling invoices on the same rental
            siblings = self.env['account.move'].search([
                ('id', '!=', move.id),
                ('property_rental_id', '=', rental.id),
                ('move_type', '=', 'out_invoice'),
                ('rental_invoice_start_date', '!=', False),
                ('rental_invoice_end_date', '!=', False),
            ])
            for sibling in siblings:
                overlaps = not (
                    move.rental_invoice_end_date < sibling.rental_invoice_start_date
                    or move.rental_invoice_start_date > sibling.rental_invoice_end_date
                )
                if overlaps:
                    raise ValidationError(
                        _('Rental period %s → %s overlaps with existing '
                          'invoice %s which covers %s → %s.')
                        % (move.rental_invoice_start_date,
                           move.rental_invoice_end_date,
                           sibling.name or sibling.id,
                           sibling.rental_invoice_start_date,
                           sibling.rental_invoice_end_date))
