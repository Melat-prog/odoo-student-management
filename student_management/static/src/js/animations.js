/**
 * Amherst Academic Animations
 * Scroll Pop-Ups, Hero Banner Entrance Reveal, Slide Transitions, Stats Count-Up, and Quick-View Modal
 */

(function () {
    function initAnimations() {
        if (!document.body) return;
        
        // Mark JS animations as active so CSS reveal styles take effect safely
        document.body.classList.add('js-animations-active');

        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        // Removed '.amherst-hero-banner' and '.amherst-hero-banner-img' to avoid scroll IntersectionObserver conflicts
        const revealElements = document.querySelectorAll('.amherst-reveal, .amherst-pop, .amherst-slide-left, .amherst-slide-right');

        // --- A. Scroll Reveal Observer (.amherst-reveal, .amherst-pop, .amherst-slide-left, .amherst-slide-right) ---
        if (prefersReducedMotion) {
            revealElements.forEach(function (el) {
                el.classList.add('amherst-in-view');
            });
        } else if ('IntersectionObserver' in window) {
            const revealObserver = new IntersectionObserver(function (entries, observer) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('amherst-in-view');
                        observer.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.15
            });

            revealElements.forEach(function (el) {
                revealObserver.observe(el);
            });
        } else {
            // Fallback for legacy browsers
            revealElements.forEach(function (el) {
                el.classList.add('amherst-in-view');
            });
        }

        // FAILSAFE: Ensure content is NEVER permanently hidden
        setTimeout(function () {
            revealElements.forEach(function (el) {
                if (!el.classList.contains('amherst-in-view')) {
                    el.classList.add('amherst-in-view');
                }
            });
        }, 500);

        // --- B. Stats Count-Up Animation ---
        const statElements = document.querySelectorAll('.amherst-stat-num');

        function animateCountUp(el) {
            const rawText = el.getAttribute('data-target') || el.textContent.trim();
            const match = rawText.match(/^([^\d]*)([\d,]+)([^\d]*)$/);
            if (!match) return;

            const prefix = match[1] || '';
            const targetNumber = parseInt(match[2].replace(/,/g, ''), 10);
            const suffix = match[3] || '';

            if (isNaN(targetNumber)) return;

            const duration = 1200; // ms
            let startTime = null;

            function easeOutCubic(t) {
                return 1 - Math.pow(1 - t, 3);
            }

            function step(timestamp) {
                if (!startTime) startTime = timestamp;
                const progress = Math.min((timestamp - startTime) / duration, 1);
                const easedProgress = easeOutCubic(progress);
                const currentVal = Math.floor(easedProgress * targetNumber);

                el.textContent = prefix + currentVal.toLocaleString() + suffix;

                if (progress < 1) {
                    requestAnimationFrame(step);
                } else {
                    el.textContent = prefix + targetNumber.toLocaleString() + suffix;
                }
            }

            requestAnimationFrame(step);
        }

        if (statElements.length > 0) {
            if (prefersReducedMotion) return;

            if ('IntersectionObserver' in window) {
                const statsObserver = new IntersectionObserver(function (entries, observer) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting) {
                            animateCountUp(entry.target);
                            observer.unobserve(entry.target);
                        }
                    });
                }, {
                    threshold: 0.05
                });

                statElements.forEach(function (el) {
                    statsObserver.observe(el);
                });
            } else {
                statElements.forEach(function (el) {
                    animateCountUp(el);
                });
            }
        }

        // --- C. Quick View Modal Interaction ---
        const quickViewButtons = document.querySelectorAll('[data-amherst-quickview]');
        const modalTitle = document.getElementById('courseModalTitle');
        const modalCode = document.getElementById('courseModalCode');
        const modalInstructor = document.getElementById('courseModalInstructor');
        const modalDuration = document.getElementById('courseModalDuration');
        const modalDescription = document.getElementById('courseModalDescription');

        quickViewButtons.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                const title = btn.getAttribute('data-title') || 'Course Overview';
                const code = btn.getAttribute('data-code') || '';
                const instructor = btn.getAttribute('data-instructor') || 'Faculty Lead';
                const duration = btn.getAttribute('data-duration') || '1 Academic Term';
                const description = btn.getAttribute('data-description') || 'Comprehensive curriculum fostering deep analytical and practical expertise.';

                if (modalTitle) modalTitle.textContent = title;
                if (modalCode) modalCode.textContent = code ? 'Code: ' + code : '';
                if (modalInstructor) modalInstructor.textContent = instructor;
                if (modalDuration) modalDuration.textContent = duration;
                if (modalDescription) modalDescription.textContent = description;

                const modalEl = document.getElementById('courseDetailModal');
                if (modalEl && window.bootstrap && window.bootstrap.Modal) {
                    const bsModal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
                    bsModal.show();
                }
            });
        });
        cleanNavbar();
    }

    function cleanNavbar() {
        // Strip out Jobs/Careers links and their parent menu items
        // Also remove duplicate Contact/Contact Us links that don't match our exact custom path
        document.querySelectorAll('#top_menu a, .o_header_standard a').forEach(function(el) {
            const href = el.getAttribute('href');
            if (href) {
                const normHref = href.toLowerCase().trim();
                if (normHref.includes('/jobs') || normHref.includes('/careers') || normHref === '/contactus' || normHref.includes('/contact-us')) {
                    const li = el.closest('li');
                    if (li) {
                        li.remove();
                    } else {
                        el.remove();
                    }
                }
            }
        });

        // Ensure the top-right gold "Contact Us" navbar button links strictly to /contact
        document.querySelectorAll('a').forEach(function(el) {
            const text = el.textContent.toLowerCase();
            const href = el.getAttribute('href');
            if (href && (href === '/contactus' || href.includes('/contact-us') || text.includes('contact us'))) {
                if (el.closest('header')) {
                    el.setAttribute('href', '/contact');
                }
            }
        });
    }

    // Load-triggered preloader for the Hero Banner Image
    function initHeroPreload() {
        var heroSection = document.querySelector('.amherst-hero-banner');
        if (!heroSection) return;

        var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (reduceMotion) {
            heroSection.classList.remove('amherst-hero-loading');
            heroSection.classList.add('amherst-hero-loaded');
            return;
        }

        // Note: this URL must stay in sync with static/src/css/style.css
        var imageUrl = 'https://images.unsplash.com/photo-1541829070764-84a7d30dd3f3?q=80&w=2000&auto=format&fit=crop';
        var preloadImg = new Image();
        preloadImg.onload = function () {
            heroSection.classList.remove('amherst-hero-loading');
            heroSection.classList.add('amherst-hero-loaded');
        };
        preloadImg.onerror = function () {
            // Fail-safe: show the section even if preload fails, so a broken
            // image URL never leaves the hero permanently invisible.
            heroSection.classList.remove('amherst-hero-loading');
            heroSection.classList.add('amherst-hero-loaded');
        };
        preloadImg.src = imageUrl;

        heroSection.addEventListener('transitionend', function handler(e) {
            if (e.propertyName === 'transform') {
                heroSection.style.willChange = 'auto';
                heroSection.removeEventListener('transitionend', handler);
            }
        });
        heroSection.style.willChange = 'transform, opacity';
    }

    // Handle both immediate execution and DOMContentLoaded/load
    if (document.readyState === 'interactive' || document.readyState === 'complete') {
        initAnimations();
        initHeroPreload();
    } else {
        document.addEventListener('DOMContentLoaded', function () {
            initAnimations();
            initHeroPreload();
        });
        window.addEventListener('load', function () {
            initAnimations();
            initHeroPreload();
        });
    }
})();
