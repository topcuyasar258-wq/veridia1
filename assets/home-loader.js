;(function initializeHomeAssets(root) {
  const document = root.document
  const assetUrls = Object.freeze([
    './assets/site-data.js?v=6',
    './assets/quote-pricing.js?v=6',
    './assets/home-content-overrides.js?v=7',
    './assets/home.js?v=8',
  ])

  let loadPromise = null

  function loadScript(url) {
    return new Promise((resolve, reject) => {
      const existing = document.querySelector(`script[src="${url}"]`)
      if (existing) {
        if (existing.dataset.loaded === 'true') {
          resolve()
          return
        }

        existing.addEventListener('load', resolve, { once: true })
        existing.addEventListener('error', () => reject(new Error(`Failed to load ${url}`)), { once: true })
        return
      }

      const script = document.createElement('script')
      script.src = url
      script.async = false
      script.addEventListener(
        'load',
        () => {
          script.dataset.loaded = 'true'
          resolve()
        },
        { once: true },
      )
      script.addEventListener('error', () => reject(new Error(`Failed to load ${url}`)), { once: true })
      document.head.appendChild(script)
    })
  }

  function loadAssets() {
    if (!loadPromise) {
      loadPromise = assetUrls.reduce(
        (sequence, url) => sequence.then(() => loadScript(url)),
        Promise.resolve(),
      )
    }
    return loadPromise
  }

  function startLoading() {
    loadAssets().catch((error) => {
      console.error('Homepage interactions could not be initialized.', error)
    })
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startLoading, { once: true })
  } else {
    startLoading()
  }
})(typeof window !== 'undefined' ? window : globalThis)
