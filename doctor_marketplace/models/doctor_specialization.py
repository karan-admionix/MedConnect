# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class DoctorSpecialization(models.Model):
    _name = 'doctor.specialization'
    _description = 'Doctor Specialization'
    _order = 'sequence, name'

    name = fields.Char(string='Specialization', required=True, translate=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')
    icon = fields.Char(string='Icon Class', default='fa-stethoscope')
    image = fields.Binary(string='Image', attachment=True)

    parent_id = fields.Many2one('doctor.specialization', string='Parent Specialization', ondelete='cascade')
    child_ids = fields.One2many('doctor.specialization', 'parent_id', string='Sub-specializations')

    doctor_ids = fields.One2many('doctor.doctor', 'specialization_id', string='Doctors')
    doctor_count = fields.Integer(compute='_compute_doctor_count', string='Doctors')

    active = fields.Boolean(string='Active', default=True)
    featured = fields.Boolean(string='Featured', default=False)
    color = fields.Integer(string='Color Index')

    _constraints = [
        models.Constraint('UNIQUE(code)', 'Specialization code must be unique!'),
    ]

    @api.depends('doctor_ids')
    def _compute_doctor_count(self):
        for record in self:
            record.doctor_count = len(record.doctor_ids.filtered(lambda d: d.state == 'approved'))
