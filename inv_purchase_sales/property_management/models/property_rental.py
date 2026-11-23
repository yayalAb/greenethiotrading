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


class PropertyRental(models.Model):
    """A class for the model property rental to represent
    the rental order of a property"""
    _name = 'property.rental'
    _description = 'Property Rent'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', readonly=True,
                       required=True, copy=False, default='New',
                       help='The reference code/sequence of the property '
                            'rental')
    property_id = fields.Many2one(
        'property.property', string='Property',
        required=True,
        help='The property to be rented',
        domain="[('state','=','available'),('sale_rent','=','for_tenancy')]")
    owner_id = fields.Many2one('res.partner', string='Land Lord',
                               related='property_id.landlord_id', store=True,
                               help='The owner / land lord of the property')
    rent_price = fields.Monetary(string='Rent Price',
                                 related='property_id.rent_month',
                                 help='The Rental price per month of the '
                                      'property')
    renter_id = fields.Many2one('res.partner', string='Renter', required=True,
                                help='The customer who is renting the property')
    state = fields.Selection(
        [('draft', 'Draft'), ('in_contract', 'In Contract'),
         ('expired', 'Expired'), ('cancel', 'Cancelled')],
        required=True, default='draft', string='Status', tracking=True,
        help="* The \'Draft\' status is used when the rental is in draft.\n"
             "* The \'In Contract\' status is used when the property is rented "
             "and is in contract\n"
             "* The \'Expired\' status is used when the property rented "
             "contract has expired.\n"
             "* The \'Cancelled\' status is used when the property rental "
             "is cancelled.\n")
    start_date = fields.Date(string='Start Date', required=True,
                             help='The starting date of the rent')
    end_date = fields.Date(string='End Date', required=True,
                           help='The Ending date of the rent')
    invoice_count = fields.Integer(string='Invoice Count',
                                   compute='_compute_invoice_count',
                                   help='The Invoices related to this rental')
    invoice_ids = fields.One2many('account.move', 'property_rental_id',
                                  string='Invoices')
    rental_bills_ids = fields.One2many('rental.bill', 'rental_id')
    payment_modality_id = fields.Many2one(
        'property.payment.modality',
        string='Payment Modality',
        help='The payment modality (e.g. Monthly, Quarterly, Annual) for this rental contract')
    penalty_id = fields.Many2one(
        'property.penalty',
        string='Penalty',
        help='Penalty rule applied to this rental contract in case of late payment')
    invoice_date = fields.Date(string='Invoice Date',
                               help='The latest Invoiced Date')
    next_invoice = fields.Date(string='Next Invoice',
                               compute='_compute_next_invoice',
                               store=True,
                               help='The next invoicing date')
    company_id = fields.Many2one('res.company',
                                 string="Property Management Company",
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='company_id.currency_id')
    @api.model_create_multi
    def create(self, vals_list):
        """Setting the sequence when record is created"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'property.rent') or 'New'
        res = super(PropertyRental, self).create(vals_list)
        return res

    def _compute_invoice_count(self):
        """Calculates the Invoice count for the property"""
        self.invoice_count = self.env['account.move'].search_count(
            [('property_rental_id', '=', self.id)])

    @api.depends('invoice_ids.rental_invoice_end_date', 'invoice_ids.state', 'end_date')
    def _compute_next_invoice(self):
        """Computes next_invoice date from the latest invoice's end date + 1 day."""
        for rec in self:
            # Find all out_invoices linked to this rental that have an end date set
            valid_invoices = rec.invoice_ids.filtered(
                lambda m: m.move_type == 'out_invoice' and m.state != 'cancel' and m.rental_invoice_end_date
            )
            if valid_invoices:
                latest_end_date = max(valid_invoices.mapped('rental_invoice_end_date'))
                next_date = latest_end_date + relativedelta(days=1)
                # Next invoice date is valid as long as it does not exceed the contract's end date
                rec.next_invoice = next_date if rec.end_date and next_date <= rec.end_date else False
            elif rec.invoice_date and rec.end_date and fields.Date.today() < rec.end_date:
                rec.next_invoice = fields.Date.add(rec.invoice_date, months=1)
            else:
                rec.next_invoice = False

    def action_cancel(self):
        """ Changes the record stage to cancel """
        self.property_id.state = 'available'
        self.state = 'cancel'

    def action_create_contract(self):
        """Opens the standard account.move invoice form view with contract default values,
        defaulting payment period to the current month's start and end date."""
        self.ensure_one()
        if self.renter_id.blacklisted:
            raise ValidationError(
                _('The Customer %r is Blacklisted.', self.renter_id.name))

        today = fields.Date.today()
        # If there's a computed next_invoice date (i.e. last invoice end date + 1), start from it
        if self.next_invoice:
            default_start = self.next_invoice
        else:
            # Default start to current month start or contract start date
            month_start = today.replace(day=1)
            default_start = max(month_start, self.start_date) if self.start_date else month_start

        # Calculate default_end based on payment_modality if configured
        if self.payment_modality_id and self.payment_modality_id.number:
            mod_num = self.payment_modality_id.number
            mod_unit = self.payment_modality_id.modality
            if mod_unit == 'days':
                target_end = default_start + relativedelta(days=mod_num - 1)
            elif mod_unit == 'years':
                target_end = default_start + relativedelta(years=mod_num, days=-1)
            else:  # months
                target_end = default_start + relativedelta(months=mod_num, days=-1)
            default_end = min(target_end, self.end_date) if self.end_date else target_end
        else:
            month_end = default_start + relativedelta(months=1, days=-1)
            default_end = min(month_end, self.end_date) if self.end_date else month_end

        if default_start > default_end:
            default_start = self.start_date or today
            default_end = self.end_date or today

        months_qty = self.env['account.move']._calculate_rental_months(default_start, default_end)

        income_account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', [self.company_id.id])
        ], limit=1)

        line_name = _('%s — Rental Period: %s to %s') % (
            self.property_id.name,
            default_start,
            default_end,
        )

        return {
            'name': _('Create Rental Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'view_id': self.env.ref('stock_picking_custom.view_move_form_fs_mrc_payment').id,
            'target': 'current',
            'context': {
                'default_move_type': 'out_invoice',
                'default_partner_id': self.renter_id.id,
                'default_property_rental_id': self.id,
                'default_rental_invoice_start_date': default_start,
                'default_rental_invoice_end_date': default_end,
                'default_invoice_date': today,
                'default_invoice_line_ids': [
                    (0, 0, {
                        'name': line_name,
                        'price_unit': self.rent_price,
                        'quantity': months_qty,
                        'account_id': income_account.id if income_account else False,
                    })
                ],
            },
        }

    def action_view_invoice(self):
        """Views all the related invoice in tree view related to the records"""
        return {
            'name': _('Invoices'),
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain': [('property_rental_id', '=', self.id),
                       ('move_type', '=', 'out_invoice')]
        }

    @api.model
    def action_check_rental(self):
        """Scheduled action to create the next invoice for rent
        else set it as expired."""
        records = self.env['property.rental'].search(
            [('state', '=', 'in_contract')])
        for rec in records:
            if not rec.next_invoice:
                rec.state = 'expired'
            if fields.Date.today() == rec.next_invoice:
                income_account = self.env['account.account'].search([
                    ('account_type', '=', 'income'),
                    ('company_ids', 'in', [rec.company_id.id])
                ], limit=1)
                self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'property_rental_id': rec.id,
                    'partner_id': rec.renter_id.id,
                    'invoice_line_ids': [fields.Command.create({
                        'name': rec.property_id.name,
                        'price_unit': rec.rent_price,
                        'currency_id': rec.env.user.company_id.currency_id.id,
                        'account_id': income_account.id,
                    })]
                })
                rec.invoice_date = fields.Date.today()
