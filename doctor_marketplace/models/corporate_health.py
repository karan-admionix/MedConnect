# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta


class CorporateAccount(models.Model):
    _name = 'corporate.account'
    _description = 'Corporate Account'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Company Name', required=True, tracking=True)
    code = fields.Char(string='Account Code', readonly=True, copy=False)
    image = fields.Binary(string='Logo', attachment=True)
    partner_id = fields.Many2one('res.partner', string='Contact', ondelete='cascade')
    
    # Contact Information
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    website = fields.Char(string='Website')
    
    # Address
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.ref('base.in', raise_if_not_found=False))
    zip_code = fields.Char(string='PIN Code')
    
    # Company Details
    industry = fields.Selection([
        ('it', 'IT & Technology'),
        ('finance', 'Finance & Banking'),
        ('healthcare', 'Healthcare'),
        ('manufacturing', 'Manufacturing'),
        ('retail', 'Retail'),
        ('education', 'Education'),
        ('government', 'Government'),
        ('other', 'Other'),
    ], string='Industry')
    
    company_size = fields.Selection([
        ('small', '1-50 Employees'),
        ('medium', '51-200 Employees'),
        ('large', '201-500 Employees'),
        ('enterprise', '500+ Employees'),
    ], string='Company Size')
    
    gst_number = fields.Char(string='GST Number')
    pan_number = fields.Char(string='PAN Number')
    
    # Primary Contact
    contact_person = fields.Char(string='Contact Person')
    contact_email = fields.Char(string='Contact Email')
    contact_phone = fields.Char(string='Contact Phone')
    contact_designation = fields.Char(string='Designation')
    
    # HR Contact
    hr_name = fields.Char(string='HR Name')
    hr_email = fields.Char(string='HR Email')
    hr_phone = fields.Char(string='HR Phone')
    
    # Plan Details
    plan_id = fields.Many2one('corporate.plan', string='Health Plan')
    contract_start = fields.Date(string='Contract Start')
    contract_end = fields.Date(string='Contract End')
    
    # Employees
    employee_ids = fields.One2many('corporate.employee', 'corporate_id', string='Employees')
    employee_count = fields.Integer(compute='_compute_employee_count', string='Total Employees')
    active_employee_count = fields.Integer(compute='_compute_employee_count', string='Active Employees')
    
    # Dependents
    max_dependents_per_employee = fields.Integer(string='Max Dependents', default=4)
    dependent_count = fields.Integer(compute='_compute_employee_count', string='Total Dependents')
    
    # Financials
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ], string='Billing Cycle', default='monthly')
    
    per_employee_cost = fields.Float(string='Per Employee Cost')
    total_monthly_cost = fields.Float(compute='_compute_costs', string='Monthly Cost')
    
    # Usage Stats
    appointment_ids = fields.One2many('doctor.appointment', 'corporate_id', string='Appointments')
    total_appointments = fields.Integer(compute='_compute_stats', string='Total Appointments')
    total_spent = fields.Float(compute='_compute_stats', string='Total Healthcare Spend')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', tracking=True)
    
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('corporate.account') or 'NEW'
        return super().create(vals_list)

    @api.depends('employee_ids', 'employee_ids.state', 'employee_ids.dependent_ids')
    def _compute_employee_count(self):
        for record in self:
            record.employee_count = len(record.employee_ids)
            record.active_employee_count = len(record.employee_ids.filtered(lambda e: e.state == 'active'))
            record.dependent_count = sum(len(e.dependent_ids) for e in record.employee_ids)

    @api.depends('active_employee_count', 'per_employee_cost')
    def _compute_costs(self):
        for record in self:
            record.total_monthly_cost = record.active_employee_count * (record.per_employee_cost or 0)

    @api.depends('appointment_ids')
    def _compute_stats(self):
        for record in self:
            completed = record.appointment_ids.filtered(lambda a: a.state == 'completed')
            record.total_appointments = len(completed)
            record.total_spent = sum(completed.mapped('final_amount'))

    def action_submit(self):
        self.state = 'pending'

    def action_approve(self):
        self.state = 'active'

    def action_suspend(self):
        self.state = 'suspended'


