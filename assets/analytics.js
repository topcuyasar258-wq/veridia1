(function initVeridiaAnalytics(root) {
  const measurementId = String(root.VERIDIA_CONFIG?.gaMeasurementId || '').trim();

  // Skip third-party work until a real production measurement id is configured.
  if (!measurementId || /^G-X+$/i.test(measurementId)) {
    return;
  }

  root.dataLayer = root.dataLayer || [];
  root.gtag = function gtag() {
    root.dataLayer.push(arguments);
  };

  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
  document.head.appendChild(script);

  root.gtag('js', new Date());
  root.gtag('config', measurementId, {
    anonymize_ip: true,
    transport_type: 'beacon',
  });
})(typeof window !== 'undefined' ? window : globalThis);
