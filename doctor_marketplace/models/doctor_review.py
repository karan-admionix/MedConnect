# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DoctorReview(models.Model):
    _name = 'doctor.review'
    _description = 'Doctor Review'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    doctor_id = fields.Many2one('doctor.doctor', string='Doctor', required=True, ondelete='cascade')
    patient_id = fields.Many2one('doctor.patient', string='Patient', required=True, ondelete='cascade')
    appointment_id = fields.Many2one('doctor.appointment', string='Appointment')

    rating = fields.Float(string='Rating', required=True)
    title = fields.Char(string='Title')
    review = fields.Text(string='Review', required=True)

    would_recommend = fields.Boolean(string='Would Recommend')

    # Aspect ratings
    punctuality_rating = fields.Float(string='Punctuality')
    communication_rating = fields.Float(string='Communication')
    treatment_rating = fields.Float(string='Treatment')

    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending')

    rejection_reason = fields.Text(string='Rejection Reason')

    doctor_response = fields.Text(string='Doctor Response')
    doctor_response_date = fields.Datetime(string='Response Date')

    helpful_count = fields.Integer(string='Helpful Votes', default=0)

    is_verified_booking = fields.Boolean(compute='_compute_verified_booking', string='Verified', store=True)

    @api.constrains('rating')
    def _check_rating(self):
        for record in self:
            if record.rating < 1 or record.rating > 5:
                raise ValidationError(_('Rating must be between 1 and 5.'))

    @api.depends('appointment_id')
    def _compute_verified_booking(self):
        for record in self:
            record.is_verified_booking = bool(record.appointment_id and record.appointment_id.state == 'completed')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            # Read appointment state directly to avoid depending on computed field
            # that may not yet be evaluated at create time
            if record.appointment_id and record.appointment_id.state == 'completed':
                record.state = 'approved'
            if record.appointment_id:
                record.appointment_id.review_id = record.id
        return records

    def action_approve(self):
        for record in self:
            record.state = 'approved'

    def action_reject(self):
        for record in self:
            record.state = 'rejected'
