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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PropertyPaymentTerm(models.Model):
    """A class for the model property payment term to represent an
    installment plan that can be assigned to a property"""

    _name = "property.payment.term"
    _description = "Property Payment Term"

    name = fields.Char(string="Name", required=True, help="Name of the payment term")
    line_ids = fields.One2many(
        "property.payment.term.line", "term_id", string="Payment Term Lines"
    )
    total_percentage = fields.Float(
        string="Total %",
        compute="_compute_total_percentage",
        help="Sum of the percentages of all the lines of this payment term",
    )

    @api.depends("line_ids.percentage")
    def _compute_total_percentage(self):
        for rec in self:
            rec.total_percentage = sum(rec.line_ids.mapped("percentage"))


class PropertyPaymentTermLine(models.Model):
    """A class for the model property payment term line to represent one
    installment of a property payment term"""

    _name = "property.payment.term.line"
    _description = "Property Payment Term Line"
    _order = "sequence, id"

    term_id = fields.Many2one(
        "property.payment.term",
        string="Payment Term",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(string="Label", help="Label of this installment")
    sequence = fields.Integer(string="Sequence", default=10)
    percentage = fields.Float(
        string="Percentage",
        required=True,
        help="Percentage of the total price due at this installment",
    )

    @api.constrains("percentage")
    def _check_percentage(self):
        for rec in self:
            if rec.percentage <= 0 or rec.percentage > 100:
                raise ValidationError("Percentage must be between 0 and 100.")
