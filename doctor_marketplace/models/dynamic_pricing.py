# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class DynamicPricingRule(models.Model):
    _name = 'dynamic.pricing.rule'
    _description = 'Dynamic Pricing Rule'
    _order = 'sequence, name'

    name = fields.Char(string='Rule Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)

    rule_type = fields.Selection([
        ('time_of_day', 'Time of Day'),
        ('day_of_week', 'Day of Week'),
        ('booking_window', 'Booking Window'),
        ('demand', 'Demand Based'),
        ('patient_type', 'Patient Type'),
    ], string='Rule Type', required=True)

    # Time of Day
    time_from = fields.Float(string='Time From')
    time_to = fields.Float(string='Time To')

    # Day of Week
    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Day')

    # Booking Window
    days_before_min = fields.Integer(string='Days Before (Min)')
    days_before_max = fields.Integer(string='Days Before (Max)')

    # Patient Type
    patient_type = fields.Selection([
        ('new', 'New Patient'),
        ('returning', 'Returning Patient'),
        ('subscriber', 'Subscriber'),
    ], string='Patient Type')

    # Adjustment
    adjustment_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ], string='Adjustment Type', default='percentage')

    adjustment_value = fields.Float(string='Adjustment Value')

    # Limits
    min_price = fields.Float(string='Min Price')
    max_price = fields.Float(string='Max Price')

    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
