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


class PropertyLocation(models.Model):
    """A class for the model property location to represent
    preconfigured locations and their address details"""

    _name = "property.location"
    _description = "Property Location"
    _order = "name"

    name = fields.Char(
        string="Location Name",
        required=True,
        help="Name of the location (e.g. Bole Medhanialem, Kazanchis)",
    )
    code = fields.Char(string="Code", help="Reference code for the location")
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
        "res.country",
        string="Country",
        ondelete="restrict",
        help="The name of the country",
    )
    latitude = fields.Float(
        string="Latitude",
        digits=(16, 5),
        help="The latitude of where the location is situated",
    )
    longitude = fields.Float(
        string="Longitude",
        digits=(16, 5),
        help="The longitude of where the location is situated",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(string="Active", default=True)
    property_ids = fields.One2many(
        "property.property", "location_id", string="Properties"
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
            "domain": [("location_id", "=", self.id)],
            "context": {"default_location_id": self.id},
        }

    @api.model
    def _geo_localize(self, street="", zip="", city="", state="", country=""):
        """Generate Latitude and Longitude based on address"""
        geo_obj = self.env["base.geocoder"]
        search = geo_obj.geo_query_address(
            street=street, zip=zip, city=city, state=state, country=country
        )
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(
                city=city, state=state, country=country
            )
            result = geo_obj.geo_find(search, force_country=country)
        return result

    @api.onchange("street", "zip", "city", "state_id", "country_id")
    def _onchange_address(self):
        """Update Latitude and Longitude on address change"""
        for rec in self.with_context(lang="en_US"):
            result = rec._geo_localize(
                rec.street,
                rec.zip,
                rec.city,
                rec.state_id.name if rec.state_id else "",
                rec.country_id.name if rec.country_id else "",
            )
            if result:
                rec.latitude = result[0]
                rec.longitude = result[1]
