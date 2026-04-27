# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta


class InsuranceProvider(models.Model):
    _name = 'insurance.provider'
    _description = 'Insurance Provider'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Provider Name', required=True, tracking=True)
    code = fields.Char(string='Provider Code', required=True)
    image = fields.Binary(string='Logo', attachment=True)
    
    # Contact Information
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    website = fields.Char(string='Website')
    
    # Address
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country',
                                 default=lambda self: self.env.ref('base.in', raise_if_not_found=False))
    zip_code = fields.Char(string='PIN Code')
    
    # Provider Details
    provider_type = fields.Selection([
        ('government', 'Government'),
        ('private', 'Private'),
        ('corporate', 'Corporate Group'),
        ('tpa', 'Third Party Administrator'),
    ], string='Provider Type', default='private', required=True)
    
    registration_number = fields.Char(string='Registration Number')
    irdai_registration = fields.Char(string='IRDAI Registration')
    
    # TPA Details (if applicable)
    is_tpa = fields.Boolean(string='Is TPA', default=False)
    parent_insurer_id = fields.Many2one('insurance.provider', string='Parent Insurer',
                                        domain="[('is_tpa', '=', False)]")
    
    # Contact Person
    contact_person = fields.Char(string='Contact Person')
    contact_email = fields.Char(string='Contact Email')
    contact_phone = fields.Char(string='Contact Phone')
    contact_designation = fields.Char(string='Designation')
    
    # Integration Settings
    api_endpoint = fields.Char(string='API Endpoint')
    api_key = fields.Char(string='API Key')
    integration_enabled = fields.Boolean(string='API Integration Enabled', default=False)
    
    # Claims Settings
    claim_submission_email = fields.Char(string='Claim Submission Email')
    preauth_email = fields.Char(string='Pre-auth Email')
    average_claim_days = fields.Integer(string='Avg. Claim Processing Days', default=15)
    
    # Plans
    plan_ids = fields.One2many('insurance.plan', 'provider_id', string='Insurance Plans')
    plan_count = fields.Integer(compute='_compute_counts', string='Plans')
    
    # Statistics
    policy_ids = fields.One2many('patient.insurance.policy', 'provider_id', string='Policies')
    active_policies = fields.Integer(compute='_compute_counts', string='Active Policies')
    claim_ids = fields.One2many('insurance.claim', 'provider_id', string='Claims')
    total_claims = fields.Integer(compute='_compute_counts', string='Total Claims')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ], string='Status', default='draft', tracking=True)
    
    active = fields.Boolean(string='Active', default=True)
    
    _constraints = [
        models.Constraint('UNIQUE(code)', 'Provider code must be unique!'),
    ]

    @api.depends('plan_ids', 'policy_ids', 'claim_ids')
    def _compute_counts(self):
        for record in self:
            record.plan_count = len(record.plan_ids)
            record.active_policies = len(record.policy_ids.filtered(lambda p: p.state == 'active'))
            record.total_claims = len(record.claim_ids)

    def action_activate(self):
        self.write({'state': 'active'})

    def action_suspend(self):
        self.write({'state': 'suspended'})

    def action_view_plans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insurance Plans'),
            'res_model': 'insurance.plan',
            'view_mode': 'list,form',
            'domain': [('provider_id', '=', self.id)],
            'context': {'default_provider_id': self.id},
        }

    def action_view_policies(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Policies'),
            'res_model': 'patient.insurance.policy',
            'view_mode': 'list,form',
            'domain': [('provider_id', '=', self.id)],
            'context': {'default_provider_id': self.id},
        }

    def action_view_claims(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Claims'),
            'res_model': 'insurance.claim',
            'view_mode': 'list,form',
            'domain': [('provider_id', '=', self.id)],
            'context': {'default_provider_id': self.id},
        }


