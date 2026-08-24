# -*- coding: utf-8 -*-
def _unlock_homepage_noupdate(env):
    env["ir.model.data"].search(
        [
            ("module", "=", "website_property_rental"),
            ("name", "=", "page_home"),
        ]
    ).write({"noupdate": False})


def _reset_homepage_customizations(env):
    """Drop website-editor copies so module XML is what visitors see."""
    View = env["ir.ui.view"].sudo()
    View.search(
        [
            (
                "key",
                "in",
                [
                    "website_property_rental.homepage_body",
                    "website_property_rental.page_home",
                    "website_property_rental.get_footer_custom",
                    "website.footer_custom",
                ],
            ),
            ("website_id", "!=", False),
        ]
    ).unlink()


def _set_website_branding(env):
    import base64
    from os.path import abspath, dirname, join

    img_path = join(dirname(abspath(__file__)), "static", "src", "img", "logo.png")
    vals = {"name": "TEMESGEN KEFEYALEW BUILDING RENT"}
    logo_b64 = False
    try:
        with open(img_path, "rb") as logo_file:
            logo_b64 = base64.b64encode(logo_file.read())
            vals["logo"] = logo_b64
            if "favicon" in env["website"]._fields:
                vals["favicon"] = logo_b64
    except OSError:
        pass
    websites = env["website"].sudo().search([])
    if websites:
        if "phone" in websites._fields:
            vals["phone"] = "+251 911 20 09 98"
        websites.write(vals)
    companies = env["res.company"].sudo().search([])
    if companies:
        company_vals = {
            "phone": "+251 911 20 09 98",
            "mobile": "+251 930 58 96 50",
        }
        if logo_b64:
            company_vals["logo"] = logo_b64
        companies.write(company_vals)


def _sync_website_menus(env):
    Data = env["ir.model.data"].sudo()
    Menu = env["website.menu"].sudo()
    updates = {
        "menu_get_for_rent": ("For Rent", "/#for-rent", 20),
        "menu_get_for_sale": ("For Sale", "/#for-sale", 25),
        "menu_get_services": ("Services", "/#services", 30),
        "menu_get_about": ("About Us", "/#about", 40),
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

    # Keep For Sale on the homepage, same pattern as For Rent.
    sale_menus = Menu.search(
        [
            "|",
            "|",
            ("name", "ilike", "For Sale"),
            ("url", "ilike", "type=sale"),
            ("url", "in", ["/#for-sale", "/property?type=sale"]),
        ]
    )
    if sale_menus:
        sale_menus.write({"name": "For Sale", "url": "/#for-sale", "sequence": 25})
    else:
        parent_menu = env.ref("website.main_menu", raise_if_not_found=False)
        if parent_menu:
            Menu.create(
                {
                    "name": "For Sale",
                    "url": "/#for-sale",
                    "parent_id": parent_menu.id,
                    "sequence": 25,
                }
            )

    Menu.search([("url", "in", ["/rentals", "/property"])]).unlink()

    _set_website_branding(env)

    # 1 Home, 2 For Rent, 3 For Sale, 4 Services, 5 About Us,
    # then Courses, Why Us, Jobs, Contact us
    parent = env.ref("website.main_menu", raise_if_not_found=False)
    if not parent:
        return
    by_name = {
        "home": 10,
        "for rent": 20,
        "for sale": 25,
        "services": 30,
        "about us": 40,
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
    _reset_homepage_customizations(env)
    _sync_website_menus(env)


def uninstall_hook(env):
    pass
