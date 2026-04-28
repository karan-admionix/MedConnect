# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class DoctorAppointment(models.Model):
    _name = 'doctor.appointment'
    _description = 'Doctor Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'appointment_date desc, appointment_time desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')

    doctor_id = fields.Many2one('doctor.doctor', string='Doctor', required=True, ondelete='restrict')
    patient_id = fields.Many2one('doctor.patient', string='Patient', required=True, ondelete='restrict')
    family_member_id = fields.Many2one('doctor.family.member', string='For Family Member')

    # Derived fields
    doctor_name = fields.Char(related='doctor_id.name', store=True)
    patient_name = fields.Char(related='patient_id.name', store=True)
    specialization_id = fields.Many2one(related='doctor_id.specialization_id', store=True)

    # Date & Time
    appointment_date = fields.Date(string='Date', required=True, tracking=True)
    appointment_time = fields.Float(string='Time', required=True)
    appointment_time_display = fields.Char(compute='_compute_time_display', string='Time')
    duration = fields.Integer(string='Duration (min)', related='doctor_id.consultation_duration')

    # Consultation Type
    consultation_type = fields.Selection([
        ('new', 'New Consultation'),
        ('followup', 'Follow-up'),
    ], string='Type', default='new', required=True)

    consultation_mode = fields.Selection([
        ('in_person', 'In-Person'),
        ('video', 'Video Call'),
        ('audio', 'Audio Call'),
        ('home_visit', 'Home Visit'),
    ], string='Mode', default='in_person')

    reason = fields.Text(string='Reason for Visit')
    symptoms = fields.Text(string='Symptoms')

    # Pricing
    base_fee = fields.Float(string='Base Fee', related='doctor_id.consultation_fee')
    consultation_fee = fields.Float(string='Consultation Fee', required=True)
    discount_amount = fields.Float(string='Discount')
    subscription_discount = fields.Float(string='Subscription Discount')
    final_amount = fields.Float(compute='_compute_final_amount', string='Final Amount', store=True)

    # Platform fees
    platform_commission_percent = fields.Float(string='Commission %', default=15.0)
    platform_commission = fields.Float(compute='_compute_commission', string='Platform Commission', store=True)
    doctor_payout = fields.Float(compute='_compute_commission', string='Doctor Payout', store=True)

    # Payment
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ], string='Payment Status', default='pending', tracking=True)
    payment_method = fields.Selection([
        ('online', 'Online Payment'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('cash', 'Cash'),
        ('subscription', 'Subscription'),
    ], string='Payment Method')
    payment_reference = fields.Char(string='Payment Reference')
    payment_date = fields.Datetime(string='Payment Date')

    refund_amount = fields.Float(string='Refund Amount')
    refund_reason = fields.Text(string='Refund Reason')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ], string='Status', default='draft', tracking=True)

    cancelled_by = fields.Selection([
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('system', 'System'),
    ], string='Cancelled By')
    cancellation_reason = fields.Text(string='Cancellation Reason')

    # Consultation Notes
    diagnosis = fields.Text(string='Diagnosis')
    prescription = fields.Html(string='Prescription', sanitize=True)
    doctor_notes = fields.Text(string='Doctor Notes')
    follow_up_required = fields.Boolean(string='Follow-up Required')
    follow_up_date = fields.Date(string='Suggested Follow-up Date')

    # Review
    review_id = fields.Many2one('doctor.review', string='Review')
    has_review = fields.Boolean(compute='_compute_has_review', string='Has Review', store=True)

    # Waitlist
    booked_from_waitlist = fields.Boolean(string='From Waitlist', default=False)
    waitlist_id = fields.Many2one('doctor.waitlist', string='Waitlist Entry')

    @api.depends('appointment_time')
    def _compute_time_display(self):
        for record in self:
            hours = int(record.appointment_time)
            minutes = int((record.appointment_time - hours) * 60)
            period = 'AM' if hours < 12 else 'PM'
            display_hours = hours if hours <= 12 else hours - 12
            if display_hours == 0:
                display_hours = 12
            record.appointment_time_display = f'{display_hours:02d}:{minutes:02d} {period}'

    @api.depends('consultation_fee', 'discount_amount', 'subscription_discount')
    def _compute_final_amount(self):
        for record in self:
            record.final_amount = record.consultation_fee - (record.discount_amount or 0) - (
                    record.subscription_discount or 0)

    @api.depends('final_amount', 'platform_commission_percent')
    def _compute_commission(self):
        for record in self:
            record.platform_commission = record.final_amount * (record.platform_commission_percent / 100)
            record.doctor_payout = record.final_amount - record.platform_commission

    @api.depends('review_id')
    def _compute_has_review(self):
        for record in self:
            record.has_review = bool(record.review_id)

    @api.constrains('appointment_date', 'appointment_time', 'doctor_id')
    def _check_slot_availability(self):
        for record in self:
            if record.state in ['cancelled', 'no_show']:
                continue
            existing = self.search([
                ('id', '!=', record.id),
                ('doctor_id', '=', record.doctor_id.id),
                ('appointment_date', '=', record.appointment_date),
                ('appointment_time', '=', record.appointment_time),
                ('state', 'not in', ['cancelled', 'no_show']),
            ])
            if existing:
                raise ValidationError(_('This time slot is already booked!'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('doctor.appointment') or 'New'
            if not vals.get('consultation_fee') and vals.get('doctor_id'):
                doctor = self.env['doctor.doctor'].browse(vals['doctor_id'])
                if vals.get('consultation_type') == 'followup':
                    vals['consultation_fee'] = doctor.followup_fee or doctor.consultation_fee
                else:
                    vals['consultation_fee'] = doctor.consultation_fee
        return super().create(vals_list)

    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'
            record.patient_id.add_loyalty_points(10, 'Booking confirmed')

    def action_start(self):
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_('Only confirmed appointments can be started.'))
            record.state = 'in_progress'

    def action_complete(self):
        for record in self:
            if record.state not in ['confirmed', 'in_progress']:
                raise UserError(_('Cannot complete this appointment.'))
            record.state = 'completed'

            # Determine earning type based on consultation type and mode
            if record.consultation_type == 'followup':
                earning_type = 'followup'
            elif record.consultation_mode == 'video':
                earning_type = 'video'
            else:
                earning_type = 'consultation'

            # Create earning record
            self.env['doctor.earning'].create({
                'doctor_id': record.doctor_id.id,
                'appointment_id': record.id,
                'date': fields.Date.today(),
                'gross_amount': record.final_amount,
                'platform_commission': record.platform_commission,
                'earning_type': earning_type,
            })

            record.patient_id.add_loyalty_points(50, 'Completed consultation')

    def action_cancel(self):
        for record in self:
            record.write({
                'state': 'cancelled',
                'cancelled_by': 'patient',
            })

    def action_no_show(self):
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_('Only confirmed appointments can be marked as no-show.'))
            record.state = 'no_show'
