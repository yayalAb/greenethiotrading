# -*- coding: utf-8 -*-
import io
import base64
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import ethiopian_calendar_util as eth_util

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class PropertyRentalSalesReportWizard(models.TransientModel):
    _name = 'property.rental.sales.report.wizard'
    _description = 'Property Rental Summary of Sales Report Wizard'

    def _default_fiscal_year(self):
        # Current Ethiopian year
        today = fields.Date.today()
        eth_date = eth_util.gregorian_to_ethiopian_date(today)
        if eth_date:
            # If current Ethiopian month is Hamle (11) or Nehase (12), next fiscal year is eth_date[0] + 1
            if eth_date[1] >= 11:
                return eth_date[0] + 1
            return eth_date[0]
        return 2018

    filter_by = fields.Selection([
        ('fiscal_year', 'Ethiopian Fiscal Year'),
        ('date_range', 'Custom Date Range'),
    ], string='Filter Period By', default='fiscal_year', required=True)

    fiscal_year = fields.Integer(
        string='Ethiopian Fiscal Year',
        default=_default_fiscal_year,
        help='The ending Ethiopian Year of the fiscal cycle (e.g. 2018 covers Hamle 1, 2017 to Sene 30, 2018)'
    )
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    property_ids = fields.Many2many(
        'property.property',
        string='Filter Properties (Optional)',
        help='Leave empty to include all properties'
    )
    location_id = fields.Many2one(
        'property.location',
        string='Location (Optional)',
        help='Filter by building/location'
    )
    floor_id = fields.Many2one(
        'property.floor',
        string='Floor (Optional)',
        help='Filter by floor'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    def _get_report_data(self):
        self.ensure_one()
        if self.filter_by == 'date_range' and self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise ValidationError(_('Start Date cannot be greater than End Date.'))
            fy_start = self.date_from
            fy_end = self.date_to
            period_title = f"{self.date_from.strftime('%d/%m/%Y')} - {self.date_to.strftime('%d/%m/%Y')}"
            # In custom date range, we still calculate months covering the range
            # Find the Ethiopian fiscal year from date_from or use current
            eth_start = eth_util.gregorian_to_ethiopian_date(self.date_from)
            fy = (eth_start[0] + 1) if eth_start and eth_start[1] >= 11 else (eth_start[0] if eth_start else self.fiscal_year)
            months = eth_util.get_ethiopian_fiscal_year_months(fy)
        else:
            months = eth_util.get_ethiopian_fiscal_year_months(self.fiscal_year or self._default_fiscal_year())
            fy_start = months[0]['start_date']
            fy_end = months[-1]['end_date']
            prev_year = (self.fiscal_year or self._default_fiscal_year()) - 1
            period_title = f"HAMLE 1, {prev_year} - SENE 30, {self.fiscal_year or self._default_fiscal_year()}"

        company_name = self.company_id.name

        # Domain for properties
        prop_domain = [('company_id', '=', self.company_id.id)]
        if self.property_ids:
            prop_domain.append(('id', 'in', self.property_ids.ids))
        if self.location_id:
            prop_domain.append(('location_id', '=', self.location_id.id))
        if self.floor_id:
            prop_domain.append(('floor_id', '=', self.floor_id.id))

        properties = self.env['property.property'].search(prop_domain, order='name asc')

        rows = []
        sn = 1

        # Totals accumulator for each month
        month_totals = {m['code']: 0.0 for m in months}
        grand_total = 0.0

        for prop in properties:
            # Find rentals for this property that overlap with this fiscal year
            rentals = self.env['property.rental'].search([
                ('property_id', '=', prop.id),
                ('state', 'in', ['in_contract', 'expired', 'draft']),
                ('start_date', '<=', fy_end),
                ('end_date', '>=', fy_start),
            ], order='start_date asc')

            if not rentals:
                # Unrented property line
                row = {
                    'sn': sn,
                    'shop_code': prop.name or '',
                    'customer_name': '',
                    'remark_cust': 'Unrented',
                    'location': prop.location_id.name if prop.location_id else '',
                    'floor': prop.floor_id.name if prop.floor_id else '',
                    'start_date': '',
                    'end_date': '',
                    'total_area': prop.total_area or 0.0,
                    'price_per_sqm': prop.price_per_m2 or 0.0,
                    'monthly_before_vat': prop.rent_month or 0.0,
                    'monthly_with_vat': (prop.rent_month * 1.15) if prop.rent_month else 0.0,
                    'month_values': {m['code']: 0.0 for m in months},
                    'total': 0.0,
                    'remark': 'Unrented',
                }
                rows.append(row)
                sn += 1
                continue

            for rental in rentals:
                # Find all invoices linked to this rental
                invoices = self.env['account.move'].search([
                    ('property_rental_id', '=', rental.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '!=', 'cancel'),
                ])

                # Monthly payments: monthly price before VAT and with VAT (15%)
                monthly_before_vat = rental.rent_price or prop.rent_month or 0.0
                monthly_with_vat = monthly_before_vat * 1.15

                # Total Area & Price per Sqm
                total_area = prop.total_area or 0.0
                price_per_sqm = prop.price_per_m2 or (monthly_before_vat / total_area if total_area else 0.0)

                # Distribute invoice revenue into each Ethiopian month column
                month_vals = {m['code']: 0.0 for m in months}
                row_total = 0.0

                for inv in invoices:
                    inv_start = inv.rental_invoice_start_date or inv.invoice_date or rental.start_date
                    inv_end = inv.rental_invoice_end_date or inv_start
                    inv_amount = inv.amount_untaxed or inv.amount_total or 0.0

                    if not inv_start or not inv_end:
                        continue

                    inv_total_days = max(1, (inv_end - inv_start).days + 1)

                    # Intersect invoice period with each Ethiopian month in the FY
                    for m in months:
                        m_start = m['start_date']
                        m_end = m['end_date']

                        overlap_start = max(inv_start, m_start)
                        overlap_end = min(inv_end, m_end)

                        if overlap_start <= overlap_end:
                            overlap_days = (overlap_end - overlap_start).days + 1
                            portion = inv_amount * (overlap_days / float(inv_total_days))
                            month_vals[m['code']] += portion
                            row_total += portion
                            month_totals[m['code']] += portion

                grand_total += row_total

                # Format dates
                start_str = rental.start_date.strftime('%d/%m/%Y') if rental.start_date else ''
                end_str = rental.end_date.strftime('%d/%m/%Y') if rental.end_date else ''

                row = {
                    'sn': sn,
                    'shop_code': prop.name or '',
                    'customer_name': rental.renter_id.name or '',
                    'remark_cust': '',
                    'location': prop.location_id.name if prop.location_id else '',
                    'floor': prop.floor_id.name if prop.floor_id else '',
                    'start_date': start_str,
                    'end_date': end_str,
                    'total_area': total_area,
                    'price_per_sqm': price_per_sqm,
                    'monthly_before_vat': monthly_before_vat,
                    'monthly_with_vat': monthly_with_vat,
                    'month_values': month_vals,
                    'total': row_total,
                    'remark': 'Active' if rental.state == 'in_contract' else (rental.state or ''),
                }
                rows.append(row)
                sn += 1

        return {
            'company_name': company_name,
            'period_title': period_title,
            'fiscal_year': self.fiscal_year,
            'months': months,
            'rows': rows,
            'month_totals': month_totals,
            'grand_total': grand_total,
        }

    def action_view_list(self):
        """Populates rental.sales.report.line and opens the report directly in List view."""
        self.ensure_one()
        # Clean existing temporary lines
        self.env['rental.sales.report.line'].search([('wizard_id', '=', self.id)]).unlink()

        data = self._get_report_data()
        line_vals = []
        for r in data['rows']:
            m_vals = r['month_values']
            line_vals.append({
                'wizard_id': self.id,
                'fiscal_year': self.fiscal_year,
                'sn': r['sn'],
                'shop_code': r['shop_code'],
                'customer_name': r['customer_name'],
                'remark_cust': r['remark_cust'],
                'location': r['location'],
                'floor': r['floor'],
                'start_date': r['start_date'],
                'end_date': r['end_date'],
                'total_area': r['total_area'],
                'price_per_sqm': r['price_per_sqm'],
                'monthly_before_vat': r['monthly_before_vat'],
                'monthly_with_vat': r['monthly_with_vat'],
                'm_0': m_vals.get('m_0', 0.0),
                'm_1': m_vals.get('m_1', 0.0),
                'm_2': m_vals.get('m_2', 0.0),
                'm_3': m_vals.get('m_3', 0.0),
                'm_4': m_vals.get('m_4', 0.0),
                'm_5': m_vals.get('m_5', 0.0),
                'm_6': m_vals.get('m_6', 0.0),
                'm_7': m_vals.get('m_7', 0.0),
                'm_8': m_vals.get('m_8', 0.0),
                'm_9': m_vals.get('m_9', 0.0),
                'm_10': m_vals.get('m_10', 0.0),
                'm_11': m_vals.get('m_11', 0.0),
                'total': r['total'],
                'remark': r['remark'],
            })
        if line_vals:
            self.env['rental.sales.report.line'].create(line_vals)

        return {
            'name': _('Rental Summary of Sales — %s') % data['period_title'],
            'type': 'ir.actions.act_window',
            'res_model': 'rental.sales.report.line',
            'view_mode': 'list',
            'domain': [('wizard_id', '=', self.id)],
            'target': 'current',
        }

    def action_generate_excel(self):
        """Returns action to download the Excel report via controller."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/rental_sales_report/download_excel?wizard_id={self.id}',
            'target': 'self',
        }

    def action_generate_pdf(self):
        """Prints PDF report."""
        self.ensure_one()
        return self.env.ref(
            'property_rental_sales_report.action_report_rental_sales'
        ).report_action(self)

    def _generate_excel_binary(self):
        self.ensure_one()
        data = self._get_report_data()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Summary of Sales')

        # Formats
        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'left', 'valign': 'vcenter'
        })
        subtitle_fmt = workbook.add_format({
            'bold': True, 'font_size': 11, 'align': 'left', 'valign': 'vcenter'
        })
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#D9E1F2', 'border': 1,
            'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'font_size': 9
        })
        cell_fmt = workbook.add_format({
            'border': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 9
        })
        num_fmt = workbook.add_format({
            'border': 1, 'align': 'right', 'valign': 'vcenter', 'num_format': '#,##0.00', 'font_size': 9
        })
        total_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': '#FFF2CC',
            'align': 'right', 'valign': 'vcenter', 'num_format': '#,##0.00', 'font_size': 9
        })
        total_lbl_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': '#FFF2CC',
            'align': 'center', 'valign': 'vcenter', 'font_size': 9
        })

        # Write Header Titles
        sheet.write(0, 0, data['company_name'], title_fmt)
        sheet.write(1, 0, 'SUMMARY OF SALES', subtitle_fmt)
        sheet.write(2, 0, data['period_title'], subtitle_fmt)

        # Columns
        headers = [
            'S/N', 'Shop Code', 'Customer Name', 'Remark', 'Location', 'Floor',
            'Rent Starting Date', 'Rent End Date', 'Total Area', 'Price /Sqm Befor vat',
            'Monthly Payments Befor vat', 'Monthly Payments With vat'
        ]
        # Append the 12 Ethiopian months
        for m in data['months']:
            headers.append(m['label'])
        headers.extend(['TOTAL', 'Remark'])

        header_row = 4
        for col_idx, h_text in enumerate(headers):
            sheet.write(header_row, col_idx, h_text, header_fmt)

        current_row = 5
        for row in data['rows']:
            sheet.write(current_row, 0, row['sn'], cell_fmt)
            sheet.write(current_row, 1, row['shop_code'], cell_fmt)
            sheet.write(current_row, 2, row['customer_name'], cell_fmt)
            sheet.write(current_row, 3, row['remark_cust'], cell_fmt)
            sheet.write(current_row, 4, row['location'], cell_fmt)
            sheet.write(current_row, 5, row['floor'], cell_fmt)
            sheet.write(current_row, 6, row['start_date'], cell_fmt)
            sheet.write(current_row, 7, row['end_date'], cell_fmt)
            sheet.write(current_row, 8, row['total_area'], num_fmt)
            sheet.write(current_row, 9, row['price_per_sqm'], num_fmt)
            sheet.write(current_row, 10, row['monthly_before_vat'], num_fmt)
            sheet.write(current_row, 11, row['monthly_with_vat'], num_fmt)

            # Month amounts
            for m_idx, m in enumerate(data['months']):
                col = 12 + m_idx
                val = row['month_values'].get(m['code'], 0.0)
                sheet.write(current_row, col, val if val else '', num_fmt)

            sheet.write(current_row, 12 + len(data['months']), row['total'], num_fmt)
            sheet.write(current_row, 13 + len(data['months']), row['remark'], cell_fmt)
            current_row += 1

        # Summary Row (TOTALS)
        sheet.write(current_row, 0, '', total_lbl_fmt)
        sheet.write(current_row, 1, 'TOTAL', total_lbl_fmt)
        for c in range(2, 12):
            sheet.write(current_row, c, '', total_lbl_fmt)

        for m_idx, m in enumerate(data['months']):
            col = 12 + m_idx
            sheet.write(current_row, col, data['month_totals'].get(m['code'], 0.0), total_fmt)

        sheet.write(current_row, 12 + len(data['months']), data['grand_total'], total_fmt)
        sheet.write(current_row, 13 + len(data['months']), '', total_lbl_fmt)

        # Set Column Widths
        sheet.set_column(0, 0, 6)    # S/N
        sheet.set_column(1, 1, 12)   # Shop Code
        sheet.set_column(2, 2, 25)   # Customer Name
        sheet.set_column(3, 3, 10)   # Remark
        sheet.set_column(4, 4, 18)   # Location
        sheet.set_column(5, 5, 12)   # Floor
        sheet.set_column(6, 7, 12)   # Dates
        sheet.set_column(8, 11, 14)  # Area, Price, Monthly
        for col_i in range(12, 12 + len(data['months']) + 1):
            sheet.set_column(col_i, col_i, 13) # Month columns & total

        workbook.close()
        output.seek(0)
        filename = f"Rental_Summary_of_Sales_{data['fiscal_year']}.xlsx"
        return output.read(), filename
