# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import timedelta
import uuid


class PatientHealthRecord(models.Model):
    _name = 'patient.health.record'
    _description = 'Patient Health Record'
    _inherit = ['mail.thread']
    _order = 'record_date desc'

    name = fields.Char(string='Record Name', required=True)

    patient_id = fields.Many2one('doctor.patient', string='Patient', required=True, ondelete='cascade')
    doctor_id = fields.Many2one('doctor.doctor', string='Doctor')
    appointment_id = fields.Many2one('doctor.appointment', string='Appointment')

    record_type = fields.Selection([
        ('consultation', 'Consultation Notes'),
        ('prescription', 'Prescription'),
        ('lab_report', 'Lab Report'),
        ('imaging', 'Imaging/Scan'),
        ('vaccination', 'Vaccination'),
        ('allergy', 'Allergy Record'),
        ('surgery', 'Surgery Record'),
        ('discharge', 'Discharge Summary'),
        ('other', 'Other'),
    ], string='Record Type', required=True)

    record_date = fields.Date(string='Date', required=True, default=fields.Date.today)

    # Content
    description = fields.Text(string='Description')
    notes = fields.Html(string='Notes', sanitize=True)

    # Attachments
    attachment = fields.Binary(string='Attachment', attachment=True)
    attachment_filename = fields.Char(string='Filename')

    # Source
    source = fields.Selection([
        ('platform', 'Platform Generated'),
        ('upload', 'Patient Upload'),
        ('external', 'External Provider'),
    ], string='Source', default='platform')

    # Sharing
    is_shared = fields.Boolean(string='Shared', default=False)
    share_token = fields.Char(string='Share Token')
    share_expiry = fields.Datetime(string='Share Expiry')
    shared_with_doctor_ids = fields.Many2many('doctor.doctor', string='Shared With')

    # Verification
    is_verified = fields.Boolean(string='Verified', default=False)
    verified_by = fields.Many2one('res.users', string='Verified By')
    verified_date = fields.Datetime(string='Verified Date')

    active = fields.Boolean(string='Active', default=True)

    def action_generate_share_link(self):
        """Generate a shareable link."""
        self.ensure_one()
        self.write({
            'is_shared': True,
            'share_token': str(uuid.uuid4()),
            'share_expiry': fields.Datetime.now() + timedelta(days=7),
        })

    def action_verify(self):
        for record in self:
            record.write({
                'is_verified': True,
                'verified_by': self.env.user.id,
                'verified_date': fields.Datetime.now(),
            })
