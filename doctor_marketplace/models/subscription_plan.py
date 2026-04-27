# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SubscriptionPlan(models.Model):
    _name = 'subscription.plan'
    _description = 'Subscription Plan'
    _order = 'sequence, price'

    name = fields.Char(string='Plan Name', required=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Html(string='Description')

    # Pricing
    price = fields.Float(string='Monthly Price', required=True)
    annual_price = fields.Float(string='Annual Price')
    annual_discount = fields.Float(compute='_compute_annual_discount', string='Annual Discount %')

    # Benefits
    free_consultations = fields.Integer(string='Free Consultations/Month', default=0)
    consultation_discount = fields.Float(string='Consultation Discount %', default=0)
    priority_booking = fields.Boolean(string='Priority Booking', default=False)
    video_consultation = fields.Boolean(string='Video Consultation Included', default=False)
    family_members = fields.Integer(string='Family Members Allowed', default=0)
    health_records = fields.Boolean(string='Health Records Access', default=False)

    # Limits
    max_family_members = fields.Integer(string='Max Family Members', default=2)

    # Display
    color = fields.Char(string='Color')
    icon = fields.Char(string='Icon')
    featured = fields.Boolean(string='Featured', default=False)

    # Status
    active = fields.Boolean(string='Active', default=True)

    @api.depends('price', 'annual_price')
    def _compute_annual_discount(self):
        for record in self:
            if record.price and record.annual_price:
                yearly_monthly = record.price * 12
                record.annual_discount = ((yearly_monthly - record.annual_price) / yearly_monthly) * 100
            else:
                record.annual_discount = 0
