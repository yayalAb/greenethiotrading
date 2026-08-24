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
        "plaza-night-banner.png",
        "plaza-night.png",
        "towers-day.png",
        "street-white.png",
        "gold-glass.png",
        "gold-tower.png",
    ]

    def _fallback_image(self, property_rec):
        name = self.FALLBACKS[property_rec.id % len(self.FALLBACKS)]
        return "%s/%s" % (self.IMG, name)

    def _property_image(self, property_rec):
        if property_rec.image:
            return "/web/image/property.property/%s/image" % property_rec.id
        return self._fallback_image(property_rec)

    def _listing_domain(self, listing_type=None, kind=None, city=None):
        listing_type = (listing_type or "rent").strip().lower()
        sale_rent = "for_sale" if listing_type == "sale" else "for_tenancy"
        domain = [
            ("state", "=", "available"),
            ("sale_rent", "=", sale_rent),
        ]
        kind = (kind or "").strip().lower()
        if kind in ("rent", "sale"):
            kind = ""
        if kind in ("office", "offices"):
            domain += [
                "|",
                "|",
                ("name", "ilike", "office"),
                ("usage", "ilike", "office"),
                ("location", "ilike", "office"),
            ]
        elif kind in ("shop", "shops"):
            domain += [
                "|",
                "|",
                "|",
                ("shop_name", "!=", False),
                ("name", "ilike", "shop"),
                ("usage", "ilike", "shop"),
                ("location", "ilike", "shop"),
            ]
        city = (city or "").strip()
        if city:
            domain += [
                "|",
                "|",
                ("city", "ilike", city),
                ("location", "ilike", city),
                ("street", "ilike", city),
            ]
        return domain

    def _listing_title(self, listing_type=None, kind=None, city=None):
        listing_type = (listing_type or "rent").strip().lower()
        kind = (kind or "").strip().lower()
        if listing_type == "sale":
            if kind in ("office", "offices"):
                return "Offices for sale"
            if kind in ("shop", "shops"):
                return "Shops for sale"
            if city:
                return "For Sale in %s" % city
            return "Units in our building for sale."
        if kind in ("office", "offices"):
            return "Offices for rent"
        if kind in ("shop", "shops"):
            return "Shops for rent"
        if city:
            return "For Rent in %s" % city
        return "Units in our building for rent."

    def _public_property(self, property_id):
        property_rec = request.env["property.property"].sudo().browse(property_id)
        if not property_rec.exists() or property_rec.sale_rent not in (
            "for_tenancy",
            "for_sale",
        ):
            return None
        return property_rec

    @http.route("/property", auth="public", website=True)
    def property(self, **kwargs):
        if kwargs.get("type") == "sale":
            return request.redirect("/#for-sale")
        listing_type = "sale" if kwargs.get("type") == "sale" else "rent"
        kind = kwargs.get("kind")
        city = kwargs.get("city")
        if (kind or "").strip().lower() in ("rent", "sale"):
            kind = None
        properties = (
            request.env["property.property"]
            .sudo()
            .search(
                self._listing_domain(listing_type=listing_type, kind=kind, city=city),
                order="id desc",
            )
        )
        return request.render(
            "website_property_rental.property_listing",
            {
                "properties": properties,
                "property_images": {
                    prop.id: self._property_image(prop) for prop in properties
                },
                "listing_type": listing_type,
                "listing_kind": kind or "",
                "listing_city": city or "",
                "listing_title": self._listing_title(
                    listing_type=listing_type, kind=kind, city=city
                ),
                "hero_image": "%s/plaza-night-banner.png" % self.IMG,
            },
        )

    @http.route("/property/<int:property_id>", auth="public", website=True)
    def property_item(self, property_id, **kwargs):
        property_rec = self._public_property(property_id)
        if not property_rec:
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
        property_rec = self._public_property(property_id)
        if not property_rec:
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
                ("Unit / floor", area),
                ("Message", message or "N/A"),
            ]
            chunks = [
                "<p><strong>%s:</strong> %s</p>" % (escape(label), escape(value))
                for label, value in rows
                if value
            ]
            email_to = request.env.company.email or "info@temesgenkefyalew.com"
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
