# -*- coding: utf-8 -*-
{
    "name": "Property Dashboard",
    "version": "18.0.1.0.0",
    "category": "Industries",
    "summary": "Rent, sales, collection and contract dashboard for Property Management",
    "description": """
Analytics dashboard for Advanced Property Management.
Shows rent collection, property sales, active contracts,
payment collection, and enquiry trends.
    """,
    "author": "Temesgen Kefyalew Building Rent",
    "depends": ["web", "advanced_property_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/property_dashboard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "property_dashboard/static/src/dashboard/property_dashboard.css",
            "property_dashboard/static/src/dashboard/property_dashboard.xml",
            "property_dashboard/static/src/dashboard/property_dashboard.js",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
