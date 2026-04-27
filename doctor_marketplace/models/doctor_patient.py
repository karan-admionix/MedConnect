# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date


class DoctorPatient(models.Model):
    _name = 'doctor.patient'
    _description = 'Patient Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Full Name', required=True, tracking=True)
    image = fields.Binary(string='Photo', attachment=True)
    partner_id = fields.Many2one('res.partner', string='Contact', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Portal User', ondelete='set null')

    # Contact
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')

    # Demographics
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(compute='_compute_age', string='Age')
    blood_group = fields.Selection([
        ('a_positive', 'A+'),
        ('a_negative', 'A-'),
        ('b_positive', 'B+'),
        ('b_negative', 'B-'),
        ('ab_positive', 'AB+'),
        ('ab_negative', 'AB-'),
        ('o_positive', 'O+'),
        ('o_negative', 'O-'),
    ], string='Blood Group')

    # Address
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country',
                                 default=lambda self: self.env.ref('base.in', raise_if_not_found=False))
    zip_code = fields.Char(string='PIN Code')

    # Emergency Contact
    emergency_contact_name = fields.Char(string='Emergency Contact Name')
    emergency_contact_phone = fields.Char(string='Emergency Contact Phone')
    emergency_contact_relation = fields.Char(string='Relationship')

    # Medical Info
    allergies = fields.Text(string='Known Allergies')
    chronic_conditions = fields.Text(string='Chronic Conditions')
    current_medications = fields.Text(string='Current Medications')

    # Family Account
    is_primary_account = fields.Boolean(string='Primary Account', default=True)
    family_member_ids = fields.One2many('doctor.family.member', 'patient_id', string='Family Members')
    family_member_count = fields.Integer(compute='_compute_family_count', string='Family Members')

    # Appointments
    appointment_ids = fields.One2many('doctor.appointment', 'patient_id', string='Appointments')
    appointment_count = fields.Integer(compute='_compute_appointment_stats', string='Appointments')
    completed_appointments = fields.Integer(compute='_compute_appointment_stats', string='Completed')

    # No-show tracking
    no_show_count = fields.Integer(compute='_compute_no_show_stats', string='No-Shows')
    cancellation_count = fields.Integer(compute='_compute_no_show_stats', string='Cancellations')
    risk_score = fields.Float(compute='_compute_no_show_stats', string='Risk Score')

    # Subscription (Phase 2)
    subscription_id = fields.Many2one('patient.subscription', string='Active Subscription')
    subscription_plan_id = fields.Many2one(related='subscription_id.plan_id', string='Plan')

    # Health Records (Phase 2)
    health_record_ids = fields.One2many('patient.health.record', 'patient_id', string='Health Records')

    # Statistics
    total_spent = fields.Float(compute='_compute_stats', string='Total Spent')
    loyalty_points = fields.Integer(string='Loyalty Points', default=0)

    active = fields.Boolean(string='Active', default=True)

    _constraints = [
        models.Constraint('UNIQUE(email)', 'Email address already exists!'),
    ]

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.date_of_birth:
                born = record.date_of_birth
                record.age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            else:
                record.age = 0

    @api.depends('family_member_ids')
    def _compute_family_count(self):
        for record in self:
            record.family_member_count = len(record.family_member_ids)

    @api.depends('appointment_ids', 'appointment_ids.state')
    def _compute_appointment_stats(self):
        for record in self:
            record.appointment_count = len(record.appointment_ids)
            record.completed_appointments = len(record.appointment_ids.filtered(lambda a: a.state == 'completed'))

    @api.depends('appointment_ids', 'appointment_ids.state')
    def _compute_no_show_stats(self):
        for record in self:
            appointments = record.appointment_ids
            record.no_show_count = len(appointments.filtered(lambda a: a.state == 'no_show'))
            record.cancellation_count = len(appointments.filtered(lambda a: a.state == 'cancelled'))

            total = len(appointments)
            if total > 0:
                record.risk_score = (record.no_show_count / total) * 100
            else:
                record.risk_score = 0

    @api.depends('appointment_ids')
    def _compute_stats(self):
        for record in self:
            completed = record.appointment_ids.filtered(lambda a: a.state == 'completed')
            record.total_spent = sum(completed.mapped('final_amount'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('partner_id'):
                partner = self.env['res.partner'].create({
                    'name': vals.get('name'),
                    'email': vals.get('email'),
                    'phone': vals.get('mobile') or vals.get('phone'),
                    'is_company': False,
                })
                vals['partner_id'] = partner.id

            # Create portal user if email provided and no user yet
            if vals.get('email') and not vals.get('user_id'):
                existing_user = self.env['res.users'].search(
                    [('login', '=', vals['email'])], limit=1
                )
                if not existing_user:
                    user = self.env['res.users'].with_context(no_reset_password=True).create({
                        'name': vals.get('name'),
                        'login': vals['email'],
                        'email': vals['email'],
                        'groups_id': [(6, 0, [
                            self.env.ref('base.group_portal').id,
                        ])],
                        'partner_id': vals['partner_id'],
                    })
                    vals['user_id'] = user.id
                else:
                    vals['user_id'] = existing_user.id

        return super().create(vals_list)

    def add_loyalty_points(self, points, reason=None):
        """Add loyalty points to patient."""
        self.ensure_one()
        self.loyalty_points += points

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'doctor.appointment',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }
