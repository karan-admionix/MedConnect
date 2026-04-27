# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request


class CountryComplianceController(http.Controller):
    """
    Compliance routes for the doctor portal.

    /get-country-compliance         — returns compliance HTML for a given country
                                      (used on doctor registration/profile pages)
    /check-compliance-accepted      — called on every portal page load for logged-in
                                      doctors; returns popup data when re-acceptance
                                      is required
    /accept-regenerated-compliance  — called when doctor clicks Accept on the popup
    """

    # ------------------------------------------------------------------
    # Public: fetch compliance description for a country
    # ------------------------------------------------------------------

    @http.route(
        "/get-country-compliance",
        type="json",
        auth="public",
        csrf=False,
    )
    def get_country_compliance(self, country_id=None, **kw):
        """
        Return compliance for the given country.
        Falls back to the global default (no country) if no match found.
        """
        Compliance = request.env["country.compliance"].sudo()

        compliance = (
            Compliance.search(
                [("country_id", "=", int(country_id))], limit=1
            )
            if country_id
            else Compliance.browse()
        )

        if not compliance:
            compliance = Compliance.search(
                [("country_id", "=", False)], limit=1
            )

        if compliance:
            return {
                "compliance_id": compliance.id,
                "description": compliance.description or "",
                "has_compliance": True,
            }
        return {
            "compliance_id": False,
            "description": "",
            "has_compliance": False,
        }

    # ------------------------------------------------------------------
    # Authenticated: compliance popup check on portal load
    # ------------------------------------------------------------------

    @http.route(
        "/check-compliance-accepted",
        type="json",
        auth="user",
        csrf=False,
    )
    def check_compliance_accepted(self, **kw):
        """
        Called on every portal page load for logged-in doctors.

        Returns:
          regenerated  : True when the popup must be shown
          old_country  : previous country name (only when country change triggered this)
          new_country  : current country name  (only when country change triggered this)
          description  : compliance HTML (always included when regenerated=True)

        Popup display rules:
          old_country + new_country present → show country-change banner + description
          old_country absent               → show description-updated banner only
        """
        user = request.env.user
        # Find the doctor.doctor record linked to this user
        doctor = (
            request.env["doctor.doctor"]
            .sudo()
            .search([("user_id", "=", user.id)], limit=1)
        )

        if not doctor or doctor.compliance_accepted:
            return {"regenerated": False}

        # No compliance assigned yet — nothing to show, skip popup
        if not doctor.compliance_id:
            return {"regenerated": False}

        old_country = None
        new_country = None

        if doctor.country_change_old_name:
            old_country = doctor.country_change_old_name
            new_country = doctor.country_id.name or "N/A"

        return {
            "regenerated": True,
            "old_country": old_country,
            "new_country": new_country,
            "description": doctor.compliance_id.description or "",
        }

    # ------------------------------------------------------------------
    # Authenticated: accept compliance popup
    # ------------------------------------------------------------------

    @http.route(
        "/accept-regenerated-compliance",
        type="json",
        auth="user",
        website=True,
    )
    def accept_regenerated_compliance(self, **kw):
        """
        Called when the doctor clicks Accept on the compliance popup.
        Sets compliance_accepted = True and clears the country-change flag.
        """
        user = request.env.user
        doctor = (
            request.env["doctor.doctor"]
            .sudo()
            .search([("user_id", "=", user.id)], limit=1)
        )

        if not doctor:
            return {"success": False}

        doctor.write(
            {
                "compliance_accepted": True,
                "compliance_accepted_on": fields.Datetime.now(),
                "country_change_old_name": False,
            }
        )

        return {"success": True}