class InsurancePlan(models.Model):
    _name = 'insurance.plan'
    _description = 'Insurance Plan'
    _order = 'provider_id, name'

    name = fields.Char(string='Plan Name', required=True)
    code = fields.Char(string='Plan Code', required=True)
    provider_id = fields.Many2one('insurance.provider', string='Insurance Provider',
                                  required=True, ondelete='cascade')
    
    description = fields.Html(string='Description')
    
    # Coverage Details
    plan_type = fields.Selection([
        ('individual', 'Individual'),
        ('family', 'Family Floater'),
        ('group', 'Group/Corporate'),
        ('senior', 'Senior Citizen'),
        ('critical', 'Critical Illness'),
    ], string='Plan Type', default='individual', required=True)
    
    sum_insured = fields.Float(string='Sum Insured')
    premium_amount = fields.Float(string='Premium Amount')
    premium_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('annual', 'Annual'),
    ], string='Premium Frequency', default='annual')
    
    # Coverage Limits
    room_rent_limit = fields.Float(string='Room Rent Limit/Day')
    room_rent_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percent', '% of Sum Insured'),
        ('no_limit', 'No Sub-limit'),
    ], string='Room Rent Type', default='no_limit')
    
    copay_percent = fields.Float(string='Co-pay %', default=0)
    deductible = fields.Float(string='Deductible Amount', default=0)
    
    # Consultation Coverage
    consultation_covered = fields.Boolean(string='OPD Consultation Covered', default=False)
    consultation_limit = fields.Float(string='OPD Limit')
    consultation_copay = fields.Float(string='OPD Co-pay %', default=0)
    
    # Pre-existing Conditions
    ped_waiting_period = fields.Integer(string='PED Waiting Period (months)', default=48)
    initial_waiting_period = fields.Integer(string='Initial Waiting (days)', default=30)
    
    # Features
    cashless_available = fields.Boolean(string='Cashless Available', default=True)
    preauth_required = fields.Boolean(string='Pre-auth Required', default=True)
    network_hospitals_only = fields.Boolean(string='Network Hospitals Only', default=False)
    
    active = fields.Boolean(string='Active', default=True)

    _constraints = [
        models.Constraint('UNIQUE(code, provider_id)', 'Plan code must be unique per provider!'),
    ]


class PatientInsurancePolicy(models.Model):
    _name = 'patient.insurance.policy'
    _description = 'Patient Insurance Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'end_date desc'

    name = fields.Char(string='Policy Number', required=True, tracking=True)
    patient_id = fields.Many2one('doctor.patient', string='Patient', required=True, ondelete='cascade')
    
    # Provider & Plan
    provider_id = fields.Many2one('insurance.provider', string='Insurance Provider',
                                  required=True, domain="[('state', '=', 'active')]")
    plan_id = fields.Many2one('insurance.plan', string='Insurance Plan',
                              domain="[('provider_id', '=', provider_id), ('active', '=', True)]")
    
    # Policy Details
    policy_type = fields.Selection([
        ('self', 'Self'),
        ('employer', 'Employer Provided'),
        ('family', 'Family Policy'),
    ], string='Policy Type', default='self')
    
    holder_name = fields.Char(string='Policy Holder Name')
    holder_relation = fields.Selection([
        ('self', 'Self'),
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
    ], string='Relation to Holder', default='self')
    
    # Coverage
    sum_insured = fields.Float(string='Sum Insured', required=True)
    sum_available = fields.Float(string='Available Sum', compute='_compute_sum_available', store=True)
    
    # Dates
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    
    # Corporate Link (if employer provided)
    corporate_id = fields.Many2one('corporate.account', string='Corporate Account')
    corporate_employee_id = fields.Many2one('corporate.employee', string='Employee')
    
    # Card Details
    card_number = fields.Char(string='Health Card Number')
    card_image = fields.Binary(string='Card Image', attachment=True)
    
    # Claims
    claim_ids = fields.One2many('insurance.claim', 'policy_id', string='Claims')
    total_claimed = fields.Float(compute='_compute_claim_stats', string='Total Claimed')
    claim_count = fields.Integer(compute='_compute_claim_stats', string='Claim Count')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    notes = fields.Text(string='Notes')
    
    _constraints = [
        models.Constraint('UNIQUE(name, provider_id)', 'Policy number must be unique per provider!'),
    ]

    @api.depends('sum_insured', 'claim_ids', 'claim_ids.state', 'claim_ids.approved_amount')
    def _compute_sum_available(self):
        for record in self:
            approved_claims = record.claim_ids.filtered(lambda c: c.state == 'settled')
            total_used = sum(approved_claims.mapped('approved_amount'))
            record.sum_available = record.sum_insured - total_used

    @api.depends('claim_ids', 'claim_ids.state', 'claim_ids.claimed_amount')
    def _compute_claim_stats(self):
        for record in self:
            record.claim_count = len(record.claim_ids)
            record.total_claimed = sum(record.claim_ids.mapped('claimed_amount'))

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.end_date and record.start_date and record.end_date < record.start_date:
                raise ValidationError(_('End date must be after start date.'))

    def action_activate(self):
        for record in self:
            if not record.plan_id:
                raise UserError(_('Please select an insurance plan.'))
            record.state = 'active'

    def action_expire(self):
        self.write({'state': 'expired'})

    def action_view_claims(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Claims'),
            'res_model': 'insurance.claim',
            'view_mode': 'list,form',
            'domain': [('policy_id', '=', self.id)],
            'context': {'default_policy_id': self.id},
        }

    @api.model
    def _cron_check_policy_expiry(self):
        """Cron job to check and update expired policies"""
        today = date.today()
        expired = self.search([
            ('state', '=', 'active'),
            ('end_date', '<', today),
        ])
        expired.write({'state': 'expired'})
        
        # Send expiry warning for policies expiring in 30 days
        warning_date = today + timedelta(days=30)
        expiring_soon = self.search([
            ('state', '=', 'active'),
            ('end_date', '>=', today),
            ('end_date', '<=', warning_date),
        ])
        for policy in expiring_soon:
            policy.message_post(
                body=_('Policy is expiring on %s. Please renew.') % policy.end_date,
                subject=_('Policy Expiry Warning'),
            )


