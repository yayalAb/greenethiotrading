/** @odoo-module */

import { Component } from "@odoo/owl"

export class DashboardCard extends Component {
    static template = "property_dashboard.DashboardCard"
    static props = {
        name: String,
        value: [Number, String],
        uom: { type: String, optional: true },
        iconClass: { type: String, optional: true },
        accent: { type: String, optional: true },
        badgeText: { type: String, optional: true },
        badgeVariant: { type: String, optional: true },
        subtitle: { type: String, optional: true },
        onClick: Function,
    }
}
