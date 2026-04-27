# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PharmacyPartner(models.Model):
    _name = 'pharmacy.partner'
    _description = 'Pharmacy Partner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Pharmacy Name', required=True, tracking=True)
    code = fields.Char(string='Partner Code', readonly=True, copy=False)
    image = fields.Binary(string='Logo', attachment=True)
    partner_id = fields.Many2one('res.partner', string='Contact', ondelete='cascade')
    
    # Contact
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    website = fields.Char(string='Website')
    
    # Address
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.ref('base.in', raise_if_not_found=False))
    zip_code = fields.Char(string='PIN Code')
    
    # License
    license_number = fields.Char(string='License Number', required=True)
    license_expiry = fields.Date(string='License Expiry')
    gst_number = fields.Char(string='GST Number')
    
    # Partnership Details
    partnership_type = fields.Selection([
        ('basic', 'Basic Partner'),
        ('preferred', 'Preferred Partner'),
        ('exclusive', 'Exclusive Partner'),
    ], string='Partnership Type', default='basic')
    
    commission_rate = fields.Float(string='Commission Rate %', default=10.0)
    contract_start = fields.Date(string='Contract Start')
    contract_end = fields.Date(string='Contract End')
    
    # Operating Hours
    operating_hours = fields.Text(string='Operating Hours')
    is_24x7 = fields.Boolean(string='24x7 Available', default=False)
    home_delivery = fields.Boolean(string='Home Delivery', default=True)
    delivery_radius = fields.Float(string='Delivery Radius (km)', default=10.0)
    
    # Bank Details
    bank_name = fields.Char(string='Bank Name')
    bank_account = fields.Char(string='Account Number')
    bank_ifsc = fields.Char(string='IFSC Code')
    
    # Statistics
    order_ids = fields.One2many('pharmacy.order', 'pharmacy_id', string='Orders')
    order_count = fields.Integer(compute='_compute_stats', string='Total Orders')
    total_revenue = fields.Float(compute='_compute_stats', string='Total Revenue')
    rating = fields.Float(string='Rating', default=0.0)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ], string='Status', default='draft', tracking=True)
    
    active = fields.Boolean(string='Active', default=True)

    _constraints = [
        models.Constraint('UNIQUE(license_number)', 'License number must be unique!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('pharmacy.partner') or 'NEW'
        return super().create(vals_list)

    @api.depends('order_ids', 'order_ids.state', 'order_ids.total_amount')
    def _compute_stats(self):
        for record in self:
            completed_orders = record.order_ids.filtered(lambda o: o.state == 'delivered')
            record.order_count = len(completed_orders)
            record.total_revenue = sum(completed_orders.mapped('total_amount'))

    def action_submit(self):
        for record in self:
            record.state = 'pending'

    def action_approve(self):
        for record in self:
            record.state = 'active'

    def action_suspend(self):
        for record in self:
            record.state = 'suspended'

    def action_terminate(self):
        for record in self:
            record.state = 'terminated'


class LabPartner(models.Model):
    _name = 'lab.partner'
    _description = 'Laboratory Partner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Lab Name', required=True, tracking=True)
    code = fields.Char(string='Partner Code', readonly=True, copy=False)
    image = fields.Binary(string='Logo', attachment=True)
    partner_id = fields.Many2one('res.partner', string='Contact', ondelete='cascade')
    
    # Contact
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    website = fields.Char(string='Website')
    
    # Address
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.ref('base.in', raise_if_not_found=False))
    zip_code = fields.Char(string='PIN Code')
    
    # Accreditation
    nabl_accredited = fields.Boolean(string='NABL Accredited', default=False)
    nabl_number = fields.Char(string='NABL Number')
    cap_accredited = fields.Boolean(string='CAP Accredited', default=False)
    license_number = fields.Char(string='License Number', required=True)
    license_expiry = fields.Date(string='License Expiry')
    
    # Partnership
    partnership_type = fields.Selection([
        ('basic', 'Basic Partner'),
        ('preferred', 'Preferred Partner'),
        ('exclusive', 'Exclusive Partner'),
    ], string='Partnership Type', default='basic')
    
    commission_rate = fields.Float(string='Commission Rate %', default=15.0)
    contract_start = fields.Date(string='Contract Start')
    contract_end = fields.Date(string='Contract End')
    
    # Services
    test_ids = fields.One2many('lab.test', 'lab_id', string='Available Tests')
    home_collection = fields.Boolean(string='Home Collection', default=True)
    home_collection_fee = fields.Float(string='Home Collection Fee')
    report_delivery_hours = fields.Integer(string='Report Delivery (hours)', default=24)
    
    # Statistics
    booking_ids = fields.One2many('lab.booking', 'lab_id', string='Bookings')
    booking_count = fields.Integer(compute='_compute_stats', string='Total Bookings')
    total_revenue = fields.Float(compute='_compute_stats', string='Total Revenue')
    rating = fields.Float(string='Rating', default=0.0)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ], string='Status', default='draft', tracking=True)
    
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('lab.partner') or 'NEW'
        return super().create(vals_list)

    @api.depends('booking_ids', 'booking_ids.state', 'booking_ids.total_amount')
    def _compute_stats(self):
        for record in self:
            completed = record.booking_ids.filtered(lambda b: b.state == 'completed')
            record.booking_count = len(completed)
            record.total_revenue = sum(completed.mapped('total_amount'))

    def action_submit(self):
        self.state = 'pending'

    def action_approve(self):
        self.state = 'active'

    def action_suspend(self):
        self.state = 'suspended'


