/* AttendIQ — script.js
   Global JS: flash auto-dismiss, ring animations, misc. */

document.addEventListener('DOMContentLoaded', () => {

    // ---- Auto-dismiss flash messages after 4s ----
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach((flash, i) => {
        setTimeout(() => {
            flash.style.transition = 'opacity 0.4s, transform 0.4s';
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-6px)';
            setTimeout(() => flash.remove(), 400);
        }, 4000 + i * 300);
    });

    // ---- Animate progress rings on load ----
    const rings = document.querySelectorAll('.ring-fill');
    rings.forEach(ring => {
        const finalOffset = parseFloat(ring.getAttribute('stroke-dashoffset'));
        const dashArray = parseFloat(ring.getAttribute('stroke-dasharray'));
        // Start at full offset (empty) and animate to final
        ring.style.strokeDashoffset = dashArray;
        requestAnimationFrame(() => {
            ring.style.transition = 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)';
            ring.style.strokeDashoffset = finalOffset;
        });
    });

    // ---- Animate progress bars ----
    const bars = document.querySelectorAll('.progress-bar-fill, .preview-bar-fill');
    bars.forEach(bar => {
        const targetWidth = bar.style.width;
        bar.style.width = '0%';
        requestAnimationFrame(() => {
            bar.style.transition = 'width 0.8s cubic-bezier(0.4,0,0.2,1)';
            bar.style.width = targetWidth;
        });
    });

    // ---- Stagger subject card animations ----
    const cards = document.querySelectorAll('.subject-card');
    cards.forEach((card, i) => {
        card.style.animationDelay = `${i * 0.08}s`;
    });

    // ---- Number counter animation for stat numbers ----
    const statNums = document.querySelectorAll('.stat-number');
    statNums.forEach(el => {
        const target = parseInt(el.textContent) || 0;
        if (target === 0) return;
        let start = 0;
        const duration = 600;
        const step = target / (duration / 16);
        const timer = setInterval(() => {
            start += step;
            if (start >= target) {
                el.textContent = target;
                clearInterval(timer);
            } else {
                el.textContent = Math.floor(start);
            }
        }, 16);
    });
});