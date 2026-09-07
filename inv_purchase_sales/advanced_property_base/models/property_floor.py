# -*- coding: utf-8 -*-
from odoo import fields, models


class PropertyFloor(models.Model):
    """A class for the model property floor to represent a floor
    that belongs to a building"""

    _name = "property.floor"
    _description = "Property Floor"
    _order = "floor_no"

    name = fields.Char(string="Name", required=True, help="Name of the floor")
    code = fields.Char(string="Code", help="Reference code for the floor")
    floor_no = fields.Integer(string="Floor Number", help="Sequence number of the floor")
    building_id = fields.Many2one(
        "property.building",
        string="Building",
        required=True,
        ondelete="restrict",
        help="The building this floor belongs to",
    )
    site_id = fields.Many2one(
        related="building_id.site_id", string="Site", store=True
    )
    company_id = fields.Many2one(
        related="building_id.company_id", string="Company", store=True
    )
    active = fields.Boolean(string="Active", default=True)