class LabTest(models.Model):
    _name = 'lab.test'
    _description = 'Lab Test'
    _order = 'name'

    name = fields.Char(string='Test Name', required=True)
    code = fields.Char(string='Test Code')
    lab_id = fields.Many2one('lab.partner', string='Lab', required=True, ondelete='cascade')
    
    category = fields.Selection([
        ('blood', 'Blood Test'),
        ('urine', 'Urine Test'),
        ('imaging', 'Imaging'),
        ('pathology', 'Pathology'),
        ('microbiology', 'Microbiology'),
        ('biochemistry', 'Biochemistry'),
        ('other', 'Other'),
    ], string='Category', default='blood')
    
    description = fields.Text(string='Description')
    preparation = fields.Text(string='Preparation Instructions')
    
    price = fields.Float(string='Price', required=True)
    discounted_price = fields.Float(string='Discounted Price')
    
    turnaround_hours = fields.Integer(string='Turnaround Time (hours)', default=24)
    sample_type = fields.Char(string='Sample Type')
    fasting_required = fields.Boolean(string='Fasting Required', default=False)
    
    active = fields.Boolean(string='Active', default=True)


class LabBooking(models.Model):
    _name = 'lab.booking'
    _description = 'Lab Booking'
    _inherit = ['mail.thread']
    _order = 'booking_date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    
    patient_id = fields.Many2one('doctor.patient', string='Patient', required=True)
    lab_id = fields.Many2one('lab.partner', string='Lab', required=True)
    appointment_id = fields.Many2one('doctor.appointment', string='Related Appointment')
    
    test_ids = fields.Many2many('lab.test', string='Tests')
    
    booking_date = fields.Date(string='Booking Date', required=True, default=fields.Date.today)
    collection_date = fields.Datetime(string='Collection Date/Time')
    
    collection_type = fields.Selection([
        ('lab', 'At Lab'),
        ('home', 'Home Collection'),
    ], string='Collection Type', default='lab')
    
    collection_address = fields.Text(string='Collection Address')
    
    # Pricing
    subtotal = fields.Float(compute='_compute_totals', string='Subtotal', store=True)
    collection_fee = fields.Float(string='Collection Fee')
    discount = fields.Float(string='Discount')
    total_amount = fields.Float(compute='_compute_totals', string='Total', store=True)
    
    # Payment
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ], string='Payment Status', default='pending')
    
    # Results
    report_file = fields.Binary(string='Report', attachment=True)
    report_filename = fields.Char(string='Report Filename')
    report_date = fields.Datetime(string='Report Date')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('sample_collected', 'Sample Collected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('lab.booking') or 'New'
        return super().create(vals_list)

    @api.depends('test_ids', 'collection_fee', 'discount')
    def _compute_totals(self):
        for record in self:
            record.subtotal = sum(
                t.discounted_price if t.discounted_price > 0 else t.price
                for t in record.test_ids
            )
            record.total_amount = record.subtotal + (record.collection_fee or 0) - (record.discount or 0)

    def action_confirm(self):
        self.state = 'confirmed'

    def action_collect_sample(self):
        self.state = 'sample_collected'

    def action_process(self):
        self.state = 'processing'

    def action_complete(self):
        self.write({
            'state': 'completed',
            'report_date': fields.Datetime.now(),
        })

    def action_cancel(self):
        self.state = 'cancelled'


class PharmacyOrder(models.Model):
    _name = 'pharmacy.order'
    _description = 'Pharmacy Order'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    
    patient_id = fields.Many2one('doctor.patient', string='Patient', required=True)
    pharmacy_id = fields.Many2one('pharmacy.partner', string='Pharmacy', required=True)
    appointment_id = fields.Many2one('doctor.appointment', string='Related Appointment')
    
    # Prescription
    prescription_image = fields.Binary(string='Prescription', attachment=True)
    prescription_filename = fields.Char(string='Filename')
    prescription_verified = fields.Boolean(string='Prescription Verified', default=False)
    
    # Order Lines
    line_ids = fields.One2many('pharmacy.order.line', 'order_id', string='Order Lines')
    
    # Delivery
    delivery_type = fields.Selection([
        ('pickup', 'Store Pickup'),
        ('delivery', 'Home Delivery'),
    ], string='Delivery Type', default='delivery')
    
    delivery_address = fields.Text(string='Delivery Address')
    delivery_date = fields.Date(string='Expected Delivery')
    delivered_date = fields.Datetime(string='Delivered Date')
    
    # Pricing
    subtotal = fields.Float(compute='_compute_totals', string='Subtotal', store=True)
    delivery_fee = fields.Float(string='Delivery Fee')
    discount = fields.Float(string='Discount')
    total_amount = fields.Float(compute='_compute_totals', string='Total', store=True)
    
    # Payment
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cod', 'Cash on Delivery'),
        ('refunded', 'Refunded'),
    ], string='Payment Status', default='pending')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('dispatched', 'Dispatched'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pharmacy.order') or 'New'
        return super().create(vals_list)

    @api.depends('line_ids.subtotal', 'delivery_fee', 'discount')
    def _compute_totals(self):
        for record in self:
            record.subtotal = sum(record.line_ids.mapped('subtotal'))
            record.total_amount = record.subtotal + (record.delivery_fee or 0) - (record.discount or 0)

    def action_confirm(self):
        self.state = 'confirmed'

    def action_process(self):
        self.state = 'processing'

    def action_ready(self):
        self.state = 'ready'

    def action_dispatch(self):
        self.state = 'dispatched'

    def action_deliver(self):
        self.write({
            'state': 'delivered',
            'delivered_date': fields.Datetime.now(),
        })

    def action_cancel(self):
        self.state = 'cancelled'


class PharmacyOrderLine(models.Model):
    _name = 'pharmacy.order.line'
    _description = 'Pharmacy Order Line'

    order_id = fields.Many2one('pharmacy.order', string='Order', required=True, ondelete='cascade')
    
    medicine_name = fields.Char(string='Medicine', required=True)
    quantity = fields.Integer(string='Quantity', default=1)
    unit_price = fields.Float(string='Unit Price')
    subtotal = fields.Float(compute='_compute_subtotal', string='Subtotal', store=True)
    
    is_available = fields.Boolean(string='Available', default=True)
    substitute_name = fields.Char(string='Substitute')
    notes = fields.Char(string='Notes')

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.quantity * (record.unit_price or 0)
