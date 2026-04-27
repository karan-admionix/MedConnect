# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta


class DoctorWaitlist(models.Model):
    _name = 'doctor.waitlist'
    _description = 'Doctor Waitlist'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')

    doctor_id = fields.Many2one('doctor.doctor', string='Doctor', required=True, ondelete='cascade')
    patient_id = fields.Many2one('doctor.patient', string='Patient', required=True, ondelete='cascade')

    # Preferred dates
    preferred_date = fields.Date(string='Preferred Date', required=True)
    date_flexibility = fields.Selection([
        ('exact', 'Exact Date'),
        ('1day', '± 1 Day'),
        ('3days', '± 3 Days'),
        ('1week', '± 1 Week'),
        ('any', 'Any Available'),
    ], string='Date Flexibility', default='3days')

    # Preferred time
    time_preference = fields.Selection([
        ('any', 'Any Time'),
        ('morning', 'Morning (9AM-12PM)'),
        ('afternoon', 'Afternoon (12PM-5PM)'),
        ('evening', 'Evening (5PM-9PM)'),
    ], string='Time Preference', default='any')

    # Auto-booking
    auto_book = fields.Boolean(string='Auto-Book When Available', default=True)
    max_price = fields.Float(string='Max Price', help='Auto-book only if price is below this')

    # Reason
    reason = fields.Text(string='Reason for Visit')

    # Priority
    priority = fields.Selection([
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='normal')

    # Status
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('notified', 'Notified'),
        ('auto_booked', 'Auto-Booked'),
        ('manually_booked', 'Manually Booked'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='waiting', tracking=True)

    # Result
    appointment_id = fields.Many2one('doctor.appointment', string='Booked Appointment')
    notified_date = fields.Datetime(string='Notified Date')
    booked_date = fields.Datetime(string='Booked Date')

    # Notifications
    notify_email = fields.Boolean(string='Email', default=True)
    notify_sms = fields.Boolean(string='SMS', default=True)

    expiry_date = fields.Date(string='Expires On')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('doctor.waitlist') or 'New'
            if not vals.get('expiry_date') and vals.get('preferred_date'):
                # Default expiry: 1 week after preferred date
                preferred = fields.Date.from_string(vals['preferred_date'])
                vals['expiry_date'] = preferred + timedelta(days=7)
        return super().create(vals_list)

    def action_notify(self):
        """Notify patient about available slot."""
        for record in self:
            record.write({
                'state': 'notified',
                'notified_date': fields.Datetime.now(),
            })
            # TODO: Send email/SMS notification

    def action_book(self, appointment_id):
        """Mark as booked."""
        self.ensure_one()
        self.write({
            'state': 'auto_booked' if self.auto_book else 'manually_booked',
            'appointment_id': appointment_id,
            'booked_date': fields.Datetime.now(),
        })

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    @api.model
    def _cron_expire_waitlist(self):
        """Expire old waitlist entries."""
        today = fields.Date.today()
        expired = self.search([
            ('state', '=', 'waiting'),
            ('expiry_date', '<', today),
        ])
        expired.write({'state': 'expired'})
