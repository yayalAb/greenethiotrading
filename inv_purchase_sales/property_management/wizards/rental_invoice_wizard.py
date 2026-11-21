# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RentalInvoiceWizard(models.TransientModel):
    """Wizard that collects the rental period before creating an invoice.
    Validates that the requested period:
      - has both dates filled in
      - starts before it ends
      - falls inside the rental contract dates
      - does not overlap any existing invoice on the same rental
    """
    _name = 'rental.invoice.wizard'
    _description = 'Create Rental Invoice'

    rental_id = fields.Many2one('property.rental', string='Rental',
                                required=True, readonly=True)
    property_id = fields.Many2one(related='rental_id.property_id',
                                  string='Property', readonly=True)
    renter_id = fields.Many2one(related='rental_id.renter_id',
                                string='Renter', readonly=True)
    rent_price = fields.Monetary(related='rental_id.rent_price',
                                 string='Rent Price', readonly=True)
    currency_id = fields.Many2one(related='rental_id.currency_id',
                                  readonly=True)
    contract_start = fields.Date(related='rental_id.start_date',
                                 string='Contract Start', readonly=True)
    contract_end = fields.Date(related='rental_id.end_date',
                               string='Contract End', readonly=True)
    period_start = fields.Date(string='Period Start', required=True,
                               help='Start of the rental period to invoice')
    period_end = fields.Date(string='Period End', required=True,
                             help='End of the rental period to invoice')

    @api.constrains('period_start', 'period_end')
    def _check_period_dates(self):
        for rec in self:
            if rec.period_start and rec.period_end:
                if rec.period_start > rec.period_end:
                    raise ValidationError(
                        _('Period Start must be before Period End.'))

    def _validate_no_overlap(self):
        """Full validation: range sanity + contract bounds + no overlap."""
        self.ensure_one()
        rental = self.rental_id

        if self.period_start < rental.start_date:
            raise ValidationError(
                _('Period Start (%s) cannot be before the contract '
                  'Start Date (%s).') % (self.period_start, rental.start_date))
        if self.period_end > rental.end_date:
            raise ValidationError(
                _('Period End (%s) cannot exceed the contract '
                  'End Date (%s).') % (self.period_end, rental.end_date))

        # Overlap check against every existing invoice on this rental
        existing = self.env['account.move'].search([
            ('property_rental_id', '=', rental.id),
            ('move_type', '=', 'out_invoice'),
            ('rental_invoice_start_date', '!=', False),
            ('rental_invoice_end_date', '!=', False),
        ])
        for inv in existing:
            overlaps = not (
                self.period_end < inv.rental_invoice_start_date
                or self.period_start > inv.rental_invoice_end_date
            )
            if overlaps:
                raise ValidationError(
                    _('The period %s → %s overlaps with existing invoice '
                      '%s which covers %s → %s.') % (
                        self.period_start,
                        self.period_end,
                        inv.name or inv.id,
                        inv.rental_invoice_start_date,
                        inv.rental_invoice_end_date,
                    ))

    def action_create_invoice(self):
        """Validate period, create the invoice, and transition state if needed."""
        self.ensure_one()
        self._validate_no_overlap()

        rental = self.rental_id
        income_account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', [rental.company_id.id]),
        ], limit=1)

        line_name = _('%s — Rental Period: %s to %s') % (
            rental.property_id.name,
            self.period_start,
            self.period_end,
        )

        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'property_rental_id': rental.id,
            'partner_id': rental.renter_id.id,
            'rental_invoice_start_date': self.period_start,
            'rental_invoice_end_date': self.period_end,
            'invoice_line_ids': [fields.Command.create({
                'name': line_name,
                'price_unit': rental.rent_price,
                'currency_id': rental.currency_id.id,
                'account_id': income_account.id,
            })],
        })

        rental.invoice_date = fields.Date.today()

        # First invoice: move rental to In Contract
        if rental.state == 'draft':
            rental.property_id.state = 'rented'
            rental.state = 'in_contract'

        # Return action to view the invoices smart button list
        return rental.action_view_invoice()
