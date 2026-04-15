(function initDeferredStyles(root) {
  function activateDeferredStyles() {
    document.querySelectorAll('link[data-deferred-style]').forEach((preload) => {
      const href = preload.getAttribute('href');
      if (!href || document.querySelector(`link[rel="stylesheet"][href="${href}"]`)) {
        return;
      }

      const sheet = document.createElement('link');
      sheet.rel = 'stylesheet';
      sheet.href = href;

      const media = preload.getAttribute('data-style-media');
      if (media) {
        sheet.media = media;
      }

      document.head.appendChild(sheet);
    });
  }

  if ('requestIdleCallback' in root) {
    root.requestIdleCallback(activateDeferredStyles, { timeout: 1200 });
    return;
  }

  root.addEventListener('load', activateDeferredStyles, { once: true });
})(typeof window !== 'undefined' ? window : globalThis);
