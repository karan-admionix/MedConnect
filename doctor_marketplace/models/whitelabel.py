# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WhitelabelConfig(models.Model):
    _name = 'whitelabel.config'
    _description = 'White-label Configuration'
    _inherit = ['mail.thread']
    _rec_name = 'brand_name'

    # Basic Branding
    brand_name = fields.Char(string='Brand Name', required=True, tracking=True,
                             default='MedConnect')
    tagline = fields.Char(string='Tagline', default='Your Health, Our Priority')
    
    # Logos
    logo = fields.Binary(string='Primary Logo', attachment=True)
    logo_small = fields.Binary(string='Small Logo (Icon)', attachment=True)
    favicon = fields.Binary(string='Favicon', attachment=True)
    
    # Colors
    primary_color = fields.Char(string='Primary Color', default='#007bff',
                                help='Main brand color (hex code)')
    secondary_color = fields.Char(string='Secondary Color', default='#6c757d')
    accent_color = fields.Char(string='Accent Color', default='#28a745')
    
    header_bg_color = fields.Char(string='Header Background', default='#ffffff')
    header_text_color = fields.Char(string='Header Text Color', default='#333333')
    footer_bg_color = fields.Char(string='Footer Background', default='#f8f9fa')
    footer_text_color = fields.Char(string='Footer Text Color', default='#666666')
    
    button_primary_color = fields.Char(string='Primary Button', default='#007bff')
    button_secondary_color = fields.Char(string='Secondary Button', default='#6c757d')
    
    # Typography
    font_family = fields.Selection([
        ('roboto', 'Roboto'),
        ('open_sans', 'Open Sans'),
        ('lato', 'Lato'),
        ('montserrat', 'Montserrat'),
        ('poppins', 'Poppins'),
        ('nunito', 'Nunito'),
        ('custom', 'Custom Font'),
    ], string='Font Family', default='roboto')
    custom_font_url = fields.Char(string='Custom Font URL',
                                   help='Google Fonts URL for custom font')
    
    # Contact Information
    support_email = fields.Char(string='Support Email')
    support_phone = fields.Char(string='Support Phone')
    support_hours = fields.Char(string='Support Hours', default='Mon-Fri 9AM-6PM')
    
    # Social Media
    facebook_url = fields.Char(string='Facebook URL')
    twitter_url = fields.Char(string='Twitter/X URL')
    instagram_url = fields.Char(string='Instagram URL')
    linkedin_url = fields.Char(string='LinkedIn URL')
    youtube_url = fields.Char(string='YouTube URL')
    
    # Legal
    company_name = fields.Char(string='Company Legal Name')
    company_address = fields.Text(string='Company Address')
    terms_url = fields.Char(string='Terms & Conditions URL')
    privacy_url = fields.Char(string='Privacy Policy URL')
    refund_url = fields.Char(string='Refund Policy URL')
    
    # Email Branding
    email_header_logo = fields.Binary(string='Email Header Logo', attachment=True)
    email_footer_text = fields.Html(string='Email Footer')
    email_signature = fields.Html(string='Email Signature')
    
    # App Store Links
    android_app_url = fields.Char(string='Android App URL')
    ios_app_url = fields.Char(string='iOS App URL')
    
    # Website Settings
    homepage_title = fields.Char(string='Homepage Title', default='Book Doctor Appointments Online')
    meta_description = fields.Text(string='Meta Description')
    google_analytics_id = fields.Char(string='Google Analytics ID')
    facebook_pixel_id = fields.Char(string='Facebook Pixel ID')
    
    # Feature Toggles
    show_ratings = fields.Boolean(string='Show Doctor Ratings', default=True)
    show_reviews = fields.Boolean(string='Show Reviews', default=True)
    show_video_consultation = fields.Boolean(string='Enable Video Consultation', default=True)
    show_home_visit = fields.Boolean(string='Enable Home Visit', default=True)
    show_pharmacy = fields.Boolean(string='Enable Pharmacy', default=True)
    show_lab = fields.Boolean(string='Enable Lab Services', default=True)
    show_subscription = fields.Boolean(string='Enable Subscriptions', default=True)
    show_corporate = fields.Boolean(string='Enable Corporate Health', default=True)
    show_insurance = fields.Boolean(string='Enable Insurance', default=True)
    show_chatbot = fields.Boolean(string='Enable AI Chatbot', default=True)
    
    # Currency Settings
    default_currency_id = fields.Many2one('res.currency', string='Default Currency',
                                          default=lambda self: self.env.ref('base.INR', raise_if_not_found=False))
    supported_currency_ids = fields.Many2many('res.currency', string='Supported Currencies')
    
    # Language Settings
    default_language_id = fields.Many2one('res.lang', string='Default Language')
    supported_language_ids = fields.Many2many('res.lang', string='Supported Languages')
    
    # Notification Settings
    sms_enabled = fields.Boolean(string='SMS Notifications', default=True)
    email_enabled = fields.Boolean(string='Email Notifications', default=True)
    whatsapp_enabled = fields.Boolean(string='WhatsApp Notifications', default=False)
    push_enabled = fields.Boolean(string='Push Notifications', default=True)
    
    # Payment Gateways
    payment_gateway = fields.Selection([
        ('razorpay', 'Razorpay'),
        ('paytm', 'Paytm'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('manual', 'Manual/Cash'),
    ], string='Primary Payment Gateway', default='razorpay')
    
    # Platform Fees
    platform_commission_percent = fields.Float(string='Platform Commission %', default=15.0)
    minimum_payout = fields.Float(string='Minimum Payout Amount', default=500.0)
    payout_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    ], string='Payout Frequency', default='weekly')
    
    # Status
    is_active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                  default=lambda self: self.env.company)

    _constraints = [
        models.Constraint('UNIQUE(company_id)', 'Only one configuration per company allowed!'),
    ]

    @api.constrains('primary_color', 'secondary_color', 'accent_color')
    def _check_color_format(self):
        import re
        hex_pattern = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
        for record in self:
            for field in ['primary_color', 'secondary_color', 'accent_color']:
                color = getattr(record, field)
                if color and not hex_pattern.match(color):
                    raise ValidationError(_('%s must be a valid hex color code (e.g., #007bff)') % field)

    @api.model
    def get_config(self, company_id=None):
        """Get whitelabel config for current or specified company"""
        if not company_id:
            company_id = self.env.company.id
        config = self.search([('company_id', '=', company_id), ('is_active', '=', True)], limit=1)
        if not config:
            # Return default values
            return {
                'brand_name': 'MedConnect',
                'primary_color': '#007bff',
                'secondary_color': '#6c757d',
                'platform_commission_percent': 15.0,
            }
        return config

    def generate_css(self):
        """Generate CSS variables from configuration"""
        self.ensure_one()
        css = f"""
:root {{
    --brand-primary: {self.primary_color or '#007bff'};
    --brand-secondary: {self.secondary_color or '#6c757d'};
    --brand-accent: {self.accent_color or '#28a745'};
    --header-bg: {self.header_bg_color or '#ffffff'};
    --header-text: {self.header_text_color or '#333333'};
    --footer-bg: {self.footer_bg_color or '#f8f9fa'};
    --footer-text: {self.footer_text_color or '#666666'};
    --btn-primary: {self.button_primary_color or '#007bff'};
    --btn-secondary: {self.button_secondary_color or '#6c757d'};
}}
"""
        font_map = {
            'roboto': "'Roboto', sans-serif",
            'open_sans': "'Open Sans', sans-serif",
            'lato': "'Lato', sans-serif",
            'montserrat': "'Montserrat', sans-serif",
            'poppins': "'Poppins', sans-serif",
            'nunito': "'Nunito', sans-serif",
        }
        if self.font_family and self.font_family != 'custom':
            css += f"""
body {{
    font-family: {font_map.get(self.font_family, "'Roboto', sans-serif")};
}}
"""
        return css


