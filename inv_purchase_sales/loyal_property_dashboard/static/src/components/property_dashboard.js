/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { KpiCard } from "./kpi_card/kpi_card";
import { ChartRenderer } from "./chart_renderer/chart_renderer";

const EMPTY_CHART = {
    labels: [],
    datasets: [{ label: "", data: [], backgroundColor: [], borderColor: [] }],
};

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function formatLocalDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
}

function mondayOf(date) {
    const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const weekday = (d.getDay() + 6) % 7;
    d.setDate(d.getDate() - weekday);
    return d;
}

export class PropertyDashboard extends Component {
    static template = "loyal_property_dashboard.PropertyDashboard";
    static components = { KpiCard, ChartRenderer };
    static props = { ...standardActionServiceProps };

    setup() {
        this.state = useState({
            start_date: "",
            end_date: "",
            available_shop: { value: 0, percentage: 0 },
            ranted_shop: { value: 0, percentage: 0 },
            this_collection: { value: 0, percentage: 0 },
            expiring_contract: { value: 0, percentage: 0 },
            expecting_collection: { value: 0, percentage: 0 },
            expired_contract: { value: 0, percentage: 0 },
            collection_by_month: { ...EMPTY_CHART },
            shop_by_state: { ...EMPTY_CHART },
            revenue_week: { labels: WEEKDAYS, datasets: [] },
            collection_trend: { labels: [], datasets: [] },
            collection_summary: { last_month: "0.00", this_month: "0.00" },
        });

        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.onAvailableShop = () =>
            this._openList("property.property", "Available", [["state", "=", "available"], ...this._dateDomain("create_date")]);
        this.onClickRantedShop = () =>
            this._openList("property.property", "Rented Shops", [["state", "=", "rented"], ...this._dateDomain("create_date")]);
        this.onThisCollection = () => this._openList("account.move", "Invoices", this._invoiceDomain());
        this.onExpiringContract = () =>
            this._openList("property.rental", "Expiring Contract", [["state", "=", "in_contract"], ...this._dateDomain("start_date")]);
        this.onExpectingCollection = () =>
            this._openList("property.rental", "Expected Collection", [["state", "!=", "cancel"], ...this._dateDomain("start_date")]);
        this.onExpiredContracts = () =>
            this._openList("account.move", "Overdue Payments", [
                ...this._invoiceDomain(),
                ["payment_state", "in", ["not_paid", "partial"]],
            ]);

        this.onMonthlyCollectionChartClick = ({ label }) => {
            const monthIndex = MONTH_LABELS.indexOf(label);
            if (monthIndex < 0) {
                return;
            }
            const year = this.state.start_date
                ? Number(this.state.start_date.slice(0, 4))
                : new Date().getFullYear();
            const start = `${year}-${String(monthIndex + 1).padStart(2, "0")}-01`;
            const lastDay = new Date(year, monthIndex + 1, 0).getDate();
            const end = `${year}-${String(monthIndex + 1).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`;
            this._openList("account.move", `Collection - ${label}`, [
                ...this._invoiceDomain(),
                ["invoice_date", ">=", start],
                ["invoice_date", "<=", end],
            ]);
        };

        this.onShopByStateChartClick = ({ label }) => {
            const stateMap = {
                Draft: "draft",
                Available: "available",
                Rented: "rented",
                Sold: "sold",
            };
            const state = stateMap[label];
            if (state) {
                this._openList("property.property", `Shop - ${label}`, [
                    ["state", "=", state],
                    ...this._dateDomain("create_date"),
                ]);
            }
        };

        this.onRevenueChartClick = ({ label }) => {
            const idx = WEEKDAYS.indexOf(label);
            if (idx < 0) {
                return;
            }
            const day = mondayOf(new Date());
            day.setDate(day.getDate() + idx);
            this._openList("account.move", `Revenue - ${label}`, [
                ...this._invoiceDomain(),
                ["invoice_date", "=", formatLocalDate(day)],
            ]);
        };

        this.onCollectionTrendChartClick = ({ label }) => {
            const today = new Date();
            for (let offset = 5; offset >= 0; offset--) {
                const start = new Date(today.getFullYear(), today.getMonth() - offset, 1);
                if (MONTH_LABELS[start.getMonth()] !== label) {
                    continue;
                }
                const end = new Date(start.getFullYear(), start.getMonth() + 1, 0);
                this._openList("account.move", `Collection - ${label}`, [
                    ...this._invoiceDomain(),
                    ["invoice_date", ">=", formatLocalDate(start)],
                    ["invoice_date", "<=", formatLocalDate(end)],
                ]);
                return;
            }
        };

        onWillStart(async () => {
            await this.refreshData();
        });
    }

    _dateDomain(fieldName) {
        const domain = [];
        if (this.state.start_date) {
            domain.push([fieldName, ">=", this.state.start_date]);
        }
        if (this.state.end_date) {
            domain.push([fieldName, "<=", this.state.end_date]);
        }
        return domain;
    }

    _invoiceDomain() {
        return [
            ["move_type", "=", "out_invoice"],
            ["state", "!=", "cancel"],
            ...this._dateDomain("invoice_date"),
        ];
    }

    _openList(model, name, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: model,
            view_mode: "list,form",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            target: "current",
            domain: domain || [],
        });
    }

    async onStartDateChange(ev) {
        this.state.start_date = ev.target.value;
        await this.refreshData();
    }

    async onEndDateChange(ev) {
        this.state.end_date = ev.target.value;
        await this.refreshData();
    }

    async refreshData() {
        try {
            const data = await this.orm.call("loyal.property.dashboard", "get_dashboard_data", [], {
                date_start: this.state.start_date || false,
                date_end: this.state.end_date || false,
            });
            Object.assign(this.state, {
                available_shop: data.available_shop,
                ranted_shop: data.ranted_shop,
                this_collection: data.this_collection,
                expecting_collection: data.expecting_collection,
                expiring_contract: data.expiring_contract,
                expired_contract: data.expired_contract,
                collection_by_month: data.collection_by_month,
                shop_by_state: data.shop_by_state,
                revenue_week: data.revenue_week,
                collection_trend: data.collection_trend,
                collection_summary: data.collection_summary,
            });
        } catch (error) {
            console.error("Property dashboard load failed:", error);
            this.notification.add("Could not load dashboard totals. Upgrade the module and refresh.", {
                type: "danger",
            });
        }
    }
}

registry.category("actions").add("loyal_property_dashboard.property_dashboard", PropertyDashboard);
