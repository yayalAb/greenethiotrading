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
        string='Rental Period Start',
        help='Start date of the rental period covered by this invoice')
    rental_invoice_end_date = fields.Date(
        string='Rental Period End',
        help='End date of the rental period covered by this invoice')

    @api.constrains('rental_invoice_start_date', 'rental_invoice_end_date',
                    'property_rental_id')
    def _check_rental_period_overlap(self):
        """Prevent saving an invoice whose rental period overlaps with any
        other invoice linked to the same rental contract."""
        for move in self:
            if not move.property_rental_id:
                continue
            if not move.rental_invoice_start_date or not move.rental_invoice_end_date:
                continue
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
