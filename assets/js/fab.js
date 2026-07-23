;(function initVeridiaFab(root) {
  const doc = root.document
  if (!doc || doc.querySelector('[data-veridia-fab]')) return

  const reducedMotion = root.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true
  const menuId = 'veridiaFabActions'
  const defaultMessage = 'Merhaba Veridia, bilgi almak istiyorum.'

  if (typeof root.VERIDIA_AI_ENABLED === 'undefined') {
    root.VERIDIA_AI_ENABLED = false
  }

  function onReady(callback) {
    if (doc.readyState === 'loading') {
      doc.addEventListener('DOMContentLoaded', callback, { once: true })
      return
    }

    callback()
  }

  function isAiEnabled() {
    const attr = doc.documentElement.dataset.veridiaAiEnabled || doc.body?.dataset.veridiaAiEnabled
    if (attr) return attr === 'true'
    return root.VERIDIA_AI_ENABLED === true
  }

  function sendEvent(eventName) {
    if (typeof root.gtag !== 'function') return
    root.gtag('event', eventName, {
      event_category: 'fab',
      event_label: eventName,
      page_path: root.location?.pathname || '/',
    })
  }

  function buildWhatsAppHref() {
    if (typeof root.buildVeridiaWhatsAppUrl === 'function') {
      return root.buildVeridiaWhatsAppUrl(defaultMessage)
    }

    const number = String(root.VERIDIA_CONFIG?.whatsapp || root.WHATSAPP_NUMBER || '905055174654').replace(/\D/g, '')
    const text = encodeURIComponent(defaultMessage)
    return /^\d{10,15}$/.test(number) ? `https://wa.me/${number}?text=${text}` : `https://wa.me/?text=${text}`
  }

  function icon(name) {
    const icons = {
      plus:
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
      close:
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
      whatsapp:
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7.2 19.2l.4-2.8a8 8 0 1 1 3.1 1.2l-3.5 1.6Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M9.2 8.8c.2-.4.4-.4.7-.4h.5c.2 0 .4.1.5.4l.6 1.4c.1.3.1.5-.1.7l-.3.4c.6 1.1 1.5 2 2.6 2.5l.5-.4c.2-.2.4-.2.7-.1l1.4.6c.3.1.4.3.4.6v.5c0 .3-.1.6-.4.8-.5.3-1.2.5-1.8.3-3.1-.8-5.4-3.1-6.2-6.2-.2-.6 0-1.2.3-1.7Z" fill="currentColor"/></svg>',
      spark:
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 3l1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M18.5 15.5l.7 2.1 2.1.7-2.1.7-.7 2.1-.7-2.1-2.1-.7 2.1-.7.7-2.1Z" fill="currentColor"/></svg>',
    }

    return icons[name]
  }

  function isVisibleElement(element) {
    if (!element || element.closest('[data-veridia-fab]')) return false
    if (element.hidden || element.getAttribute('aria-hidden') === 'true') return false
    const style = root.getComputedStyle(element)
    if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) return false
    const rect = element.getBoundingClientRect()
    return rect.width > 0 && rect.height > 0
  }

  function hasBlockingLayer() {
    const selectors = [
      'dialog[open]',
      '[aria-modal="true"]',
      '[data-cookie-banner]',
      '[data-cookie-consent]',
      '#cookieBanner',
      '#cookieConsent',
      '.cookie-banner',
      '.cookie-consent',
      '.modal.open',
      '.modal.is-open',
      '.mobile-menu.open',
      '#veridiaCampaignPopup',
    ]

    return selectors.some((selector) => Array.from(doc.querySelectorAll(selector)).some(isVisibleElement))
  }

  onReady(() => {
    const fab = doc.createElement('div')
    fab.className = 'veridia-fab'
    fab.setAttribute('data-veridia-fab', '')

    const actions = doc.createElement('div')
    actions.className = 'veridia-fab__actions'
    actions.id = menuId
    actions.setAttribute('aria-hidden', 'true')

    const whatsapp = doc.createElement('a')
    whatsapp.className = 'veridia-fab__action'
    whatsapp.href = buildWhatsAppHref()
    whatsapp.target = '_blank'
    whatsapp.rel = 'noopener'
    whatsapp.setAttribute('aria-label', "WhatsApp'tan yaz")
    whatsapp.tabIndex = -1
    whatsapp.innerHTML = `${icon('whatsapp')}<span>WhatsApp'tan yaz</span>`
    actions.append(whatsapp)

    if (isAiEnabled()) {
      const ai = doc.createElement('button')
      ai.className = 'veridia-fab__action'
      ai.type = 'button'
      ai.setAttribute('aria-label', 'Yapay zekaya sor')
      ai.tabIndex = -1
      ai.innerHTML = `${icon('spark')}<span>Yapay zekaya sor</span>`
      ai.addEventListener('click', () => {
        sendEvent('fab_ai_click')
        root.dispatchEvent(new CustomEvent('veridia:open-chat'))
        closeMenu()
      })
      actions.append(ai)
    }

    const toggle = doc.createElement('button')
    toggle.className = 'veridia-fab__button'
    toggle.type = 'button'
    toggle.setAttribute('aria-label', 'Hızlı aksiyonları aç')
    toggle.setAttribute('aria-expanded', 'false')
    toggle.setAttribute('aria-controls', menuId)
    toggle.tabIndex = reducedMotion ? 0 : -1
    toggle.innerHTML =
      `<span class="veridia-fab__button-icon-open">${icon('plus')}</span>` +
      `<span class="veridia-fab__button-icon-close">${icon('close')}</span>`

    fab.append(actions, toggle)
    doc.body.append(fab)

    let hasShown = reducedMotion
    let pulseTimer = null

    function setActionTabs(isOpen) {
      actions.setAttribute('aria-hidden', String(!isOpen))
      actions.querySelectorAll('a, button').forEach((action) => {
        action.tabIndex = isOpen ? 0 : -1
      })
    }

    function closeMenu() {
      fab.classList.remove('is-open')
      toggle.setAttribute('aria-expanded', 'false')
      toggle.setAttribute('aria-label', 'Hızlı aksiyonları aç')
      setActionTabs(false)
    }

    function openMenu() {
      if (fab.classList.contains('is-suppressed')) return
      fab.classList.add('is-open')
      toggle.setAttribute('aria-expanded', 'true')
      toggle.setAttribute('aria-label', 'Hızlı aksiyonları kapat')
      setActionTabs(true)
      sendEvent('fab_open')
    }

    function updateSuppression() {
      const suppressed = hasBlockingLayer()
      fab.classList.toggle('is-suppressed', suppressed)
      if (suppressed) closeMenu()
    }

    function reveal() {
      if (hasShown) return
      const scrollable = doc.documentElement.scrollHeight - root.innerHeight
      const progress = scrollable <= 0 ? 1 : root.scrollY / scrollable
      if (progress < 0.25) return
      hasShown = true
      fab.classList.add('is-visible')
      toggle.tabIndex = 0
      if (!reducedMotion) {
        pulseTimer = root.setInterval(() => {
          if (!fab.classList.contains('is-visible') || fab.classList.contains('is-suppressed')) return
          fab.classList.add('is-pulsing')
          root.setTimeout(() => fab.classList.remove('is-pulsing'), 750)
        }, 6000)
      }
    }

    toggle.addEventListener('click', (event) => {
      event.stopPropagation()
      if (fab.classList.contains('is-open')) {
        closeMenu()
      } else {
        openMenu()
      }
    })

    whatsapp.addEventListener('click', () => {
      sendEvent('fab_whatsapp_click')
      closeMenu()
    })

    doc.addEventListener('click', (event) => {
      if (!fab.classList.contains('is-open') || fab.contains(event.target)) return
      closeMenu()
    })

    doc.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMenu()
    })

    root.addEventListener('scroll', reveal, { passive: true })
    root.addEventListener('resize', updateSuppression, { passive: true })

    const observer = new MutationObserver(updateSuppression)
    observer.observe(doc.body, {
      attributes: true,
      childList: true,
      subtree: true,
      attributeFilter: ['class', 'style', 'open', 'hidden', 'aria-hidden'],
    })

    if (reducedMotion) {
      fab.classList.add('is-visible')
      toggle.tabIndex = 0
    } else {
      reveal()
    }

    updateSuppression()

    root.addEventListener('pagehide', () => {
      if (pulseTimer) root.clearInterval(pulseTimer)
      observer.disconnect()
    })
  })
})('undefined' !== typeof window ? window : globalThis)
