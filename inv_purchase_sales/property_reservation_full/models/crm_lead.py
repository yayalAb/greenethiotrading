# -*- coding: utf-8 -*-
##############################################################################
#    Ahadubit Technologies
#    Copyright (C) 2024-TODAY Ahadubit Technologies(<https://ahadubit.com>).
#    Author: Ahadubit Technologies (<https://ahadubit.com>)
##############################################################################
from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    reservation_ids = fields.One2many('property.reservation', inverse_name='crm_lead_id', string="Reservations")
    reservation_count = fields.Integer(compute='_compute_reservation_count')

    def _compute_reservation_count(self):
        for rec in self:
            rec.reservation_count = len(rec.reservation_ids)

    def action_view_reservations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reservations',
            'res_model': 'property.reservation',
            'view_mode': 'list,form',
            'domain': [('crm_lead_id', '=', self.id)],
            'context': {'default_crm_lead_id': self.id, 'default_partner_id': self.partner_id.id},
        }

    def action_set_reserved(self):
        """Move the opportunity to the 'Reserved' stage once its linked
        property reservation is sufficiently paid."""
        stage = self.env['crm.stage'].search([('name', 'ilike', 'Reserved')], limit=1)
        if stage:
            self.write({'stage_id': stage.id})

    def action_reserve(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reservation',
            'res_model': 'property.reservation',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_crm_lead_id': self.id,
            }
        }
