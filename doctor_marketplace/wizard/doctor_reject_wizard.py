# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DoctorRejectWizard(models.TransientModel):
    _name = 'doctor.reject.wizard'
    _description = 'Doctor Registration Rejection Wizard'

    doctor_id = fields.Many2one(
        'doctor.doctor',
        string='Doctor',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
    )

    def action_confirm_reject(self):
        """Write the rejection reason and delegate state change to the model."""
        self.ensure_one()
        if not self.rejection_reason or not self.rejection_reason.strip():
            raise ValidationError(_('A rejection reason is mandatory.'))

        self.doctor_id.write({'rejection_reason': self.rejection_reason.strip()})
        self.doctor_id.action_reject()
        return {'type': 'ir.actions.act_window_close'}
