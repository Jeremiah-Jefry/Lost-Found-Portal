/* ─────────────────────────────────────────────────────────────────────────
   KG Community Recovery Portal — main.js
   Global client-side utilities loaded on every page via base.html.

   Sections:
     1. Mobile sidebar  — openMobile / closeMobile
     2. Animated counter — countUp / initCounters  (data-count="N")
     3. Handover toggle  — initHandoverToggle()
        Wires the Handover & Security sections on report.html and edit.html.
        Both pages share the same element IDs so this runs harmlessly on
        all other pages (guard: returns early when elements are absent).
     4. DOMContentLoaded bootstrap — initialises all of the above +
        auto-dismisses flash messages after 6 s.
───────────────────────────────────────────────────────────────────────── */

'use strict';


/* ── 1. Mobile sidebar ───────────────────────────────────────────────────── */

function openMobile() {
    document.getElementById('mobile-overlay').classList.remove('hidden');
    document.getElementById('mobile-sidebar').classList.remove('-translate-x-full');
}

function closeMobile() {
    document.getElementById('mobile-overlay').classList.add('hidden');
    document.getElementById('mobile-sidebar').classList.add('-translate-x-full');
}


/* ── 2. Animated counter ─────────────────────────────────────────────────── */

/**
 * countUp(el, target, duration)
 * Animates a numeric text node from 0 to `target` with an ease-out cubic curve.
 * Reads initial value from data-count attribute; call initCounters() to batch.
 */
function countUp(el, target, duration) {
    duration = duration || 900;
    var start     = performance.now();
    var formatted = target.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');

    function step(now) {
        var elapsed  = now - start;
        var progress = Math.min(elapsed / duration, 1);
        var eased    = 1 - Math.pow(1 - progress, 3);   /* ease-out cubic */
        el.textContent = Math.floor(eased * target)
                           .toString()
                           .replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            el.textContent = formatted;
        }
    }
    requestAnimationFrame(step);
}

function initCounters() {
    document.querySelectorAll('[data-count]').forEach(function (el) {
        countUp(el, parseInt(el.dataset.count, 10));
    });
}


/* ── 3. Handover / Security toggle ──────────────────────────────────────── */

/**
 * initHandoverToggle()
 *
 * Wires the following show/hide behaviour on report.html and edit.html:
 *   • #handover-section  — visible only when Report Type = FOUND
 *   • #security-fields   — visible only when Custody  = SECURITY
 *
 * Uses the .slide-section / .open CSS classes defined in style.css so the
 * reveal is animated.  Returns immediately on pages that lack these elements.
 */
function initHandoverToggle() {
    var statusEl  = document.getElementById('status');
    var hdSection = document.getElementById('handover-section');
    var hdSelect  = document.getElementById('handover_status');
    var secFields = document.getElementById('security-fields');

    /* Not on a form page — nothing to do */
    if (!statusEl || !hdSection) { return; }

    function toggleHandover() {
        var isFound = statusEl.value === 'FOUND';
        hdSection.classList.toggle('open', isFound);
        if (!isFound && hdSelect) {
            hdSelect.value = '';
            if (secFields) { secFields.classList.remove('open'); }
        }
    }

    function toggleSecurity() {
        if (!hdSelect || !secFields) { return; }
        secFields.classList.toggle('open', hdSelect.value === 'SECURITY');
    }

    statusEl.addEventListener('change', toggleHandover);
    if (hdSelect) { hdSelect.addEventListener('change', toggleSecurity); }

    /* Reflect pre-selected values (e.g. server-side re-render on validation error) */
    toggleHandover();
    toggleSecurity();
}


/* ── 4. DOMContentLoaded bootstrap ──────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {

    /* Animated stat counters */
    initCounters();

    /* Handover form logic */
    initHandoverToggle();

    /* Auto-dismiss flash messages after 6 s with staggered fade-out */
    var flashContainer = document.getElementById('flash-container');
    if (flashContainer) {
        setTimeout(function () {
            Array.from(flashContainer.children).forEach(function (el, i) {
                setTimeout(function () {
                    el.style.transition = 'opacity .4s ease, transform .4s ease';
                    el.style.opacity    = '0';
                    el.style.transform  = 'translateY(-6px)';
                    setTimeout(function () { el.remove(); }, 420);
                }, i * 120);
            });
        }, 6000);
    }
});
