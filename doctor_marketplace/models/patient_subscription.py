# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class PatientSubscription(models.Model):
    _name = 'patient.subscription'
    _description = 'Patient Subscription'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')

    patient_id = fields.Many2one('doctor.patient', string='Patient', required=True, ondelete='cascade')
    plan_id = fields.Many2one('subscription.plan', string='Plan', required=True)

    # Billing
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
    ], string='Billing Cycle', default='monthly', required=True)

    amount = fields.Float(string='Amount', compute='_compute_amount', store=True)

    # Dates
    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    end_date = fields.Date(string='End Date', compute='_compute_end_date', store=True)
    next_billing_date = fields.Date(string='Next Billing', compute='_compute_end_date', store=True)

    # Usage
    free_consultations_remaining = fields.Integer(string='Free Consultations Left')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    auto_renew = fields.Boolean(string='Auto-Renew', default=True)

    # Payment
    payment_ids = fields.One2many('subscription.payment', 'subscription_id', string='Payments')

    @api.depends('plan_id', 'billing_cycle')
    def _compute_amount(self):
        for record in self:
            if record.plan_id:
                if record.billing_cycle == 'annual':
                    record.amount = record.plan_id.annual_price or (record.plan_id.price * 12)
                else:
                    record.amount = record.plan_id.price
            else:
                record.amount = 0

    @api.depends('start_date', 'billing_cycle')
    def _compute_end_date(self):
        for record in self:
            if record.start_date:
                if record.billing_cycle == 'annual':
                    record.end_date = record.start_date + relativedelta(years=1)
                else:
                    record.end_date = record.start_date + relativedelta(months=1)
                record.next_billing_date = record.end_date
            else:
                record.end_date = False
                record.next_billing_date = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('patient.subscription') or 'New'
            # Set initial free consultations
            if vals.get('plan_id'):
                plan = self.env['subscription.plan'].browse(vals['plan_id'])
                vals['free_consultations_remaining'] = plan.free_consultations
        return super().create(vals_list)

    def action_activate(self):
        for record in self:
            record.state = 'active'
            # Link to patient
            record.patient_id.subscription_id = record.id

    def action_pause(self):
        for record in self:
            record.state = 'paused'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
            if record.patient_id.subscription_id == record:
                record.patient_id.subscription_id = False

    def use_free_consultation(self):
        """Use one free consultation."""
        self.ensure_one()
        if self.free_consultations_remaining > 0:
            self.free_consultations_remaining -= 1
            return True
        return False

    def get_discount_amount(self, base_price):
        """Get discount based on subscription plan."""
        self.ensure_one()
        if self.plan_id.consultation_discount:
            return base_price * (self.plan_id.consultation_discount / 100)
        return 0


class SubscriptionPayment(models.Model):
    _name = 'subscription.payment'
    _description = 'Subscription Payment'
    _order = 'payment_date desc'

    subscription_id = fields.Many2one('patient.subscription', string='Subscription', required=True, ondelete='cascade')

    amount = fields.Float(string='Amount', required=True)
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.today)
    payment_method = fields.Char(string='Payment Method')
    payment_reference = fields.Char(string='Reference')

    state = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ], string='Status', default='pending')
