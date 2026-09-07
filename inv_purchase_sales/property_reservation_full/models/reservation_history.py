# -*- coding: utf-8 -*-
##############################################################################
#    Ahadubit Technologies
#    Copyright (C) 2024-TODAY Ahadubit Technologies(<https://ahadubit.com>).
#    Author: Ahadubit Technologies (<https://ahadubit.com>)
##############################################################################
from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class ReservationCancel(models.Model):
    _name = 'property.reservation.cancel'
    _rec_name = 'name'
    name = fields.Char(string="Reason", required=True)


class PropertyReservationHistory(models.Model):
    _name = 'property.reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Reservation History'
    _rec_name = 'reservation_type_id'
    _order = 'create_date desc'

    # Basic Information
    property_id = fields.Many2one('property.property',
                                 domain=[('state', 'in', ['available'])],
                                 string="Property", required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer",
                                tracking=True, required=True)
    reservation_type_id = fields.Many2one('property.reservation.configuration',
                                         string="Reservation Type",
                                          domain=[('is_used_use', '!=', True)],
                                         tracking=True, required=True)

    # Dates and Status
    expire_date = fields.Datetime(string="End Date", tracking=True)
    canceled_time = fields.Datetime(string="Canceled Time", tracking=True)
    canceled_reason = fields.Text(string="Cancellation Reason", tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('reserved', 'Reserved'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ("pending_sales", "Pending Sales"),
        ('sold', 'Sold'),
    ], string='Status', tracking=True, default='draft')

    # Related Records
    original_reservation_id = fields.Many2one('property.reservation', string="Property")
    payment_line_ids = fields.One2many('property.reservation.payment',
                                       domain=[('payment_status', '!=', 'canceled')],
                                      inverse_name='reservation_id', tracking=True)


    extension_ids = fields.One2many('property.reservation.extend.history', 
                                   inverse_name='reservation_id')
    transfer_ids = fields.One2many('property.reservation.transfer.history',

                                   inverse_name='reservation_id')

    # Computed Fields
    is_sufficient = fields.Boolean('Is Sufficient', compute='compute_total_amount',store=True)
    payment_diff = fields.Float('Difference', compute='compute_total_amount')
    expected_amount = fields.Float('Expected Amount', compute='compute_total_amount')
    is_special = fields.Boolean('Is Special', compute='check_is_special_reservation')
    show_approve_button = fields.Boolean(compute='_compute_show_approve_button', store=True)
    # Documents
    request_letter = fields.Binary(string='Request Letter')
    # Status Fields
    extension_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Extension State', tracking=True)

    transfer_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Transfer Status', tracking=True)

    amendment_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Amendment Status', tracking=True)

    show_transfer_extend = fields.Boolean(compute='_compute_show_transfer_extend')
    is_payment_required = fields.Boolean(related="reservation_type_id.is_payment_required")
    print_report_name = fields.Char(compute="_compute_print_report_name")
    is_from_sales = fields.Boolean()
    is_creator=fields.Boolean(compute="compute_is_creator")
    salesperson_ids = fields.Many2one('res.users', string="Salesperson" , readonly=True)
    crm_lead_id = fields.Many2one('crm.lead', string="CRM Opportunity", tracking=True)



    # def save_record(self):
       
    #     vals = {
    #         'partner_id': self.partner_id.id,
    #         'property_id': self.property_id.id,
    #         'reservation_type_id': self.reservation_type_id.id,
    #         'expire_date': self.expire_date,
    #         'status': self.status,
    #     }
    #     if self.id:
    #         self.write(vals)
    #     else:
    #         self.create(vals)
    def compute_is_creator(self):
        for rec in self:
            rec.is_creator=rec.create_uid== self.env.user and rec.status in ['reserved','requested']


    def print_change_history(self):
        for record in self:
            tracking_values = self.env['mail.tracking.value'].search([
                ('mail_message_id', 'in', record.message_ids.ids)
            ])
            data_list=[]
            for rec in tracking_values:
                data_list.append({
                    'user': rec.create_uid.name,
                    'fields': rec.field_id.name,
                    'old_value': rec.old_value_char,
                    'new_value': rec.new_value_char,
                    'date': rec.create_date,
                })
            data_list = sorted(data_list, key=lambda x: x['date'], reverse=True) 

            for item in data_list:
                item['date'] = item['date'] + timedelta(hours=3)
            data = {
                'datas': data_list,
                'property': self.property_id.name,
                'partner': self.partner_id.name,
                'reservation': self.reservation_type_id.name,
            }
            return self.env.ref(
                'property_reservation_full.property_reservation_report_action_report').report_action(
                self, data=data)

    def _compute_print_report_name(self):
        for record in self:
            record.print_report_name = f"{record.partner_id.name} - {record.property_id.name}"

    @api.depends('reservation_type_id')
    def _compute_show_transfer_extend(self):
        for rec in self:
            if rec.reservation_type_id and rec.reservation_type_id.reservation_type != "quick":
                rec.show_transfer_extend=True
            else:
                rec.show_transfer_extend = False


    @api.onchange('reservation_type_id')
    def _onchange_property_id(self):
        self.expire_date = self.get_expire_date(self.reservation_type_id.id)

    # Compute Methods
    @api.depends('reservation_type_id')
    def check_is_special_reservation(self):
        """Check if the reservation type is special."""
        for rec in self:
            rec.is_special = rec.reservation_type_id.reservation_type == 'special'

    def action_print_reservation_details(self):
        """Action to print the reservation details report."""
        return self.env.ref('property_reservation_full.Reservation_details_report_action').report_action(self)


        
    @api.depends('status', 'is_sufficient', 'reservation_type_id.is_payment_required')
    def _compute_show_approve_button(self):
        for rec in self:
            if rec.reservation_type_id.reservation_type == 'quick' and rec.status == 'draft':
                show_button = True
            else:
                show_button = rec.status == 'requested' and (
                    not rec.reservation_type_id.is_payment_required or 
                    (rec.reservation_type_id.is_payment_required and rec.is_sufficient)
                )
            rec.show_approve_button = show_button

    @api.depends('payment_line_ids', 'reservation_type_id', 'property_id','partner_id')
    def compute_total_amount(self):
        """Compute payment totals and sufficiency."""
        for rec in self:
            if rec.reservation_type_id.is_payment_required:
                total = sum(rec.payment_line_ids.mapped('amount'))
                expected = rec.compute_expected_amount()
                discount = rec.compute_discount_amount()
                expected = expected - (expected * discount)
                rec.expected_amount = expected
                rec.is_sufficient = total >= expected
                rec.payment_diff = expected - total
            else:
                rec.expected_amount = 0
                rec.payment_diff = 0
                rec.is_sufficient = True
            if rec.id and rec.is_sufficient and rec.status=="draft":
                rec.write({'status':"requested"})
                rec.status="requested"
                if rec.crm_lead_id:
                    rec.crm_lead_id.action_set_reserved()

    def compute_expected_amount(self):
        """Calculate the expected payment amount based on payment type."""
        self.ensure_one()
        if self.reservation_type_id.payment_type == "fixed":
            return self.reservation_type_id.amount

        # Calculate percentage-based amount
        payment_term_line = self.env['property.payment.term.line'].search(
            [('term_id', '=', self.property_id.payment_structure_id.id)],
            order='sequence', limit=1)

        expected_per = payment_term_line.percentage if payment_term_line else 0
        base_amount = (self.property_id.unit_price 
                      if self.property_id.sale_rent == "for_sale" 
                      else self.property_id.rent_month)
        return (base_amount * expected_per / 100) * (self.reservation_type_id.amount / 100)

    def compute_discount_amount(self):
        for rec in self:
            total = 0.0
            discounts = self.env['property.special.discount'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('property_id', '=', rec.property_id.id),
                ('status', '=', 'approved')
            ])
            for dis in discounts:
                total += dis.discount

            return total

    # Approval Methods
    def special_reservation_approve(self):
        """Approve a special reservation request."""
        self.ensure_one()
        self.property_id.sudo().write({'state': 'reserved'})
        self.status = "reserved"

    def action_reset_to_draft(self):
        """Reset the reservation back to draft status."""
        self.write({'status': 'draft'})

    def approve_reservation(self):
        """Approve a regular reservation request."""
        self.ensure_one()
        if self.property_id.state != 'available':
            raise ValidationError(
                _("Cannot approve reservation request. Property %s is in %s state") % 
                (self.property_id.name, self.property_id.state))
        channel = self.env['discuss.channel'].search([('name','=','general')], limit=1)
        if channel:
            expire_date = self.expire_date + timedelta(hours=3)
            channel.message_post(
                body=(f"Property {self.property_id.name} is reserved, reservation will expire on {expire_date}"),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
        
        self.property_id.sudo().write({'state': 'reserved'})
        self.status = 'reserved'

        # for p in self.payment_line_ids:
        #     p._check_receipt_data()

    # Transfer Methods
    def transfer_reservation(self):
        """Prepare transfer request with payment lines."""
        self.ensure_one()
        payment_lines = [(0, 0, {
            'payment_line_id': payment.id,
            'payment_receipt': payment.payment_receipt,
            'document_type_id': payment.document_type_id.id,
            'bank_id': payment.bank_id.id,
            'ref_number': payment.ref_number,
            'transaction_date': payment.transaction_date,
            'amount': payment.amount,
            'amount_display': payment.amount,
            'id_editable': True,
        }) for payment in self.payment_line_ids]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfer Reservation',
            'res_model': 'property.reservation.transfer.history',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reservation_id': self.id,
                'default_reservation_id2': self.id,
                'default_old_property_id': self.property_id.id,
                'default_payment_line_ids': payment_lines,
            }
        }


    # Sale Methods
    def sale_property_reserved(self):
        """Convert reservation to sale."""
        payment_term_id = self.property_id.payment_structure_id.id
        self.ensure_one()
        sale = self.env['property.sale'].create({
            'property_id': self.property_id.id,
            'partner_id': self.partner_id.id,
            'property_payment_term': payment_term_id,
            'reservation_id': self.id,
            'is_from_reservation': True,
        })
        
        self.sudo().write({'status': 'pending_sales'})
        self.property_id.sudo().write({'state': 'pending_sales'})
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale',
            'res_model': 'property.sale',
            'view_mode': 'form',
            'target': 'current',
            'res_id': sale.id,
        }

    # Expiration Methods
    def check_expired_reservation(self):
        """Check and update expired reservations."""
        reservations = self.search([
            ('status', 'in', ['requested','reserved']),
            ('expire_date', '<=', fields.datetime.now()),
        ])
        for reservation in reservations:
            status=reservation.status
            reservation.sudo().write({
                'status': 'expired',
                'canceled_time': datetime.now()
            })
            if status =="reserved":
                reservation.property_id.sudo().write({
                    'state': 'available'
                })
            stage = self.env['crm.stage'].search([('name', 'ilike', "Follow Up")], limit=1)
            if stage and reservation.crm_lead_id:
                reservation.crm_lead_id.write({
                    'stage_id': stage.id,
                })


    # Extension Methods
    def reservation_extend(self):
        """Prepare extension request."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Extend Reservation',
            'res_model': 'property.reservation.extend.history',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reservation_id': self.id,
                'default_reservation_id1': self.id,
                'default_old_end_date': self.expire_date,
            }
        }

    # Cancellation Methods
    def cancel_reservation(self):
        """Cancel an active reservation."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Reservation',
            'res_model': 'cancellation.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reservation_id': self.id,
            }
        }
    
    def get_expire_date(self, reservation_type_id):
        """Calculate the expiration date based on reservation type."""
        reservation_type = self.env['property.reservation.configuration'].browse(reservation_type_id)
        expire_date = False
        if reservation_type:
            current_time = fields.Datetime.now()
            if reservation_type.duration_in == "minutes":
                expire_date = current_time + timedelta(minutes=reservation_type.duration)
            elif reservation_type.duration_in == "hours":
                expire_date = current_time + timedelta(hours=reservation_type.duration)
            elif reservation_type.duration_in == "days":
                expire_date = current_time + timedelta(days=reservation_type.duration)
            elif reservation_type.duration_in == "weeks":
                expire_date = current_time + timedelta(weeks=reservation_type.duration)
            else:  # months
                expire_date = current_time + relativedelta(months=reservation_type.duration)
            sunday_count = 0
            # Count Sundays
            while current_time <= expire_date:
                if current_time.weekday() == 6:  # Sunday is represented by 6
                    sunday_count += 1
                current_time += timedelta(days=1)
            if sunday_count:
                expire_date = expire_date + timedelta(days=sunday_count)
        return expire_date

    def property_reservation_detail(self):
        """Show transfer request details."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reservation Detail'),
            'res_model': self._name,
            'view_mode': 'form,list',
            'target': 'current',
            'res_id': self.id,
        }
    @api.model
    def create(self, vals):
        """Create a new reservation with calculated expiration date."""

        expire_date = self.get_expire_date(vals.get('reservation_type_id'))
        status = "requested" if self.is_sufficient else "draft"



        vals.update({
            'expire_date': expire_date,
            'status': status
        })
        res =super(PropertyReservationHistory, self).create(vals)
        if res.reservation_type_id.one_time_use:
            res.reservation_type_id.sudo().write({'is_used_use':True,
                                       'used_by_id':self.env.user.id})
        res.property_id.sudo().write({'state': 'reserved'})
        return res
    
    def get_sales_from_reservation(self):
        for rec in self:
            sales=self.env['property.sale'].search([('reservation_id', '=', rec.id)])
            if sales:
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Sales'),
                    'res_model': 'property.sale',
                    'view_mode': 'form,list',
                    'target': 'current',
                    'res_id': sales.id,
                }
            else:
                raise  ValidationError("This reservation is not related to any sales")



class Property(models.Model):
    """A class for the model property to represent the property"""

    _inherit = "property.property"
    state = fields.Selection(selection_add=[('reserved', 'Reserved'), ('pending_sales', 'Pending Sales')],
                              ondelete={'reserved': 'set default', 'pending_sales': 'set default'})
    reservation_line_ids = fields.One2many('property.reservation', inverse_name='property_id')

    def action_reserve(self):
        for rec in self:
            if rec.state != 'available':
                raise ValidationError(f"You can't Reserve product in {rec.state} state")
            return {
                'type': 'ir.actions.act_window',
                'name': 'Reservation',
                'res_model': 'property.reservation',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_property_id': rec.id,
                }
            }
    def cancel_reservation(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Cancel  Reservation',
                'res_model': 'cancellation.reason.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_property_id': rec.id,
                }
            }



class PropertySale(models.Model):
    _inherit = 'property.sale'
    _description = 'Property Sale'

    # 'confirm' already existed; 'cancel' is added so a sale can be cancelled
    # when its linked reservation payment is cancelled (see PropertyReservationPayment)
    state = fields.Selection(selection_add=[('cancel', 'Cancelled')], ondelete={'cancel': 'set default'})
    reservation_id=fields.Many2one('property.reservation')
    on_reservation_amount=fields.Float(compute="compute_reservation_total_paid")
    is_from_reservation = fields.Boolean(
        string="is from Reservation",
        compute="compute_is_from_reservation"
    )
    property_payment_term = fields.Many2one('property.payment.term', string="Payment Term")
    discount = fields.Float(
        string="Discount", tracking=True,
        help="Flat amount deducted from the last installment of the payment schedule")
    payment_line_ids = fields.One2many('property.payment.line', 'sale_id', string="Payment Schedule")
    total_paid = fields.Float(string="Total Paid", compute="_compute_total_paid", store=True)

    @api.depends('payment_line_ids.amount', 'payment_line_ids.is_paid')
    def _compute_total_paid(self):
        for rec in self:
            rec.total_paid = sum(rec.payment_line_ids.filtered('is_paid').mapped('amount'))

    @api.onchange('property_payment_term')
    def recalculate_payment_line_based_on_payment_term(self):
        for rec in self:
            if rec.id and not isinstance(rec.id, models.NewId):
                rec.compute_sale_payment_line()

    def compute_sale_payment_line(self):
        for res in self:
            if not res.id or isinstance(res.id, models.NewId):
                continue
            self.env['property.payment.line'].search([('sale_id', '=', res.id)]).unlink()
            self.create_payment_term_line(res.id, res.property_payment_term.id, res.reservation_id.id,
                                          (res.sale_price - res.discount), res)
            self.add_discount_on_payment_term(res)
            self.add__special_discount_on_payment_term(res)

    def create_payment_term_line(self, sale_id, payment_term_id, reservation_id, total_amount, sale_record):
        """Generate one property.payment.line per installment of the
        selected payment term, sized as a percentage of total_amount."""
        term_lines = self.env['property.payment.term.line'].search(
            [('term_id', '=', payment_term_id)], order='sequence')
        if not term_lines:
            return
        vals_list = [{
            'sale_id': sale_id,
            'term_line_id': line.id,
            'amount': total_amount * line.percentage / 100,
        } for line in term_lines]
        self.env['property.payment.line'].create(vals_list)

    def add_discount_on_payment_term(self, sale):
        """Deduct the sale's flat discount from the last installment."""
        if not sale.discount:
            return
        last_line = self.env['property.payment.line'].search(
            [('sale_id', '=', sale.id)], order='sequence desc', limit=1)
        if last_line:
            last_line.amount = max(last_line.amount - sale.discount, 0)

    def add__special_discount_on_payment_term(self, sale):
        """Deduct approved property.special.discount records on the first or
        last installment, based on their discount_start_from preference."""
        discounts = self.env['property.special.discount'].search([
            ('partner_id', '=', sale.partner_id.id),
            ('property_id', '=', sale.property_id.id),
            ('status', '=', 'approved'),
        ])
        for discount in discounts:
            order = 'sequence' if discount.discount_start_from == '1' else 'sequence desc'
            line = self.env['property.payment.line'].search(
                [('sale_id', '=', sale.id)], order=order, limit=1)
            if line:
                line.amount = max(line.amount - (line.amount * discount.discount), 0)

    @api.depends('reservation_id')
    def compute_reservation_total_paid(self):
        for res in self:
            amount = sum(line.amount for line in res.reservation_id.payment_line_ids)

            if amount>res.total_paid:
                self.compute_sale_payment_line()
            res.on_reservation_amount = amount
            if res.reservation_id:
                res.reservation_id.write({
                    'is_from_sales': False
                })
                for payment in res.reservation_id.payment_line_ids:
                    payment.write({
                        "id_editable": False
                    })

    def add_payment_list(self):
        for rec in self:
            if rec.reservation_id:
                rec.reservation_id.write({
                    'is_from_sales':True
                })
                for payment in rec.reservation_id.payment_line_ids:
                    payment.write({
                        "id_editable":True
                    })
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Reservation'),
                    'res_model': 'property.reservation',
                    'view_mode': 'form,list',
                    'target': 'new',
                    'res_id': rec.reservation_id.id,
                }






    @api.depends('reservation_id')
    def compute_is_from_reservation(self):
        for rec in self:
            if rec.reservation_id:
                rec.is_from_reservation=True
            else:
                rec.is_from_reservation=False


    def action_confirm(self):
        """Confirm the sale order and Change necessary fields"""
        self.ensure_one()
        super(PropertySale, self).action_confirm()
        if self.reservation_id:
            self.reservation_id.status = 'sold'