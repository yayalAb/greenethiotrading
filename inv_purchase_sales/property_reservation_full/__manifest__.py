# -*- coding: utf-8 -*-
{
    'name': "Property Reservation",
    'version': '18.0.1.0.0',
    'summary': """
        Property reservation management system with advanced features
        """,
    'description': """
        Real Estate Reservation System Features:
        * Property reservation management
        * Special discount handling
        * Reservation history tracking
        * Cancellation management
        * Extension and transfer features
    """,

    'category': 'Sales',

    'depends': [
        'base',
        'crm',
        'advanced_property_management',
    ],

    'data': [


        'security/reservation_security.xml',
        'security/ir.model.access.csv',
        'data/reservation_data.xml',
        'data/reservation_cron.xml',
        # Views
        'views/reservation_special_discount.xml',
        'views/reservation_config_views.xml',
        'views/property_reservation_views.xml',
        'views/reservation_extension_views.xml',
        'wizard/cancellation_reason_wizard_views.xml',
        'wizard/payment_cancel_reason.xml',
        'views/reservation_transfer_views.xml',
        # report
        'report/reservation_report.xml',
        'report/reservation_log_report.xml'




    ],
    'external_dependencies': {
        # Add all required Python libraries
        'python': ['pytesseract', 'cv2', 'PIL', 'numpy', 'pdf2image'],
    },
    'images': ['static/description/icon.png'],
    'demo': [

    ],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False,
}
