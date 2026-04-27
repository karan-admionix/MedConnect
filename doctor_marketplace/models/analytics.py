# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class AnalyticsDashboard(models.Model):
    _name = 'doctor.analytics.dashboard'
    _description = 'Analytics Dashboard'
    _auto = False  # This is a view/report model

    # Time-based filters
    date = fields.Date(string='Date')
    month = fields.Char(string='Month')
    year = fields.Char(string='Year')
    
    # Metrics
    total_appointments = fields.Integer(string='Total Appointments')
    completed_appointments = fields.Integer(string='Completed')
    cancelled_appointments = fields.Integer(string='Cancelled')
    no_show_appointments = fields.Integer(string='No Shows')
    
    total_revenue = fields.Float(string='Total Revenue')
    platform_commission = fields.Float(string='Platform Commission')
    doctor_payouts = fields.Float(string='Doctor Payouts')
    
    new_patients = fields.Integer(string='New Patients')
    new_doctors = fields.Integer(string='New Doctors')
    
    average_rating = fields.Float(string='Average Rating')
    total_reviews = fields.Integer(string='Total Reviews')

    def init(self):
        self.env.cr.execute("""
            DROP VIEW IF EXISTS doctor_analytics_dashboard;
            CREATE OR REPLACE VIEW doctor_analytics_dashboard AS (
                SELECT
                    row_number() OVER () as id,
                    a.appointment_date::date as date,
                    TO_CHAR(a.appointment_date, 'YYYY-MM') as month,
                    TO_CHAR(a.appointment_date, 'YYYY') as year,
                    COUNT(a.id) as total_appointments,
                    COUNT(CASE WHEN a.state = 'completed' THEN 1 END) as completed_appointments,
                    COUNT(CASE WHEN a.state = 'cancelled' THEN 1 END) as cancelled_appointments,
                    COUNT(CASE WHEN a.state = 'no_show' THEN 1 END) as no_show_appointments,
                    COALESCE(SUM(CASE WHEN a.state = 'completed' THEN a.final_amount ELSE 0 END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN a.state = 'completed' THEN a.platform_commission ELSE 0 END), 0) as platform_commission,
                    COALESCE(SUM(CASE WHEN a.state = 'completed' THEN a.doctor_payout ELSE 0 END), 0) as doctor_payouts,
                    0 as new_patients,
                    0 as new_doctors,
                    0 as average_rating,
                    0 as total_reviews
                FROM doctor_appointment a
                WHERE a.appointment_date IS NOT NULL
                GROUP BY a.appointment_date::date, TO_CHAR(a.appointment_date, 'YYYY-MM'), TO_CHAR(a.appointment_date, 'YYYY')
            )
        """)


