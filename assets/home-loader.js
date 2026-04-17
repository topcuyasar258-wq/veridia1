(function initDeferredHomepage(root) {
  const doc = root.document;
  const homepageScripts = [
    './assets/site-data.js?v=4',
    './assets/quote-pricing.js?v=4',
    './assets/home.js?v=4',
  ];
  let homepageBootPromise = null;
  let analyticsScheduled = false;

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const existing = doc.querySelector(`script[src="${src}"]`);
      if (existing) {
        if (existing.dataset.loaded === 'true') {
          resolve();
          return;
        }

        existing.addEventListener('load', () => resolve(), { once: true });
        existing.addEventListener('error', () => reject(new Error(`Failed to load ${src}`)), { once: true });
        return;
      }

      const script = doc.createElement('script');
      script.src = src;
      script.async = false;
      script.addEventListener('load', () => {
        script.dataset.loaded = 'true';
        resolve();
      }, { once: true });
      script.addEventListener('error', () => reject(new Error(`Failed to load ${src}`)), { once: true });
      doc.head.appendChild(script);
    });
  }

  function loadScriptChain(sources) {
    return sources.reduce(
      (promise, src) => promise.then(() => loadScript(src)),
      Promise.resolve(),
    );
  }

  function ensureHomepageScripts() {
    if (!homepageBootPromise) {
      homepageBootPromise = loadScriptChain(homepageScripts);
    }

    return homepageBootPromise;
  }

  function scheduleHomepageBoot() {
    ensureHomepageScripts();
    stopWatching();
  }

  let sectionObserver = null;

  function stopWatching() {
    sectionObserver?.disconnect();
  }

  function watchSections() {
    if (!('IntersectionObserver' in root)) {
      return;
    }

    const targets = ['#about', '#services', '#quote', '#portfolio']
      .map((selector) => doc.querySelector(selector))
      .filter(Boolean);

    if (targets.length === 0) {
      return;
    }

    sectionObserver = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        scheduleHomepageBoot();
      }
    }, { rootMargin: '320px 0px' });

    targets.forEach((target) => sectionObserver.observe(target));
  }

  function scheduleAnalytics() {
    if (analyticsScheduled) {
      return;
    }

    analyticsScheduled = true;
    const loadAnalytics = () => {
      loadScript('./assets/analytics.js').catch(() => {});
    };

    if ('requestIdleCallback' in root) {
      root.requestIdleCallback(loadAnalytics, { timeout: 2000 });
      return;
    }

    root.setTimeout(loadAnalytics, 1400);
  }

  watchSections();

  root.addEventListener('scroll', scheduleHomepageBoot, { passive: true, once: true });
  doc.addEventListener('touchstart', scheduleHomepageBoot, { passive: true, once: true });
  doc.addEventListener('pointerdown', scheduleHomepageBoot, { passive: true, once: true });

  if ('requestIdleCallback' in root) {
    root.requestIdleCallback(() => ensureHomepageScripts(), { timeout: 1800 });
  } else {
    root.setTimeout(() => ensureHomepageScripts(), 1200);
  }

  if (doc.readyState === 'complete') {
    scheduleAnalytics();
  } else {
    root.addEventListener('load', scheduleAnalytics, { once: true });
  }
})(typeof window !== 'undefined' ? window : globalThis);
