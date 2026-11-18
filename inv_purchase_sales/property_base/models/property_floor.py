# -*- coding: utf-8 -*-
from odoo import fields, models


class PropertyFloor(models.Model):
    """Extends property.floor to link floors to buildings and sites"""

    _inherit = "property.floor"

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