class PlatformKPI(models.Model):
    _name = 'platform.kpi'
    _description = 'Platform KPI Snapshot'
    _order = 'date desc'

    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    kpi_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='KPI Type', default='daily', required=True)
    
    # Appointment Metrics
    appointments_booked = fields.Integer(string='Appointments Booked')
    appointments_completed = fields.Integer(string='Appointments Completed')
    appointments_cancelled = fields.Integer(string='Appointments Cancelled')
    appointments_no_show = fields.Integer(string='No Shows')
    completion_rate = fields.Float(string='Completion Rate %')
    
    # Revenue Metrics
    gross_revenue = fields.Float(string='Gross Revenue')
    platform_commission = fields.Float(string='Platform Commission')
    net_doctor_payouts = fields.Float(string='Net Doctor Payouts')
    average_consultation_fee = fields.Float(string='Avg Consultation Fee')
    
    # User Metrics
    new_patients = fields.Integer(string='New Patients')
    active_patients = fields.Integer(string='Active Patients')
    new_doctors = fields.Integer(string='New Doctors')
    active_doctors = fields.Integer(string='Active Doctors')
    
    # Subscription Metrics
    new_subscriptions = fields.Integer(string='New Subscriptions')
    subscription_revenue = fields.Float(string='Subscription Revenue')
    active_subscriptions = fields.Integer(string='Active Subscriptions')
    churn_count = fields.Integer(string='Churned Subscriptions')
    
    # Insurance Metrics
    insurance_claims_submitted = fields.Integer(string='Claims Submitted')
    insurance_claims_approved = fields.Integer(string='Claims Approved')
    insurance_amount_claimed = fields.Float(string='Amount Claimed')
    insurance_amount_settled = fields.Float(string='Amount Settled')
    
    # Engagement Metrics
    reviews_submitted = fields.Integer(string='Reviews Submitted')
    average_rating = fields.Float(string='Average Rating')
    waitlist_conversions = fields.Integer(string='Waitlist Conversions')
    
    # Corporate Metrics
    corporate_appointments = fields.Integer(string='Corporate Appointments')
    corporate_revenue = fields.Float(string='Corporate Revenue')

    @api.model
    def _cron_generate_daily_kpi(self):
        """Generate daily KPI snapshot"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Check if already generated
        existing = self.search([('date', '=', yesterday), ('kpi_type', '=', 'daily')])
        if existing:
            return
        
        # Calculate metrics
        Appointment = self.env['doctor.appointment']
        Patient = self.env['doctor.patient']
        Doctor = self.env['doctor.doctor']
        Review = self.env['doctor.review']
        
        appointments = Appointment.search([('appointment_date', '=', yesterday)])
        
        completed = appointments.filtered(lambda a: a.state == 'completed')
        cancelled = appointments.filtered(lambda a: a.state == 'cancelled')
        no_show = appointments.filtered(lambda a: a.state == 'no_show')
        
        new_patients = Patient.search_count([('create_date', '>=', str(yesterday)), 
                                              ('create_date', '<', str(today))])
        new_doctors = Doctor.search_count([('create_date', '>=', str(yesterday)),
                                            ('create_date', '<', str(today))])
        
        reviews = Review.search([('create_date', '>=', str(yesterday)),
                                  ('create_date', '<', str(today))])
        
        total_appointments = len(appointments)
        completion_rate = (len(completed) / total_appointments * 100) if total_appointments else 0
        
        gross_revenue = sum(completed.mapped('final_amount'))
        platform_commission = sum(completed.mapped('platform_commission'))
        
        vals = {
            'date': yesterday,
            'kpi_type': 'daily',
            'appointments_booked': total_appointments,
            'appointments_completed': len(completed),
            'appointments_cancelled': len(cancelled),
            'appointments_no_show': len(no_show),
            'completion_rate': completion_rate,
            'gross_revenue': gross_revenue,
            'platform_commission': platform_commission,
            'net_doctor_payouts': gross_revenue - platform_commission,
            'average_consultation_fee': (gross_revenue / len(completed)) if completed else 0,
            'new_patients': new_patients,
            'new_doctors': new_doctors,
            'reviews_submitted': len(reviews),
            'average_rating': sum(reviews.mapped('rating')) / len(reviews) if reviews else 0,
        }
        
        # Insurance metrics
        if 'insurance.claim' in self.env:
            Claim = self.env['insurance.claim']
            claims = Claim.search([('submission_date', '=', yesterday)])
            approved = Claim.search([('processing_date', '=', yesterday), ('state', '=', 'approved')])
            settled = Claim.search([('settlement_date', '=', yesterday)])
            
            vals.update({
                'insurance_claims_submitted': len(claims),
                'insurance_claims_approved': len(approved),
                'insurance_amount_claimed': sum(claims.mapped('claimed_amount')),
                'insurance_amount_settled': sum(settled.mapped('settlement_amount')),
            })
        
        self.create(vals)

    @api.model
    def _cron_generate_weekly_kpi(self):
        """Generate weekly KPI snapshot (runs on Monday)"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday() + 7)  # Last Monday
        week_end = week_start + timedelta(days=6)  # Last Sunday
        
        existing = self.search([('date', '=', week_end), ('kpi_type', '=', 'weekly')])
        if existing:
            return
        
        # Aggregate daily KPIs
        daily_kpis = self.search([
            ('date', '>=', week_start),
            ('date', '<=', week_end),
            ('kpi_type', '=', 'daily'),
        ])
        
        if not daily_kpis:
            return
        
        vals = {
            'date': week_end,
            'kpi_type': 'weekly',
            'appointments_booked': sum(daily_kpis.mapped('appointments_booked')),
            'appointments_completed': sum(daily_kpis.mapped('appointments_completed')),
            'appointments_cancelled': sum(daily_kpis.mapped('appointments_cancelled')),
            'appointments_no_show': sum(daily_kpis.mapped('appointments_no_show')),
            'gross_revenue': sum(daily_kpis.mapped('gross_revenue')),
            'platform_commission': sum(daily_kpis.mapped('platform_commission')),
            'net_doctor_payouts': sum(daily_kpis.mapped('net_doctor_payouts')),
            'new_patients': sum(daily_kpis.mapped('new_patients')),
            'new_doctors': sum(daily_kpis.mapped('new_doctors')),
            'reviews_submitted': sum(daily_kpis.mapped('reviews_submitted')),
            'insurance_claims_submitted': sum(daily_kpis.mapped('insurance_claims_submitted')),
            'insurance_amount_settled': sum(daily_kpis.mapped('insurance_amount_settled')),
        }
        
        # Calculate averages
        if vals['appointments_booked']:
            vals['completion_rate'] = (vals['appointments_completed'] / vals['appointments_booked']) * 100
        if vals['appointments_completed']:
            vals['average_consultation_fee'] = vals['gross_revenue'] / vals['appointments_completed']
        if daily_kpis:
            ratings = [k.average_rating for k in daily_kpis if k.average_rating]
            vals['average_rating'] = sum(ratings) / len(ratings) if ratings else 0
        
        self.create(vals)


