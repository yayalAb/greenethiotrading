# -*- coding: utf-8 -*-
from odoo import api, models

class ReportRentalSales(models.AbstractModel):
    _name = 'report.property_rental_sales_report.report_rental_sales'
    _description = 'Property Rental Summary of Sales QWeb Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['property.rental.sales.report.wizard'].browse(docids)
        if not wizard.exists():
            wizard = self.env['property.rental.sales.report.wizard'].search([], limit=1, order='id desc')
        if not wizard:
            wizard = self.env['property.rental.sales.report.wizard'].create({})
        report_data = wizard._get_report_data()
        return {
            'doc_ids': docids or [wizard.id],
            'doc_model': 'property.rental.sales.report.wizard',
            'docs': wizard,
            'data': report_data,
        }
