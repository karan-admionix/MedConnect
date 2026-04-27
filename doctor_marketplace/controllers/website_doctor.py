# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from odoo.addons.portal.controllers.portal import CustomerPortal
import logging

_logger = logging.getLogger(__name__)


class DoctorCustomerPortal(CustomerPortal):
    """
    Extends the standard CustomerPortal to inject appointment_count
    into the portal home page (/my/home) values.
    """

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        # Patient: count of their own booked appointments
        if 'appointment_count' in counters:
            patient = request.env['doctor.patient'].sudo().search([
                ('user_id', '=', request.env.user.id)
            ], limit=1)
            values['appointment_count'] = request.env['doctor.appointment'].sudo().search_count([
                ('patient_id', '=', patient.id),
                ('state', 'not in', ['cancelled', 'no_show']),
            ]) if patient else 0

        # Doctor: count of appointments assigned to them
        if 'doctor_appointment_count' in counters:
            doctor = request.env['doctor.doctor'].sudo().search([
                ('user_id', '=', request.env.user.id)
            ], limit=1)
            values['doctor_appointment_count'] = request.env['doctor.appointment'].sudo().search_count([
                ('doctor_id', '=', doctor.id),
                ('state', 'not in', ['cancelled', 'no_show']),
            ]) if doctor else 0

        return values


