# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestPropertyDashboard(TransactionCase):

    def test_get_dashboard_data_structure(self):
        data = self.env["property.dashboard"].get_dashboard_data()
        self.assertIn("kpis", data)
        self.assertEqual(len(data["kpis"]), 4)
        self.assertIn("collection", data)
        self.assertIn("charts", data)
        self.assertEqual(len(data["charts"]["months"]), 12)
        self.assertIn("top_properties", data)
        self.assertIn("countries", data)
        action = self.env["property.dashboard"].action_open("contracts")
        self.assertEqual(action["res_model"], "property.rental")
