# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class DoctorBadge(models.Model):
    _name = 'doctor.badge'
    _description = 'Doctor Badge'
    _order = 'level_number desc, name'

    name = fields.Char(string='Badge Name', required=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')

    level = fields.Selection([
        ('verified', 'Verified'),
        ('certified', 'Certified'),
        ('excellence', 'Excellence'),
        ('master', 'Master'),
    ], string='Level', required=True)

    level_number = fields.Integer(compute='_compute_level_number', store=True)

    icon = fields.Char(string='Icon', default='fa-certificate')
    color = fields.Char(string='Color', default='#4CAF50')
    image = fields.Binary(string='Image', attachment=True)

    # Criteria for auto-assignment
    auto_assign = fields.Boolean(string='Auto-Assign', default=False)
    min_rating = fields.Float(string='Min Rating')
    min_reviews = fields.Integer(string='Min Reviews')
    min_consultations = fields.Integer(string='Min Consultations')
    min_months_active = fields.Integer(string='Min Months Active')
    max_complaint_rate = fields.Float(string='Max Complaint Rate %')

    # Benefits
    search_priority = fields.Integer(string='Search Priority Boost', default=0)
    premium_percentage = fields.Float(string='Premium Charge Allowed %', default=0)
    featured_eligible = fields.Boolean(string='Featured Eligible', default=False)

    # Requires audit
    requires_audit = fields.Boolean(string='Requires Manual Audit', default=False)

    active = fields.Boolean(string='Active', default=True)

    doctor_ids = fields.Many2many('doctor.doctor', string='Doctors with Badge')
    doctor_count = fields.Integer(compute='_compute_doctor_count', string='Doctors')

    @api.depends('level')
    def _compute_level_number(self):
        level_map = {'verified': 1, 'certified': 2, 'excellence': 3, 'master': 4}
        for record in self:
            record.level_number = level_map.get(record.level, 0)

    @api.depends('doctor_ids')
    def _compute_doctor_count(self):
        for record in self:
            record.doctor_count = len(record.doctor_ids)