class WebsiteDoctorController(http.Controller):

    # =========================================================
    # DOCTOR LISTING PAGE
    # /doctors
    # =========================================================

    @http.route('/doctors', type='http', auth='public', website=True)
    def doctor_list(self, page=1, specialization=None, city=None, search=None, **kwargs):
        """
        Public doctor listing page.
        Shows only approved doctors.
        Supports filtering by specialization, city, and search term.
        """
        DoctorDoctor = request.env['doctor.doctor'].sudo()
        Specialization = request.env['doctor.specialization'].sudo()

        domain = [('state', '=', 'approved'), ('active', '=', True)]

        if specialization:
            domain.append(('specialization_id.id', '=', int(specialization)))
        if city:
            domain.append(('city', 'ilike', city))
        if search:
            domain += ['|', '|',
                       ('name', 'ilike', search),
                       ('specialization_id.name', 'ilike', search),
                       ('city', 'ilike', search)]

        per_page = 12
        offset = (int(page) - 1) * per_page
        total = DoctorDoctor.search_count(domain)
        doctors = DoctorDoctor.search(domain, limit=per_page, offset=offset, order='is_featured desc, rating desc')
        page_count = max(1, -(-total // per_page))
        specializations = Specialization.search([('active', '=', True)], order='sequence, name')

        values = {
            'doctors': doctors,
            'specializations': specializations,
            'selected_specialization': int(specialization) if specialization else None,
            'selected_city': city or '',
            'search': search or '',
            'page': int(page),
            'page_count': page_count,
            'total': total,
        }
        return request.render('doctor_marketplace.website_doctor_list', values)

    # =========================================================
    # DOCTOR DETAIL PAGE
    # /doctors/<int:doctor_id>
    # =========================================================

    @http.route('/doctors/<int:doctor_id>', type='http', auth='public', website=True)
    def doctor_detail(self, doctor_id, **kwargs):
        """
        Public doctor profile page.
        Only approved doctors are accessible.
        """
        doctor = request.env['doctor.doctor'].sudo().search([
            ('id', '=', doctor_id),
            ('state', '=', 'approved'),
            ('active', '=', True),
        ], limit=1)

        if not doctor:
            return request.not_found()

        reviews = request.env['doctor.review'].sudo().search([
            ('doctor_id', '=', doctor.id),
            ('state', '=', 'approved'),
        ], order='create_date desc', limit=10)

        values = {
            'doctor': doctor,
            'reviews': reviews,
        }
        return request.render('doctor_marketplace.website_doctor_detail', values)

    # =========================================================
    # DOCTOR REGISTRATION PAGE
    # /doctor-registration  (GET → form, POST → submit)
    # =========================================================

    @http.route('/doctor-registration', type='http', auth='public', website=True, methods=['GET', 'POST'])
    def doctor_registration(self, **kwargs):
        specializations = request.env['doctor.specialization'].sudo().search(
            [('active', '=', True)], order='sequence, name'
        )
        countries = request.env['res.country'].sudo().search([], order='name')
        if request.httprequest.method == 'POST':
            return self._handle_doctor_registration(kwargs, specializations, countries)
        values = {
            'specializations': specializations,
            'countries': countries,
            'error': {},
            'form_data': {},
        }
        return request.render('doctor_marketplace.website_doctor_registration', values)

    def _handle_doctor_registration(self, post, specializations, countries=None):
        if countries is None:
            countries = request.env['res.country'].sudo().search([], order='name')
        error = {}
        form_data = post

        required_fields = {
            'name': 'Full Name',
            'email': 'Email',
            'mobile': 'Mobile',
            'specialization_id': 'Specialization',
            'registration_number': 'Registration Number',
            'consultation_fee': 'Consultation Fee',
        }
        for field, label in required_fields.items():
            if not post.get(field, '').strip():
                error[field] = _('%s is required.') % label

        if not error.get('email') and post.get('email'):
            existing = request.env['doctor.doctor'].sudo().search(
                [('email', '=', post['email'].strip().lower())], limit=1
            )
            if existing:
                error['email'] = _('A doctor with this email is already registered.')

        if not error.get('consultation_fee'):
            try:
                fee = float(post.get('consultation_fee', 0))
                if fee <= 0:
                    error['consultation_fee'] = _('Consultation fee must be greater than 0.')
            except (ValueError, TypeError):
                error['consultation_fee'] = _('Please enter a valid consultation fee.')

        if error:
            return request.render('doctor_marketplace.website_doctor_registration', {
                'specializations': specializations,
                'countries': countries,
                'error': error,
                'form_data': form_data,
            })

        try:
            partner = request.env['res.partner'].sudo().create({
                'name': post['name'].strip(),
                'email': post['email'].strip().lower(),
                'phone': post.get('mobile', '').strip(),
                'is_company': False,
            })

            doctor_vals = {
                'name': post['name'].strip(),
                'email': post['email'].strip().lower(),
                'mobile': post.get('mobile', '').strip(),
                'phone': post.get('phone', '').strip(),
                'specialization_id': int(post['specialization_id']),
                'registration_number': post.get('registration_number', '').strip(),
                'medical_council': post.get('medical_council', '').strip(),
                'qualification': post.get('qualification', '').strip(),
                'experience_years': int(post.get('experience_years') or 0),
                'consultation_fee': float(post.get('consultation_fee', 0)),
                'clinic_name': post.get('clinic_name', '').strip(),
                'city': post.get('city', '').strip(),
                'bio': post.get('bio', '').strip(),
                'partner_id': partner.id,
                'state': 'pending',
            }

            # --- Compliance: resolve country and store accepted compliance ---
            raw_country = post.get('country_id', '').strip()
            if raw_country:
                try:
                    doctor_vals['country_id'] = int(raw_country)
                except (ValueError, TypeError):
                    pass

            raw_compliance = post.get('compliance_id', '').strip()
            if raw_compliance:
                try:
                    compliance_id = int(raw_compliance)
                    # Verify it exists and is accessible
                    compliance = request.env['country.compliance'].sudo().browse(compliance_id)
                    if compliance.exists():
                        doctor_vals['compliance_id'] = compliance_id
                        doctor_vals['compliance_accepted'] = bool(post.get('compliance_accepted'))
                        if doctor_vals['compliance_accepted']:
                            from odoo import fields as odoo_fields
                            doctor_vals['compliance_accepted_on'] = odoo_fields.Datetime.now()
                except (ValueError, TypeError):
                    pass

            existing_user = request.env['res.users'].sudo().search(
                [('login', '=', doctor_vals['email'])], limit=1
            )
            if existing_user:
                if request.env.ref('base.group_portal') in existing_user.groups_id:
                    existing_user.sudo().write({
                        'group_ids': [(3, request.env.ref('base.group_portal').id)]
                    })
                    existing_user.sudo().write({
                        'group_ids': [(4, request.env.ref('base.group_user').id)]
                    })
                doctor_vals['user_id'] = existing_user.id
            else:
                portal_user = request.env['res.users'].sudo().with_context(
                    no_reset_password=True
                ).create({
                    'name': doctor_vals['name'],
                    'login': doctor_vals['email'],
                    'email': doctor_vals['email'],
                    'partner_id': partner.id,
                    'group_ids': [(6, 0, [request.env.ref('base.group_portal').id])],
                })
                doctor_vals['user_id'] = portal_user.id

            request.env['doctor.doctor'].sudo().create(doctor_vals)
            return request.render('doctor_marketplace.website_doctor_registration_success', {})

        except (ValidationError, UserError) as e:
            return request.render('doctor_marketplace.website_doctor_registration', {
                'specializations': specializations,
                'countries': countries,
                'error': {'general': str(e.args[0]) if e.args else _('An error occurred. Please try again.')},
                'form_data': form_data,
            })
        except Exception as e:
            _logger.exception("Doctor registration failed: %s", str(e))
            return request.render('doctor_marketplace.website_doctor_registration', {
                'specializations': specializations,
                'countries': countries,
                'error': {'general': _('An unexpected error occurred. Please try again.')},
                'form_data': form_data,
            })

    # =========================================================
    # APPOINTMENT BOOKING — STEP 1: Pick a slot
    # /book-appointment/<int:doctor_id>
    # =========================================================

    @http.route('/book-appointment/<int:doctor_id>', type='http', auth='public', website=True)
    def book_appointment(self, doctor_id, **kwargs):
        """
        Booking page — public can view.
        Guest sees "Log in to Book" button.
        Logged-in user sees "Confirm Booking" submit button.
        """
        doctor = request.env['doctor.doctor'].sudo().search([
            ('id', '=', doctor_id),
            ('state', '=', 'approved'),
            ('active', '=', True),
        ], limit=1)

        if not doctor:
            return request.not_found()

        # Check if free signup is enabled
        signup_enabled = False
        try:
            icp = request.env['ir.config_parameter'].sudo()
            signup_enabled = icp.get_param('auth_signup.invitation_scope', 'b2b') == 'b2c'
        except Exception:
            pass

        values = {
            'doctor': doctor,
            'error': {},
            'form_data': {},
            'signup_enabled': signup_enabled,
        }
        return request.render('doctor_marketplace.website_appointment_booking', values)

    # =========================================================
    # APPOINTMENT BOOKING — STEP 2: Confirm (requires login)
    # /book-appointment/<int:doctor_id>/confirm  (POST only)
    # =========================================================

    @http.route(
        '/book-appointment/<int:doctor_id>/confirm',
        type='http', auth='user', website=True, methods=['POST']
    )
    def confirm_appointment(self, doctor_id, **kwargs):
        """
        auth='user' — Odoo redirects unauthenticated requests to /web/login
        automatically. No guest logic needed here.
        After login, user is returned to /book-appointment/<id> to submit again.
        """
        doctor = request.env['doctor.doctor'].sudo().search([
            ('id', '=', doctor_id),
            ('state', '=', 'approved'),
            ('active', '=', True),
        ], limit=1)

        if not doctor:
            return request.not_found()

        post = kwargs
        error = {}

        # --- Validate booking fields ---
        if not post.get('appointment_date'):
            error['appointment_date'] = _('Please select a date.')
        if not post.get('appointment_time'):
            error['appointment_time'] = _('Please select a time slot.')
        if not post.get('consultation_type'):
            error['consultation_type'] = _('Please select consultation type.')

        if error:
            return request.render('doctor_marketplace.website_appointment_booking', {
                'doctor': doctor, 'error': error, 'form_data': post,
                'signup_enabled': False,
            })

        try:
            # Find or auto-create patient record for the logged-in user
            patient = request.env['doctor.patient'].sudo().search([
                ('user_id', '=', request.env.user.id)
            ], limit=1)
            if not patient:
                patient = request.env['doctor.patient'].sudo().create({
                    'name': request.env.user.name,
                    'email': request.env.user.email or request.env.user.login,
                    'mobile': request.env.user.partner_id.phone or '',
                    'partner_id': request.env.user.partner_id.id,
                    'user_id': request.env.user.id,
                })

            appointment_time = float(post.get('appointment_time', 0))
            consultation_type = post.get('consultation_type', 'new')
            fee = (doctor.followup_fee or doctor.consultation_fee
                   if consultation_type == 'followup'
                   else doctor.consultation_fee)

            appointment = request.env['doctor.appointment'].sudo().create({
                'doctor_id': doctor.id,
                'patient_id': patient.id,
                'appointment_date': post['appointment_date'],
                'appointment_time': appointment_time,
                'consultation_type': consultation_type,
                'consultation_mode': post.get('consultation_mode', 'in_person'),
                'reason': post.get('reason', '').strip() if post.get('reason') else '',
                'symptoms': post.get('symptoms', '').strip() if post.get('symptoms') else '',
                'consultation_fee': fee,
                'state': 'draft',
            })

            return request.render('doctor_marketplace.website_appointment_success', {
                'appointment': appointment, 'doctor': doctor,
            })

        except Exception as e:
            _logger.exception("Appointment booking failed: %s", str(e))
            return request.render('doctor_marketplace.website_appointment_booking', {
                'doctor': doctor,
                'error': {'general': _('Booking failed. Please try again.')},
                'form_data': post,
                'signup_enabled': False,
            })

    # =========================================================
    # AJAX — Get available time slots for a doctor on a date
    # /book-appointment/slots  (POST, JSON)
    # =========================================================

    @http.route(
        '/book-appointment/slots',
        type='jsonrpc', auth='public', website=True, methods=['POST']
    )
    def get_available_slots(self, doctor_id, appointment_date, **kwargs):
        """
        Returns available time slots for a doctor on a given date.
        Used by the booking form via AJAX to dynamically populate time options.
        """
        from datetime import datetime

        try:
            doctor = request.env['doctor.doctor'].sudo().browse(int(doctor_id))
            if not doctor.exists() or doctor.state != 'approved':
                return {'slots': []}

            appt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            day_of_week = str(appt_date.weekday())

            schedule = request.env['doctor.schedule'].sudo().search([
                ('doctor_id', '=', doctor.id),
                ('day_of_week', '=', day_of_week),
                ('is_available', '=', True),
            ], limit=1)

            if not schedule:
                return {'slots': []}

            booked_times = request.env['doctor.appointment'].sudo().search([
                ('doctor_id', '=', doctor.id),
                ('appointment_date', '=', appointment_date),
                ('state', 'not in', ['cancelled', 'no_show']),
            ]).mapped('appointment_time')

            duration_h = (doctor.consultation_duration or 15) / 60.0
            buffer_h = (doctor.buffer_time or 0) / 60.0
            step = duration_h + buffer_h

            slots = []
            current = schedule.time_from
            while current + duration_h <= schedule.time_to:
                if current not in booked_times:
                    hours = int(current)
                    minutes = int(round((current - hours) * 60))
                    period = 'AM' if hours < 12 else 'PM'
                    disp_h = hours if hours <= 12 else hours - 12
                    if disp_h == 0:
                        disp_h = 12
                    label = '%02d:%02d %s' % (disp_h, minutes, period)
                    slots.append({'value': current, 'label': label})
                current = round(current + step, 4)

            return {'slots': slots}

        except Exception as e:
            _logger.exception("Slot fetch failed: %s", str(e))
            return {'slots': [], 'error': str(e)}

    # =========================================================
    # PATIENT PORTAL — My Appointments
    # /my/appointments
    # =========================================================

    @http.route('/my/appointments', type='http', auth='user', website=True)
    def portal_my_appointments(self, **kwargs):
        """
        Portal page for logged-in patients to view their appointments.
        """
        patient = request.env['doctor.patient'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)

        appointments = request.env['doctor.appointment'].sudo().search(
            [('patient_id', '=', patient.id)] if patient else [('id', '=', False)],
            order='appointment_date desc, appointment_time desc'
        )

        values = {
            'appointments': appointments,
            'patient': patient,
        }
        return request.render('doctor_marketplace.portal_my_appointments', values)

    # =========================================================
    # DOCTOR PORTAL — My Appointments (as Doctor)
    # /my/doctor-appointments
    # =========================================================

    @http.route('/my/doctor-appointments', type='http', auth='user', website=True)
    def portal_doctor_appointments(self, **kwargs):
        """
        Portal page for logged-in doctors to view their patient appointments.
        Redirects to /my/home if the current user is not linked to a doctor record.
        """
        doctor = request.env['doctor.doctor'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)

        if not doctor:
            return request.redirect('/my/home')

        appointments = request.env['doctor.appointment'].sudo().search([
            ('doctor_id', '=', doctor.id),
        ], order='appointment_date desc, appointment_time desc')

        values = {
            'doctor': doctor,
            'appointments': appointments,
            'page_name': 'doctor_appointments',
        }
        return request.render('doctor_marketplace.portal_doctor_appointments', values)
