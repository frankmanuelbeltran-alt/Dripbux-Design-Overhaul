/**
 * particles.js — DripBux Premium Pink Lightbug Particles
 * Floating pink lightbugs that drift along the edges of the page
 */

(function () {
    'use strict';

    /* ── Config ──────────────────────────────────────────────────── */
    const CONFIG = {
        maxParticles: 20,
        spawnInterval: 800,
        colors: ['#ff4d8d', '#ff80ab', '#ff6b9d', '#e91e63', '#ff4081'],
        sizes: ['tiny', 'small', '', 'large'],
        edgeMargin: 30,
        driftDuration: { min: 8000, max: 20000 },
    };

    let particleLayer = null;
    let spawnTimer = null;
    let activeParticles = 0;
    let isEnabled = true;

    /* ── Get or create particle layer ────────────────────────────── */
    function getLayer() {
        if (!particleLayer) {
            particleLayer = document.createElement('div');
            particleLayer.className = 'particle-layer';
            particleLayer.id = 'particleLayer';
            document.body.appendChild(particleLayer);
        }
        return particleLayer;
    }

    /* ── Create a lightbug particle ──────────────────────────────── */
    function spawnParticle() {
        if (!isEnabled || activeParticles >= CONFIG.maxParticles) return;

        const layer = getLayer();
        const bug = document.createElement('div');

        // Pick random properties
        const color = CONFIG.colors[Math.floor(Math.random() * CONFIG.colors.length)];
        const sizeClass = CONFIG.sizes[Math.floor(Math.random() * CONFIG.sizes.length)];
        const edge = Math.floor(Math.random() * 4); // 0=top, 1=right, 2=bottom, 3=left

        bug.className = `lightbug ${sizeClass}`.trim();
        bug.style.setProperty('--bug-color', color);
        bug.style.opacity = '0';

        // Position based on edge
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        let startX, startY, endX, endY;

        switch (edge) {
            case 0: // Top edge
                startX = Math.random() * vw;
                startY = -10;
                endX = startX + (Math.random() - 0.5) * 300;
                endY = vh + 10;
                break;
            case 1: // Right edge
                startX = vw + 10;
                startY = Math.random() * vh;
                endX = -10;
                endY = startY + (Math.random() - 0.5) * 300;
                break;
            case 2: // Bottom edge
                startX = Math.random() * vw;
                startY = vh + 10;
                endX = startX + (Math.random() - 0.5) * 300;
                endY = -10;
                break;
            case 3: // Left edge
                startX = -10;
                startY = Math.random() * vh;
                endX = vw + 10;
                endY = startY + (Math.random() - 0.5) * 300;
                break;
        }

        bug.style.left = startX + 'px';
        bug.style.top = startY + 'px';

        // Random duration
        const duration = CONFIG.driftDuration.min + Math.random() * (CONFIG.driftDuration.max - CONFIG.driftDuration.min);

        layer.appendChild(bug);
        activeParticles++;

        // Animate using Web Animations API
        const animation = bug.animate([
            { transform: 'translate(0, 0) scale(0.5)', opacity: 0 },
            { transform: 'translate(0, 0) scale(1)', opacity: 1, offset: 0.05 },
            { transform: `translate(${endX - startX}px, ${endY - startY}px) scale(1)`, opacity: 1, offset: 0.95 },
            { transform: `translate(${endX - startX}px, ${endY - startY}px) scale(0.5)`, opacity: 0 }
        ], {
            duration: duration,
            easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
            fill: 'forwards'
        });

        // Spawn trails occasionally
        if (Math.random() > 0.5) {
            spawnTrail(bug, startX, startY, color);
        }

        animation.onfinish = () => {
            if (bug.parentNode) bug.parentNode.removeChild(bug);
            activeParticles--;
        };
    }

    /* ── Spawn trailing dots behind a lightbug ───────────────────── */
    function spawnTrail(bug, startX, startY, color) {
        const layer = getLayer();
        const trailInterval = setInterval(() => {
            if (!bug.parentNode) {
                clearInterval(trailInterval);
                return;
            }

            const rect = bug.getBoundingClientRect();
            const trail = document.createElement('div');
            trail.className = 'lightbug-trail';
            trail.style.left = (rect.left + rect.width / 2) + 'px';
            trail.style.top = (rect.top + rect.height / 2) + 'px';
            trail.style.setProperty('--trail-color', color);
            layer.appendChild(trail);

            setTimeout(() => {
                if (trail.parentNode) trail.parentNode.removeChild(trail);
            }, 1500);
        }, 200);
    }

    /* ── Spawn corner sparkles ───────────────────────────────────── */
    function spawnCornerSparkle() {
        if (!isEnabled) return;

        const layer = getLayer();
        const sparkle = document.createElement('div');
        const color = CONFIG.colors[Math.floor(Math.random() * CONFIG.colors.length)];
        const corner = Math.floor(Math.random() * 4);

        sparkle.style.cssText = `
            position: absolute;
            width: 3px;
            height: 3px;
            border-radius: 50%;
            background: ${color};
            box-shadow: 0 0 6px ${color}, 0 0 12px ${color};
            pointer-events: none;
            animation: twinkle 2s ease-in-out infinite;
        `;

        const margin = 20;
        switch (corner) {
            case 0: sparkle.style.left = margin + 'px'; sparkle.style.top = margin + 'px'; break;
            case 1: sparkle.style.right = margin + 'px'; sparkle.style.top = margin + 'px'; break;
            case 2: sparkle.style.left = margin + 'px'; sparkle.style.bottom = margin + 'px'; break;
            case 3: sparkle.style.right = margin + 'px'; sparkle.style.bottom = margin + 'px'; break;
        }

        layer.appendChild(sparkle);
        setTimeout(() => {
            if (sparkle.parentNode) sparkle.parentNode.removeChild(sparkle);
        }, 2000 + Math.random() * 3000);
    }

    /* ── Start / Stop ────────────────────────────────────────────── */
    function start() {
        isEnabled = true;
        if (spawnTimer) clearInterval(spawnTimer);
        spawnTimer = setInterval(spawnParticle, CONFIG.spawnInterval);
        // Also spawn corner sparkles
        setInterval(spawnCornerSparkle, 2500);
        // Initial spawn
        for (let i = 0; i < 3; i++) {
            setTimeout(spawnParticle, i * 300);
        }
    }

    function stop() {
        isEnabled = false;
        if (spawnTimer) {
            clearInterval(spawnTimer);
            spawnTimer = null;
        }
        // Clear existing particles
        const layer = getLayer();
        layer.innerHTML = '';
        activeParticles = 0;
    }

    function toggle() {
        isEnabled = !isEnabled;
        if (isEnabled) start();
        else stop();
        return isEnabled;
    }

    function isRunning() {
        return isEnabled;
    }

    /* ── Expose global API ───────────────────────────────────────── */
    window.DripBuxParticles = {
        start,
        stop,
        toggle,
        isRunning
    };

    /* ── Boot on DOM ready ───────────────────────────────────────── */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            // Check saved preference
            const saved = localStorage.getItem('dripbux_particles');
            if (saved !== 'false') {
                start();
            }
        });
    } else {
        const saved = localStorage.getItem('dripbux_particles');
        if (saved !== 'false') {
            start();
        }
    }
})();
