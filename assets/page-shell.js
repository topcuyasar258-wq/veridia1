(function initPageShell(root) {
  const doc = root.document;
  const prefersReducedMotion = root.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const scrollBar = doc.getElementById('scrollBar');
  const navbar = doc.getElementById('navbar');
  const mobileMenu = doc.getElementById('mobileMenu');
  const hamburger = doc.getElementById('hamburger');
  const cursor = doc.getElementById('cursor');
  const cursorRing = doc.getElementById('cursorRing');
  const hasFinePointer = root.matchMedia('(hover: hover) and (pointer: fine)').matches;
  let scrollTicking = false;
  let ringTimer = null;

  function setBodyLock(locked) {
    doc.body.style.overflow = locked ? 'hidden' : '';
  }

  function setMobileMenuState(open) {
    if (!mobileMenu || !hamburger) {
      return;
    }

    mobileMenu.classList.toggle('open', open);
    mobileMenu.setAttribute('aria-hidden', String(!open));
    hamburger.classList.toggle('open', open);
    hamburger.setAttribute('aria-expanded', String(open));
    setBodyLock(open);
  }

  function toggleMobileMenu() {
    if (!mobileMenu) {
      return;
    }

    setMobileMenuState(!mobileMenu.classList.contains('open'));
  }

  function closeMobileMenu() {
    setMobileMenuState(false);
  }

  function applyTheme(theme) {
    const isLight = theme === 'light';
    doc.documentElement.dataset.theme = isLight ? 'light' : '';
    doc.querySelector('meta[name="theme-color"]')?.setAttribute('content', isLight ? '#edf1eb' : '#0a0a0f');

    const themeIcon = doc.getElementById('themeIcon');
    const themeLabel = doc.getElementById('themeLabel');

    if (themeIcon) {
      themeIcon.textContent = isLight ? '☀️' : '🌙';
    }

    if (themeLabel) {
      themeLabel.textContent = isLight ? 'Açık' : 'Koyu';
    }
  }

  function toggleTheme() {
    const nextTheme = doc.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
    applyTheme(nextTheme);
    root.localStorage.setItem('veridia-theme', nextTheme);
  }

  function updateScrollUi() {
    const scrolled = doc.documentElement.scrollTop || doc.body.scrollTop;
    const height = doc.documentElement.scrollHeight - doc.documentElement.clientHeight;

    if (scrollBar) {
      scrollBar.style.width = `${height > 0 ? (scrolled / height) * 100 : 0}%`;
    }

    navbar?.classList.toggle('scrolled', scrolled > 50);
    scrollTicking = false;
  }

  function queueScrollUi() {
    if (scrollTicking) {
      return;
    }

    scrollTicking = true;
    root.requestAnimationFrame(updateScrollUi);
  }

  if (!prefersReducedMotion && hasFinePointer && cursor && cursorRing) {
    doc.addEventListener('mousemove', (event) => {
      cursor.style.left = `${event.clientX}px`;
      cursor.style.top = `${event.clientY}px`;
      root.clearTimeout(ringTimer);
      ringTimer = root.setTimeout(() => {
        cursorRing.style.left = `${event.clientX}px`;
        cursorRing.style.top = `${event.clientY}px`;
      }, 40);
    });

    doc.querySelectorAll('a, button, [role="button"], .blog-card').forEach((element) => {
      element.addEventListener('mouseenter', () => {
        cursorRing.style.transform = 'translate(-50%, -50%) scale(1.5)';
        cursorRing.style.opacity = '1';
      });

      element.addEventListener('mouseleave', () => {
        cursorRing.style.transform = 'translate(-50%, -50%) scale(1)';
        cursorRing.style.opacity = '0.6';
      });
    });
  }

  doc.addEventListener('click', (event) => {
    const closeTrigger = event.target.closest('[data-mobile-close]');
    if (closeTrigger) {
      closeMobileMenu();
      return;
    }

    const toggleTrigger = event.target.closest('[data-mobile-toggle]');
    if (toggleTrigger) {
      toggleMobileMenu();
      return;
    }

    const themeTrigger = event.target.closest('[data-theme-toggle]');
    if (themeTrigger) {
      toggleTheme();
    }
  });

  doc.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && mobileMenu?.classList.contains('open')) {
      closeMobileMenu();
    }
  });

  root.addEventListener('scroll', queueScrollUi, { passive: true });

  applyTheme(root.localStorage.getItem('veridia-theme') || 'dark');
  updateScrollUi();
})(typeof window !== 'undefined' ? window : globalThis);
