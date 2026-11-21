# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class RentalSalesReportController(http.Controller):

    @http.route('/rental_sales_report/download_excel', type='http', auth='user')
    def download_excel(self, wizard_id, **kw):
        wizard = request.env['property.rental.sales.report.wizard'].browse(int(wizard_id))
        if not wizard.exists():
            return request.not_found()

        excel_data, filename = wizard._generate_excel_binary()
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', f'attachment; filename="{filename}"'),
            ('Content-Length', len(excel_data)),
        ]
        return request.make_response(excel_data, headers=headers)