class DoctorPerformanceReport(models.Model):
    _name = 'doctor.performance.report'
    _description = 'Doctor Performance Report'
    _auto = False

    doctor_id = fields.Many2one('doctor.doctor', string='Doctor', readonly=True)
    doctor_name = fields.Char(string='Doctor Name', readonly=True)
    specialization = fields.Char(string='Specialization', readonly=True)
    
    period = fields.Date(string='Period', readonly=True)
    
    total_appointments = fields.Integer(string='Total Appointments', readonly=True)
    completed_appointments = fields.Integer(string='Completed', readonly=True)
    cancelled_appointments = fields.Integer(string='Cancelled', readonly=True)
    no_show_appointments = fields.Integer(string='No Shows', readonly=True)
    
    completion_rate = fields.Float(string='Completion Rate %', readonly=True)
    
    gross_earnings = fields.Float(string='Gross Earnings', readonly=True)
    platform_commission = fields.Float(string='Platform Commission', readonly=True)
    net_earnings = fields.Float(string='Net Earnings', readonly=True)
    
    average_rating = fields.Float(string='Avg Rating', readonly=True)
    total_reviews = fields.Integer(string='Reviews', readonly=True)
    
    patients_served = fields.Integer(string='Patients Served', readonly=True)

    def init(self):
        self.env.cr.execute("""
            DROP VIEW IF EXISTS doctor_performance_report;
            CREATE OR REPLACE VIEW doctor_performance_report AS (
                SELECT
                    row_number() OVER () as id,
                    d.id as doctor_id,
                    d.name as doctor_name,
                    s.name as specialization,
                    DATE_TRUNC('month', a.appointment_date)::date as period,
                    COUNT(a.id) as total_appointments,
                    COUNT(CASE WHEN a.state = 'completed' THEN 1 END) as completed_appointments,
                    COUNT(CASE WHEN a.state = 'cancelled' THEN 1 END) as cancelled_appointments,
                    COUNT(CASE WHEN a.state = 'no_show' THEN 1 END) as no_show_appointments,
                    CASE 
                        WHEN COUNT(a.id) > 0 
                        THEN (COUNT(CASE WHEN a.state = 'completed' THEN 1 END)::float / COUNT(a.id)::float * 100)
                        ELSE 0 
                    END as completion_rate,
                    COALESCE(SUM(CASE WHEN a.state = 'completed' THEN a.final_amount ELSE 0 END), 0) as gross_earnings,
                    COALESCE(SUM(CASE WHEN a.state = 'completed' THEN a.platform_commission ELSE 0 END), 0) as platform_commission,
                    COALESCE(SUM(CASE WHEN a.state = 'completed' THEN a.doctor_payout ELSE 0 END), 0) as net_earnings,
                    COALESCE(AVG(r.rating), 0) as average_rating,
                    COUNT(DISTINCT r.id) as total_reviews,
                    COUNT(DISTINCT a.patient_id) as patients_served
                FROM doctor_doctor d
                LEFT JOIN doctor_specialization s ON s.id = d.specialization_id
                LEFT JOIN doctor_appointment a ON a.doctor_id = d.id
                LEFT JOIN doctor_review r ON r.doctor_id = d.id AND r.state = 'approved'
                WHERE d.active = true
                GROUP BY d.id, d.name, s.name, DATE_TRUNC('month', a.appointment_date)
            )
        """)


