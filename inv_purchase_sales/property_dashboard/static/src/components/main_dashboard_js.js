/** @odoo-module **/

import { Component, onMounted, onWillStart, useRef, useState } from "@odoo/owl"
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
import { DashboardCard } from "./dashboard_card/dashboard_card"
import { ChartRenderer } from "./chart_renderer/chart_renderer"

const PROPERTY_TYPE_LABELS = {
    land: "Land",
    residential: "Residential",
    commercial: "Commercial",
    industry: "Industry",
}
const PROPERTY_STATE_LABELS = {
    draft: "Draft",
    available: "Available",
    reserved: "Reserved",
    rented: "Rented",
    pending_sales: "Pending Sale",
    sold: "Sold",
}
const RENTAL_STATE_LABELS = {
    draft: "Draft",
    in_contract: "In Contract",
    expired: "Expired",
    cancel: "Cancelled",
}
const RESERVATION_STATE_LABELS = {
    draft: "Draft",
    requested: "Requested",
    reserved: "Reserved",
    pending_sales: "Pending Sale",
    sold: "Sold",
    expired: "Expired",
    canceled: "Cancelled",
}
const RESERVATION_ACTIVE_STATES = ["requested", "reserved"]
const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
const PALETTE = ["#023384", "#fe5a34", "#22c55e", "#f59e0b", "#5576AD", "#8b5cf6", "#06b6d4", "#ec4899"]
const DAY_MS = 24 * 60 * 60 * 1000

function emptyChart() {
    return { labels: [], datasets: [{ label: "", data: [], backgroundColor: [], borderColor: [], borderWidth: 1 }] }
}

function toDateStr(date) {
    return date.toISOString().split("T")[0]
}

function startOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth(), 1)
}

function startOfWeek(date) {
    const result = new Date(date)
    const day = (date.getDay() + 6) % 7 // Monday = 0
    result.setDate(date.getDate() - day)
    return result
}

function startOfYear(date) {
    return new Date(date.getFullYear(), 0, 1)
}

function computeDateRange(preset) {
    const today = new Date()
    let from
    if (preset === "wtd") {
        from = startOfWeek(today)
    } else if (preset === "mtd") {
        from = startOfMonth(today)
    } else if (preset === "ytd") {
        from = startOfYear(today)
    } else {
        from = today
    }
    return { from: toDateStr(from), to: toDateStr(today) }
}

function occupancyColor(percent) {
    if (percent >= 70) {
        return "#22c55e"
    }
    if (percent >= 40) {
        return "#f59e0b"
    }
    return "#ef4444"
}

function clampPercent(value) {
    return Math.max(0, Math.min(100, Math.round(value)))
}

function csvCell(value) {
    return `"${String(value).replace(/"/g, '""')}"`
}

