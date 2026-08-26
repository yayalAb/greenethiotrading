# -*- coding: utf-8 -*-
def _unlock_homepage_noupdate(env):
    """Allow homepage XML to refresh on every module upgrade."""
    env['ir.model.data'].search([
        ('module', '=', 'website_greenethio'),
        ('name', '=', 'page_home'),
    ]).write({'noupdate': False})


def _sync_website_menus(env):
    """Keep public nav labels aligned after upgrades."""
    Menu = env['website.menu'].sudo()
    Data = env['ir.model.data'].sudo()
    updates = {
        'menu_get_about': ('About Us', '/#about', 10),
        'menu_get_services': ('Services', '/#services', 20),
        'menu_get_exports': ('Exports', '/#exports', 30),
        'menu_get_imports': ('Imports', '/#imports', 40),
        'menu_get_why': ('Why GET', '/#why-us', 50),
        'menu_get_contact': ('Contact', '/#contact', 80),
    }
    for xmlid, (name, url, sequence) in updates.items():
        rec = Data.search([('module', '=', 'website_greenethio'), ('name', '=', xmlid)], limit=1)
        if rec:
            rec.write({'noupdate': False})
            menu = env.ref(f'website_greenethio.{xmlid}', raise_if_not_found=False)
            if menu:
                menu.write({'name': name, 'url': url, 'sequence': sequence})

    for xmlid in ('menu_get_markets', 'menu_get_quote'):
        menu = env.ref(f'website_greenethio.{xmlid}', raise_if_not_found=False)
        if menu:
            menu.unlink()
    Menu.search([
        '|',
        ('name', 'in', ['Global Markets', 'Request Quote']),
        ('url', 'in', ['/#markets', '/#quote']),
    ]).unlink()


def post_init_hook(env):
    _unlock_homepage_noupdate(env)
    _sync_website_menus(env)


def uninstall_hook(env):
    pass
