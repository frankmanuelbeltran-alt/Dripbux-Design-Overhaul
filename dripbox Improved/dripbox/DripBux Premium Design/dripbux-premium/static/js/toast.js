/**
 * toast.js — DripBux Premium Toast Notification System
 *
 * Provides a global `DripBuxToast` API for popup notifications.
 * Adapted from ArmsDealer with pink luxury theme.
 *
 * USAGE:
 *   DripBuxToast.show('Message here', 'success');
 *   DripBuxToast.show('Message here', 'error');
 *   DripBuxToast.show('Message here', 'warning');
 *   DripBuxToast.show('Message here', 'info');
 */

(function () {
    'use strict';

    /* ── Config ──────────────────────────────────────────────────── */
    const DURATION_MS = 4500;
    const ANIM_DELAY_MS = 40;

    /* ── Lucide icon map ─────────────────────────────────────────── */
    const ICONS = {
        success: 'check-circle',
        error: 'alert-circle',
        warning: 'alert-triangle',
        info: 'info',
    };

    /* ── Label map ───────────────────────────────────────────────── */
    const LABELS = {
        success: 'SUCCESS',
        error: 'ERROR',
        warning: 'WARNING',
        info: 'INFO',
    };

    /* ── Container (created once, lazily) ───────────────────────── */
    let container = null;

    function getContainer() {
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    /* ── Core show function ──────────────────────────────────────── */
    function show(message, type, durationMs) {
        const variant = ['success', 'error', 'warning', 'info'].includes(type) ? type : 'info';
        const duration = typeof durationMs === 'number' ? durationMs : DURATION_MS;

        const toast = document.createElement('div');
        toast.className = `toast toast--${variant}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');

        toast.innerHTML = `
            <div class="toast__icon"><i data-lucide="${ICONS[variant]}"></i></div>
            <div class="toast__label">${LABELS[variant]}</div>
            <div class="toast__message">${escapeHtml(message)}</div>
            <button class="toast__close" aria-label="Dismiss"><i data-lucide="x"></i></button>
            <div class="toast__progress" style="animation-duration:${duration}ms"></div>
        `;

        getContainer().appendChild(toast);

        // Initialize Lucide icons inside the toast
        if (typeof lucide !== 'undefined') {
            lucide.createIcons({ nodes: [toast] });
        }

        // Trigger enter animation on next frame
        requestAnimationFrame(() => {
            setTimeout(() => toast.classList.add('toast--visible'), ANIM_DELAY_MS);
        });

        // Auto-dismiss
        const timer = setTimeout(() => dismiss(toast), duration);

        // Manual dismiss
        toast.querySelector('.toast__close').addEventListener('click', () => {
            clearTimeout(timer);
            dismiss(toast);
        });

        // Pause on hover
        toast.addEventListener('mouseenter', () => {
            const progress = toast.querySelector('.toast__progress');
            if (progress) progress.style.animationPlayState = 'paused';
        });
        toast.addEventListener('mouseleave', () => {
            const progress = toast.querySelector('.toast__progress');
            if (progress) progress.style.animationPlayState = 'running';
        });
    }

    function dismiss(toast) {
        toast.classList.remove('toast--visible');
        toast.classList.add('toast--hiding');
        toast.addEventListener('transitionend', () => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, { once: true });
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    /* ── Auto-init from Flask flash messages ───────────────────── */
    function initFromDOM() {
        document.querySelectorAll('[data-toast]').forEach(function (el) {
            const type = el.dataset.type || 'info';
            const message = el.dataset.message || '';
            if (message) show(message, type);
            if (el.parentNode) el.parentNode.removeChild(el);
        });
    }

    /* ── Expose global API ───────────────────────────────────────── */
    window.DripBuxToast = { show: show };

    /* ── Boot on DOM ready ───────────────────────────────────────── */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFromDOM);
    } else {
        initFromDOM();
    }
})();
