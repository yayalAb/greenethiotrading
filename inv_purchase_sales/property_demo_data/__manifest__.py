# -*- coding: utf-8 -*-
{
    'name': 'Property & Reservation Demo Data',
    'version': '18.0.1.0.0',
    'category': 'Industries',
    'summary': 'Demo/sample data for Property Management and Property Reservation',
    'description': """
        Property & Reservation Demo Data
        =================================
        Seeds a realistic sample dataset so the Property Dashboard and the
        reservation workflow can be explored without manual data entry:
        - Partners (landlords, buyers, tenants, reservation customers)
        - A payment term and reservation configurations
        - Properties across every type, status and sale/rent mode
        - Confirmed sales, active rentals
        - Reservations covering requested, reserved, sold, expired and
          cancelled outcomes

        This module has no models of its own and only loads demo data;
        uninstall it any time to remove the sample records it created.
    """,
    'author': 'Yayal Abayneh',
    'depends': ['property_management', 'property_reservation_full'],
    'data': [],
    'demo': [
        'demo/partners_demo.xml',
        'demo/reservation_config_demo.xml',
        'demo/property_demo.xml',
        'demo/sale_rental_demo.xml',
        'demo/reservation_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
