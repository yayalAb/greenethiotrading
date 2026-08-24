# -*- coding: utf-8 -*-
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

PAID_STATES = ("paid", "in_payment")
UNPAID_STATES = ("not_paid", "partial")
MAP_POS = {
    "ethiopia": (58, 50),
    "united states": (22, 38),
    "united states of america": (22, 38),
    "china": (78, 38),
    "brazil": (32, 62),
    "india": (70, 45),
    "united kingdom": (48, 32),
    "germany": (51, 33),
    "kenya": (59, 55),
    "united arab emirates": (64, 42),
    "uae": (64, 42),
    "france": (49, 34),
    "canada": (20, 28),
    "nigeria": (50, 52),
    "south africa": (54, 72),
    "egypt": (56, 42),
}


class PropertyDashboard(models.AbstractModel):
    _name = "property.dashboard"
    _description = "Property Rent & Sales Dashboard"

    def _fmt(self, amount, compact=False):
        currency = self.env.company.currency_id
        value = amount or 0.0
        if compact:
            abs_amt = abs(value)
            symbol = currency.symbol or currency.name or ""
            if abs_amt >= 1000000:
                return "%s%.1fM" % (symbol, value / 1000000.0)
            if abs_amt >= 1000:
                return "%s%.1fk" % (symbol, value / 1000.0)
        return currency.format(value)

    def _pct(self, current, previous):
        if not previous:
            return 100.0 if current else 0.0
        return round(((current - previous) / previous) * 100.0, 1)

    def _month_bounds(self, day):
        start = day.replace(day=1)
        return start, start + relativedelta(months=1)

    def _as_dt(self, day, end=False):
        stamp = "%s %s" % (day, "23:59:59" if end else "00:00:00")
        return fields.Datetime.to_datetime(stamp)

    def _paid_amount(self, move):
        if move.payment_state in PAID_STATES:
            return move.amount_total
        if move.payment_state == "partial":
            return move.amount_total - move.amount_residual
        return 0.0

    def _property_of(self, move):
        if move.property_rental_id:
            return move.property_rental_id.property_id
        if move.property_order_id:
            return move.property_order_id.property_id
        return self.env["property.property"]

    def _enquiry_count(self, date_from, date_to):
        domain = [
            ("create_date", ">=", self._as_dt(date_from)),
            ("create_date", "<", self._as_dt(date_to)),
        ]
        if "property.rental.request" in self.env:
            return self.env["property.rental.request"].search_count(domain)
        return self.env["property.rental"].search_count(domain)

    def _enquiry_monthly(self, months):
        counts = [0] * len(months)
        model_name = (
            "property.rental.request"
            if "property.rental.request" in self.env
            else "property.rental"
        )
        start = months[0][0]
        end = months[-1][1]
        records = self.env[model_name].search(
            [
                ("create_date", ">=", self._as_dt(start)),
                ("create_date", "<", self._as_dt(end)),
            ]
        )
        for record in records:
            created = fields.Date.to_date(record.create_date)
            for index, (month_start, month_end) in enumerate(months):
                if month_start <= created < month_end:
                    counts[index] += 1
                    break
        return counts

    @api.model
    def get_dashboard_data(self):
        today = fields.Date.context_today(self)
        yesterday = today - relativedelta(days=1)
        this_start, this_end = self._month_bounds(today)
        last_start, last_end = self._month_bounds(today - relativedelta(months=1))
        week_start = today - relativedelta(days=today.weekday())
        lookback = today.replace(day=1) - relativedelta(months=11)
        company = self.env.company

        Move = self.env["account.move"].sudo()
        Property = self.env["property.property"]
        Rental = self.env["property.rental"]
        Sale = self.env["property.sale"]

        invoice_domain = [
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("company_id", "=", company.id),
            "|",
            ("property_rental_id", "!=", False),
            ("property_order_id", "!=", False),
        ]
        recent_moves = Move.search(
            invoice_domain + [("invoice_date", ">=", lookback)]
        )
        outstanding_moves = Move.search(
            invoice_domain + [("payment_state", "in", list(UNPAID_STATES))]
        )

        month_windows = []
        for offset in range(11, -1, -1):
            month_day = today.replace(day=1) - relativedelta(months=offset)
            month_windows.append(self._month_bounds(month_day))

        rent_trend = [0.0] * 12
        sale_trend = [0.0] * 12
        billed_trend = [0.0] * 12
        collected_trend = [0.0] * 12
        months = [window[0].strftime("%b") for window in month_windows]
        rent_week = [0.0] * 7
        sale_week = [0.0] * 7
        invoice_week = [0] * 7
        property_totals = defaultdict(float)

        rent_paid_today = sale_paid_today = 0.0
        rent_paid_yesterday = sale_paid_yesterday = 0.0
        rent_paid_month = sale_paid_month = 0.0
        rent_billed_month = sale_billed_month = 0.0
        last_collected = this_collected = 0.0

        for move in recent_moves:
            invoice_date = move.invoice_date or fields.Date.to_date(move.create_date)
            paid = self._paid_amount(move)
            is_rent = bool(move.property_rental_id)
            is_sale = bool(move.property_order_id)

            if invoice_date == today:
                if is_rent:
                    rent_paid_today += paid
                if is_sale:
                    sale_paid_today += paid
            elif invoice_date == yesterday:
                if is_rent:
                    rent_paid_yesterday += paid
                if is_sale:
                    sale_paid_yesterday += paid

            if this_start <= invoice_date < this_end:
                this_collected += paid
                if is_rent:
                    rent_paid_month += paid
                    rent_billed_month += move.amount_total
                if is_sale:
                    sale_paid_month += paid
                    sale_billed_month += move.amount_total
            elif last_start <= invoice_date < last_end:
                last_collected += paid

            if week_start <= invoice_date <= today:
                idx = invoice_date.weekday()
                invoice_week[idx] += 1
                if is_rent:
                    rent_week[idx] += move.amount_total
                if is_sale:
                    sale_week[idx] += move.amount_total

            for index, (start, end) in enumerate(month_windows):
                if start <= invoice_date < end:
                    billed_trend[index] += move.amount_total
                    collected_trend[index] += paid
                    if is_rent:
                        rent_trend[index] += paid
                    if is_sale:
                        sale_trend[index] += paid
                    break

            if paid:
                prop = self._property_of(move)
                if prop:
                    property_totals[prop] += paid

        outstanding = sum(outstanding_moves.mapped("amount_residual"))
        overdue_count = len(
            outstanding_moves.filtered(
                lambda move: move.invoice_date_due
                and move.invoice_date_due < today
            )
        )
        billed_month = rent_billed_month + sale_billed_month
        collected_month = rent_paid_month + sale_paid_month
        collection_rate = (
            round((collected_month / billed_month) * 100.0, 1) if billed_month else 0.0
        )

        contracts_active = Rental.search_count([("state", "=", "in_contract")])
        contracts_yesterday = Rental.search_count(
            [("state", "=", "in_contract"), ("start_date", "<=", yesterday)]
        )
        enquiries_today = self._enquiry_count(today, today + relativedelta(days=1))
        enquiries_yesterday = self._enquiry_count(yesterday, today)

        contract_week = [0] * 7
        week_contracts = Rental.search(
            [
                ("start_date", ">=", week_start),
                ("start_date", "<=", today),
                ("state", "in", ["in_contract", "expired"]),
            ]
        )
        for rental in week_contracts:
            contract_week[rental.start_date.weekday()] += 1

        colors = ["#0095FF", "#00E096", "#884DFF", "#FFCF00", "#FF8F0D", "#EB3B5A"]
        ranked = sorted(property_totals.items(), key=lambda item: item[1], reverse=True)[:6]
        max_total = ranked[0][1] if ranked else 1.0
        top_rows = []
        for index, (prop, total) in enumerate(ranked):
            top_rows.append(
                {
                    "index": index + 1,
                    "name": prop.name,
                    "city": prop.city or (prop.country_id.name or ""),
                    "kind": "Rent" if prop.sale_rent == "for_tenancy" else "Sale",
                    "amount": self._fmt(total),
                    "popularity": int(round((total / max_total) * 100)),
                    "color": colors[index % len(colors)],
                }
            )

        region_map = defaultdict(lambda: {"count": 0, "amount": 0.0})
        for prop, total in property_totals.items():
            region = prop.city or prop.country_id.name or "Unknown"
            region_map[region]["count"] += 1
            region_map[region]["amount"] += total
            region_map[region]["country"] = prop.country_id.name or region

        countries = []
        for index, (name, vals) in enumerate(
            sorted(region_map.items(), key=lambda item: item[1]["amount"], reverse=True)[:6]
        ):
            country_name = (vals.get("country") or name).lower()
            x, y = MAP_POS.get(name.lower(), MAP_POS.get(country_name, (50 + index * 4, 42)))
            countries.append(
                {
                    "name": name,
                    "count": vals["count"],
                    "amount": self._fmt(vals["amount"]),
                    "color": colors[index % len(colors)],
                    "x": x,
                    "y": y,
                }
            )

        return {
            "currency": company.currency_id.symbol or "",
            "kpis": [
                {
                    "key": "rent",
                    "label": "Total Rent",
                    "hint": "Paid rental invoices today",
                    "value": self._fmt(rent_paid_today, compact=True),
                    "change": self._pct(rent_paid_today, rent_paid_yesterday),
                    "tone": "pink",
                    "icon": "fa-bar-chart",
                    "action": "rent_invoices",
                },
                {
                    "key": "sale",
                    "label": "Property Sales",
                    "hint": "Paid sale invoices today",
                    "value": self._fmt(sale_paid_today, compact=True),
                    "change": self._pct(sale_paid_today, sale_paid_yesterday),
                    "tone": "peach",
                    "icon": "fa-file-text-o",
                    "action": "sale_invoices",
                },
                {
                    "key": "contracts",
                    "label": "Active Contracts",
                    "hint": "Rentals currently in contract",
                    "value": str(contracts_active),
                    "change": self._pct(contracts_active, contracts_yesterday),
                    "tone": "green",
                    "icon": "fa-tag",
                    "action": "contracts",
                },
                {
                    "key": "leads",
                    "label": "New Enquiries",
                    "hint": "Enquiries received today",
                    "value": str(enquiries_today),
                    "change": self._pct(enquiries_today, enquiries_yesterday),
                    "tone": "purple",
                    "icon": "fa-user-o",
                    "action": "enquiries",
                },
            ],
            "collection": {
                "outstanding": self._fmt(outstanding),
                "overdue": overdue_count,
                "rate": collection_rate,
                "rent_month": self._fmt(rent_paid_month),
                "sale_month": self._fmt(sale_paid_month),
                "billed_month": self._fmt(billed_month),
                "collected_month": self._fmt(collected_month),
                "last_month": self._fmt(last_collected),
                "this_month": self._fmt(this_collected),
                "last_month_raw": last_collected,
                "this_month_raw": this_collected,
            },
            "charts": {
                "months": months,
                "rent_trend": rent_trend,
                "sale_trend": sale_trend,
                "enquiry_trend": self._enquiry_monthly(month_windows),
                "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "rent_week": rent_week,
                "sale_week": sale_week,
                "target": billed_trend[-6:],
                "reality": collected_trend[-6:],
                "target_months": months[-6:],
                "contract_week": contract_week,
                "invoice_week": invoice_week,
            },
            "top_properties": top_rows,
            "countries": countries,
            "summary": {
                "available": Property.search_count([("state", "=", "available")]),
                "rented": Property.search_count([("state", "=", "rented")]),
                "sold": Property.search_count([("state", "=", "sold")]),
                "sales_confirm": Sale.search_count([("state", "=", "confirm")]),
                "rentals_draft": Rental.search_count([("state", "=", "draft")]),
                "volume_total": sum(invoice_week),
                "service_total": sum(contract_week),
            },
        }

    @api.model
    def action_open(self, kind):
        today = fields.Date.context_today(self)
        if kind == "rent_invoices":
            return {
                "type": "ir.actions.act_window",
                "name": "Rental Invoices",
                "res_model": "account.move",
                "view_mode": "list,form",
                "domain": [
                    ("move_type", "=", "out_invoice"),
                    ("property_rental_id", "!=", False),
                ],
            }
        if kind == "sale_invoices":
            return {
                "type": "ir.actions.act_window",
                "name": "Sale Invoices",
                "res_model": "account.move",
                "view_mode": "list,form",
                "domain": [
                    ("move_type", "=", "out_invoice"),
                    ("property_order_id", "!=", False),
                ],
            }
        if kind == "contracts":
            return {
                "type": "ir.actions.act_window",
                "name": "Active Contracts",
                "res_model": "property.rental",
                "view_mode": "list,form",
                "domain": [("state", "=", "in_contract")],
            }
        if kind == "enquiries" and "property.rental.request" in self.env:
            return {
                "type": "ir.actions.act_window",
                "name": "Enquiries",
                "res_model": "property.rental.request",
                "view_mode": "list,form",
                "domain": [("create_date", ">=", self._as_dt(today))],
            }
        if kind == "enquiries":
            return {
                "type": "ir.actions.act_window",
                "name": "Draft Rentals",
                "res_model": "property.rental",
                "view_mode": "list,form",
                "domain": [("state", "=", "draft")],
            }
        if kind == "overdue":
            return {
                "type": "ir.actions.act_window",
                "name": "Overdue Collection",
                "res_model": "account.move",
                "view_mode": "list,form",
                "domain": [
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "in", list(UNPAID_STATES)),
                    ("invoice_date_due", "<", today),
                    "|",
                    ("property_rental_id", "!=", False),
                    ("property_order_id", "!=", False),
                ],
            }
        return {"type": "ir.actions.act_window_close"}
