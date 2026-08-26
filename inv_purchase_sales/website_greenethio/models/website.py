# -*- coding: utf-8 -*-
import base64
from pathlib import Path

from odoo import api, models


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def _get_sync_menus(self):
        from odoo.addons.website_greenethio.hooks import _sync_website_menus, _unlock_homepage_noupdate
        _unlock_homepage_noupdate(self.env)
        _sync_website_menus(self.env)
        return True

    @api.model
    def _website_greenethio_apply_branding(self):
        """Apply Green Ethio Trading logo and website name on install/upgrade."""
        logo_path = Path(__file__).resolve().parents[1] / 'static' / 'src' / 'img' / 'logo.png'
        logo_b64 = base64.b64encode(logo_path.read_bytes()) if logo_path.is_file() else False

        self.env['ir.model.data'].search([
            ('module', '=', 'website'),
            ('name', '=', 'default_website'),
        ]).write({'noupdate': False})

        website = self.env.ref('website.default_website', raise_if_not_found=False)
        if not website:
            website = self.search([], limit=1)
        if not website:
            return

        values = {
            'name': 'Green Ethio Trading P.L.C.',
        }
        if logo_b64:
            values['logo'] = logo_b64
            if 'favicon' in website._fields:
                values['favicon'] = logo_b64
        website.sudo().write(values)

        company = self.env.company.sudo()
        company_vals = {
            'phone': '+251 928 399 539',
            'mobile': '+251 930 589 650',
        }
        if not company.email:
            company_vals['email'] = 'info@greenethiotrading.com'
        if logo_b64:
            company_vals['logo'] = logo_b64
        company.write(company_vals)

        default_home = self.env.ref('website.homepage_page', raise_if_not_found=False)
        if default_home:
            default_home.sudo().write({'is_published': False})

        self.env['ir.model.data'].search([
            ('module', '=', 'website_greenethio'),
            ('name', '=', 'page_home'),
        ]).write({'noupdate': False})
