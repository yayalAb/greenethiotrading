/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

function getScrollRoot() {
    return document.getElementById("wrapwrap") || document.scrollingElement || document.documentElement;
}

function getHashId(href) {
    if (!href) {
        return "";
    }
    const hashIndex = href.indexOf("#");
    if (hashIndex === -1) {
        return "";
    }
    return href.slice(hashIndex);
}

function scrollToTarget(target, headerOffset = 88) {
    if (!target) {
        return;
    }
    const wrap = document.getElementById("wrapwrap");
    const wrapScrolls = wrap && wrap.scrollHeight > wrap.clientHeight + 2;
    const rect = target.getBoundingClientRect();
    if (wrapScrolls) {
        const top = wrap.scrollTop + rect.top - wrap.getBoundingClientRect().top - headerOffset;
        wrap.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
        return;
    }
    const top = rect.top + (window.pageYOffset || document.documentElement.scrollTop || 0) - headerOffset;
    window.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
}

function animateCount(el, delay = 0) {
    const target = Number(el.dataset.getCount || 0);
    const suffix = el.dataset.getSuffix || "";
    const valueEl = el.querySelector(".get-stat__value");
    if (!valueEl || Number.isNaN(target) || el.dataset.getCounted === "1") {
        return;
    }
    el.dataset.getCounted = "1";
    valueEl.textContent = `0${suffix}`;

    const finish = (value) => {
        valueEl.textContent = `${value}${suffix}`;
        el.classList.remove("is-counting");
        el.classList.add("is-counted");
    };

    const run = () => {
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            finish(target);
            return;
        }

        el.classList.add("is-counting");

        // Pace so each integer is readable: 1, 2, 3 â€¦ then settle on the total
        const msPerStep = target <= 40 ? 60 : target <= 150 ? 22 : 8;
        const duration = Math.min(3200, Math.max(1800, target * msPerStep));
        const start = performance.now();
        let lastShown = -1;

        const tick = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            // Near-linear so early steps (1,2,3â€¦) stay visible
            const eased = progress < 1 ? Math.pow(progress, 0.92) : 1;
            const current = Math.round(target * eased);
            if (current !== lastShown) {
                lastShown = current;
                valueEl.textContent = `${current}${suffix}`;
            }
            if (progress < 1) {
                requestAnimationFrame(tick);
            } else {
                finish(target);
            }
        };
        requestAnimationFrame(tick);
    };

    if (delay > 0) {
        window.setTimeout(run, delay);
    } else {
        run();
    }
}

function animateStatsIn(root) {
    const stats = root.classList.contains("get-stat")
        ? [root]
        : [...root.querySelectorAll(".get-stat[data-get-count]")];
    stats.forEach((stat, index) => animateCount(stat, index * 160));
}

publicWidget.registry.GetWebsite = publicWidget.Widget.extend({
    selector: ".get-site",
    events: {
        "click a[href*='#']": "_onAnchorClick",
    },

    start() {
        this.el.classList.add("get-js-ready");
        this._setupReveals();
        this._bindGlobalAnchors();
        this._bindScrollChrome();
        return this._super(...arguments);
    },

    destroy() {
        if (this._globalClickHandler) {
            document.removeEventListener("click", this._globalClickHandler, true);
        }
        if (this._scrollHandler) {
            const root = getScrollRoot();
            root.removeEventListener("scroll", this._scrollHandler);
            window.removeEventListener("scroll", this._scrollHandler);
        }
        return this._super(...arguments);
    },

    _bindGlobalAnchors() {
        this._globalClickHandler = (event) => {
            const anchor = event.target.closest("a[href*='#']");
            if (!anchor || !document.querySelector(".get-site")) {
                return;
            }
            this._scrollFromAnchor(event, anchor);
        };
        document.addEventListener("click", this._globalClickHandler, true);
    },

    _onAnchorClick(event) {
        this._scrollFromAnchor(event, event.currentTarget);
    },

    _scrollFromAnchor(event, anchor) {
        const id = getHashId(anchor.getAttribute("href"));
        if (!id || id === "#") {
            return;
        }
        const target = document.getElementById(id.slice(1)) || document.querySelector(id);
        if (!target) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        if (anchor.classList.contains("get-pcard__cta")) {
            const title = anchor.closest(".get-pcard") && anchor.closest(".get-pcard").querySelector("h3");
            const input = document.getElementById("get_q_product");
            if (title && input) {
                input.value = title.textContent.trim();
            }
        }
        scrollToTarget(target);
        if (history.replaceState) {
            history.replaceState(null, "", id);
        }
    },

    _bindScrollChrome() {
        const root = getScrollRoot();
        const wrap = document.getElementById("wrapwrap");
        this._scrollHandler = () => {
            const y = root.scrollTop || window.pageYOffset || 0;
            if (wrap) {
                wrap.classList.toggle("get-scrolled", y > 24);
            }
            document.body.classList.toggle("get-scrolled", y > 24);
        };
        root.addEventListener("scroll", this._scrollHandler, { passive: true });
        window.addEventListener("scroll", this._scrollHandler, { passive: true });
        this._scrollHandler();
    },

    _setupReveals() {
        const nodes = this.el.querySelectorAll("[data-get-anim]");
        nodes.forEach((node) => {
            const delay = Number(node.dataset.getDelay || 0);
            if (delay) {
                node.style.setProperty("--get-delay", `${delay}ms`);
            }
        });

        const revealNow = (node) => {
            if (node.classList.contains("is-visible") && node.dataset.getRevealed === "1") {
                return;
            }
            node.dataset.getRevealed = "1";
            node.classList.add("is-visible");
            if (node.classList.contains("get-stats") || node.querySelector(".get-stat[data-get-count]")) {
                animateStatsIn(node);
            }

            // Unlock per-word hover after staggered entrance finishes
            const words = node.querySelectorAll(".get-word, .get-amp");
            if (words.length) {
                const maxDelay = 180 + (words.length - 1) * 120 + 800;
                window.setTimeout(() => {
                    words.forEach((word) => word.classList.add("is-live"));
                }, maxDelay);
            }
        };

        if (!("IntersectionObserver" in window)) {
            nodes.forEach(revealNow);
            return;
        }

        const scrollRoot = getScrollRoot();
        const observerRoot =
            scrollRoot && scrollRoot !== document.documentElement && scrollRoot !== document.body
                ? scrollRoot
                : null;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) {
                        return;
                    }
                    revealNow(entry.target);
                    observer.unobserve(entry.target);
                });
            },
            { root: observerRoot, threshold: 0.2, rootMargin: "0px 0px -10% 0px" }
        );

        nodes.forEach((node) => observer.observe(node));

        requestAnimationFrame(() => {
            const viewH = observerRoot ? observerRoot.clientHeight : window.innerHeight;
            nodes.forEach((node) => {
                const rect = node.getBoundingClientRect();
                if (rect.top < viewH * 0.88 && rect.bottom > 0) {
                    revealNow(node);
                    observer.unobserve(node);
                }
            });
        });
    },
});

