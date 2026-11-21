# -*- coding: utf-8 -*-
{
    'name': 'Property Rental Summary of Sales Report',
    'version': '18.0.1.0.0',
    'category': 'Real Estate/Property Management',
    'summary': 'Summary of Sales / Rental Invoices Report matching Ethiopian Fiscal Year Matrix format',
    'description': """
        Generates Summary of Sales report for Property Rentals and their invoices:
        - Monthly columns across the selected Ethiopian fiscal year (Hamle -> Sene)
        - Shop Code, Customer Name, Location, Floor, Dates, Total Area, Price/Sqm, Monthly Payments Before/After VAT, Months Breakdown, Total, Remark
        - Available in both Excel (.xlsx) and printable PDF format
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'depends': ['base', 'property_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'reports/rental_sales_report_templates.xml',
        'reports/rental_sales_report_actions.xml',
        'wizards/property_rental_sales_report_wizard_views.xml',
        'views/rental_sales_report_line_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
