# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DoctorSchedule(models.Model):
    _name = 'doctor.schedule'
    _description = 'Doctor Weekly Schedule'
    _order = 'day_of_week, time_from'

    doctor_id = fields.Many2one('doctor.doctor', string='Doctor', required=True, ondelete='cascade')

    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Day', required=True)

    time_from = fields.Float(string='From', required=True)
    time_to = fields.Float(string='To', required=True)
    is_available = fields.Boolean(string='Available', default=True)

    slot_count = fields.Integer(compute='_compute_slot_count', string='Slots')

    @api.constrains('time_from', 'time_to')
    def _check_times(self):
        for record in self:
            if record.time_from >= record.time_to:
                raise ValidationError(_('End time must be after start time.'))
            if record.time_from < 0 or record.time_from >= 24:
                raise ValidationError(_('Invalid start time.'))
            if record.time_to <= 0 or record.time_to > 24:
                raise ValidationError(_('Invalid end time.'))

    @api.depends('time_from', 'time_to', 'doctor_id.consultation_duration', 'doctor_id.buffer_time')
    def _compute_slot_count(self):
        for record in self:
            if record.doctor_id:
                duration = (record.doctor_id.consultation_duration or 15) / 60
                buffer = (record.doctor_id.buffer_time or 0) / 60
                total_time = record.time_to - record.time_from
                if duration + buffer > 0:
                    record.slot_count = int(total_time / (duration + buffer))
                else:
                    record.slot_count = 0
            else:
                record.slot_count = 0
