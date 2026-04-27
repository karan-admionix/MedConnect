# -*- coding: utf-8 -*-
{
    'name': 'MedConnect',
    'version': '19.0.4.0.0',
    'category': 'Healthcare',
    'summary': 'Complete Healthcare Ecosystem with Insurance & Analytics',
    'description': """
MedConnect Enterprise Edition
======================================

A comprehensive healthcare platform built for Odoo 19 Enterprise.

PHASE 1 - FOUNDATION:
---------------------
* Doctor registration and verification workflow
* Patient management with family accounts
* Appointment booking system
* Smart waitlist with auto-booking
* No-show prediction and prevention
* Review and rating system
* Doctor earnings and payouts
* Schedule management

PHASE 2 - GROWTH:
-----------------
* Patient subscription plans (Free/Basic/Premium)
* Dynamic pricing engine
* Health records vault (PHR)
* Doctor badges and trust levels
* Premium features

PHASE 3 - DIFFERENTIATION:
--------------------------
* Pharmacy/Lab partnerships
* AI Chatbot for patient support
* Doctor matching engine
* Corporate health module (B2B)
* Symptom checker

PHASE 4 - SCALE:
----------------
* Insurance integration (Providers, Plans, Claims, Pre-auth)
* Multi-currency support
* White-label configuration
* Advanced analytics and KPIs
* Doctor performance reports
* Revenue analysis
    """,
    'author': 'ADX Medicare',
    'website': 'https://admionixsolutions.com',
    'license': 'OEEL-1',

    'depends': [
        'base',
        'mail',
        'portal',
        'website',
        'payment',
        'auth_signup',
    ],

    'data': [
        # Security
        'security/doctor_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/ir_sequence_data.xml',
        'data/doctor_specialization_data.xml',
        'data/subscription_plan_data.xml',
        'data/doctor_badge_data.xml',

        # Views - Configuration
        'views/doctor_specialization_views.xml',
        'views/doctor_consultation_type_views.xml',
        'views/subscription_plan_views.xml',
        'views/doctor_badge_views.xml',
        'views/country_compliance_views.xml',

        # Views - Main
        'views/doctor_doctor_views.xml',
        'views/doctor_reject_wizard_views.xml',
        'views/doctor_patient_views.xml',
        'views/doctor_appointment_views.xml',
        'views/doctor_schedule_views.xml',
        'views/doctor_review_views.xml',
        'views/doctor_earning_views.xml',
        'views/doctor_payout_views.xml',
        'views/doctor_waitlist_views.xml',
        'views/health_record_views.xml',
        'views/patient_subscription_views.xml',

        # Phase 3 Views
        'views/pharmacy_lab_views.xml',
        'views/chatbot_symptom_views.xml',
        'views/doctor_matching_views.xml',
        'views/corporate_health_views.xml',

        # Phase 4 Views
        'views/insurance_views.xml',
        'views/analytics_views.xml',
        'views/whitelabel_views.xml',

        # Website Menu Items (navbar)
        'data/website_menu_data.xml',

        # Website Templates
        'views/portal_templates.xml',
        'views/website_doctor_templates.xml',
        'views/website_appointment_templates.xml',

        # Menus
        'views/doctor_menus.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'doctor_marketplace/static/src/css/doctor_marketplace.css',
        ],
        'web.assets_frontend': [
            'doctor_marketplace/static/src/css/website_doctor.css',
            'doctor_marketplace/static/src/xml/compliance_popup.xml',
            'doctor_marketplace/static/src/js/compliance_popup.js',
            'doctor_marketplace/static/src/js/compliance_registration.js',
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
