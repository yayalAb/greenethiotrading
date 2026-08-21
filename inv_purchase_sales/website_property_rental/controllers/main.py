# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from markupsafe import escape, Markup

from odoo.addons.advanced_property_management.controllers.advanced_property_management import (
    PropertyController,
)


class WebsitePropertyRental(PropertyController):
    IMG = "/website_property_rental/static/src/img"
    FALLBACKS = [
        "podium.jpg",
        "street-day.jpg",
        "lobby.jpg",
        "facade.jpg",
        "aerial.jpg",
        "night.jpg",
        "corner.jpg",
        "retail.jpg",
    ]

    def _fallback_image(self, property_rec):
        name = self.FALLBACKS[property_rec.id % len(self.FALLBACKS)]
        return "%s/%s" % (self.IMG, name)

    def _property_image(self, property_rec):
        if property_rec.image:
            return "/web/image/property.property/%s/image" % property_rec.id
        return self._fallback_image(property_rec)

    def _listing_domain(self, listing_type):
        domain = [("state", "=", "available")]
        if listing_type == "sale":
            domain.append(("sale_rent", "=", "for_sale"))
        else:
            domain.append(("sale_rent", "=", "for_tenancy"))
        return domain

    @http.route("/property", auth="public", website=True)
    def property(self, **kwargs):
        listing_type = "sale" if kwargs.get("type") == "sale" else "rent"
        properties = (
            request.env["property.property"]
            .sudo()
            .search(self._listing_domain(listing_type), order="id desc")
        )
        return request.render(
            "website_property_rental.property_listing",
            {
                "properties": properties,
                "property_images": {
                    prop.id: self._property_image(prop) for prop in properties
                },
                "listing_type": listing_type,
                "hero_image": "%s/%s"
                % (self.IMG, "street-day.jpg" if listing_type == "sale" else "hero.jpg"),
            },
        )

    @http.route("/property/<int:property_id>", auth="public", website=True)
    def property_item(self, property_id, **kwargs):
        property_rec = request.env["property.property"].sudo().browse(property_id)
        if not property_rec.exists():
            return request.not_found()
        gallery = []
        if property_rec.image:
            gallery.append("/web/image/property.property/%s/image" % property_rec.id)
        gallery.extend(
            "/web/image/property.image/%s/image" % img.id
            for img in property_rec.property_image_ids
        )
        if not gallery:
            gallery = ["%s/%s" % (self.IMG, name) for name in self.FALLBACKS[:6]]
        return request.render(
            "website_property_rental.property_detail",
            {
                "property_id": property_rec,
                "gallery": gallery,
                "success": kwargs.get("success"),
                "error": kwargs.get("error"),
            },
        )

    @http.route(
        ["/rentals", "/rentals/page/<int:page>", "/rentals/<int:property_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def rentals_redirect(self, property_id=None, **kwargs):
        if property_id:
            return request.redirect("/property/%s" % property_id)
        return request.redirect("/property?type=rent")

    @http.route(
        "/property/<int:property_id>/enquire",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def rental_enquire(self, property_id, **post):
        property_rec = request.env["property.property"].sudo().browse(property_id)
        if not property_rec.exists():
            return request.not_found()
        name = (post.get("partner_name") or "").strip()
        email = (post.get("partner_email") or "").strip()
        if not name or not email:
            return request.redirect("/property/%s?error=missing" % property_id)
        request.env["property.rental.request"].sudo().create(
            {
                "property_id": property_rec.id,
                "partner_name": name,
                "partner_email": email,
                "partner_phone": post.get("partner_phone"),
                "start_date": post.get("start_date") or False,
                "duration_months": int(post.get("duration_months") or 12),
                "message": post.get("message"),
            }
        )
        return request.redirect("/property/%s?success=1" % property_id)

    @http.route(
        "/get/contact",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def website_contact(self, **post):
        name = (post.get("name") or "").strip()
        email = (post.get("email") or "").strip()
        phone = (post.get("phone") or "").strip()
        message = (post.get("message") or "").strip()
        form_type = (post.get("form_type") or "contact").strip()
        interest = (post.get("product") or "").strip()
        area = (post.get("quantity") or "").strip()
        if name and email:
            rows = [
                ("Form", "Enquiry" if form_type == "enquire" else "Contact"),
                ("Name", name),
                ("Email", email),
                ("Phone", phone or "N/A"),
                ("Interest", interest),
                ("City / area", area),
                ("Message", message or "N/A"),
            ]
            chunks = [
                "<p><strong>%s:</strong> %s</p>" % (escape(label), escape(value))
                for label, value in rows
                if value
            ]
            email_to = request.env.company.email or "info@greenethiotrading.com"
            request.env["mail.mail"].sudo().create(
                {
                    "subject": "Website %s — %s"
                    % ("enquiry" if form_type == "enquire" else "contact", name),
                    "email_from": request.env.company.email_formatted or email_to,
                    "reply_to": email,
                    "email_to": email_to,
                    "body_html": Markup("".join(chunks)),
                }
            ).send()
        return request.render("website_property_rental.contact_thanks")