class MultiCurrencyConfig(models.Model):
    _name = 'multicurrency.config'
    _description = 'Multi-currency Configuration'

    name = fields.Char(string='Name', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    
    # Exchange Rate Settings
    auto_update = fields.Boolean(string='Auto-update Rates', default=True)
    update_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('manual', 'Manual'),
    ], string='Update Frequency', default='daily')
    
    # Rounding
    rounding_method = fields.Selection([
        ('round', 'Round'),
        ('round_up', 'Round Up'),
        ('round_down', 'Round Down'),
    ], string='Rounding Method', default='round')
    
    # Display
    symbol_position = fields.Selection([
        ('before', 'Before Amount'),
        ('after', 'After Amount'),
    ], string='Symbol Position', default='before')
    
    is_active = fields.Boolean(string='Active', default=True)


# Extend Doctor for multi-currency
class DoctorDoctorCurrency(models.Model):
    _inherit = 'doctor.doctor'

    currency_id = fields.Many2one('res.currency', string='Currency',
                                   default=lambda self: self.env.company.currency_id)
    
    # Currency-aware fees
    consultation_fee_currency = fields.Monetary(string='Consultation Fee',
                                                 currency_field='currency_id')
    followup_fee_currency = fields.Monetary(string='Follow-up Fee',
                                            currency_field='currency_id')
    video_fee_currency = fields.Monetary(string='Video Fee',
                                         currency_field='currency_id')
    home_visit_fee_currency = fields.Monetary(string='Home Visit Fee',
                                              currency_field='currency_id')


# Extend Appointment for multi-currency
class DoctorAppointmentCurrency(models.Model):
    _inherit = 'doctor.appointment'

    currency_id = fields.Many2one('res.currency', string='Currency',
                                   default=lambda self: self.env.company.currency_id)
    
    # Make amount fields currency-aware
    consultation_fee_display = fields.Monetary(string='Consultation Fee',
                                                compute='_compute_fee_display',
                                                currency_field='currency_id')
    final_amount_display = fields.Monetary(string='Final Amount',
                                           compute='_compute_fee_display',
                                           currency_field='currency_id')

    @api.depends('consultation_fee', 'final_amount', 'currency_id')
    def _compute_fee_display(self):
        for record in self:
            record.consultation_fee_display = record.consultation_fee
            record.final_amount_display = record.final_amount


# Extend Subscription Plan for multi-currency
class SubscriptionPlanCurrency(models.Model):
    _inherit = 'subscription.plan'

    currency_id = fields.Many2one('res.currency', string='Currency',
                                   default=lambda self: self.env.company.currency_id)
    
    price_display = fields.Monetary(string='Monthly Price',
                                    compute='_compute_price_display',
                                    currency_field='currency_id')
    annual_price_display = fields.Monetary(string='Annual Price',
                                           compute='_compute_price_display',
                                           currency_field='currency_id')

    @api.depends('price', 'annual_price', 'currency_id')
    def _compute_price_display(self):
        for record in self:
            record.price_display = record.price
            record.annual_price_display = record.annual_price
