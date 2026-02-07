// Marty Schneider - Cybersecurity Portfolio
// Main JavaScript

(function () {
  'use strict';

  // --- Typing Animation ---
  const typingPhrases = [
    'Vulnerability Management',
    'Penetration Testing',
    'Security Operations',
    'Threat Analysis',
    'Incident Response',
    'Network Defense',
  ];

  let phraseIndex = 0;
  let charIndex = 0;
  let isDeleting = false;
  const typingEl = document.getElementById('typing-text');

  function typeEffect() {
    if (!typingEl) return;

    const currentPhrase = typingPhrases[phraseIndex];

    if (isDeleting) {
      charIndex--;
      typingEl.textContent = currentPhrase.substring(0, charIndex);
    } else {
      charIndex++;
      typingEl.textContent = currentPhrase.substring(0, charIndex);
    }

    let delay = isDeleting ? 40 : 80;

    if (!isDeleting && charIndex === currentPhrase.length) {
      delay = 2000;
      isDeleting = true;
    } else if (isDeleting && charIndex === 0) {
      isDeleting = false;
      phraseIndex = (phraseIndex + 1) % typingPhrases.length;
      delay = 500;
    }

    setTimeout(typeEffect, delay);
  }

  // --- Navigation Scroll Effect ---
  const nav = document.getElementById('nav');

  function handleScroll() {
    if (window.scrollY > 50) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  }

  // --- Mobile Navigation Toggle ---
  const navToggle = document.getElementById('nav-toggle');
  const navMobile = document.getElementById('nav-mobile');

  function toggleMobileNav() {
    navToggle.classList.toggle('active');
    navMobile.classList.toggle('open');
  }

  // Close mobile nav on link click
  if (navMobile) {
    navMobile.querySelectorAll('.nav-link').forEach(function (link) {
      link.addEventListener('click', function () {
        navToggle.classList.remove('active');
        navMobile.classList.remove('open');
      });
    });
  }

  // --- Scroll Fade-in Animation ---
  function initFadeIn() {
    var elements = document.querySelectorAll(
      '.terminal-block, .timeline-item, .cert-card, .project-card, .contact-content'
    );

    elements.forEach(function (el) {
      el.classList.add('fade-in');
    });

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );

    elements.forEach(function (el) {
      observer.observe(el);
    });
  }

  // --- Profile Image Fallback ---
  function initProfileFallback() {
    var img = document.getElementById('profile-img');
    if (!img) return;

    img.addEventListener('error', function () {
      img.classList.add('error');
      var wrapper = img.parentElement;
      if (!wrapper.querySelector('.photo-fallback')) {
        var fallback = document.createElement('div');
        fallback.className = 'photo-fallback';
        fallback.textContent = 'MS';
        wrapper.appendChild(fallback);
      }
    });
  }

  // --- Initialize ---
  document.addEventListener('DOMContentLoaded', function () {
    typeEffect();
    initFadeIn();
    initProfileFallback();

    if (navToggle) {
      navToggle.addEventListener('click', toggleMobileNav);
    }

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
  });
})();
