/** @odoo-module **/
/**
 * compliance_registration.js
 *
 * Runs on the public doctor registration form.
 * When the doctor selects a country, fetches the matching compliance record
 * via /get-country-compliance and shows/hides the compliance section.
 *
 * No backend dependency — works with auth='public'.
 */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ComplianceRegistration = publicWidget.Widget.extend({
    selector: 'form[action="/doctor-registration"]',

    events: {
        'change select[name="country_id"]': '_onCountryChange',
    },

    async start() {
        await this._super(...arguments);
        // If the form was re-rendered with a pre-selected country (POST error),
        // fetch compliance immediately so the section is visible.
        const countrySelect = this.el.querySelector('select[name="country_id"]');
        if (countrySelect && countrySelect.value) {
            await this._fetchCompliance(countrySelect.value);
        }
    },

    async _onCountryChange(ev) {
        await this._fetchCompliance(ev.currentTarget.value || null);
    },

    async _fetchCompliance(countryId) {
        const section     = document.getElementById('compliance_section');
        const descEl      = document.getElementById('compliance_description');
        const idInput     = document.getElementById('compliance_id');
        const checkbox    = document.getElementById('compliance_accepted');

        if (!section || !descEl || !idInput) return;

        // Reset state before fetch
        if (checkbox) {
            checkbox.checked = false;
            checkbox.removeAttribute('required');
        }

        if (!countryId) {
            section.style.display = 'none';
            descEl.innerHTML = '';
            idInput.value = '';
            return;
        }

        try {
            const response = await fetch('/get-country-compliance', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method:  'call',
                    params:  { country_id: parseInt(countryId) },
                }),
            });
            const { result } = await response.json();

            if (result && result.has_compliance) {
                descEl.innerHTML   = result.description || '';
                idInput.value      = result.compliance_id || '';
                section.style.display = '';
                if (checkbox) checkbox.setAttribute('required', 'required');
            } else {
                section.style.display = 'none';
                descEl.innerHTML   = '';
                idInput.value      = '';
            }
        } catch (err) {
            console.error('Compliance fetch error:', err);
            section.style.display = 'none';
        }
    },
});
