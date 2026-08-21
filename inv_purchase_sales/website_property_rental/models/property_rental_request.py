# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PropertyRentalRequest(models.Model):
    _name = "property.rental.request"
    _description = "Website Rental Enquiry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        default="New",
        readonly=True,
    )
    property_id = fields.Many2one(
        "property.property",
        string="Property",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    partner_name = fields.Char(string="Name", required=True)
    partner_email = fields.Char(string="Email", required=True)
    partner_phone = fields.Char(string="Phone")
    start_date = fields.Date(string="Desired Start Date")
    duration_months = fields.Integer(string="Duration (Months)", default=12)
    message = fields.Text(string="Message")
    state = fields.Selection(
        [
            ("new", "New"),
            ("in_progress", "In Progress"),
            ("won", "Converted"),
            ("lost", "Declined"),
        ],
        string="Status",
        default="new",
        tracking=True,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        default=lambda self: self.env.user,
        tracking=True,
    )
    rent_month = fields.Monetary(
        related="property_id.rent_month",
        string="Listed Rent / Month",
    )
    currency_id = fields.Many2one(related="property_id.currency_id")
    company_id = fields.Many2one(
        "res.company",
        related="property_id.company_id",
        store=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].sudo().next_by_code(
                        "property.rental.request"
                    )
                    or "New"
                )
        records = super().create(vals_list)
        for record in records:
            record._notify_responsible()
        return records

    def _notify_responsible(self):
        self.ensure_one()
        responsible = self.property_id.responsible_id or self.env.user
        if responsible:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=responsible.id,
                summary=_("New rental enquiry for %s") % self.property_id.name,
                note=_(
                    "From %(name)s (%(email)s)<br/>Phone: %(phone)s<br/>%(message)s"
                )
                % {
                    "name": self.partner_name,
                    "email": self.partner_email,
                    "phone": self.partner_phone or "-",
                    "message": self.message or "",
                },
            )
            self.user_id = responsible

    def action_in_progress(self):
        self.state = "in_progress"

    def action_won(self):
        self.state = "won"

    def action_lost(self):
        self.state = "lost"

    def action_open_property(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "property.property",
            "res_id": self.property_id.id,
            "view_mode": "form",
        }
