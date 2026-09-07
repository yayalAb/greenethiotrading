# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Property(models.Model):
    """Extends property.property to link a property to a Site,
    Building and Floor"""

    _inherit = "property.property"

    site_id = fields.Many2one(
        "property.site", string="Site", help="The site this property belongs to"
    )
    building_id = fields.Many2one(
        "property.building",
        string="Building",
        domain="[('site_id', '=', site_id)]",
        help="The building this property belongs to",
    )
    floor_id = fields.Many2one(
        "property.floor",
        string="Floor",
        domain="[('building_id', '=', building_id)]",
        help="The floor this property is located on",
    )

    @api.onchange("site_id")
    def _onchange_site_id(self):
        """Reset the building and floor when the site changes"""
        if self.building_id.site_id != self.site_id:
            self.building_id = False
            self.floor_id = False

    @api.onchange("building_id")
    def _onchange_building_id(self):
        """Reset the floor when the building changes"""
        if self.floor_id.building_id != self.building_id:
            self.floor_id = False
