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


class PropertyFloor(models.Model):
    """A class for the model property floor to represent
    the floor configuration for properties"""

    _name = "property.floor"
    _description = "Property Floor"
    _order = "sequence, floor_no, id"

    name = fields.Char(
        string="Floor Name",
        required=True,
        help="Name of the floor (e.g. Ground Floor, 1st Floor)",
    )
    code = fields.Char(
        string="Code", help="Reference code for the floor (e.g. GF, 1F, 2F)"
    )
    floor_no = fields.Integer(
        string="Floor Number",
        help="Sequence or numeric level of the floor (e.g. 0 for Ground, 1 for 1st Floor, -1 for Basement)",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Gives the sequence order when displaying floors",
    )
    active = fields.Boolean(string="Active", default=True)
    property_ids = fields.One2many(
        "property.property", "floor_id", string="Properties"
    )
    property_count = fields.Integer(
        string="Property Count", compute="_compute_property_count"
    )

    @api.depends("property_ids")
    def _compute_property_count(self):
        for rec in self:
            rec.property_count = len(rec.property_ids)

    def action_view_properties(self):
        self.ensure_one()
        return {
            "name": _("Properties"),
            "type": "ir.actions.act_window",
            "res_model": "property.property",
            "view_mode": "list,kanban,form",
            "domain": [("floor_id", "=", self.id)],
            "context": {"default_floor_id": self.id},
        }
