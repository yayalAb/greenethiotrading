# -*- coding: utf-8 -*-
{
    'name': 'Green Ethio Trading Website',
    'version': '18.0.1.1.1',
    'summary': 'Public website for Greenethiotrading PLC — import & export',
    'description': """
        Branded Odoo website for Green Ethio Trading P.L.C.

        - Company name, phones, slogan, and Addis Ababa contact
        - Export: coffee, soybean, sesame, and oil seeds
        - Import: construction machinery, heavy trucks, cars, and metal
    """,
    'author': 'Green Ethio Trading P.L.C.',
    'website': 'https://greenethiotrading.com',
    'category': 'Website/Theme',
    'license': 'LGPL-3',
    'depends': ['website', 'mail'],
    'images': ['static/description/icon.png'],
    'data': [
        'data/unlock_homepage.xml',
        'data/website_config.xml',
        'views/header.xml',
        'views/homepage_body.xml',
        'views/layout.xml',
        'views/thanks.xml',
        'data/pages/home.xml',
        'data/menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_greenethio/static/src/css/get_website.css',
            'website_greenethio/static/src/css/get_brand.css',
            'website_greenethio/static/src/js/get_website.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
