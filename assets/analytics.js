!function (root) {
  const measurementId = String(root.VERIDIA_CONFIG?.gaMeasurementId || '').trim()
  if (!measurementId || /^G-X+$/i.test(measurementId)) return

  root.dataLayer = root.dataLayer || []
  root.gtag = function () {
    root.dataLayer.push(arguments)
  }

  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`
  document.head.appendChild(script)
  root.gtag('js', new Date())
  root.gtag('config', measurementId, { anonymize_ip: true, transport_type: 'beacon' })

  function sendDeclarativeEvent(target) {
    const eventName = target?.dataset?.analyticsEvent
    if (!eventName) return
    root.gtag('event', eventName, {
      event_category: target.dataset.analyticsCategory || 'cta',
      event_label: target.dataset.analyticsLabel || target.textContent?.trim() || eventName,
      page_path: root.location?.pathname || '/',
    })
  }

  document.addEventListener('click', (event) => {
    sendDeclarativeEvent(event.target.closest('[data-analytics-event]'))
  })
  document.addEventListener('submit', (event) => {
    sendDeclarativeEvent(event.target.closest('form[data-analytics-event]'))
  })
}('undefined' != typeof window ? window : globalThis)