class RevenueAnalysisReport(models.Model):
    _name = 'revenue.analysis.report'
    _description = 'Revenue Analysis Report'
    _auto = False

    period = fields.Date(string='Period', readonly=True)
    period_type = fields.Char(string='Period Type', readonly=True)
    
    # Consultation Revenue
    consultation_revenue = fields.Float(string='Consultation Revenue', readonly=True)
    video_consultation_revenue = fields.Float(string='Video Consultation Revenue', readonly=True)
    followup_revenue = fields.Float(string='Follow-up Revenue', readonly=True)
    
    # Subscription Revenue
    subscription_revenue = fields.Float(string='Subscription Revenue', readonly=True)
    
    # Corporate Revenue
    corporate_revenue = fields.Float(string='Corporate Revenue', readonly=True)
    
    # Insurance
    insurance_claims_revenue = fields.Float(string='Insurance Claims', readonly=True)
    
    # Total
    total_revenue = fields.Float(string='Total Revenue', readonly=True)
    platform_commission = fields.Float(string='Platform Commission', readonly=True)
    
    # Counts
    total_transactions = fields.Integer(string='Total Transactions', readonly=True)

    def init(self):
        self.env.cr.execute("""
            DROP VIEW IF EXISTS revenue_analysis_report;
            CREATE OR REPLACE VIEW revenue_analysis_report AS (
                SELECT
                    row_number() OVER () as id,
                    DATE_TRUNC('month', a.appointment_date)::date as period,
                    'monthly' as period_type,
                    COALESCE(SUM(CASE 
                        WHEN a.state = 'completed' AND a.consultation_mode = 'in_person' 
                        THEN a.final_amount ELSE 0 END), 0) as consultation_revenue,
                    COALESCE(SUM(CASE 
                        WHEN a.state = 'completed' AND a.consultation_mode = 'video' 
                        THEN a.final_amount ELSE 0 END), 0) as video_consultation_revenue,
                    COALESCE(SUM(CASE 
                        WHEN a.state = 'completed' AND a.consultation_type = 'followup' 
                        THEN a.final_amount ELSE 0 END), 0) as followup_revenue,
                    0 as subscription_revenue,
                    COALESCE(SUM(CASE 
                        WHEN a.state = 'completed' AND a.corporate_id IS NOT NULL 
                        THEN a.final_amount ELSE 0 END), 0) as corporate_revenue,
                    0 as insurance_claims_revenue,
                    COALESCE(SUM(CASE WHEN a.state = 'completed' THEN a.final_amount ELSE 0 END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN a.state = 'completed' THEN a.platform_commission ELSE 0 END), 0) as platform_commission,
                    COUNT(CASE WHEN a.state = 'completed' THEN 1 END) as total_transactions
                FROM doctor_appointment a
                WHERE a.appointment_date IS NOT NULL
                GROUP BY DATE_TRUNC('month', a.appointment_date)
                ORDER BY period DESC
            )
        """)


class PatientAnalyticsReport(models.Model):
    _name = 'patient.analytics.report'
    _description = 'Patient Analytics Report'
    _auto = False

    period = fields.Date(string='Period', readonly=True)
    
    new_registrations = fields.Integer(string='New Registrations', readonly=True)
    active_patients = fields.Integer(string='Active Patients', readonly=True)
    returning_patients = fields.Integer(string='Returning Patients', readonly=True)
    
    total_appointments = fields.Integer(string='Total Appointments', readonly=True)
    avg_appointments_per_patient = fields.Float(string='Avg Appointments/Patient', readonly=True)
    
    subscription_conversions = fields.Integer(string='Subscription Conversions', readonly=True)
    
    total_spent = fields.Float(string='Total Spent', readonly=True)
    avg_spend_per_patient = fields.Float(string='Avg Spend/Patient', readonly=True)

    def init(self):
        self.env.cr.execute("""
            DROP VIEW IF EXISTS patient_analytics_report;
            CREATE OR REPLACE VIEW patient_analytics_report AS (
                SELECT
                    row_number() OVER () as id,
                    DATE_TRUNC('month', p.create_date)::date as period,
                    COUNT(DISTINCT p.id) as new_registrations,
                    COUNT(DISTINCT CASE WHEN a.id IS NOT NULL THEN p.id END) as active_patients,
                    COUNT(DISTINCT CASE WHEN a.consultation_type = 'followup' THEN p.id END) as returning_patients,
                    COUNT(a.id) as total_appointments,
                    CASE 
                        WHEN COUNT(DISTINCT p.id) > 0 
                        THEN COUNT(a.id)::float / COUNT(DISTINCT p.id)::float 
                        ELSE 0 
                    END as avg_appointments_per_patient,
                    0 as subscription_conversions,
                    COALESCE(SUM(a.final_amount), 0) as total_spent,
                    CASE 
                        WHEN COUNT(DISTINCT p.id) > 0 
                        THEN COALESCE(SUM(a.final_amount), 0) / COUNT(DISTINCT p.id)::float 
                        ELSE 0 
                    END as avg_spend_per_patient
                FROM doctor_patient p
                LEFT JOIN doctor_appointment a ON a.patient_id = p.id AND a.state = 'completed'
                GROUP BY DATE_TRUNC('month', p.create_date)
                ORDER BY period DESC
            )
        """)
