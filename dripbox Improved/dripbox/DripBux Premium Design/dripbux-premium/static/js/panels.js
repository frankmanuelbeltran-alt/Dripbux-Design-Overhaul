/**
 * panels.js — DripBux Premium Account & Settings Panels
 * Sliding sidebar panels for account info and site settings
 */

(function () {
    'use strict';

    /* ── Account Panel ───────────────────────────────────────────── */
    function initAccountPanel() {
        const overlay = document.getElementById('acctOverlay');
        const sidebar = document.getElementById('acctSidebar');
        const closeBtn = document.getElementById('acctClose');

        if (!overlay || !sidebar) return;

        function open() {
            overlay.classList.add('active');
            sidebar.classList.add('open');
            document.body.style.overflow = 'hidden';
            // Close settings if open
            closeSettingsPanel();
        }

        function close() {
            overlay.classList.remove('active');
            sidebar.classList.remove('open');
            document.body.style.overflow = '';
        }

        overlay.addEventListener('click', close);
        if (closeBtn) closeBtn.addEventListener('click', close);

        // Expose
        window.openAccountPanel = open;
        window.closeAccountPanel = close;

        // Keyboard: ESC to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && sidebar.classList.contains('open')) {
                close();
            }
        });
    }

    /* ── Settings Panel ──────────────────────────────────────────── */
    function initSettingsPanel() {
        const overlay = document.getElementById('setOverlay');
        const sidebar = document.getElementById('setSidebar');
        const closeBtn = document.getElementById('setClose');

        if (!overlay || !sidebar) return;

        function open() {
            overlay.classList.add('active');
            sidebar.classList.add('open');
            document.body.style.overflow = 'hidden';
            // Close account if open
            closeAccountPanel();
            // Sync toggle state
            syncToggleStates();
        }

        function close() {
            overlay.classList.remove('active');
            sidebar.classList.remove('open');
            document.body.style.overflow = '';
        }

        overlay.addEventListener('click', close);
        if (closeBtn) closeBtn.addEventListener('click', close);

        // Expose
        window.openSettingsPanel = open;
        window.closeSettingsPanel = close;

        // Keyboard: ESC to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && sidebar.classList.contains('open')) {
                close();
            }
        });
    }

    /* ── Sync toggle states from localStorage ────────────────────── */
    function syncToggleStates() {
        const particleToggle = document.getElementById('particleToggle');
        const soundToggle = document.getElementById('soundToggle');

        if (particleToggle) {
            particleToggle.checked = localStorage.getItem('dripbux_particles') !== 'false';
        }
        if (soundToggle) {
            soundToggle.checked = localStorage.getItem('dripbux_sound') === 'true';
        }
    }

    /* ── Initialize on DOM ready ─────────────────────────────────── */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initAccountPanel();
            initSettingsPanel();
        });
    } else {
        initAccountPanel();
        initSettingsPanel();
    }
})();

/* ── Toggle Particles Setting (global) ─────────────────────────── */
function toggleParticlesSetting() {
    const toggle = document.getElementById('particleToggle');
    const enabled = toggle ? toggle.checked : true;

    localStorage.setItem('dripbux_particles', enabled ? 'true' : 'false');

    if (enabled) {
        if (window.DripBuxParticles) window.DripBuxParticles.start();
    } else {
        if (window.DripBuxParticles) window.DripBuxParticles.stop();
    }

    if (window.DripBuxToast) {
        window.DripBuxToast.show(
            enabled ? 'Pink lightbugs enabled!' : 'Pink lightbugs disabled',
            enabled ? 'success' : 'info'
        );
    }
}

/* ── Toggle Sound Setting (global) ─────────────────────────────── */
function toggleSoundSetting() {
    const toggle = document.getElementById('soundToggle');
    const enabled = toggle ? toggle.checked : false;

    localStorage.setItem('dripbux_sound', enabled ? 'true' : 'false');

    if (window.DripBuxToast) {
        window.DripBuxToast.show(
            enabled ? 'Sound effects enabled!' : 'Sound effects disabled',
            enabled ? 'success' : 'info'
        );
    }
}
