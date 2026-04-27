# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)


class DoctorDoctor(models.Model):
    _name = 'doctor.doctor'
    _description = 'Doctor Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Basic Information
    name = fields.Char(string='Full Name', required=True, tracking=True)
    image = fields.Binary(string='Photo', attachment=True)
    partner_id = fields.Many2one('res.partner', string='Contact', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Portal User', ondelete='set null')

    # Contact
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile', required=True)
    website = fields.Char(string='Website')

    # Demographics
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    date_of_birth = fields.Date(string='Date of Birth')

    # Professional Information
    specialization_id = fields.Many2one('doctor.specialization', string='Primary Specialization', required=True)
    qualification = fields.Char(string='Primary Qualification')
    additional_qualifications = fields.Text(string='Additional Qualifications')
    medical_council = fields.Char(string='Medical Council')
    registration_number = fields.Char(string='Registration Number', required=True)
    registration_year = fields.Integer(string='Registration Year')
    experience_years = fields.Integer(string='Years of Experience')
    bio = fields.Html(string='About', sanitize=True)

    # Practice Information
    clinic_name = fields.Char(string='Clinic/Hospital Name')
    clinic_address = fields.Text(string='Clinic Address')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country',
                                 default=lambda self: self.env.ref('base.in', raise_if_not_found=False))
    zip_code = fields.Char(string='PIN Code')

    # Consultation Settings
    consultation_fee = fields.Float(string='Consultation Fee', required=True)
    followup_fee = fields.Float(string='Follow-up Fee')
    followup_validity_days = fields.Integer(string='Follow-up Valid (Days)', default=15)
    consultation_duration = fields.Integer(string='Consultation Duration (min)', default=15)
    buffer_time = fields.Integer(string='Buffer Time (min)', default=5)

    offers_video = fields.Boolean(string='Offers Video Consultation')
    video_fee = fields.Float(string='Video Consultation Fee')
    offers_home_visit = fields.Boolean(string='Offers Home Visit')
    home_visit_fee = fields.Float(string='Home Visit Fee')

    # Schedule
    schedule_ids = fields.One2many('doctor.schedule', 'doctor_id', string='Weekly Schedule')
    advance_booking_days = fields.Integer(string='Advance Booking Days', default=30)
    same_day_booking = fields.Boolean(string='Allow Same Day Booking', default=True)

    # Ratings & Reviews
    rating = fields.Float(string='Rating', compute='_compute_rating', store=True, digits=(2, 1))
    rating_count = fields.Integer(compute='_compute_rating', string='Reviews Count', store=True)
    review_ids = fields.One2many('doctor.review', 'doctor_id', string='Reviews')

    # Documents
    document_ids = fields.One2many('doctor.document', 'doctor_id', string='Documents')

    # Appointments
    appointment_ids = fields.One2many('doctor.appointment', 'doctor_id', string='Appointments')
    total_appointments = fields.Integer(compute='_compute_statistics', string='Total Appointments')
    completed_appointments = fields.Integer(compute='_compute_statistics', string='Completed')

    # Earnings
    earning_ids = fields.One2many('doctor.earning', 'doctor_id', string='Earnings')
    payout_ids = fields.One2many('doctor.payout', 'doctor_id', string='Payouts')
    total_earnings = fields.Float(compute='_compute_earnings', string='Total Earnings')
    pending_payout = fields.Float(compute='_compute_earnings', string='Pending Payout')

    # Bank Details
    bank_name = fields.Char(string='Bank Name')
    bank_account_number = fields.Char(string='Account Number')
    bank_ifsc = fields.Char(string='IFSC Code')
    bank_account_name = fields.Char(string='Account Holder Name')
    upi_id = fields.Char(string='UPI ID')

    # Country Compliance
    compliance_id = fields.Many2one(
        comodel_name="country.compliance",
        string="Compliance",
        tracking=True,
    )
    compliance_accepted = fields.Boolean(
        string="Compliance Accepted?",
        tracking=True,
    )
    compliance_accepted_on = fields.Datetime(string="Accepted On")
    # Stores old country name when admin changes country_id from the backend.
    # Drives the old→new banner in the compliance popup.
    # Cleared when the doctor re-accepts compliance.
    country_change_old_name = fields.Char(
        string="Previous Country (before last change)",
        copy=False,
    )

    # Badges (Phase 2)
    badge_ids = fields.Many2many('doctor.badge', string='Badges')
    is_verified = fields.Boolean(string='Verified', default=False)
    is_featured = fields.Boolean(string='Featured', default=False)

    # Dynamic Pricing (Phase 2)
    dynamic_pricing_enabled = fields.Boolean(string='Enable Dynamic Pricing', default=False)
    dynamic_pricing_min = fields.Float(string='Minimum Price')
    dynamic_pricing_max = fields.Float(string='Maximum Price')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('suspended', 'Suspended'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)

    approved_date = fields.Datetime(string='Approved Date')
    approved_by = fields.Many2one('res.users', string='Approved By')
    rejection_reason = fields.Text(string='Rejection Reason')
    active = fields.Boolean(string='Active', default=True)

    _constraints = [
        models.Constraint('UNIQUE(email)', 'Email address must be unique!'),
        models.Constraint('UNIQUE(registration_number, medical_council)', 'Registration number already exists!'),
    ]

    @api.depends('review_ids', 'review_ids.rating', 'review_ids.state')
    def _compute_rating(self):
        for record in self:
            approved_reviews = record.review_ids.filtered(lambda r: r.state == 'approved')
            if approved_reviews:
                record.rating = sum(approved_reviews.mapped('rating')) / len(approved_reviews)
                record.rating_count = len(approved_reviews)
            else:
                record.rating = 0
                record.rating_count = 0

    @api.depends('appointment_ids', 'appointment_ids.state')
    def _compute_statistics(self):
        for record in self:
            record.total_appointments = len(record.appointment_ids)
            record.completed_appointments = len(record.appointment_ids.filtered(lambda a: a.state == 'completed'))

    @api.depends('earning_ids', 'payout_ids')
    def _compute_earnings(self):
        for record in self:
            record.total_earnings = sum(record.earning_ids.mapped('net_amount'))
            paid = sum(record.payout_ids.filtered(lambda p: p.state == 'completed').mapped('amount'))
            record.pending_payout = record.total_earnings - paid

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
        return super().create(vals_list)

    def action_submit_verification(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft profiles can be submitted.'))
            if not record.document_ids:
                raise UserError(_('Please upload verification documents.'))
            record.state = 'pending'

    def action_approve(self):
        for record in self:
            if record.state != 'pending':
                raise UserError(_('Only pending profiles can be approved.'))

            if not record.user_id:
                existing_user = self.env['res.users'].sudo().search(
                    [('login', '=', record.email)], limit=1
                )
                if existing_user:
                    # Use ORM to update groups - remove portal, add internal user and doctor group
                    portal_group = self.env.ref('base.group_portal')
                    internal_group = self.env.ref('base.group_user')
                    doctor_group = self.env.ref('doctor_marketplace.group_doctor_marketplace_doctor')
                    
                    existing_user.sudo().write({
                        'group_ids': [
                            (3, portal_group.id),  # Remove portal group
                            (4, internal_group.id),  # Add internal user group
                            (4, doctor_group.id),  # Add doctor group
                        ]
                    })
                    record.user_id = existing_user.id
                else:
                    doctor_group = self.env.ref('doctor_marketplace.group_doctor_marketplace_doctor')
                    user = self.env['res.users'].sudo().with_context(no_reset_password=True).create({
                        'name': record.name,
                        'login': record.email,
                        'email': record.email,
                        'group_ids': [
                            (4, self.env.ref('base.group_user').id),
                            (4, doctor_group.id),
                        ],
                    })
                    record.user_id = user.id

            record.write({
                'state': 'approved',
                'approved_date': fields.Datetime.now(),
                'approved_by': self.env.user.id,
                'is_verified': True,
            })

    def action_reject(self):
        for record in self:
            record.state = 'rejected'

    def action_open_reject_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Doctor Registration'),
            'res_model': 'doctor.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_doctor_id': self.id},
        }

    def action_suspend(self):
        for record in self:
            record.state = 'suspended'

    def action_reactivate(self):
        for record in self:
            if record.state == 'suspended':
                record.state = 'approved'

    # ------------------------------------------------------------------
    # Country Compliance helpers
    # ------------------------------------------------------------------

    def _find_compliance_for_country(self, country_id):
        """Return best-matching country.compliance (exact match → global default)."""
        Compliance = self.env["country.compliance"].sudo()
        if country_id:
            rec = Compliance.search([("country_id", "=", country_id)], limit=1)
            if rec:
                return rec
        return Compliance.search([("country_id", "=", False)], limit=1)

    def write(self, vals):
        """
        When country_id is changed from the backend doctor.doctor form:
          1. Resolve matching compliance for the new country → update compliance_id.
          2. Reset compliance_accepted = False on this record.
          3. Store old country name in country_change_old_name.
          4. Sync compliance reset to the linked portal user's partner if present.
          5. Post chatter notes.
        No existing workflow logic is altered.
        """
        country_changing = "country_id" in vals

        old_country_map = {}
        if country_changing:
            for rec in self:
                old_country_map[rec.id] = (
                    rec.country_id.id,
                    rec.country_id.name or "N/A",
                )

        result = super().write(vals)

        if country_changing:
            for rec in self:
                new_cid = rec.country_id.id
                old_cid, old_cname = old_country_map.get(rec.id, (False, "N/A"))
                if new_cid == old_cid:
                    continue

                new_cname = rec.country_id.name or "N/A"
                compliance = rec._find_compliance_for_country(new_cid)

                _logger.info(
                    "doctor.doctor %s: country %s → %s, compliance reset.",
                    rec.id,
                    old_cname,
                    new_cname,
                )

                # Update doctor.doctor record (call super to avoid recursion)
                super(DoctorDoctor, rec).write(
                    {
                        "compliance_id": compliance.id if compliance else False,
                        "compliance_accepted": False,
                        "country_change_old_name": old_cname,
                    }
                )

                # Chatter on doctor record
                rec.message_post(
                    body=Markup(
                        "⚠️ <b>Country Changed</b>: Updated from "
                        "<b>{old}</b> → <b>{new}</b>. "
                        "<b>Compliance Accepted?</b> automatically reset to <b>No</b>."
                    ).format(old=old_cname, new=new_cname),
                    subtype_xmlid="mail.mt_note",
                )

        return result

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'doctor.appointment',
            'view_mode': 'list,form',
            'domain': [('doctor_id', '=', self.id)],
            'context': {'default_doctor_id': self.id},
        }