export class MainDashboard extends Component {
    setup() {
        const defaultRange = computeDateRange("mtd")
        this.state = useState({
            today_label: new Date().toLocaleDateString(undefined, {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
            }),
            filters: { propertyType: "", saleRent: "", readiness: "" },
            datePreset: "mtd",
            dateFrom: defaultRange.from,
            dateTo: defaultRange.to,

            total_properties: { value: 0, current_month_count: 0 },
            available_properties: { value: 0 },
            reserved_properties: { value: 0 },
            sold_properties: { value: 0 },
            rented_properties: { value: 0 },
            total_sales_value: { value: 0, current_month_count: 0 },
            monthly_rent_revenue: { value: 0, current_month_count: 0 },
            active_reservations: { value: 0, current_month_count: 0 },
            reservation_pipeline_value: { value: 0 },
            reservations_expiring: { value: 0 },
            reservations_insufficient: { value: 0 },
            reservations_sold: { value: 0 },
            occupancy: { percent: 0, color: "#cbd5e1" },
            currency_symbol: "",

            properties_by_type: emptyChart(),
            properties_by_status: emptyChart(),
            sales_by_month: emptyChart(),
            rentals_by_status: emptyChart(),
            reservations_by_status: emptyChart(),
            weekly_activity: emptyChart(),

            reservation_pipeline: [],
            alerts: [],
        })

        this.orm = useService("orm")
        this.action = useService("action")

        this.dashboardRootRef = useRef("dashboardRoot")
        this.dashboardInnerRef = useRef("dashboardInner")
        onMounted(() => {
            const root = this.dashboardRootRef.el
            const pane = this.dashboardInnerRef.el
            if (!root || !pane) {
                return
            }
            root.style.setProperty("display", "flex", "important")
            root.style.setProperty("flex-direction", "column", "important")
            root.style.setProperty("height", "100%", "important")
            root.style.setProperty("max-height", "100%", "important")
            root.style.setProperty("min-height", "0", "important")
            root.style.setProperty("overflow", "hidden", "important")

            pane.style.setProperty("flex", "1 1 auto", "important")
            pane.style.setProperty("min-height", "0", "important")
            pane.style.setProperty("overflow-y", "auto", "important")
            pane.style.setProperty("overflow-x", "hidden", "important")
            pane.style.setProperty("-webkit-overflow-scrolling", "touch")
        })

        onWillStart(async () => {
            await this.loadCurrencySymbol()
            await this.refreshData()
        })

        this.onTotalPropertiesClick = () => this.openProperties("All Properties", [])
        this.onAvailablePropertiesClick = () => this.openProperties("Available Properties", [["state", "=", "available"]])
        this.onReservedPropertiesClick = () => this.openProperties("Reserved Properties", [["state", "=", "reserved"]])
        this.onSoldPropertiesClick = () => this.openProperties("Sold Properties", [["state", "=", "sold"]])
        this.onRentedPropertiesClick = () => this.openProperties("Rented Properties", [["state", "=", "rented"]])
        this.onSalesClick = () => this.openWindow("Confirmed Sales", "property.sale", this.buildSaleDomain())
        this.onRentalsClick = () => this.openWindow("Active Rentals", "property.rental", this.buildRentalDomain())

        this.onActiveReservationsClick = () =>
            this.openWindow("Active Reservations", "property.reservation", [
                ...this.buildReservationDomain(),
                ["status", "in", RESERVATION_ACTIVE_STATES],
            ])
        this.onExpiringReservationsClick = () => {
            const cutoff = new Date(Date.now() + 7 * DAY_MS).toISOString()
            this.openWindow("Expiring Soon", "property.reservation", [
                ...this.buildReservationDomain(),
                ["status", "in", RESERVATION_ACTIVE_STATES],
                ["expire_date", "<=", cutoff],
            ])
        }
        this.onInsufficientReservationsClick = () =>
            this.openWindow("Awaiting Payment", "property.reservation", [
                ...this.buildReservationDomain(),
                ["is_sufficient", "=", false],
                ["status", "in", ["draft", "requested"]],
            ])
        this.onConvertedReservationsClick = () =>
            this.openWindow("Converted to Sale", "property.reservation", [...this.buildReservationDomain(), ["status", "=", "sold"]])
        this.onPipelineRowClick = (row) => this.openReservationForm(row.id)

        this.onPropertiesByTypeClick = ({ label }) => {
            const type = Object.keys(PROPERTY_TYPE_LABELS).find((key) => PROPERTY_TYPE_LABELS[key] === label)
            this.openProperties(label, type ? [["property_type", "=", type]] : [])
        }
        this.onPropertiesByStatusClick = ({ label }) => {
            const state = Object.keys(PROPERTY_STATE_LABELS).find((key) => PROPERTY_STATE_LABELS[key] === label)
            this.openProperties(label, state ? [["state", "=", state]] : [])
        }
        this.onRentalsByStatusClick = ({ label }) => {
            const state = Object.keys(RENTAL_STATE_LABELS).find((key) => RENTAL_STATE_LABELS[key] === label)
            this.openWindow(label, "property.rental", state ? [...this.buildRentalBaseDomain(), ["state", "=", state]] : this.buildRentalBaseDomain())
        }
        this.onReservationsByStatusClick = ({ label }) => {
            const status = Object.keys(RESERVATION_STATE_LABELS).find((key) => RESERVATION_STATE_LABELS[key] === label)
            this.openWindow(label, "property.reservation", status ? [...this.buildReservationDomain(), ["status", "=", status]] : this.buildReservationDomain())
        }
        this.onSalesByMonthClick = ({ label }) => {
            const monthIndex = MONTH_LABELS.indexOf(label.split(" ")[0])
            const year = parseInt(label.split(" ")[1], 10)
            if (monthIndex === -1 || isNaN(year)) {
                return
            }
            const start = new Date(year, monthIndex, 1).toISOString().split("T")[0]
            const end = new Date(year, monthIndex + 1, 0).toISOString().split("T")[0]
            this.openWindow(`Sales - ${label}`, "property.sale", [
                ...this.buildPropertyScopedDomain("property_id"),
                ["state", "=", "confirm"],
                ["order_date", ">=", start],
                ["order_date", "<=", end],
            ])
        }

        this.onFilterChange = (key, value) => {
            this.state.filters[key] = value
            this.refreshData()
        }
        this.onDatePreset = (preset) => {
            this.state.datePreset = preset
            const range = computeDateRange(preset)
            this.state.dateFrom = range.from
            this.state.dateTo = range.to
            this.refreshData()
        }
        this.onDateFromChange = (value) => {
            this.state.dateFrom = value
            this.state.datePreset = "custom"
            this.refreshData()
        }
        this.onDateToChange = (value) => {
            this.state.dateTo = value
            this.state.datePreset = "custom"
            this.refreshData()
        }
        this.onRefreshClick = () => this.refreshData()
        this.onExportClick = () => this.exportPipelineCsv()
    }

