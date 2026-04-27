# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DoctorPayout(models.Model):
    _name = 'doctor.payout'
    _description = 'Doctor Payout'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    doctor_id = fields.Many2one('doctor.doctor', string='Doctor', required=True, ondelete='restrict')

    amount = fields.Float(string='Amount', required=True)

    earning_ids = fields.One2many('doctor.earning', 'payout_id', string='Earnings')
    earning_count = fields.Integer(compute='_compute_earning_count', string='Earnings')

    # Payment Details
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque'),
    ], string='Payment Method', default='bank_transfer')

    payment_reference = fields.Char(string='Transaction Reference')
    payment_date = fields.Date(string='Payment Date')

    # Bank details snapshot
    bank_name = fields.Char(string='Bank Name')
    bank_account = fields.Char(string='Account Number')
    bank_ifsc = fields.Char(string='IFSC')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    notes = fields.Text(string='Notes')

    @api.depends('earning_ids')
    def _compute_earning_count(self):
        for record in self:
            record.earning_count = len(record.earning_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('doctor.payout') or 'New'
            # Snapshot bank details
            if vals.get('doctor_id'):
                doctor = self.env['doctor.doctor'].browse(vals['doctor_id'])
                vals['bank_name'] = doctor.bank_name
                vals['bank_account'] = doctor.bank_account_number
                vals['bank_ifsc'] = doctor.bank_ifsc
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft payouts can be submitted.'))
            record.state = 'pending'

    def action_process(self):
        for record in self:
            record.state = 'processing'

    def action_complete(self):
        for record in self:
            record.write({
                'state': 'completed',
                'payment_date': fields.Date.today(),
            })

    def action_fail(self):
        for record in self:
            record.state = 'failed'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
