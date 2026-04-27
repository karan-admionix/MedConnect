# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class DoctorConsultationType(models.Model):
    _name = 'doctor.consultation.type'
    _description = 'Consultation Type'
    _order = 'sequence, name'

    name = fields.Char(string='Type', required=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')
    icon = fields.Char(string='Icon', default='fa-user-md')
    active = fields.Boolean(string='Active', default=True)