    // --- Domain builders (respect the toolbar filters) ---------------

    buildPropertyDomain() {
        const domain = []
        if (this.state.filters.propertyType) {
            domain.push(["property_type", "=", this.state.filters.propertyType])
        }
        if (this.state.filters.saleRent) {
            domain.push(["sale_rent", "=", this.state.filters.saleRent])
        }
        return domain
    }

    buildPropertyScopedDomain(pathPrefix) {
        const domain = []
        if (this.state.filters.propertyType) {
            domain.push([`${pathPrefix}.property_type`, "=", this.state.filters.propertyType])
        }
        if (this.state.filters.saleRent) {
            domain.push([`${pathPrefix}.sale_rent`, "=", this.state.filters.saleRent])
        }
        return domain
    }

    buildReservationDomain() {
        const domain = this.buildPropertyScopedDomain("property_id")
        if (this.state.filters.readiness === "sufficient") {
            domain.push(["is_sufficient", "=", true])
        } else if (this.state.filters.readiness === "awaiting") {
            domain.push(["is_sufficient", "=", false])
        }
        return domain
    }

    buildSaleDomain() {
        return [
            ...this.buildPropertyScopedDomain("property_id"),
            ["state", "=", "confirm"],
            ["order_date", ">=", this.state.dateFrom],
            ["order_date", "<=", this.state.dateTo],
        ]
    }

    buildRentalBaseDomain() {
        return this.buildPropertyScopedDomain("property_id")
    }

    buildRentalDomain() {
        return [...this.buildRentalBaseDomain(), ["state", "=", "in_contract"]]
    }

    // --- Navigation ----------------------------------------------------

    openProperties(name, domain) {
        this.openWindow(name, "property.property", [...this.buildPropertyDomain(), ...domain])
    }

