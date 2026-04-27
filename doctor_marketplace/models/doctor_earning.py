# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class DoctorEarning(models.Model):
    _name = 'doctor.earning'
    _description = 'Doctor Earning'
    _order = 'date desc'

    doctor_id = fields.Many2one('doctor.doctor', string='Doctor', required=True, ondelete='cascade')
    appointment_id = fields.Many2one('doctor.appointment', string='Appointment', ondelete='set null')

    date = fields.Date(string='Date', required=True, default=fields.Date.today)

    earning_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('followup', 'Follow-up'),
        ('video', 'Video Consultation'),
        ('referral', 'Referral Commission'),
        ('bonus', 'Bonus'),
        ('adjustment', 'Adjustment'),
    ], string='Type', default='consultation')

    description = fields.Char(string='Description')

    gross_amount = fields.Float(string='Gross Amount')
    platform_commission = fields.Float(string='Platform Commission')
    net_amount = fields.Float(compute='_compute_net_amount', string='Net Amount', store=True)

    payout_id = fields.Many2one('doctor.payout', string='Payout')
    is_paid = fields.Boolean(compute='_compute_is_paid', string='Paid', store=True)

    @api.depends('gross_amount', 'platform_commission')
    def _compute_net_amount(self):
        for record in self:
            record.net_amount = record.gross_amount - (record.platform_commission or 0)

    @api.depends('payout_id', 'payout_id.state')
    def _compute_is_paid(self):
        for record in self:
            record.is_paid = record.payout_id and record.payout_id.state == 'completed'
