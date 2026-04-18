(function initVeridiaAnalytics(root) {
  const measurementId = String(root.VERIDIA_CONFIG?.gaMeasurementId || '').trim();

  if (!measurementId || /^G-X+$/i.test(measurementId)) {
    return;
  }

  root.dataLayer = root.dataLayer || [];
  root.gtag = function gtag() {
    root.dataLayer.push(arguments);
  };
  root.gtag('js', new Date());
  root.gtag('config', measurementId, {
    anonymize_ip: true,
    transport_type: 'beacon',
  });

  function injectGtag() {
    setTimeout(function () {
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
      document.head.appendChild(script);
    }, 2000);
  }

  if (root.document.readyState === 'complete') {
    injectGtag();
  } else {
    root.addEventListener('load', injectGtag);
  }
})(typeof window !== 'undefined' ? window : globalThis);
