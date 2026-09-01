# -*- coding: utf-8 -*-
{
    "name": "Website Property Rental",
    "version": "18.0.1.5.1",
    "category": "Website/Website",
    "summary": "Public building rental website for Advanced Property Management",
    "description": """
Public website for Temesgen Kefyalew Building Rent.
Visitors can browse For Rent listings, view galleries,
and submit rental enquiries.
    """,
    "author": "Temesgen Kefyalew Building Rent",
    "depends": ["website", "mail", "advanced_property_management"],
    "data": [
        "security/ir.model.access.csv",
        "data/unlock_homepage.xml",
        "views/layout.xml",
        "views/property_card.xml",
        "views/homepage_body.xml",
        "views/website_templates.xml",
        "views/thanks.xml",
        "views/rental_request_views.xml",
        "data/pages/home.xml",
        "data/website_menu.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_property_rental/static/src/css/kad_website.css",
            "website_property_rental/static/src/css/get_website.css",
            "website_property_rental/static/src/scss/rental_website.scss",
            "website_property_rental/static/src/js/kad_website.js",
            "website_property_rental/static/src/js/rental_website.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
