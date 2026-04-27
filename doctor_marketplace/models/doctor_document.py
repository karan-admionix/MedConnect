# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class DoctorDocument(models.Model):
    _name = 'doctor.document'
    _description = 'Doctor Verification Document'
    _order = 'document_type, create_date desc'

    doctor_id = fields.Many2one('doctor.doctor', string='Doctor', required=True, ondelete='cascade')

    name = fields.Char(string='Document Name', required=True)
    document_type = fields.Selection([
        ('license', 'Medical License'),
        ('degree', 'Degree Certificate'),
        ('registration', 'Registration Certificate'),
        ('identity', 'Identity Proof'),
        ('address', 'Address Proof'),
        ('photo', 'Photo'),
        ('other', 'Other'),
    ], string='Document Type', required=True)

    attachment = fields.Binary(string='Document', required=True, attachment=True)
    attachment_filename = fields.Char(string='Filename')

    state = fields.Selection([
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending')

    verified_by = fields.Many2one('res.users', string='Verified By')
    verified_date = fields.Datetime(string='Verified Date')
    rejection_reason = fields.Text(string='Rejection Reason')

    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    notes = fields.Text(string='Notes')

    def action_verify(self):
        for record in self:
            record.write({
                'state': 'verified',
                'verified_by': self.env.user.id,
                'verified_date': fields.Datetime.now(),
            })

    def action_reject(self):
        for record in self:
            record.state = 'rejected'
