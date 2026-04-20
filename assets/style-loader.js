(function initDeferredStyles(root) {
  const doc = root.document;
  let activated = false;

  function activateDeferredStyles() {
    if (activated) {
      return;
    }

    activated = true;
    doc.querySelectorAll('link[data-deferred-style]').forEach((preload) => {
      const href = preload.dataset.href || preload.getAttribute('href');
      if (!href || doc.querySelector(`link[rel="stylesheet"][href="${href}"]`)) {
        return;
      }

      const sheet = doc.createElement('link');
      sheet.rel = 'stylesheet';
      sheet.href = href;

      const media = preload.getAttribute('data-style-media');
      if (media) {
        sheet.media = media;
      }

      doc.head.appendChild(sheet);
    });
  }

  function scheduleDeferredStyles() {
    activateDeferredStyles();
    sectionObserver?.disconnect();
  }

  let sectionObserver = null;

  if ('IntersectionObserver' in root) {
    const targets = ['#about', '#services', '#portfolio', '#quote', '#contact']
      .map((selector) => doc.querySelector(selector))
      .filter(Boolean);

    if (targets.length > 0) {
      sectionObserver = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          scheduleDeferredStyles();
        }
      }, { rootMargin: '180px 0px' });

      targets.forEach((target) => sectionObserver.observe(target));
    }
  }

  root.addEventListener('scroll', scheduleDeferredStyles, { passive: true, once: true });
  doc.addEventListener('pointerdown', scheduleDeferredStyles, { passive: true, once: true });
  doc.addEventListener('touchstart', scheduleDeferredStyles, { passive: true, once: true });
  doc.addEventListener('focusin', scheduleDeferredStyles, { once: true });
})(typeof window !== 'undefined' ? window : globalThis);