class CorporatePlan(models.Model):
    _name = 'corporate.plan'
    _description = 'Corporate Health Plan'
    _order = 'sequence, name'

    name = fields.Char(string='Plan Name', required=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Html(string='Description')
    
    # Pricing
    base_price_per_employee = fields.Float(string='Base Price/Employee')
    dependent_price = fields.Float(string='Dependent Price')
    
    # Benefits
    free_consultations = fields.Integer(string='Free Consultations/Year', default=0)
    consultation_discount = fields.Float(string='Consultation Discount %', default=0)
    
    lab_discount = fields.Float(string='Lab Test Discount %', default=0)
    pharmacy_discount = fields.Float(string='Pharmacy Discount %', default=0)
    
    health_checkup_included = fields.Boolean(string='Annual Health Checkup', default=False)
    dental_included = fields.Boolean(string='Dental Coverage', default=False)
    vision_included = fields.Boolean(string='Vision Coverage', default=False)
    mental_health_included = fields.Boolean(string='Mental Health Coverage', default=False)
    
    # Limits
    annual_limit = fields.Float(string='Annual Limit')
    consultation_limit = fields.Integer(string='Consultation Limit/Year')
    
    # Features
    video_consultation = fields.Boolean(string='Video Consultation', default=True)
    home_visit = fields.Boolean(string='Home Visit', default=False)
    priority_booking = fields.Boolean(string='Priority Booking', default=False)
    dedicated_support = fields.Boolean(string='Dedicated Support', default=False)
    
    active = fields.Boolean(string='Active', default=True)


class CorporateEmployee(models.Model):
    _name = 'corporate.employee'
    _description = 'Corporate Employee'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string='Employee Name', required=True)
    employee_id_number = fields.Char(string='Employee ID', required=True)
    corporate_id = fields.Many2one('corporate.account', string='Company', required=True, ondelete='cascade')
    patient_id = fields.Many2one('doctor.patient', string='Patient Profile')
    
    # Contact
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    
    # Personal
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    date_of_birth = fields.Date(string='Date of Birth')
    
    # Employment
    department = fields.Char(string='Department')
    designation = fields.Char(string='Designation')
    joining_date = fields.Date(string='Joining Date')
    
    # Dependents
    dependent_ids = fields.One2many('corporate.dependent', 'employee_id', string='Dependents')
    dependent_count = fields.Integer(compute='_compute_dependent_count', string='Dependents')
    
    # Usage
    appointments_used = fields.Integer(compute='_compute_usage', string='Appointments Used')
    benefits_used = fields.Float(compute='_compute_usage', string='Benefits Used')
    
    # Status
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
    ], string='Status', default='active')
    
    enrollment_date = fields.Date(string='Enrollment Date', default=fields.Date.today)

    _constraints = [
        models.Constraint('UNIQUE(corporate_id, employee_id_number)', 'Employee ID must be unique within company!'),
    ]

    @api.depends('dependent_ids')
    def _compute_dependent_count(self):
        for record in self:
            record.dependent_count = len(record.dependent_ids)

    @api.depends('patient_id.appointment_ids')
    def _compute_usage(self):
        for record in self:
            if record.patient_id:
                year_start = date(date.today().year, 1, 1)
                appointments = record.patient_id.appointment_ids.filtered(
                    lambda a: a.state == 'completed' and a.appointment_date >= year_start
                )
                record.appointments_used = len(appointments)
                record.benefits_used = sum(appointments.mapped('subscription_discount'))
            else:
                record.appointments_used = 0
                record.benefits_used = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Link to existing patient or create new if not exists
            if not vals.get('patient_id') and vals.get('email'):
                # Search for existing patient by email first
                existing_patient = self.env['doctor.patient'].search(
                    [('email', '=', vals.get('email'))], limit=1
                )
                if existing_patient:
                    vals['patient_id'] = existing_patient.id
                else:
                    patient = self.env['doctor.patient'].create({
                        'name': vals.get('name'),
                        'email': vals.get('email'),
                        'mobile': vals.get('phone'),
                        'gender': vals.get('gender'),
                        'date_of_birth': vals.get('date_of_birth'),
                    })
                    vals['patient_id'] = patient.id
        return super().create(vals_list)


class CorporateDependent(models.Model):
    _name = 'corporate.dependent'
    _description = 'Corporate Employee Dependent'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    employee_id = fields.Many2one('corporate.employee', string='Employee', required=True, ondelete='cascade')
    patient_id = fields.Many2one('doctor.patient', string='Patient Profile')
    
    relationship = fields.Selection([
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
    ], string='Relationship', required=True)
    
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    date_of_birth = fields.Date(string='Date of Birth')
    
    is_active = fields.Boolean(string='Active', default=True)

    @api.constrains('employee_id')
    def _check_max_dependents(self):
        for record in self:
            max_deps = record.employee_id.corporate_id.max_dependents_per_employee
            current_deps = len(record.employee_id.dependent_ids)
            if current_deps > max_deps:
                raise ValidationError(_('Maximum %s dependents allowed per employee.') % max_deps)


class CorporateHealthCheckup(models.Model):
    _name = 'corporate.health.checkup'
    _description = 'Corporate Health Checkup Campaign'
    _inherit = ['mail.thread']
    _order = 'scheduled_date desc'

    name = fields.Char(string='Campaign Name', required=True)
    corporate_id = fields.Many2one('corporate.account', string='Company', required=True)
    
    scheduled_date = fields.Date(string='Scheduled Date', required=True)
    location = fields.Char(string='Location')
    
    lab_partner_id = fields.Many2one('lab.partner', string='Lab Partner')
    
    # Tests included
    test_ids = fields.Many2many('lab.test', string='Tests Included')
    
    # Participants
    employee_ids = fields.Many2many('corporate.employee', string='Participants')
    participant_count = fields.Integer(compute='_compute_counts', string='Participants')
    
    # Results
    completed_count = fields.Integer(string='Completed')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')

    @api.depends('employee_ids')
    def _compute_counts(self):
        for record in self:
            record.participant_count = len(record.employee_ids)

    def action_schedule(self):
        self.state = 'scheduled'

    def action_start(self):
        self.state = 'in_progress'

    def action_complete(self):
        self.state = 'completed'


# Extend Appointment model to include corporate
class DoctorAppointment(models.Model):
    _inherit = 'doctor.appointment'

    corporate_id = fields.Many2one('corporate.account', string='Corporate Account')
    corporate_employee_id = fields.Many2one('corporate.employee', string='Corporate Employee')
    is_corporate = fields.Boolean(string='Corporate Booking', compute='_compute_is_corporate', store=False)

    @api.depends('corporate_id')
    def _compute_is_corporate(self):
        for record in self:
            record.is_corporate = bool(record.corporate_id)
