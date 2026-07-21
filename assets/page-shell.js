;(function (window) {
  const document = window.document
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches
  const scrollBar = document.getElementById('scrollBar')
  const navbar = document.getElementById('navbar')
  const mobileMenu = document.getElementById('mobileMenu')
  const hamburger = document.getElementById('hamburger')
  const cursor = document.getElementById('cursor')
  const cursorRing = document.getElementById('cursorRing')
  const themeMeta = document.querySelector('meta[name="theme-color"]')

  let ticking = false
  let ringTimer = null

  function readStoredTheme() {
    try {
      return window.localStorage.getItem('veridia-theme') === 'light' ? 'light' : 'dark'
    } catch (_error) {
      return 'dark'
    }
  }

  function storeTheme(theme) {
    try {
      window.localStorage.setItem('veridia-theme', theme)
    } catch (_error) {
      // Theme persistence is a progressive enhancement.
    }
  }

  function updateThemeToggle(toggle, isLight) {
    const icon = toggle.querySelector('[data-theme-icon], .theme-toggle-icon') || toggle.querySelector('span')
    const label = toggle.querySelector('[data-theme-label], .theme-toggle-label') || toggle.querySelector('span:last-child')

    if (icon) icon.textContent = isLight ? '☀️' : '🌙'
    if (label) label.textContent = isLight ? 'Açık' : 'Koyu'

    toggle.setAttribute('aria-label', isLight ? 'Koyu temaya geç' : 'Açık temaya geç')
    toggle.setAttribute('aria-pressed', String(isLight))
  }

  function applyTheme(theme) {
    const isLight = theme === 'light'
    if (isLight) {
      document.documentElement.dataset.theme = 'light'
    } else {
      delete document.documentElement.dataset.theme
    }

    themeMeta?.setAttribute('content', isLight ? '#edf1eb' : '#0a0a0f')
    document.querySelectorAll('[data-theme-toggle]').forEach((toggle) => updateThemeToggle(toggle, isLight))
  }

  function ensureThemeToggle() {
    const nav = document.getElementById('navbar') || document.querySelector('body > nav[aria-label="Ana Menü"]')
    if (!nav || nav.querySelector('.revision-nav-theme')) return

    const themeButton = document.createElement('button')
    themeButton.className = 'revision-nav-theme'
    themeButton.type = 'button'
    themeButton.setAttribute('data-theme-toggle', '')
    themeButton.innerHTML =
      '<span class="theme-toggle-icon" data-theme-icon aria-hidden="true">🌙</span><span data-theme-label>Koyu</span>'

    let actionSlot = nav.querySelector('.nav-mobile-right, .nav-actions')
    if (!actionSlot) {
      actionSlot = document.createElement('div')
      actionSlot.className = 'nav-actions'
      const existingMenuToggle = nav.querySelector('[data-mobile-toggle], .hamburger')
      if (existingMenuToggle) {
        nav.insertBefore(actionSlot, existingMenuToggle)
        actionSlot.append(existingMenuToggle)
      } else {
        nav.append(actionSlot)
      }
    }

    const menuToggle = actionSlot.querySelector('[data-mobile-toggle], .hamburger')
    if (menuToggle) {
      actionSlot.insertBefore(themeButton, menuToggle)
    } else {
      actionSlot.append(themeButton)
    }
  }

  function setMobileMenuOpen(isOpen) {
    if (!(mobileMenu && hamburger)) return
    mobileMenu.classList.toggle('open', isOpen)
    mobileMenu.setAttribute('aria-hidden', String(!isOpen))
    hamburger.classList.toggle('open', isOpen)
    hamburger.setAttribute('aria-expanded', String(isOpen))
    document.body.style.overflow = isOpen ? 'hidden' : ''
  }

  function closeMobileMenu() {
    setMobileMenuOpen(false)
  }

  function updateScrollState() {
    const scrollTop = document.documentElement.scrollTop || document.body.scrollTop
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight
    if (scrollBar) scrollBar.style.width = `${scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0}%`
    navbar?.classList.toggle('scrolled', scrollTop > 50)
    ticking = false
  }

  ensureThemeToggle()
  applyTheme(readStoredTheme())

  if (!reducedMotion && finePointer && cursor && cursorRing) {
    document.addEventListener('mousemove', (event) => {
      cursor.style.left = `${event.clientX}px`
      cursor.style.top = `${event.clientY}px`
      window.clearTimeout(ringTimer)
      ringTimer = window.setTimeout(() => {
        cursorRing.style.left = `${event.clientX}px`
        cursorRing.style.top = `${event.clientY}px`
      }, 40)
    })

    const bindHoverTargets = () => {
      document.querySelectorAll('a, button, [role="button"], .blog-card').forEach((element) => {
        element.addEventListener('mouseenter', () => {
          cursorRing.style.transform = 'translate(-50%, -50%) scale(1.5)'
          cursorRing.style.opacity = '1'
        })
        element.addEventListener('mouseleave', () => {
          cursorRing.style.transform = 'translate(-50%, -50%) scale(1)'
          cursorRing.style.opacity = '0.6'
        })
      })
    }

    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(bindHoverTargets, { timeout: 2000 })
    } else {
      window.setTimeout(bindHoverTargets, 500)
    }
  }

  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-mobile-close]')) {
      closeMobileMenu()
      return
    }

    if (event.target.closest('[data-mobile-toggle]')) {
      if (mobileMenu) setMobileMenuOpen(!mobileMenu.classList.contains('open'))
      return
    }

    if (event.target.closest('[data-theme-toggle]')) {
      const nextTheme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light'
      applyTheme(nextTheme)
      storeTheme(nextTheme)
    }
  })

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && mobileMenu?.classList.contains('open')) closeMobileMenu()
  })

  window.addEventListener(
    'scroll',
    () => {
      if (!ticking) {
        ticking = true
        window.requestAnimationFrame(updateScrollState)
      }
    },
    { passive: true }
  )

  updateScrollState()
})('undefined' !== typeof window ? window : globalThis)
