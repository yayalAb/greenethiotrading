# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from ..wizards import ethiopian_calendar_util as eth_util


class RentalSalesReportLine(models.Model):
    """Stores generated report rows for direct list view display,
    sorting, filtering, and export (Excel & PDF)."""
    _name = 'rental.sales.report.line'
    _description = 'Rental Summary of Sales Line'
    _order = 'sn asc, shop_code asc'

    wizard_id = fields.Integer(string='Report Wizard ID', index=True)
    fiscal_year = fields.Integer(string='Ethiopian Fiscal Year', index=True, default=2018)

    sn = fields.Integer(string='S/N')
    shop_code = fields.Char(string='Shop Code')
    customer_name = fields.Char(string='Customer Name')
    remark_cust = fields.Char(string='Customer Remark')
    location = fields.Char(string='Location')
    floor = fields.Char(string='Floor')
    start_date = fields.Char(string='Rent Starting Date')
    end_date = fields.Char(string='Rent End Date')
    total_area = fields.Float(string='Total Area (m²)', digits=(16, 2))
    price_per_sqm = fields.Float(string='Price /Sqm Befor vat', digits=(16, 2))
    monthly_before_vat = fields.Float(string='Monthly Payments Befor vat', digits=(16, 2))
    monthly_with_vat = fields.Float(string='Monthly Payments With vat', digits=(16, 2))

    # 12 Ethiopian Month Columns
    m_0 = fields.Float(string='Hmle/Prev', digits=(16, 2))
    m_1 = fields.Float(string='Nehase/Prev', digits=(16, 2))
    m_2 = fields.Float(string='Meskerem/Curr', digits=(16, 2))
    m_3 = fields.Float(string='Tikimt/Curr', digits=(16, 2))
    m_4 = fields.Float(string='Hidar/Curr', digits=(16, 2))
    m_5 = fields.Float(string='Tahsas/Curr', digits=(16, 2))
    m_6 = fields.Float(string='Tir/Curr', digits=(16, 2))
    m_7 = fields.Float(string='Yekatit/Curr', digits=(16, 2))
    m_8 = fields.Float(string='Megabit/Curr', digits=(16, 2))
    m_9 = fields.Float(string='Miazia/Curr', digits=(16, 2))
    m_10 = fields.Float(string='Ginbot/Curr', digits=(16, 2))
    m_11 = fields.Float(string='Sene/Curr', digits=(16, 2))

    total = fields.Float(string='TOTAL', digits=(16, 2))
    remark = fields.Char(string='Remark')

    @api.model
    def action_refresh_data(self):
        """Populates report lines with current data and opens the list view directly."""
        wizard = self.env['property.rental.sales.report.wizard'].create({})
        return wizard.action_view_list()

    def action_export_excel(self):
        """Export full report or selected records to Excel."""
        wizard = self.env['property.rental.sales.report.wizard'].search([], limit=1, order='id desc')
        if not wizard:
            wizard = self.env['property.rental.sales.report.wizard'].create({})
        return wizard.action_generate_excel()

    def action_export_pdf(self):
        """Print / Export PDF report."""
        wizard = self.env['property.rental.sales.report.wizard'].search([], limit=1, order='id desc')
        if not wizard:
            wizard = self.env['property.rental.sales.report.wizard'].create({})
        return wizard.action_generate_pdf()
