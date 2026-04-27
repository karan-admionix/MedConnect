# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date


class DoctorFamilyMember(models.Model):
    _name = 'doctor.family.member'
    _description = 'Patient Family Member'
    _order = 'name'

    patient_id = fields.Many2one('doctor.patient', string='Primary Account', required=True, ondelete='cascade')

    name = fields.Char(string='Name', required=True)
    relationship = fields.Selection([
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    ], string='Relationship', required=True)

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(compute='_compute_age', string='Age')
    is_minor = fields.Boolean(compute='_compute_age', string='Is Minor')

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

    allergies = fields.Text(string='Known Allergies')
    chronic_conditions = fields.Text(string='Chronic Conditions')

    appointment_ids = fields.One2many('doctor.appointment', 'family_member_id', string='Appointments')
    appointment_count = fields.Integer(compute='_compute_appointments', string='Appointments')

    active = fields.Boolean(string='Active', default=True)

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.date_of_birth:
                born = record.date_of_birth
                record.age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                record.is_minor = record.age < 18
            else:
                record.age = 0
                record.is_minor = False

    @api.depends('appointment_ids')
    def _compute_appointments(self):
        for record in self:
            record.appointment_count = len(record.appointment_ids)
