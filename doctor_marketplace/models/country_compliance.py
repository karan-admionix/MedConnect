# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)


class CountryCompliance(models.Model):
    _name = "country.compliance"
    _description = "Country Compliance"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    country_id = fields.Many2one("res.country", string="Country", tracking=True)
    description = fields.Html(string="Description", required=True)

    # Odoo 19: use models.Constraint instead of _sql_constraints
    # Uniqueness enforced via @api.constrains below (no unique DB index needed
    # since global/null-country rows are allowed and SQL UNIQUE can't handle
    # multiple NULLs correctly across all DBs)
    @api.constrains("country_id")
    def _check_unique_country(self):
        for record in self:
            domain = [("id", "!=", record.id)]
            domain.append(
                (
                    "country_id",
                    "=",
                    record.country_id.id if record.country_id else False,
                )
            )
            if self.search_count(domain) > 0:
                raise ValidationError(
                    "A compliance record already exists for this country."
                )

    def unlink(self):
        for record in self:
            doc = self.env["doctor.doctor"].search(
                [("compliance_id", "=", record.id)], limit=1
            )
            if doc:
                raise ValidationError(
                    f"Cannot delete '{record.name}' "
                    f"— assigned to doctor '{doc.name}'."
                )
        return super().unlink()

    def write(self, vals):
        """
        When compliance description changes:
          - Reset compliance_accepted = False on all linked doctors who had accepted.
          - Post chatter note on compliance and on each affected doctor.doctor record.
        """
        description_changing = "description" in vals

        old_texts = {}
        if description_changing:
            for record in self:
                old_texts[record.id] = html2plaintext(record.description or "").strip()

        result = super().write(vals)

        for record in self:
            if description_changing:
                new_text = html2plaintext(vals["description"] or "").strip()
                if old_texts.get(record.id) == new_text:
                    continue  # no real change

                record.message_post(
                    body=Markup(
                        "📝 <b>Description updated</b> for country: <b>{country}</b>"
                    ).format(country=record.country_id.name or "Global"),
                    subtype_xmlid="mail.mt_note",
                )

                # Reset only doctors who had accepted
                doctors = (
                    self.env["doctor.doctor"]
                    .sudo()
                    .search(
                        [
                            ("compliance_accepted", "=", True),
                            "|",
                            ("compliance_id", "=", record.id),
                            ("country_id", "=", record.country_id.id),
                        ]
                    )
                )
                if doctors:
                    doctors.write({"compliance_accepted": False})
                    for doctor in doctors:
                        doctor.message_post(
                            body=Markup(
                                "⚠️ <b>Compliance Updated</b>: "
                                "Country compliance for <b>{country}</b> "
                                "has changed. Re-acceptance required."
                            ).format(country=record.country_id.name or "Global"),
                            subtype_xmlid="mail.mt_note",
                        )

                _logger.info(
                    "country.compliance %s: description changed, reset %d doctor(s).",
                    record.id,
                    len(doctors),
                )

        return result