    openWindow(name, resModel, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: resModel,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain,
        })
    }

    openReservationForm(resId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Reservation",
            res_model: "property.reservation",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
            res_id: resId,
        })
    }

    // --- Data loading ----------------------------------------------------

    async loadCurrencySymbol() {
        try {
            const company = await this.orm.searchRead("res.company", [], ["currency_id"], { limit: 1 })
            const currencyId = company[0]?.currency_id?.[0]
            if (!currencyId) {
                return
            }
            const currency = await this.orm.read("res.currency", [currencyId], ["symbol"])
            this.state.currency_symbol = currency[0]?.symbol || ""
        } catch (error) {
            this.state.currency_symbol = ""
        }
    }

    async refreshData() {
        await Promise.all([
            this.getPropertyStats(),
            this.getSalesStats(),
            this.getRentalStats(),
            this.getPropertiesByType(),
            this.getPropertiesByStatus(),
            this.getRentalsByStatus(),
            this.getSalesByMonth(),
            this.getReservationStats(),
            this.getReservationsByStatus(),
            this.getReservationPipeline(),
            this.getWeeklyReservationActivity(),
        ])
        await this.buildAlerts()
    }

    async getPropertyStats() {
        try {
            const domain = this.buildPropertyDomain()
            const properties = await this.orm.searchRead("property.property", domain, ["state", "create_date"])
            const counts = { draft: 0, available: 0, reserved: 0, rented: 0, pending_sales: 0, sold: 0 }
            let newInRange = 0
            for (const property of properties) {
                if (property.state in counts) {
                    counts[property.state] += 1
                }
                if (property.create_date && property.create_date >= this.state.dateFrom && property.create_date <= `${this.state.dateTo} 23:59:59`) {
                    newInRange += 1
                }
            }
            this.state.total_properties.value = properties.length
            this.state.total_properties.current_month_count = newInRange
            this.state.available_properties.value = counts.available
            this.state.reserved_properties.value = counts.reserved
            this.state.sold_properties.value = counts.sold
            this.state.rented_properties.value = counts.rented

            const occupied = counts.rented + counts.sold
            const percent = properties.length ? Math.round((occupied / properties.length) * 100) : 0
            this.state.occupancy = { percent, color: occupancyColor(percent) }
        } catch (error) {
            this.state.total_properties = { value: 0, current_month_count: 0 }
            this.state.available_properties = { value: 0 }
            this.state.reserved_properties = { value: 0 }
            this.state.sold_properties = { value: 0 }
            this.state.rented_properties = { value: 0 }
            this.state.occupancy = { percent: 0, color: "#cbd5e1" }
        }
    }

    async getSalesStats() {
        try {
            const sales = await this.orm.searchRead("property.sale", this.buildSaleDomain(), ["sale_price"])
            const total = sales.reduce((sum, sale) => sum + (sale.sale_price || 0), 0)
            this.state.total_sales_value.value = Math.round(total)
            this.state.total_sales_value.current_month_count = sales.length
        } catch (error) {
            this.state.total_sales_value = { value: 0, current_month_count: 0 }
        }
    }

    async getRentalStats() {
        try {
            const rentals = await this.orm.searchRead("property.rental", this.buildRentalDomain(), ["rent_price"])
            const total = rentals.reduce((sum, rental) => sum + (rental.rent_price || 0), 0)
            this.state.monthly_rent_revenue.value = Math.round(total)
            this.state.monthly_rent_revenue.current_month_count = rentals.length
        } catch (error) {
            this.state.monthly_rent_revenue = { value: 0, current_month_count: 0 }
        }
    }

    async getReservationStats() {
        try {
            const cutoffIso = new Date(Date.now() + 7 * DAY_MS).toISOString()
            const reservations = await this.orm.searchRead(
                "property.reservation",
                this.buildReservationDomain(),
                ["status", "expire_date", "is_sufficient", "expected_amount", "create_date"]
            )
            let activeCount = 0
            let activeInRange = 0
            let pipelineValue = 0
            let expiringSoon = 0
            let insufficient = 0
            let sold = 0
            const nowIso = new Date().toISOString()
            for (const reservation of reservations) {
                const isActive = RESERVATION_ACTIVE_STATES.includes(reservation.status)
                if (isActive) {
                    activeCount += 1
                    pipelineValue += reservation.expected_amount || 0
                    if (reservation.create_date && reservation.create_date >= this.state.dateFrom && reservation.create_date <= `${this.state.dateTo} 23:59:59`) {
                        activeInRange += 1
                    }
                    if (reservation.expire_date && reservation.expire_date >= nowIso && reservation.expire_date <= cutoffIso) {
                        expiringSoon += 1
                    }
                }
                if (!reservation.is_sufficient && ["draft", "requested"].includes(reservation.status)) {
                    insufficient += 1
                }
                if (reservation.status === "sold") {
                    sold += 1
                }
            }
            this.state.active_reservations = { value: activeCount, current_month_count: activeInRange }
            this.state.reservation_pipeline_value = { value: Math.round(pipelineValue) }
            this.state.reservations_expiring = { value: expiringSoon }
            this.state.reservations_insufficient = { value: insufficient }
            this.state.reservations_sold = { value: sold }
        } catch (error) {
            this.state.active_reservations = { value: 0, current_month_count: 0 }
            this.state.reservation_pipeline_value = { value: 0 }
            this.state.reservations_expiring = { value: 0 }
            this.state.reservations_insufficient = { value: 0 }
            this.state.reservations_sold = { value: 0 }
        }
    }

    async getPropertiesByType() {
        try {
            const rows = await this.orm.readGroup("property.property", this.buildPropertyDomain(), ["__count"], ["property_type"], { lazy: false })
            const entries = rows
                .map((row) => [row.property_type, Number(row.__count || 0)])
                .filter(([type, count]) => Boolean(type) && count > 0)
            this.state.properties_by_type = {
                labels: entries.map(([type]) => PROPERTY_TYPE_LABELS[type] || type),
                datasets: [{
                    label: "Properties",
                    data: entries.map(([, count]) => count),
                    backgroundColor: entries.map((_, i) => PALETTE[i % PALETTE.length]),
                    borderColor: entries.map((_, i) => PALETTE[i % PALETTE.length]),
                    borderWidth: 1,
                }],
            }
        } catch (error) {
            this.state.properties_by_type = emptyChart()
        }
    }

    async getPropertiesByStatus() {
        try {
            const rows = await this.orm.readGroup("property.property", this.buildPropertyDomain(), ["__count"], ["state"], { lazy: false })
            const entries = rows
                .map((row) => [row.state, Number(row.__count || 0)])
                .filter(([state, count]) => Boolean(state) && count > 0)
            this.state.properties_by_status = {
                labels: entries.map(([state]) => PROPERTY_STATE_LABELS[state] || state),
                datasets: [{
                    label: "Properties",
                    data: entries.map(([, count]) => count),
                    backgroundColor: entries.map((_, i) => PALETTE[i % PALETTE.length]),
                    borderColor: "#ffffff",
                    borderWidth: 2,
                }],
            }
        } catch (error) {
            this.state.properties_by_status = emptyChart()
        }
    }

    async getRentalsByStatus() {
        try {
            const rows = await this.orm.readGroup("property.rental", this.buildRentalBaseDomain(), ["__count"], ["state"], { lazy: false })
            const entries = rows
                .map((row) => [row.state, Number(row.__count || 0)])
                .filter(([state, count]) => Boolean(state) && count > 0)
            this.state.rentals_by_status = {
                labels: entries.map(([state]) => RENTAL_STATE_LABELS[state] || state),
                datasets: [{
                    label: "Rentals",
                    data: entries.map(([, count]) => count),
                    backgroundColor: entries.map((_, i) => PALETTE[i % PALETTE.length]),
                    borderColor: entries.map((_, i) => PALETTE[i % PALETTE.length]),
                    borderWidth: 1,
                }],
            }
        } catch (error) {
            this.state.rentals_by_status = emptyChart()
        }
    }

    async getReservationsByStatus() {
        try {
            const rows = await this.orm.readGroup("property.reservation", this.buildReservationDomain(), ["__count"], ["status"], { lazy: false })
            const entries = rows
                .map((row) => [row.status, Number(row.__count || 0)])
                .filter(([status, count]) => Boolean(status) && count > 0)
            this.state.reservations_by_status = {
                labels: entries.map(([status]) => RESERVATION_STATE_LABELS[status] || status),
                datasets: [{
                    label: "Reservations",
                    data: entries.map(([, count]) => count),
                    backgroundColor: entries.map((_, i) => PALETTE[i % PALETTE.length]),
                    borderColor: "#ffffff",
                    borderWidth: 2,
                }],
            }
        } catch (error) {
            this.state.reservations_by_status = emptyChart()
        }
    }

    async getSalesByMonth() {
        try {
            const currentYear = new Date().getFullYear()
            const sales = await this.orm.searchRead(
                "property.sale",
                [
                    ...this.buildPropertyScopedDomain("property_id"),
                    ["state", "=", "confirm"],
                    ["order_date", ">=", `${currentYear}-01-01`],
                    ["order_date", "<=", `${currentYear}-12-31`],
                ],
                ["sale_price", "order_date"]
            )
            const totals = new Array(12).fill(0)
            for (const sale of sales) {
                if (!sale.order_date) {
                    continue
                }
                const month = new Date(sale.order_date).getMonth()
                totals[month] += sale.sale_price || 0
            }
            this.state.sales_by_month = {
                labels: MONTH_LABELS.map((label) => `${label} ${currentYear}`),
                datasets: [{
                    label: "Sales Revenue",
                    data: totals.map((value) => Math.round(value)),
                    backgroundColor: "rgba(2, 51, 132, 0.12)",
                    borderColor: "#023384",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                }],
            }
        } catch (error) {
            this.state.sales_by_month = emptyChart()
        }
    }

    async getReservationPipeline() {
        try {
            const rows = await this.orm.searchRead(
                "property.reservation",
                [...this.buildReservationDomain(), ["status", "in", RESERVATION_ACTIVE_STATES]],
                ["property_id", "partner_id", "reservation_type_id", "expire_date", "expected_amount", "payment_diff", "is_sufficient", "status"],
                { order: "expire_date asc", limit: 8 }
            )
            const now = Date.now()
            const symbol = this.state.currency_symbol
            this.state.reservation_pipeline = rows.map((row) => {
                const expected = row.expected_amount || 0
                const percentPaid = expected > 0 ? clampPercent(((expected - (row.payment_diff || 0)) / expected) * 100) : 100
                let readinessLabel
                let readinessClass
                if (row.is_sufficient) {
                    readinessLabel = "Ready (100%)"
                    readinessClass = "ok"
                } else if (percentPaid > 0) {
                    readinessLabel = `Partial (${percentPaid}%)`
                    readinessClass = "warning"
                } else {
                    readinessLabel = "Pending (0%)"
                    readinessClass = "danger"
                }

                let daysLeft = null
                let riskLabel = "On Schedule"
                if (row.expire_date) {
                    daysLeft = Math.ceil((new Date(row.expire_date).getTime() - now) / DAY_MS)
                    if (daysLeft <= 1) {
                        riskLabel = daysLeft < 0 ? "Overdue" : "Expiring Today"
                    } else if (daysLeft <= 3) {
                        riskLabel = `Expiring in ${daysLeft}d`
                    }
                }
                if (!row.is_sufficient) {
                    riskLabel = "Awaiting Payment"
                }

                return {
                    id: row.id,
                    partner_name: row.partner_id ? row.partner_id[1] : "",
                    type_name: row.reservation_type_id ? row.reservation_type_id[1] : "",
                    property_name: row.property_id ? row.property_id[1] : "",
                    target_label: expected > 0 ? `${Math.round(expected).toLocaleString()} ${symbol}`.trim() : "No Payment Req.",
                    percent_paid: percentPaid,
                    readiness_label: readinessLabel,
                    readiness_class: readinessClass,
                    risk_label: riskLabel,
                    expire_label: row.expire_date
                        ? new Date(row.expire_date).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
                        : "—",
                    days_left: daysLeft,
                }
            })
        } catch (error) {
            this.state.reservation_pipeline = []
        }
    }

    async getWeeklyReservationActivity() {
        try {
            const since = new Date()
            since.setDate(since.getDate() - 6)
            since.setHours(0, 0, 0, 0)
            const rows = await this.orm.searchRead(
                "property.reservation",
                [...this.buildReservationDomain(), ["create_date", ">=", since.toISOString().slice(0, 19).replace("T", " ")]],
                ["create_date"]
            )
            const counts = new Array(7).fill(0)
            const today = new Date()
            today.setHours(0, 0, 0, 0)
            for (const row of rows) {
                if (!row.create_date) {
                    continue
                }
                const created = new Date(row.create_date)
                created.setHours(0, 0, 0, 0)
                const diffDays = Math.round((today.getTime() - created.getTime()) / DAY_MS)
                const bucket = 6 - diffDays
                if (bucket >= 0 && bucket < 7) {
                    counts[bucket] += 1
                }
            }
            const labels = []
            for (let i = 6; i >= 0; i -= 1) {
                const d = new Date(today)
                d.setDate(today.getDate() - i)
                labels.push(WEEKDAY_LABELS[d.getDay()])
            }
            this.state.weekly_activity = {
                labels,
                datasets: [{
                    label: "New Reservations",
                    data: counts,
                    backgroundColor: counts.map((_, i) => (i === counts.length - 1 ? "#22c55e" : "#023384")),
                    borderColor: counts.map((_, i) => (i === counts.length - 1 ? "#22c55e" : "#023384")),
                    borderWidth: 1,
                }],
            }
        } catch (error) {
            this.state.weekly_activity = emptyChart()
        }
    }

    async buildAlerts() {
        const alerts = []
        for (const row of this.state.reservation_pipeline) {
            if (row.days_left !== null && row.days_left <= 1) {
                alerts.push({
                    severity: "critical",
                    badge: row.days_left < 0 ? "Overdue" : "Expiring Today",
                    title: `Reservation Expiring: ${row.property_name}`,
                    description: `${row.partner_name} — expires ${row.expire_label}`,
                })
            } else if (!row.is_sufficient) {
                alerts.push({
                    severity: "warning",
                    badge: "Payment Shortfall",
                    title: `Awaiting Payment: ${row.property_name}`,
                    description: `${row.partner_name} — ${row.percent_paid}% paid of ${row.target_label}`,
                })
            }
        }

        try {
            const cutoff = new Date(Date.now() + 14 * DAY_MS).toISOString().split("T")[0]
            const today = toDateStr(new Date())
            const endingLeases = await this.orm.searchRead(
                "property.rental",
                [...this.buildRentalDomain(), ["end_date", "<=", cutoff], ["end_date", ">=", today]],
                ["property_id", "renter_id", "end_date"],
                { order: "end_date asc", limit: 5 }
            )
            for (const lease of endingLeases) {
                alerts.push({
                    severity: "warning",
                    badge: "Lease Ending",
                    title: `Lease Ending Soon: ${lease.property_id ? lease.property_id[1] : ""}`,
                    description: `${lease.renter_id ? lease.renter_id[1] : ""} — ends ${lease.end_date}`,
                })
            }
        } catch (error) {
            // property.rental may be unavailable to the current user; skip lease alerts.
        }

        const severityOrder = { critical: 0, warning: 1, info: 2 }
        alerts.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity])
        this.state.alerts = alerts.slice(0, 6)
    }

    exportPipelineCsv() {
        const rows = this.state.reservation_pipeline
        if (!rows.length) {
            return
        }
        const header = ["Customer", "Reservation Type", "Property", "Target", "Paid %", "Readiness", "Risk Flag"]
        const lines = [header.map(csvCell).join(",")]
        for (const row of rows) {
            lines.push([
                row.partner_name,
                row.type_name,
                row.property_name,
                row.target_label,
                `${row.percent_paid}%`,
                row.readiness_label,
                row.risk_label,
            ].map(csvCell).join(","))
        }
        const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" })
        const url = URL.createObjectURL(blob)
        const link = document.createElement("a")
        link.href = url
        link.download = "reservation_pipeline.csv"
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
    }
}

MainDashboard.template = "property_dashboard.MainDashboard"
MainDashboard.components = { DashboardCard, ChartRenderer }

registry.category("actions").add("property_dashboard.dashboard_main_view", MainDashboard)
