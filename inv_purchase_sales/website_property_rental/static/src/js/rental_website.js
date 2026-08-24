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

publicWidget.registry.WebsitePropertyHero = publicWidget.Widget.extend({
    selector: ".kad-hero__slides",
    start() {
        this._photos = [...this.el.querySelectorAll(".kad-hero__photo")];
        if (this._photos.length > 1) {
            this._index = this._photos.findIndex((photo) => photo.classList.contains("is-active"));
            if (this._index < 0) {
                this._index = 0;
            }
            this._timer = window.setInterval(() => this._next(), 6000);
        }
        return this._super(...arguments);
    },
    destroy() {
        if (this._timer) {
            window.clearInterval(this._timer);
        }
        return this._super(...arguments);
    },
    _next() {
        this._photos[this._index].classList.remove("is-active");
        this._index = (this._index + 1) % this._photos.length;
        this._photos[this._index].classList.add("is-active");
    },
});
