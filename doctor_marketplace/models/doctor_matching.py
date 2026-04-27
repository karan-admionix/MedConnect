# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta


class DoctorMatchRequest(models.Model):
    _name = 'doctor.match.request'
    _description = 'Doctor Match Request'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    
    patient_id = fields.Many2one('doctor.patient', string='Patient')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    
    # Search Criteria
    specialization_id = fields.Many2one('doctor.specialization', string='Specialization')
    symptom_check_id = fields.Many2one('symptom.check', string='Symptom Check')
    
    # Location
    city = fields.Char(string='City')
    latitude = fields.Float(string='Latitude', digits=(10, 6))
    longitude = fields.Float(string='Longitude', digits=(10, 6))
    max_distance = fields.Float(string='Max Distance (km)', default=10.0)
    
    # Preferences
    preferred_gender = fields.Selection([
        ('any', 'Any'),
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Preferred Gender', default='any')
    
    min_rating = fields.Float(string='Minimum Rating', default=0.0)
    min_experience = fields.Integer(string='Minimum Experience (years)', default=0)
    
    max_fee = fields.Float(string='Maximum Fee')
    
    consultation_mode = fields.Selection([
        ('any', 'Any'),
        ('in_person', 'In-Person'),
        ('video', 'Video'),
        ('home_visit', 'Home Visit'),
    ], string='Consultation Mode', default='any')
    
    # Date preferences
    preferred_date = fields.Date(string='Preferred Date')
    preferred_time = fields.Selection([
        ('any', 'Any Time'),
        ('morning', 'Morning (9AM-12PM)'),
        ('afternoon', 'Afternoon (12PM-5PM)'),
        ('evening', 'Evening (5PM-9PM)'),
    ], string='Preferred Time', default='any')
    
    urgency = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent (Within 24 hours)'),
        ('emergency', 'Emergency (ASAP)'),
    ], string='Urgency', default='normal')
    
    # Results
    match_ids = fields.One2many('doctor.match.result', 'request_id', string='Matches')
    match_count = fields.Integer(compute='_compute_match_count', string='Matches Found')
    
    selected_doctor_id = fields.Many2one('doctor.doctor', string='Selected Doctor')
    appointment_id = fields.Many2one('doctor.appointment', string='Booked Appointment')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('searching', 'Searching'),
        ('found', 'Matches Found'),
        ('booked', 'Appointment Booked'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('doctor.match.request') or 'New'
        return super().create(vals_list)

    @api.depends('match_ids')
    def _compute_match_count(self):
        for record in self:
            record.match_count = len(record.match_ids)

    def action_search(self):
        """Execute doctor matching algorithm."""
        self.ensure_one()
        self.state = 'searching'
        
        # Clear previous results
        self.match_ids.unlink()
        
        # Build domain
        domain = [('state', '=', 'approved'), ('active', '=', True)]
        
        if self.specialization_id:
            domain.append(('specialization_id', '=', self.specialization_id.id))
        
        if self.preferred_gender and self.preferred_gender != 'any':
            domain.append(('gender', '=', self.preferred_gender))
        
        if self.min_rating > 0:
            domain.append(('rating', '>=', self.min_rating))
        
        if self.min_experience > 0:
            domain.append(('experience_years', '>=', self.min_experience))
        
        if self.max_fee:
            domain.append(('consultation_fee', '<=', self.max_fee))
        
        if self.consultation_mode == 'video':
            domain.append(('offers_video', '=', True))
        elif self.consultation_mode == 'home_visit':
            domain.append(('offers_home_visit', '=', True))
        
        if self.city:
            domain.append(('city', 'ilike', self.city))
        
        # Search doctors
        doctors = self.env['doctor.doctor'].search(domain, limit=20)
        
        # Calculate match scores and create results
        for doctor in doctors:
            score = self._calculate_match_score(doctor)
            self.env['doctor.match.result'].create({
                'request_id': self.id,
                'doctor_id': doctor.id,
                'match_score': score,
            })
        
        self.state = 'found' if self.match_ids else 'draft'
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Match Results',
            'res_model': 'doctor.match.result',
            'view_mode': 'list,form',
            'domain': [('request_id', '=', self.id)],
        }

    def _calculate_match_score(self, doctor):
        """Calculate match score for a doctor (0-100)."""
        score = 50  # Base score
        
        # Rating bonus (up to 20 points)
        if doctor.rating:
            score += (doctor.rating / 5) * 20
        
        # Experience bonus (up to 15 points)
        if doctor.experience_years:
            score += min(doctor.experience_years / 20, 1) * 15
        
        # Reviews bonus (up to 10 points)
        if doctor.rating_count:
            score += min(doctor.rating_count / 100, 1) * 10
        
        # Verified bonus
        if doctor.is_verified:
            score += 5
        
        # Price match (if cheaper than max, bonus)
        if self.max_fee and doctor.consultation_fee < self.max_fee:
            price_ratio = 1 - (doctor.consultation_fee / self.max_fee)
            score += price_ratio * 10
        
        return min(score, 100)


class DoctorMatchResult(models.Model):
    _name = 'doctor.match.result'
    _description = 'Doctor Match Result'
    _order = 'match_score desc'

    request_id = fields.Many2one('doctor.match.request', string='Request', required=True, ondelete='cascade')
    doctor_id = fields.Many2one('doctor.doctor', string='Doctor', required=True)
    
    # Doctor info (for display)
    doctor_name = fields.Char(related='doctor_id.name')
    specialization = fields.Char(related='doctor_id.specialization_id.name')
    rating = fields.Float(related='doctor_id.rating')
    experience = fields.Integer(related='doctor_id.experience_years')
    fee = fields.Float(related='doctor_id.consultation_fee')
    city = fields.Char(related='doctor_id.city')
    
    # Match details
    match_score = fields.Float(string='Match Score', digits=(5, 2))
    distance_km = fields.Float(string='Distance (km)')
    
    # Availability
    next_available = fields.Datetime(string='Next Available')
    available_slots_today = fields.Integer(string='Slots Today')
    
    is_selected = fields.Boolean(string='Selected', default=False)

    def action_select(self):
        """Select this doctor for booking."""
        self.ensure_one()
        # Unselect others
        self.request_id.match_ids.write({'is_selected': False})
        self.is_selected = True
        self.request_id.selected_doctor_id = self.doctor_id

    def action_book(self):
        """Book appointment with this doctor."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Book Appointment',
            'res_model': 'doctor.appointment',
            'view_mode': 'form',
            'context': {
                'default_doctor_id': self.doctor_id.id,
                'default_patient_id': self.request_id.patient_id.id,
            },
        }
