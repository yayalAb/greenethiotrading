# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertySite(models.Model):
    """A class for the model property site to represent a site that
    groups a number of buildings"""

    _name = "property.site"
    _description = "Property Site"

    name = fields.Char(string="Name", required=True, help="Name of the site")
    code = fields.Char(string="Code", help="Reference code for the site")
    street = fields.Char(string="Street", help="The street name")
    street2 = fields.Char(string="Street2", help="The street2 name")
    zip = fields.Char(string="Zip", help="Zip code for the place")
    city = fields.Char(string="City", help="The name of the city")
    state_id = fields.Many2one(
        "res.country.state",
        string="State",
        domain="[('country_id', '=?', country_id)]",
        help="The name of the state",
    )
    country_id = fields.Many2one(
        "res.country", string="Country", help="The name of the country"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    building_ids = fields.One2many(
        "property.building", "site_id", string="Buildings"
    )
    building_count = fields.Integer(
        string="Building Count", compute="_compute_building_count"
    )
    active = fields.Boolean(string="Active", default=True)

    @api.depends("building_ids")
    def _compute_building_count(self):
        for rec in self:
            rec.building_count = len(rec.building_ids)
