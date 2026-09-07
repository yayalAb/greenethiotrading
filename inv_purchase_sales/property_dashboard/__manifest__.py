# __manifest__.py
{
    'name': 'Property Dashboard',
    'version': '18.0.1.0.0',
    'category': 'Industries',
    'summary': 'Dashboard for the Property Management app',
    'description': """
        Property Dashboard
        ===================
        Gives property managers an overview of:
        - Property inventory by type and status
        - Sales performance and revenue
        - Rental contracts and monthly rent revenue
    """,
    'author': 'Yayal Abayneh',
    'website': 'https://www.yourwebsite.com',
    'depends': ['base', 'web', 'property_management'],
    'data': [
        'views/menu_items.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'property_dashboard/static/src/components/chart_renderer/chart_renderer.js',
            'property_dashboard/static/src/components/chart_renderer/chart_renderer.xml',
            'property_dashboard/static/src/components/dashboard_card/dashboard_card.js',
            'property_dashboard/static/src/components/dashboard_card/dashboard_card.xml',
            'property_dashboard/static/src/components/dashboard_main_view.xml',
            'property_dashboard/static/src/components/main_dashboard_js.js',
            'property_dashboard/static/src/css/custom_styles.css',
        ]
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
