# -*- coding: utf-8 -*-
def _unlock_homepage_noupdate(env):
    env["ir.model.data"].search(
        [
            ("module", "=", "website_property_rental"),
            ("name", "=", "page_home"),
        ]
    ).write({"noupdate": False})


def _sync_website_menus(env):
    Data = env["ir.model.data"].sudo()
    Menu = env["website.menu"].sudo()
    updates = {
        "menu_get_for_rent": ("For Rent", "/#for-rent", 20),
        "menu_get_for_sale": ("For Sale", "/#for-sale", 30),
        "menu_get_services": ("Services", "/#services", 40),
        "menu_get_about": ("About Us", "/#about", 50),
        "menu_get_why": ("Why Us", "/#why-us", 70),
        "menu_get_enquire": ("Enquire", "/#enquire", 85),
        "menu_get_contact": ("Contact", "/#contact", 95),
    }
    for xmlid, (name, url, sequence) in updates.items():
        rec = Data.search(
            [("module", "=", "website_property_rental"), ("name", "=", xmlid)], limit=1
        )
        if rec:
            rec.write({"noupdate": False})
            menu = env.ref(
                "website_property_rental.%s" % xmlid, raise_if_not_found=False
            )
            if menu:
                menu.write({"name": name, "url": url, "sequence": sequence})

    extra = env.ref(
        "advanced_property_management.menu_property_form", raise_if_not_found=False
    )
    if extra:
        extra.unlink()

    Menu.search([("url", "in", ["/rentals", "/property"])]).unlink()

    # 1 Home, 2 For Rent, 3 For Sale, 4 Services, 5 About Us,
    # then Courses, Why Us, Jobs, Contact us
    parent = env.ref("website.main_menu", raise_if_not_found=False)
    if not parent:
        return
    by_name = {
        "home": 10,
        "for rent": 20,
        "for sale": 30,
        "services": 40,
        "about us": 50,
        "courses": 60,
        "why us": 70,
        "jobs": 80,
        "enquire": 85,
        "contact us": 90,
        "contact": 95,
    }
    for menu in Menu.search([("parent_id", "=", parent.id)]):
        name = (menu.name or "").strip().lower()
        url = (menu.url or "").strip()
        if url in ("/", "") or name == "home":
            menu.sequence = 10
        elif name in by_name:
            menu.sequence = by_name[name]


def post_init_hook(env):
    _unlock_homepage_noupdate(env)
    _sync_website_menus(env)


def uninstall_hook(env):
    pass
