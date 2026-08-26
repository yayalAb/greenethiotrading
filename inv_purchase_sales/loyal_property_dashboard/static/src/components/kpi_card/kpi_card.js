/** @odoo-module **/

import { Component } from "@odoo/owl";

export class KpiCard extends Component {
    static template = "loyal_property_dashboard.KpiCard";
    static props = {
        name: String,
        value: { type: [Number, String], optional: true },
        percentage: { type: Number, optional: true },
        iconClass: { type: String, optional: true },
        bgColor: { type: String, optional: true },
        onClick: { type: Function, optional: true },
    };
    static defaultProps = {
        value: 0,
        percentage: 0,
        iconClass: "fa-arrow-up",
        bgColor: "#FFFFFF",
    };

    onCardClick() {
        if (typeof this.props.onClick === "function") {
            this.props.onClick();
        }
    }

    get displayPercentage() {
        const pct = Number(this.props.percentage);
        if (Number.isNaN(pct) || !Number.isFinite(pct)) {
            return "0.0";
        }
        return pct.toFixed(1);
    }
}
