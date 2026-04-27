# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Symptom(models.Model):
    _name = 'medical.symptom'
    _description = 'Medical Symptom'
    _order = 'name'

    name = fields.Char(string='Symptom', required=True, translate=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    
    # Body System
    body_system = fields.Selection([
        ('general', 'General'),
        ('head', 'Head & Neurological'),
        ('eyes', 'Eyes'),
        ('ears', 'Ears'),
        ('nose', 'Nose & Sinuses'),
        ('throat', 'Throat'),
        ('respiratory', 'Respiratory'),
        ('cardiovascular', 'Cardiovascular'),
        ('gastrointestinal', 'Gastrointestinal'),
        ('urinary', 'Urinary'),
        ('musculoskeletal', 'Musculoskeletal'),
        ('skin', 'Skin'),
        ('mental', 'Mental Health'),
        ('reproductive', 'Reproductive'),
    ], string='Body System', required=True)
    
    # Severity indicators
    severity_weight = fields.Integer(string='Severity Weight', default=1, help='1-10 scale')
    is_emergency = fields.Boolean(string='Emergency Indicator', default=False)
    emergency_keywords = fields.Text(string='Emergency Keywords')
    
    # Related
    related_symptom_ids = fields.Many2many('medical.symptom', 'symptom_related_rel',
                                           'symptom_id', 'related_id', string='Related Symptoms')
    
    specialization_ids = fields.Many2many('doctor.specialization', string='Related Specializations')
    condition_ids = fields.Many2many('medical.condition', 'symptom_condition_rel',
                                     'symptom_id', 'condition_id', string='Related Conditions')
    
    # Questions to ask
    followup_questions = fields.Text(string='Follow-up Questions', help='One question per line')
    
    active = fields.Boolean(string='Active', default=True)


class MedicalCondition(models.Model):
    _name = 'medical.condition'
    _description = 'Medical Condition'
    _order = 'name'

    name = fields.Char(string='Condition', required=True)
    code = fields.Char(string='ICD Code')
    description = fields.Text(string='Description')
    
    # Severity
    severity = fields.Selection([
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical'),
    ], string='Typical Severity', default='mild')
    
    is_emergency = fields.Boolean(string='Emergency Condition', default=False)
    
    # Symptoms
    primary_symptom_ids = fields.Many2many('medical.symptom', 'condition_primary_symptom_rel',
                                           'condition_id', 'symptom_id', string='Primary Symptoms')
    secondary_symptom_ids = fields.Many2many('medical.symptom', 'condition_secondary_symptom_rel',
                                              'condition_id', 'symptom_id', string='Secondary Symptoms')
    
    # Related
    specialization_ids = fields.Many2many('doctor.specialization', string='Recommended Specializations')
    
    # Advice
    home_care_advice = fields.Text(string='Home Care Advice')
    when_to_see_doctor = fields.Text(string='When to See Doctor')
    emergency_signs = fields.Text(string='Emergency Signs')
    
    active = fields.Boolean(string='Active', default=True)


class SymptomCheck(models.Model):
    _name = 'symptom.check'
    _description = 'Symptom Check Session'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    
    patient_id = fields.Many2one('doctor.patient', string='Patient')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    
    # Patient Info (for anonymous checks)
    patient_age = fields.Integer(string='Age')
    patient_gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    
    # Symptoms
    symptom_ids = fields.Many2many('medical.symptom', string='Reported Symptoms')
    primary_symptom_id = fields.Many2one('medical.symptom', string='Primary Symptom')
    
    # Additional Info
    symptom_duration = fields.Selection([
        ('hours', 'Few Hours'),
        ('day', '1 Day'),
        ('days', '2-3 Days'),
        ('week', 'About a Week'),
        ('weeks', 'More than a Week'),
        ('month', 'More than a Month'),
    ], string='Duration')
    
    symptom_severity = fields.Selection([
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    ], string='Severity')
    
    additional_notes = fields.Text(string='Additional Notes')
    
    # Results
    possible_condition_ids = fields.Many2many('medical.condition', string='Possible Conditions')
    recommended_specialization_ids = fields.Many2many('doctor.specialization', string='Recommended Specialists')
    
    urgency_level = fields.Selection([
        ('low', 'Low - Can wait'),
        ('medium', 'Medium - See doctor soon'),
        ('high', 'High - See doctor today'),
        ('emergency', 'Emergency - Seek immediate care'),
    ], string='Urgency Level', compute='_compute_urgency', store=True)
    
    advice = fields.Text(string='General Advice')
    emergency_warning = fields.Boolean(string='Emergency Warning', compute='_compute_urgency', store=True)
    
    # Outcome
    doctor_matched_ids = fields.Many2many('doctor.doctor', string='Matched Doctors')
    appointment_id = fields.Many2one('doctor.appointment', string='Created Appointment')
    
    # Chatbot link
    conversation_id = fields.Many2one('chatbot.conversation', string='Chatbot Conversation')
    
    state = fields.Selection([
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('appointment_booked', 'Appointment Booked'),
    ], string='Status', default='in_progress')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('symptom.check') or 'New'
        return super().create(vals_list)

    @api.depends('symptom_ids', 'symptom_ids.severity_weight', 'symptom_ids.is_emergency')
    def _compute_urgency(self):
        for record in self:
            if any(s.is_emergency for s in record.symptom_ids):
                record.urgency_level = 'emergency'
                record.emergency_warning = True
            else:
                max_weight = max(record.symptom_ids.mapped('severity_weight') or [1])
                if max_weight >= 8:
                    record.urgency_level = 'high'
                elif max_weight >= 5:
                    record.urgency_level = 'medium'
                else:
                    record.urgency_level = 'low'
                record.emergency_warning = False

    def action_analyze(self):
        """Analyze symptoms and provide recommendations."""
        self.ensure_one()
        
        # Find possible conditions based on symptoms
        conditions = self.env['medical.condition'].search([
            '|',
            ('primary_symptom_ids', 'in', self.symptom_ids.ids),
            ('secondary_symptom_ids', 'in', self.symptom_ids.ids),
        ])
        self.possible_condition_ids = conditions
        
        # Find recommended specializations
        specializations = self.symptom_ids.mapped('specialization_ids')
        specializations |= conditions.mapped('specialization_ids')
        self.recommended_specialization_ids = specializations
        
        # Generate advice
        advice_lines = []
        for condition in conditions[:3]:
            if condition.home_care_advice:
                advice_lines.append(f"• {condition.name}: {condition.home_care_advice}")
        self.advice = '\n'.join(advice_lines) if advice_lines else 'Please consult a doctor for personalized advice.'
        
        self.state = 'completed'

    def action_match_doctors(self):
        """Find matching doctors based on symptoms."""
        self.ensure_one()
        
        if not self.recommended_specialization_ids:
            self.action_analyze()
        
        # Find approved doctors with matching specializations
        doctors = self.env['doctor.doctor'].search([
            ('state', '=', 'approved'),
            ('specialization_id', 'in', self.recommended_specialization_ids.ids),
        ], limit=10, order='rating desc')
        
        self.doctor_matched_ids = doctors
        return {
            'type': 'ir.actions.act_window',
            'name': 'Matched Doctors',
            'res_model': 'doctor.doctor',
            'view_mode': 'list,form',
            'domain': [('id', 'in', doctors.ids)],
        }
