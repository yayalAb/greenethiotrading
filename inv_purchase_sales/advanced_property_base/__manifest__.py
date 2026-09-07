# -*- coding: utf-8 -*-
{
    'name': "Advanced Property Base",
    'version': '18.0.1.0.0',
    'category': 'Industries',
    'summary': """Adds Site, Building and Floor structure to properties""",
    'description': """This module introduces Site, Building and Floor models
    and links each Property to a Site, Building and Floor.""",
    'author': "Niyat Consultancy",
    'company': 'Niyat Consultancy',
    'maintainer': 'Niyat Consultancy',
    'website': 'https://niyatconsultancy.com',
    'depends': ['advanced_property_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/property_floor_views.xml',
        'views/property_building_views.xml',
        'views/property_site_views.xml',
        'views/property_property_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
