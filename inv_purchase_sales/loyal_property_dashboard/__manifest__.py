# -*- coding: utf-8 -*-
{
    "name": "Property Dashboard",
    "version": "18.0.1.2.0",
    "category": "Industries",
    "summary": "Property Dashboard",
    "description": """
        Property Dashboard for Advanced Property Management.
    """,
    "author": "Yayal Abayneh",
    "website": "https://www.yourwebsite.com",
    "depends": ["base", "web", "account", "advanced_property_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/loyal_property_dashboard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "loyal_property_dashboard/static/src/components/chart_renderer/chart_renderer.js",
            "loyal_property_dashboard/static/src/components/chart_renderer/chart_renderer.xml",
            "loyal_property_dashboard/static/src/components/kpi_card/kpi_card.js",
            "loyal_property_dashboard/static/src/components/kpi_card/kpi_card.xml",
            "loyal_property_dashboard/static/src/components/property_dashboard.js",
            "loyal_property_dashboard/static/src/components/property_dashboard.xml",
            "loyal_property_dashboard/static/src/css/custom_styles.css",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
