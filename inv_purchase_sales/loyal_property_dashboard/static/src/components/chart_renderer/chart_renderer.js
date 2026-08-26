/** @odoo-module **/

import { Component, onWillStart, useRef, onMounted, onPatched, onWillUnmount } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class ChartRenderer extends Component {
    static template = "loyal_property_dashboard.ChartRenderer";
    static props = {
        type: String,
        title: { type: String, optional: true },
        y_title: { type: String, optional: true },
        x_title: { type: String, optional: true },
        data: Object,
        onChartClick: { type: Function, optional: true },
        variant: { type: String, optional: true },
        showLegend: { type: Boolean, optional: true },
    };
    static defaultProps = {
        variant: "default",
        showLegend: true,
    };

    setup() {
        this.chartRef = useRef("chart");
        this.chartInstance = null;

        onWillStart(async () => {
            if (!window.Chart) {
                try {
                    await loadJS("/loyal_property_dashboard/static/lib/chart.umd.min.js");
                } catch (_error) {
                    await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
                }
            }
        });

        onMounted(() => this.renderChart());
        onPatched(() => this.renderChart());
        onWillUnmount(() => this.destroyChart());
    }

    destroyChart() {
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
    }

    _chartOptions() {
        const isPie = ["pie", "doughnut"].includes(this.props.type);
        const insight = this.props.variant === "insight";
        const showLegend = this.props.showLegend !== false;

        if (insight) {
            return {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: false },
                    legend: {
                        display: showLegend,
                        position: "bottom",
                        labels: {
                            usePointStyle: true,
                            pointStyle: "circle",
                            boxWidth: 8,
                            padding: 16,
                            color: "#425166",
                        },
                    },
                },
                scales: isPie
                    ? {}
                    : {
                          x: { grid: { display: false }, ticks: { color: "#94a3b8" } },
                          y: {
                              beginAtZero: true,
                              grid: { color: "rgba(148,163,184,0.18)" },
                              ticks: { color: "#94a3b8" },
                          },
                      },
                onClick: (event, elements) => {
                    if (elements.length > 0 && typeof this.props.onChartClick === "function") {
                        const index = elements[0].index;
                        const label = this.props.data.labels[index];
                        this.props.onChartClick({ chartType: this.props.type, label });
                    }
                },
            };
        }

        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: !!this.props.title, text: this.props.title || "" },
                legend: { display: showLegend },
            },
            scales: isPie
                ? {}
                : {
                      y: {
                          beginAtZero: true,
                          title: { display: true, text: this.props.y_title || "" },
                      },
                      x: {
                          title: { display: true, text: this.props.x_title || "" },
                      },
                  },
            onClick: (event, elements) => {
                if (elements.length > 0 && typeof this.props.onChartClick === "function") {
                    const index = elements[0].index;
                    const label = this.props.data.labels[index];
                    this.props.onChartClick({ chartType: this.props.type, label });
                }
            },
        };
    }

    renderChart() {
        this.destroyChart();
        if (!this.chartRef.el || !window.Chart) {
            return;
        }
        if (!this.props.data?.labels?.length || !this.props.data?.datasets?.length) {
            return;
        }

        const ctx = this.chartRef.el.getContext("2d");
        this.chartInstance = new window.Chart(ctx, {
            type: this.props.type,
            data: this.props.data,
            options: this._chartOptions(),
        });
    }
}
