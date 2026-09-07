/** @odoo-module **/

import { Component, onWillStart, useRef, onMounted, onPatched, onWillUnmount } from "@odoo/owl"
import { loadJS } from "@web/core/assets"

export class ChartRenderer extends Component {
    static template = "property_dashboard.ChartRenderer"

    setup() {
        this.chartRef = useRef("chart")
        this.chartInstance = null

        onWillStart(async () => {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js")
        })

        onMounted(() => this.renderChart())
        onPatched(() => {
            if (!this.chartRef.el) {
                return
            }
            if (this.chartInstance) {
                this.updateChart()
            } else {
                this.renderChart()
            }
        })
        onWillUnmount(() => this.destroyChart())
    }

    get hasData() {
        const data = this.props.data
        return Boolean(data && data.labels && data.labels.length && data.datasets && data.datasets[0])
    }

    destroyChart() {
        if (this.chartInstance) {
            this.chartInstance.destroy()
            this.chartInstance = null
        }
    }

    renderChart() {
        if (!this.chartRef.el || !window.Chart || !this.hasData) {
            return
        }
        this.destroyChart()

        const ctx = this.chartRef.el.getContext("2d")
        this.chartInstance = new Chart(ctx, {
            type: this.props.type,
            data: this.props.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: false, text: this.props.title },
                    legend: {
                        display: this.props.legend !== false,
                        labels: { boxWidth: 12, padding: 14, font: { size: 12 } },
                    },
                },
                scales: this.props.type === "pie" || this.props.type === "doughnut" ? {} : {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: this.props.y_title },
                    },
                    x: {
                        title: { display: true, text: this.props.x_title },
                    },
                },
                onClick: (event, elements) => {
                    if (elements.length > 0 && typeof this.props.onChartClick === "function") {
                        const element = elements[0]
                        const index = element.index
                        const datasetIndex = element.datasetIndex
                        const label = this.props.data.labels[index]
                        const datasetLabel = this.props.datasetLabels && this.props.datasetLabels[datasetIndex]
                            ? this.props.datasetLabels[datasetIndex]
                            : this.props.data.datasets[datasetIndex].label
                        this.props.onChartClick({ chartType: this.props.type, label, datasetLabel })
                    }
                },
            },
        })
    }

    updateChart() {
        if (!this.chartInstance) {
            return
        }
        if (!this.hasData) {
            this.destroyChart()
            return
        }
        this.chartInstance.data = this.props.data
        this.chartInstance.update()
    }
}
