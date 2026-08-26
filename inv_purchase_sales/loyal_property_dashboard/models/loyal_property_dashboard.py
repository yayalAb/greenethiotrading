# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

PAID_STATES = ("paid", "in_payment")
UNPAID_STATES = ("not_paid", "partial")
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CHART_COLORS = [
    "rgba(255, 99, 132, 1)",
    "rgba(54, 162, 235, 1)",
    "rgba(255, 206, 86, 1)",
    "rgba(75, 192, 192, 1)",
    "rgba(153, 102, 255, 1)",
    "rgba(255, 159, 64, 1)",
]
COLORS = {
    "blue": "#0095FF",
    "green": "#00E096",
}


class LoyalPropertyDashboard(models.AbstractModel):
    _name = "loyal.property.dashboard"
    _description = "Loyal Property Dashboard"

    def _fmt(self, amount):
        return self.env.company.currency_id.format(amount or 0.0)

    def _pct(self, part, total):
        if not total:
            return 0.0
        return round((part / total) * 100.0, 1)

    def _parse_date(self, value):
        if not value:
            return False
        return fields.Date.to_date(value)

    def _move_date(self, move):
        return move.invoice_date or move.date or fields.Date.to_date(move.create_date)

    def _paid_amount(self, move):
        if move.payment_state in PAID_STATES:
            return move.amount_total or 0.0
        if move.payment_state == "partial":
            return (move.amount_total or 0.0) - (move.amount_residual or 0.0)
        return 0.0

    def _in_range(self, day, date_start, date_end):
        if not day:
            return False
        if date_start and day < date_start:
            return False
        if date_end and day > date_end:
            return False
        return True

    def _in_period(self, day, date_start, date_end):
        if not date_start and not date_end:
            return True
        return self._in_range(day, date_start, date_end)

    def _invoice_moves(self, date_start, date_end):
        Move = self.env["account.move"].sudo()
        domain = [
            ("move_type", "=", "out_invoice"),
            ("state", "!=", "cancel"),
        ]
        linked_domain = domain + [
            "|",
            ("property_rental_id", "!=", False),
            ("property_order_id", "!=", False),
        ]
        moves = Move.search(linked_domain)
        if not moves:
            sale_invoices = self.env["property.sale"].sudo().search([]).mapped("invoice_id")
            moves = sale_invoices.filtered(
                lambda move: move.move_type == "out_invoice" and move.state != "cancel"
            )
        if not moves:
            moves = Move.search(domain)
        if date_start or date_end:
            moves = moves.filtered(
                lambda move: self._in_range(self._move_date(move), date_start, date_end)
            )
        return moves

    def _empty_revenue(self):
        return {
            "labels": WEEKDAYS,
            "datasets": [
                {
                    "label": "Rental Income",
                    "data": [0] * 7,
                    "backgroundColor": COLORS["blue"],
                    "borderRadius": 6,
                    "barPercentage": 0.55,
                },
                {
                    "label": "Sales Income",
                    "data": [0] * 7,
                    "backgroundColor": COLORS["green"],
                    "borderRadius": 6,
                    "barPercentage": 0.55,
                },
            ],
        }

    def _empty_trend(self, labels):
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Billed",
                    "data": [0] * len(labels),
                    "borderColor": COLORS["blue"],
                    "backgroundColor": "rgba(0,149,255,0.18)",
                    "fill": True,
                    "tension": 0.45,
                    "pointRadius": 0,
                    "borderWidth": 2,
                },
                {
                    "label": "Collected",
                    "data": [0] * len(labels),
                    "borderColor": COLORS["green"],
                    "backgroundColor": "rgba(0,224,150,0.18)",
                    "fill": True,
                    "tension": 0.45,
                    "pointRadius": 0,
                    "borderWidth": 2,
                },
            ],
        }

    @api.model
    def get_dashboard_data(self, date_start=False, date_end=False):
        today = fields.Date.context_today(self)
        date_start = self._parse_date(date_start)
        date_end = self._parse_date(date_end)
        this_month_start = today.replace(day=1)
        last_month_start = this_month_start - relativedelta(months=1)
        last_month_end = this_month_start - relativedelta(days=1)
        expiring_until = today + relativedelta(days=30)

        Property = self.env["property.property"].sudo()
        Rental = self.env["property.rental"].sudo()
        Sale = self.env["property.sale"].sudo()
        Bill = self.env["rental.bill"].sudo() if "rental.bill" in self.env else False

        property_domain = []
        rental_domain = [("state", "!=", "cancel")]
        sale_domain = []
        if date_start:
            property_domain.append(("create_date", ">=", "%s 00:00:00" % date_start))
            rental_domain.append(("start_date", ">=", date_start))
            sale_domain.append(("order_date", ">=", date_start))
        if date_end:
            property_domain.append(("create_date", "<=", "%s 23:59:59" % date_end))
            rental_domain.append(("start_date", "<=", date_end))
            sale_domain.append(("order_date", "<=", date_end))

        properties = Property.search(property_domain)
        rentals = Rental.search(rental_domain)
        sales = Sale.search(sale_domain)
        bills = Bill.search([]) if Bill is not False else self.env["rental.bill"]
        moves = self._invoice_moves(date_start, date_end)

        available = len(properties.filtered(lambda rec: rec.state == "available"))
        rented = len(properties.filtered(lambda rec: rec.state == "rented"))
        sold = len(properties.filtered(lambda rec: rec.state == "sold"))
        draft_props = len(properties.filtered(lambda rec: rec.state == "draft"))
        total_props = len(properties) or 0

        active_rentals = rentals.filtered(lambda rec: rec.state == "in_contract")
        expired_rentals = rentals.filtered(lambda rec: rec.state == "expired")
        expiring = active_rentals.filtered(
            lambda rec: rec.end_date and today <= rec.end_date <= expiring_until
        )
        if not expiring:
            expiring = active_rentals

        expected_rent = sum(rentals.mapped("rent_price"))
        expected_sales = sum(
            sales.filtered(lambda rec: rec.state == "confirm" and not rec.invoiced).mapped("sale_price")
        )
        expected_bills = sum(bills.mapped("amount"))
        expected_total = expected_rent + expected_sales + expected_bills

        billed_total = 0.0
        collected_total = 0.0
        overdue_amount = 0.0
        overdue_count = 0
        rent_week = [0.0] * 7
        sale_week = [0.0] * 7
        month_totals = [0.0] * 12
        last_collected = 0.0
        this_collected = 0.0

        month_windows = []
        for offset in range(5, -1, -1):
            start = (today.replace(day=1) - relativedelta(months=offset))
            end = start + relativedelta(months=1) - relativedelta(days=1)
            month_windows.append({"label": start.strftime("%b"), "start": start, "end": end})
        billed_trend = [0.0] * 6
        collected_trend = [0.0] * 6

        for move in moves:
            day = self._move_date(move)
            if not day:
                continue
            amount = move.amount_total or 0.0
            paid = self._paid_amount(move)
            billed_total += amount
            collected_total += paid
            weekday = day.weekday()
            is_sale = bool(move.property_order_id)
            is_rent = bool(move.property_rental_id) or not is_sale
            if is_rent:
                rent_week[weekday] += amount
            if is_sale:
                sale_week[weekday] += amount
            month_totals[day.month - 1] += paid or amount
            if this_month_start <= day <= today:
                this_collected += paid or amount
            elif last_month_start <= day <= last_month_end:
                last_collected += paid or amount
            for index, window in enumerate(month_windows):
                if window["start"] <= day <= window["end"]:
                    billed_trend[index] += amount
                    collected_trend[index] += paid
                    break
            if (
                move.payment_state in UNPAID_STATES
                and move.invoice_date_due
                and move.invoice_date_due < today
            ):
                overdue_amount += move.amount_residual or amount
                overdue_count += 1

        if billed_total <= 0:
            for rental in rentals:
                day = rental.start_date or rental.invoice_date
                if day and not self._in_period(day, date_start, date_end):
                    continue
                amount = rental.rent_price or 0.0
                billed_total += amount
                if day:
                    rent_week[day.weekday()] += amount
                    month_totals[day.month - 1] += amount
                    if this_month_start <= day <= today:
                        this_collected += amount
                    elif last_month_start <= day <= last_month_end:
                        last_collected += amount
                    for index, window in enumerate(month_windows):
                        if window["start"] <= day <= window["end"]:
                            billed_trend[index] += amount
                            collected_trend[index] += amount if rental.state != "draft" else 0.0
                            break
            for sale in sales:
                day = sale.order_date
                amount = sale.sale_price or 0.0
                if day and not self._in_period(day, date_start, date_end):
                    continue
                billed_total += amount
                if day:
                    sale_week[day.weekday()] += amount
                    month_totals[day.month - 1] += amount
                    if this_month_start <= day <= today:
                        this_collected += amount
                    elif last_month_start <= day <= last_month_end:
                        last_collected += amount
                    for index, window in enumerate(month_windows):
                        if window["start"] <= day <= window["end"]:
                            billed_trend[index] += amount
                            collected_trend[index] += amount if sale.invoiced else 0.0
                            break
            for bill in bills:
                amount = bill.amount or 0.0
                billed_total += amount
                day = bill.rental_id.start_date if bill.rental_id else today
                if day:
                    rent_week[day.weekday()] += amount
                    month_totals[day.month - 1] += amount
                    this_collected += amount
                    for index, window in enumerate(month_windows):
                        if window["start"] <= day <= window["end"]:
                            billed_trend[index] += amount
                            collected_trend[index] += amount
                            break
            if collected_total <= 0:
                collected_total = this_collected + last_collected

        if overdue_count == 0 and expired_rentals:
            overdue_count = len(expired_rentals)
            overdue_amount = sum(expired_rentals.mapped("rent_price"))

        display_collection = collected_total or billed_total
        display_expected = expected_total or billed_total

        revenue = self._empty_revenue()
        revenue["datasets"][0]["data"] = rent_week
        revenue["datasets"][1]["data"] = sale_week

        trend_labels = [window["label"] for window in month_windows]
        trend = self._empty_trend(trend_labels)
        trend["datasets"][0]["data"] = billed_trend
        trend["datasets"][1]["data"] = collected_trend

        collection_by_month = {
            "labels": MONTH_LABELS,
            "datasets": [
                {
                    "label": "Amount by Month",
                    "data": month_totals,
                    "backgroundColor": CHART_COLORS * 2,
                    "borderColor": CHART_COLORS * 2,
                    "borderWidth": 1,
                    "fill": False,
                    "tension": 0.3,
                }
            ],
        }
        shop_by_state = {
            "labels": ["Draft", "Available", "Rented", "Sold"],
            "datasets": [
                {
                    "label": "Shop By Status",
                    "data": [draft_props, available, rented, sold],
                    "backgroundColor": [
                        "rgba(153, 102, 255, 1)",
                        "rgba(255, 159, 64, 1)",
                        "rgba(75, 192, 192, 1)",
                        "rgba(54, 162, 235, 1)",
                    ],
                    "borderColor": [
                        "rgba(153, 102, 255, 1)",
                        "rgba(255, 159, 64, 1)",
                        "rgba(75, 192, 192, 1)",
                        "rgba(54, 162, 235, 1)",
                    ],
                    "borderWidth": 1,
                }
            ],
        }

        return {
            "available_shop": {
                "value": available,
                "percentage": self._pct(available, total_props),
            },
            "ranted_shop": {
                "value": rented,
                "percentage": self._pct(rented, total_props),
            },
            "this_collection": {
                "value": self._fmt(display_collection),
                "percentage": self._pct(collected_total, billed_total or display_collection),
            },
            "expecting_collection": {
                "value": self._fmt(display_expected),
                "percentage": self._pct(display_expected, billed_total or display_expected),
            },
            "expiring_contract": {
                "value": len(expiring),
                "percentage": self._pct(len(expiring), len(rentals)),
            },
            "expired_contract": {
                "value": self._fmt(overdue_amount) if overdue_amount else overdue_count,
                "percentage": self._pct(overdue_count, len(moves) or overdue_count),
            },
            "collection_by_month": collection_by_month,
            "shop_by_state": shop_by_state,
            "revenue_week": revenue,
            "collection_trend": trend,
            "collection_summary": {
                "last_month": self._fmt(last_collected),
                "this_month": self._fmt(this_collected),
            },
        }