class InsuranceClaim(models.Model):
    _name = 'insurance.claim'
    _description = 'Insurance Claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Claim Reference', readonly=True, copy=False, default='New')
    
    # Links
    policy_id = fields.Many2one('patient.insurance.policy', string='Insurance Policy',
                                required=True, domain="[('state', '=', 'active')]")
    patient_id = fields.Many2one(related='policy_id.patient_id', store=True, string='Patient')
    provider_id = fields.Many2one(related='policy_id.provider_id', store=True, string='Provider')
    appointment_id = fields.Many2one('doctor.appointment', string='Appointment')
    
    # Claim Type
    claim_type = fields.Selection([
        ('cashless', 'Cashless'),
        ('reimbursement', 'Reimbursement'),
    ], string='Claim Type', default='reimbursement', required=True)
    
    treatment_type = fields.Selection([
        ('opd', 'OPD Consultation'),
        ('ipd', 'Hospitalization'),
        ('daycare', 'Day Care'),
        ('maternity', 'Maternity'),
        ('diagnostic', 'Diagnostic'),
    ], string='Treatment Type', default='opd', required=True)
    
    # Treatment Details
    admission_date = fields.Date(string='Admission/Treatment Date')
    discharge_date = fields.Date(string='Discharge Date')
    diagnosis = fields.Text(string='Diagnosis')
    treatment_details = fields.Text(string='Treatment Details')
    
    doctor_id = fields.Many2one('doctor.doctor', string='Treating Doctor')
    hospital_name = fields.Char(string='Hospital/Clinic Name')
    
    # Amounts
    claimed_amount = fields.Float(string='Claimed Amount', required=True, tracking=True)
    approved_amount = fields.Float(string='Approved Amount', tracking=True)
    copay_amount = fields.Float(string='Co-pay Amount')
    deductible_amount = fields.Float(string='Deductible')
    settlement_amount = fields.Float(compute='_compute_settlement', string='Settlement Amount', store=True)
    
    # Documents
    document_ids = fields.One2many('insurance.claim.document', 'claim_id', string='Documents')
    
    # Pre-authorization (for cashless)
    preauth_id = fields.Many2one('insurance.preauth', string='Pre-authorization')
    preauth_required = fields.Boolean(related='policy_id.plan_id.preauth_required')
    
    # Processing
    submission_date = fields.Date(string='Submission Date', default=fields.Date.today)
    processing_date = fields.Date(string='Processing Date')
    settlement_date = fields.Date(string='Settlement Date')
    
    tpa_claim_number = fields.Char(string='TPA Claim Number')
    insurer_claim_number = fields.Char(string='Insurer Claim Number')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('query', 'Query Raised'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('settled', 'Settled'),
    ], string='Status', default='draft', tracking=True)
    
    rejection_reason = fields.Text(string='Rejection Reason')
    query_details = fields.Text(string='Query Details')
    
    notes = fields.Text(string='Internal Notes')

    @api.depends('approved_amount', 'copay_amount', 'deductible_amount')
    def _compute_settlement(self):
        for record in self:
            record.settlement_amount = (record.approved_amount or 0) - (record.copay_amount or 0) - (record.deductible_amount or 0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('insurance.claim') or 'New'
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if record.claim_type == 'cashless' and record.preauth_required and not record.preauth_id:
                raise UserError(_('Pre-authorization is required for cashless claims.'))
            record.state = 'submitted'

    def action_review(self):
        self.write({'state': 'under_review', 'processing_date': fields.Date.today()})

    def action_raise_query(self):
        self.write({'state': 'query'})

    def action_approve(self):
        for record in self:
            if not record.approved_amount:
                raise UserError(_('Please enter approved amount.'))
            record.state = 'approved'

    def action_reject(self):
        for record in self:
            if not record.rejection_reason:
                raise UserError(_('Please enter rejection reason.'))
            record.state = 'rejected'

    def action_settle(self):
        for record in self:
            if record.state != 'approved':
                raise UserError(_('Only approved claims can be settled.'))
            record.state = 'settled'
            record.settlement_date = fields.Date.today()


class InsuranceClaimDocument(models.Model):
    _name = 'insurance.claim.document'
    _description = 'Claim Document'
    _order = 'sequence, id'

    claim_id = fields.Many2one('insurance.claim', string='Claim', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    
    name = fields.Char(string='Document Name', required=True)
    document_type = fields.Selection([
        ('prescription', 'Prescription'),
        ('invoice', 'Invoice/Bill'),
        ('discharge_summary', 'Discharge Summary'),
        ('investigation', 'Investigation Report'),
        ('id_proof', 'ID Proof'),
        ('policy_card', 'Policy Card'),
        ('other', 'Other'),
    ], string='Document Type', required=True)
    
    file = fields.Binary(string='File', required=True, attachment=True)
    file_name = fields.Char(string='File Name')
    
    notes = fields.Text(string='Notes')


class InsurancePreauth(models.Model):
    _name = 'insurance.preauth'
    _description = 'Insurance Pre-authorization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Pre-auth Reference', readonly=True, copy=False, default='New')
    
    # Links
    policy_id = fields.Many2one('patient.insurance.policy', string='Insurance Policy',
                                required=True, domain="[('state', '=', 'active')]")
    patient_id = fields.Many2one(related='policy_id.patient_id', store=True, string='Patient')
    provider_id = fields.Many2one(related='policy_id.provider_id', store=True, string='Provider')
    appointment_id = fields.Many2one('doctor.appointment', string='Related Appointment')
    
    # Treatment Details
    treatment_type = fields.Selection([
        ('opd', 'OPD Consultation'),
        ('ipd', 'Hospitalization'),
        ('daycare', 'Day Care'),
        ('maternity', 'Maternity'),
        ('diagnostic', 'Diagnostic'),
    ], string='Treatment Type', default='opd', required=True)
    
    planned_date = fields.Date(string='Planned Treatment Date', required=True)
    expected_days = fields.Integer(string='Expected Days')
    
    doctor_id = fields.Many2one('doctor.doctor', string='Treating Doctor')
    hospital_name = fields.Char(string='Hospital/Clinic Name')
    
    diagnosis = fields.Text(string='Provisional Diagnosis')
    treatment_plan = fields.Text(string='Treatment Plan')
    
    # Amounts
    estimated_amount = fields.Float(string='Estimated Amount', required=True)
    approved_amount = fields.Float(string='Approved Amount')
    
    # Processing
    request_date = fields.Date(string='Request Date', default=fields.Date.today)
    response_date = fields.Date(string='Response Date')
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    
    insurer_preauth_number = fields.Char(string='Insurer Pre-auth Number')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('partially_approved', 'Partially Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('used', 'Used'),
    ], string='Status', default='draft', tracking=True)
    
    rejection_reason = fields.Text(string='Rejection Reason')
    conditions = fields.Text(string='Approval Conditions')
    
    # Related Claim
    claim_ids = fields.One2many('insurance.claim', 'preauth_id', string='Claims')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('insurance.preauth') or 'New'
        return super().create(vals_list)

    def action_request(self):
        self.write({'state': 'requested'})

    def action_approve(self):
        for record in self:
            if not record.approved_amount:
                raise UserError(_('Please enter approved amount.'))
            if record.approved_amount < record.estimated_amount:
                record.state = 'partially_approved'
            else:
                record.state = 'approved'
            record.response_date = fields.Date.today()
            if not record.valid_from:
                record.valid_from = fields.Date.today()
            if not record.valid_to:
                record.valid_to = record.valid_from + timedelta(days=30)

    def action_reject(self):
        for record in self:
            if not record.rejection_reason:
                raise UserError(_('Please enter rejection reason.'))
            record.state = 'rejected'
            record.response_date = fields.Date.today()


