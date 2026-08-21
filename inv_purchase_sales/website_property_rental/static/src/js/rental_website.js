/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsitePropertyRental = publicWidget.Widget.extend({
    selector: ".wr-wrap",
    events: {
        "click .wr-thumbs img, .kad-thumbs img": "_onThumbClick",
    },
    _onThumbClick(ev) {
        const main = this.el.querySelector(".wr-gallery-main, .kad-gallery-main");
        if (main && ev.currentTarget.src) {
            main.src = ev.currentTarget.src;
        }
    },
});
