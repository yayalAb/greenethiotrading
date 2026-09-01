# -*- coding: utf-8 -*-
from odoo import api, models


class Website(models.Model):
    _inherit = "website"

    @api.model
    def _get_sync_menus(self):
        from odoo.addons.website_property_rental.hooks import (
            _sync_website_menus,
            _unlock_homepage_noupdate,
            _reset_homepage_customizations,
        )

        _unlock_homepage_noupdate(self.env)
        _reset_homepage_customizations(self.env)
        _sync_website_menus(self.env)
        return True