# Extend Patient model for insurance
class DoctorPatientInsurance(models.Model):
    _inherit = 'doctor.patient'

    insurance_policy_ids = fields.One2many('patient.insurance.policy', 'patient_id', string='Insurance Policies')
    active_policy_id = fields.Many2one('patient.insurance.policy', string='Primary Insurance',
                                       compute='_compute_active_policy', store=True)
    has_insurance = fields.Boolean(compute='_compute_has_insurance', string='Has Active Insurance')

    @api.depends('insurance_policy_ids', 'insurance_policy_ids.state')
    def _compute_active_policy(self):
        for record in self:
            active = record.insurance_policy_ids.filtered(lambda p: p.state == 'active')
            record.active_policy_id = active[0] if active else False

    @api.depends('insurance_policy_ids', 'insurance_policy_ids.state')
    def _compute_has_insurance(self):
        for record in self:
            record.has_insurance = bool(record.insurance_policy_ids.filtered(lambda p: p.state == 'active'))


# Extend Appointment model for insurance
class DoctorAppointmentInsurance(models.Model):
    _inherit = 'doctor.appointment'

    # Insurance Fields
    insurance_policy_id = fields.Many2one('patient.insurance.policy', string='Insurance Policy',
                                          domain="[('patient_id', '=', patient_id), ('state', '=', 'active')]")
    is_insured = fields.Boolean(string='Insurance Claim', default=False)
    insurance_claim_id = fields.Many2one('insurance.claim', string='Insurance Claim')
    insurance_preauth_id = fields.Many2one('insurance.preauth', string='Pre-authorization')
    
    # Insurance amounts
    insurance_covered = fields.Float(string='Insurance Covered')
    patient_payable = fields.Float(compute='_compute_patient_payable', string='Patient Payable', store=True)

    @api.depends('final_amount', 'insurance_covered')
    def _compute_patient_payable(self):
        for record in self:
            record.patient_payable = record.final_amount - (record.insurance_covered or 0)

    @api.onchange('is_insured', 'patient_id')
    def _onchange_insurance(self):
        if self.is_insured and self.patient_id:
            active_policy = self.patient_id.insurance_policy_ids.filtered(lambda p: p.state == 'active')
            if active_policy:
                self.insurance_policy_id = active_policy[0]
            else:
                self.is_insured = False
                return {'warning': {
                    'title': _('No Active Insurance'),
                    'message': _('This patient does not have an active insurance policy.')
                }}
