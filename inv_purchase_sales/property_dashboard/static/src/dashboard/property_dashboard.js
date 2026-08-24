/** @odoo-module **/

import { Component, onMounted, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";
import { loadJS } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const COLORS = {
    blue: "#0095FF",
    green: "#00E096",
    purple: "#884DFF",
    red: "#EF4444",
    yellow: "#FFCF00",
};

export class PropertyDashboard extends Component {
    static template = "property_dashboard.PropertyDashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            data: {
                kpis: [],
                collection: {},
                charts: {},
                top_properties: [],
                countries: [],
                summary: {},
            },
        });
        this.insightRef = useRef("insightChart");
        this.revenueRef = useRef("revenueChart");
        this.satisfactionRef = useRef("satisfactionChart");
        this.targetRef = useRef("targetChart");
        this.volumeRef = useRef("volumeChart");
        this.charts = {};

        onWillStart(async () => {
            if (!window.Chart) {
                try {
                    await loadJS("/property_dashboard/static/lib/chart.umd.min.js");
                } catch (_error) {
                    await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
                }
            }
            this.state.data = await this.orm.call("property.dashboard", "get_dashboard_data", []);
            this.state.loading = false;
        });
        onMounted(() => this.renderCharts());
        onWillUnmount(() => this.destroyCharts());
    }

    destroyCharts() {
        Object.values(this.charts).forEach((chart) => chart.destroy());
        this.charts = {};
    }

    baseOptions(legendBottom = true) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: legendBottom,
                    position: "bottom",
                    labels: { usePointStyle: true, pointStyle: "circle", boxWidth: 8, padding: 16 },
                },
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: "#94a3b8" } },
                y: { beginAtZero: true, grid: { color: "rgba(148,163,184,0.18)" }, ticks: { color: "#94a3b8" } },
            },
        };
    }

    draw(key, ref, config) {
        if (!ref.el || !window.Chart) {
            return;
        }
        if (this.charts[key]) {
            this.charts[key].destroy();
        }
        this.charts[key] = new window.Chart(ref.el, config);
    }

    renderCharts() {
        const charts = this.state.data.charts || {};
        const months = charts.months || [];

        this.draw("insight", this.insightRef, {
            type: "line",
            data: {
                labels: months,
                datasets: [
                    {
                        label: "Rent Collected",
                        data: charts.rent_trend || [],
                        borderColor: COLORS.purple,
                        backgroundColor: COLORS.purple,
                        tension: 0.4,
                        pointRadius: 0,
                        borderWidth: 3,
                    },
                    {
                        label: "Property Sales",
                        data: charts.sale_trend || [],
                        borderColor: COLORS.red,
                        backgroundColor: COLORS.red,
                        tension: 0.4,
                        pointRadius: 0,
                        borderWidth: 3,
                    },
                    {
                        label: "Enquiries",
                        data: charts.enquiry_trend || [],
                        borderColor: COLORS.green,
                        backgroundColor: COLORS.green,
                        tension: 0.4,
                        pointRadius: 0,
                        borderWidth: 3,
                    },
                ],
            },
            options: this.baseOptions(),
        });

        this.draw("revenue", this.revenueRef, {
            type: "bar",
            data: {
                labels: charts.weekdays || [],
                datasets: [
                    {
                        label: "Rental Income",
                        data: charts.rent_week || [],
                        backgroundColor: COLORS.blue,
                        borderRadius: 6,
                        barPercentage: 0.55,
                    },
                    {
                        label: "Sales Income",
                        data: charts.sale_week || [],
                        backgroundColor: COLORS.green,
                        borderRadius: 6,
                        barPercentage: 0.55,
                    },
                ],
            },
            options: this.baseOptions(),
        });

        this.draw("satisfaction", this.satisfactionRef, {
            type: "line",
            data: {
                labels: charts.target_months || months.slice(-6),
                datasets: [
                    {
                        label: "Billed",
                        data: charts.target || [],
                        borderColor: COLORS.blue,
                        backgroundColor: "rgba(0,149,255,0.18)",
                        fill: true,
                        tension: 0.45,
                        pointRadius: 0,
                    },
                    {
                        label: "Collected",
                        data: charts.reality || [],
                        borderColor: COLORS.green,
                        backgroundColor: "rgba(0,224,150,0.18)",
                        fill: true,
                        tension: 0.45,
                        pointRadius: 0,
                    },
                ],
            },
            options: { ...this.baseOptions(false), plugins: { legend: { display: false } } },
        });

        this.draw("target", this.targetRef, {
            type: "bar",
            data: {
                labels: charts.target_months || [],
                datasets: [
                    {
                        label: "Reality",
                        data: charts.reality || [],
                        backgroundColor: COLORS.green,
                        borderRadius: 6,
                        barPercentage: 0.55,
                    },
                    {
                        label: "Target",
                        data: charts.target || [],
                        backgroundColor: COLORS.yellow,
                        borderRadius: 6,
                        barPercentage: 0.55,
                    },
                ],
            },
            options: { ...this.baseOptions(false), plugins: { legend: { display: false } } },
        });

        this.draw("volume", this.volumeRef, {
            type: "bar",
            data: {
                labels: charts.weekdays || [],
                datasets: [
                    {
                        label: "Volume",
                        data: charts.invoice_week || [],
                        backgroundColor: COLORS.blue,
                        borderRadius: 4,
                    },
                    {
                        label: "Services",
                        data: charts.contract_week || [],
                        backgroundColor: COLORS.green,
                        borderRadius: 4,
                    },
                ],
            },
            options: {
                ...this.baseOptions(),
                scales: {
                    x: { stacked: true, grid: { display: false }, ticks: { color: "#94a3b8" } },
                    y: { stacked: true, beginAtZero: true, grid: { color: "rgba(148,163,184,0.18)" }, ticks: { color: "#94a3b8" } },
                },
            },
        });
    }

    async onOpen(kind) {
        const action = await this.orm.call("property.dashboard", "action_open", [kind]);
        if (action && action.type !== "ir.actions.act_window_close") {
            this.action.doAction(action);
        }
    }

    onExport() {
        const data = this.state.data;
        const lines = [
            "Metric,Value",
            ...data.kpis.map((kpi) => `${kpi.label},${kpi.value}`),
            `Outstanding,${data.collection.outstanding || ""}`,
            `Overdue,${data.collection.overdue || 0}`,
            `Collection rate,${data.collection.rate || 0}%`,
            "",
            "Rank,Property,Location,Share",
            ...data.top_properties.map((row) => `${row.index},${row.name},${row.city},${row.popularity}%`),
        ];
        const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "property_dashboard.csv";
        link.click();
        URL.revokeObjectURL(url);
    }
}

registry.category("actions").add("property_dashboard", PropertyDashboard);
