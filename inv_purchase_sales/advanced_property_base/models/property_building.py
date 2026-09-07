# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyBuilding(models.Model):
    """A class for the model property building to represent a building
    that belongs to a site and groups a number of floors"""

    _name = "property.building"
    _description = "Property Building"

    name = fields.Char(string="Name", required=True, help="Name of the building")
    code = fields.Char(string="Code", help="Reference code for the building")
    site_id = fields.Many2one(
        "property.site",
        string="Site",
        required=True,
        ondelete="restrict",
        help="The site this building belongs to",
    )
    company_id = fields.Many2one(
        related="site_id.company_id", string="Company", store=True
    )
    total_floors = fields.Integer(
        string="Total Floors", help="Total number of floors in the building"
    )
    floor_ids = fields.One2many(
        "property.floor", "building_id", string="Floors"
    )
    floor_count = fields.Integer(
        string="Floor Count", compute="_compute_floor_count"
    )
    active = fields.Boolean(string="Active", default=True)

    @api.depends("floor_ids")
    def _compute_floor_count(self):
        for rec in self:
            rec.floor_count = len(rec.floor_ids)
