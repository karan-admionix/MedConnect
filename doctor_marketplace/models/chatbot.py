# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime


class ChatbotConversation(models.Model):
    _name = 'chatbot.conversation'
    _description = 'AI Chatbot Conversation'
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    
    patient_id = fields.Many2one('doctor.patient', string='Patient')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    session_id = fields.Char(string='Session ID')
    
    # Conversation Details
    start_time = fields.Datetime(string='Started', default=fields.Datetime.now)
    end_time = fields.Datetime(string='Ended')
    duration_minutes = fields.Integer(compute='_compute_duration', string='Duration (min)')
    
    message_ids = fields.One2many('chatbot.message', 'conversation_id', string='Messages')
    message_count = fields.Integer(compute='_compute_message_count', string='Messages')
    
    # Context
    context_type = fields.Selection([
        ('general', 'General Inquiry'),
        ('symptom', 'Symptom Check'),
        ('appointment', 'Appointment Booking'),
        ('prescription', 'Prescription Query'),
        ('followup', 'Follow-up'),
        ('emergency', 'Emergency'),
    ], string='Context', default='general')
    
    # Outcome
    outcome = fields.Selection([
        ('resolved', 'Resolved'),
        ('escalated_doctor', 'Escalated to Doctor'),
        ('appointment_booked', 'Appointment Booked'),
        ('abandoned', 'Abandoned'),
        ('ongoing', 'Ongoing'),
    ], string='Outcome', default='ongoing')
    
    escalated_to = fields.Many2one('doctor.doctor', string='Escalated To')
    appointment_id = fields.Many2one('doctor.appointment', string='Created Appointment')
    
    # Symptom Check Results
    symptom_check_id = fields.Many2one('symptom.check', string='Symptom Check')
    
    # Satisfaction
    rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent'),
    ], string='Rating')
    feedback = fields.Text(string='Feedback')
    
    state = fields.Selection([
        ('active', 'Active'),
        ('closed', 'Closed'),
    ], string='Status', default='active')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('chatbot.conversation') or 'New'
        return super().create(vals_list)

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration_minutes = int(delta.total_seconds() / 60)
            else:
                record.duration_minutes = 0

    @api.depends('message_ids')
    def _compute_message_count(self):
        for record in self:
            record.message_count = len(record.message_ids)

    def action_close(self):
        self.write({
            'state': 'closed',
            'end_time': fields.Datetime.now(),
        })

    def action_escalate(self):
        """Escalate to human support."""
        self.outcome = 'escalated_doctor'


class ChatbotMessage(models.Model):
    _name = 'chatbot.message'
    _description = 'Chatbot Message'
    _order = 'timestamp'

    conversation_id = fields.Many2one('chatbot.conversation', string='Conversation', required=True, ondelete='cascade')
    
    sender = fields.Selection([
        ('user', 'User'),
        ('bot', 'Chatbot'),
        ('system', 'System'),
    ], string='Sender', required=True)
    
    message = fields.Text(string='Message', required=True)
    timestamp = fields.Datetime(string='Time', default=fields.Datetime.now)
    
    # For bot responses
    intent_detected = fields.Char(string='Intent')
    confidence = fields.Float(string='Confidence')
    
    # Attachments
    attachment = fields.Binary(string='Attachment', attachment=True)
    attachment_filename = fields.Char(string='Filename')
    
    # Quick replies offered
    quick_replies = fields.Text(string='Quick Replies')
    selected_reply = fields.Char(string='Selected Reply')


class ChatbotIntent(models.Model):
    _name = 'chatbot.intent'
    _description = 'Chatbot Intent'
    _order = 'name'

    name = fields.Char(string='Intent Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    
    # Training phrases
    training_phrases = fields.Text(string='Training Phrases', help='One phrase per line')
    
    # Response templates
    response_templates = fields.Text(string='Response Templates', help='One template per line')
    
    # Actions
    action_type = fields.Selection([
        ('respond', 'Respond'),
        ('book_appointment', 'Book Appointment'),
        ('check_symptoms', 'Check Symptoms'),
        ('escalate', 'Escalate'),
        ('show_doctors', 'Show Doctors'),
        ('show_pharmacy', 'Show Pharmacy'),
    ], string='Action Type', default='respond')
    
    followup_intent_ids = fields.Many2many('chatbot.intent', 'chatbot_intent_followup_rel', 
                                           'intent_id', 'followup_id', string='Follow-up Intents')
    
    active = fields.Boolean(string='Active', default=True)


class ChatbotFAQ(models.Model):
    _name = 'chatbot.faq'
    _description = 'Chatbot FAQ'
    _order = 'sequence, question'

    sequence = fields.Integer(string='Sequence', default=10)
    question = fields.Char(string='Question', required=True)
    answer = fields.Text(string='Answer', required=True)
    
    category = fields.Selection([
        ('general', 'General'),
        ('appointment', 'Appointments'),
        ('payment', 'Payments'),
        ('prescription', 'Prescriptions'),
        ('insurance', 'Insurance'),
        ('technical', 'Technical'),
    ], string='Category', default='general')
    
    keywords = fields.Char(string='Keywords', help='Comma-separated keywords')
    
    helpful_count = fields.Integer(string='Helpful', default=0)
    not_helpful_count = fields.Integer(string='Not Helpful', default=0)
    
    active = fields.Boolean(string='Active', default=True)
