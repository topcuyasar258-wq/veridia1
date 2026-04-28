;(function (window) {
  const document = window.document
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const revealElements = [...document.querySelectorAll('.reveal')]
  if (reducedMotion) {
    revealElements.forEach((element) => element.classList.add('visible'))
  } else if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return
          entry.target.classList.add('visible')
          revealObserver.unobserve(entry.target)
        })
      },
      { threshold: 0.1 }
    )
    revealElements.forEach((element) => revealObserver.observe(element))
  } else {
    revealElements.forEach((element) => element.classList.add('visible'))
  }

  function animateTicker(element) {
    const target = Number(element.dataset.target || 0)
    const divide = element.dataset.divide ? Number(element.dataset.divide) : 1
    const suffix = element.dataset.suffix || ''
    let startedAt = null

    window.requestAnimationFrame(function step(timestamp) {
      if (startedAt === null) startedAt = timestamp
      const progress = Math.min((timestamp - startedAt) / 1800, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      const value = (target * eased) / divide
      element.textContent = divide > 1 ? `${value.toFixed(1)}${suffix}` : `${Math.floor(value)}${suffix}`
      if (progress < 1) window.requestAnimationFrame(step)
    })
  }

  const statsTicker = document.querySelector('.stats-ticker')
  if (statsTicker && !reducedMotion && 'IntersectionObserver' in window) {
    const tickerObserver = new IntersectionObserver(
      (entries) => {
        if (!entries[0]?.isIntersecting) return
        document.querySelectorAll('.ticker-number').forEach(animateTicker)
        tickerObserver.disconnect()
      },
      { threshold: 0.5 }
    )
    tickerObserver.observe(statsTicker)
  } else {
    document.querySelectorAll('.ticker-number').forEach((element) => {
      const target = Number(element.dataset.target || 0)
      const divide = element.dataset.divide ? Number(element.dataset.divide) : 1
      const suffix = element.dataset.suffix || ''
      const value = divide > 1 ? (target / divide).toFixed(1) : String(target)
      element.textContent = `${value}${suffix}`
    })
  }

  const config = window.VERIDIA_CONFIG
  const pricingApi = window.VeridiaQuotePricing
  const quoteSteps = window.quoteSteps
  const serviceDetails = window.serviceDetails
  const portfolioProjects = window.portfolioProjects
  const portfolioProjectMetrics = window.portfolioProjectMetrics
  const defaultPortfolioMetrics = window.defaultPortfolioMetrics

  if (!(config && pricingApi && Array.isArray(quoteSteps) && serviceDetails && portfolioProjects)) {
    return
  }

  const {
    PRICING_CONFIG,
    calculateQuickQuote,
    buildWhyThisPriceText,
    formatMultiplier,
    formatTryCurrency,
  } = pricingApi

  const whatsapp = config.whatsapp || ''
  const deliverableMap = {
    branding: 'Marka konumlandırması, mesaj mimarisi ve stratejik yön çerçevesi',
    strategy: 'Marka konumlandırması, mesaj mimarisi ve stratejik yön çerçevesi',
    social: 'Sosyal medya planı, yayın ritmi ve topluluk yönetimi sistemi',
    performance: 'Reklam kampanyası kurulumu, optimizasyonu ve performans takibi',
    content: 'İçerik üretimi, kreatif adaptasyon ve format planlaması',
    pr: 'Basın görünürlüğü, duyuru planı ve marka güveni oluşturan iletişim yönetimi',
    influencer: 'Influencer eşleşmesi, brief süreci ve yayın koordinasyonu',
  }

  const quoteState = {
    stepIndex: 0,
    answers: { service: [] },
    result: null,
    approved: false,
  }

  const formatCurrency = (value) => formatTryCurrency(value)

  function selectedValues(step) {
    if (step.multiple) {
      return Array.isArray(quoteState.answers[step.key]) ? [...new Set(quoteState.answers[step.key])] : []
    }
    return quoteState.answers[step.key] ? [quoteState.answers[step.key]] : []
  }

  function optionLabel(step, value) {
    const option = step.options.find((item) => item.value === value)
    return option ? option.label : value
  }

  function optionLabels(step, values) {
    return [...new Set(values)].map((value) => optionLabel(step, value)).filter(Boolean)
  }

  function setValidationError(message = '') {
    const target = document.getElementById('quoteValidationError')
    if (!target) return
    target.textContent = message
    target.classList.toggle('active', Boolean(message))
  }

  function renderProgress() {
    const container = document.getElementById('quoteProgress')
    if (!container) return
    container.innerHTML = ''
    quoteSteps.forEach((step, index) => {
      const dot = document.createElement('div')
      dot.className = 'quote-progress-dot'
      if (index < quoteState.stepIndex) dot.classList.add('done')
      if (index === quoteState.stepIndex) dot.classList.add('active')
      dot.innerHTML = '<span></span>'
      container.appendChild(dot)
    })
  }

  function appendChatBubble(role, text) {
    const chat = document.getElementById('quoteChat')
    if (!chat) return
    const bubble = document.createElement('div')
    bubble.className = `chat-bubble ${role}`
    bubble.textContent = text
    chat.appendChild(bubble)
    chat.scrollTop = chat.scrollHeight
  }

  function buildPricingNote(result) {
    let text = [
      `Hizmet toplamı: ${result.basePoints} puan`,
      `Sektör etkisi: ${formatMultiplier(result.sectorMultiplier)}`,
      `İş büyüklüğü: ${formatMultiplier(result.scaleMultiplier)}`,
      `Başlangıç hızı: ${formatMultiplier(result.urgencyMultiplier)}`,
      `Puan başı bedel: ${formatCurrency(result.unitPrice)}`,
    ].join(' • ')

    text += `. Ara hesap ${formatCurrency(result.subtotalBeforeDiscount)} oldu.`
    if (result.discountAmount > 0) text += ` Paket indirimi olarak ${formatCurrency(result.discountAmount)} düşüldü.`
    if (result.minimumApplied) text += ` Minimum başlangıç bedeli olarak ${formatCurrency(result.minimumPrice)} baz alındı.`
    text += ` Son fiyat ${formatCurrency(result.finalPrice)} olarak belirlendi.`
    return text
  }

  function buildQuoteResult(answers) {
    const result = calculateQuickQuote({
      services: answers.service,
      sector: answers.sector,
      scale: answers.scale,
      urgency: answers.urgency,
    })

    const services = Array.isArray(answers.service) ? answers.service : []
    const deliverables = services.map((key) => deliverableMap[key]).filter(Boolean)
    if (services.length >= PRICING_CONFIG.bundleDiscount.minServices) {
      deliverables.push('Tek ekip gibi çalışan koordinasyon ve tek raporlama katmanı')
    }

    const reference = `VER-${new Date().toISOString().slice(2, 10).replace(/-/g, '')}-${Math.random()
      .toString(36)
      .slice(2, 6)
      .toUpperCase()}`
    const intro = result.discountRate > 0
      ? `%${Math.round(100 * result.discountRate)} paket indirimi dahil aylık başlangıç hizmet bedeli.`
      : 'Seçilen kapsam için aylık başlangıç hizmet bedeli.'

    return {
      packageName: result.packageName,
      monthly: result.finalPrice,
      reference,
      rangeText: result.minimumApplied ? `${intro} Minimum teklif koruması uygulandı.` : intro,
      whyThisPrice: buildWhyThisPriceText(result),
      pricingNote: buildPricingNote(result),
      serviceLabels: optionLabels(quoteSteps[0], answers.service),
      sectorLabel: optionLabel(quoteSteps[1], answers.sector),
      scaleLabel: optionLabel(quoteSteps[2], answers.scale),
      goalLabel: optionLabel(quoteSteps[3], answers.goal),
      urgencyLabel: optionLabel(quoteSteps[4], answers.urgency),
      contactLabel: optionLabel(quoteSteps[5], answers.contactMode),
      contactMode: answers.contactMode,
      deliverables,
      breakdown: [
        { label: 'Hizmet toplamı', value: `${result.basePoints} puan` },
        { label: 'Sektör etkisi', value: formatMultiplier(result.sectorMultiplier) },
        { label: 'İş büyüklüğü etkisi', value: formatMultiplier(result.scaleMultiplier) },
        { label: 'Başlangıç hızı etkisi', value: formatMultiplier(result.urgencyMultiplier) },
        { label: 'Puan başı bedel', value: formatCurrency(result.unitPrice) },
        { label: 'Ara hesap', value: formatCurrency(result.subtotalBeforeDiscount) },
        ...(result.discountAmount > 0
          ? [{ label: `Paket indirimi (%${Math.round(100 * result.discountRate)})`, value: `-${formatCurrency(result.discountAmount)}` }]
          : []),
        ...(result.minimumApplied
          ? [{ label: 'Minimum başlangıç bedeli', value: formatCurrency(result.minimumPrice) }]
          : []),
        { label: 'Son aylık teklif', value: formatCurrency(result.finalPrice) },
      ],
    }
  }

  function renderQuoteSummary() {
    const summaryCard = document.getElementById('quoteSummaryCard')
    const approvalBox = document.getElementById('quoteApprovalBox')
    const result = quoteState.result
    if (!(summaryCard && approvalBox && result)) return

    renderProgress()
    document.querySelectorAll('.quote-progress-dot').forEach((dot) => dot.classList.add('done'))
    document.getElementById('quoteStepTag').textContent = 'Teklif Hazır'
    document.getElementById('quoteQuestion').textContent = 'Ön teklifiniz oluşturuldu.'
    document.getElementById('quoteHelper').textContent =
      'Kapsam özetini inceleyin, uygunsa ön onay verip görüşme özetini açın.'
    document.getElementById('quoteOptions').innerHTML = ''
    document.getElementById('quoteStepActions').innerHTML = ''
    document.getElementById('quotePackageName').textContent = result.packageName
    document.getElementById('quotePrice').innerHTML = `${formatCurrency(result.monthly)} <small>/ aylık</small>`
    document.getElementById('quoteRange').textContent = result.rangeText
    document.getElementById('quoteReadiness').textContent = result.whyThisPrice
    document.getElementById('quoteAiNote').textContent = result.pricingNote
    document.getElementById('quoteReference').textContent = `Referans kodu: ${result.reference}`

    const breakdown = document.getElementById('quoteBreakdown')
    breakdown.innerHTML = ''
    result.breakdown.forEach((item) => {
      const element = document.createElement('li')
      element.innerHTML = `<span>${item.label}</span><strong>${item.value}</strong>`
      breakdown.appendChild(element)
    })

    const deliverables = document.getElementById('quoteDeliverables')
    deliverables.innerHTML = ''
    result.deliverables.forEach((item) => {
      const element = document.createElement('li')
      element.textContent = item
      deliverables.appendChild(element)
    })

    summaryCard.classList.add('active')
    approvalBox.classList.add('active')
    appendChatBubble(
      'bot',
      `${result.packageName} hazır. Tahmini aylık başlangıç fiyatı ${formatCurrency(
        result.monthly
      )} seviyesinde. Hazırsanız görüşme özetini WhatsApp'ta açabilirsiniz.`
    )
    window.localStorage.setItem(
      'veridia-latest-quote',
      JSON.stringify({ answers: quoteState.answers, result })
    )
  }

  function submitStep() {
    const step = quoteSteps[quoteState.stepIndex]
    const values = selectedValues(step)
    const labels = step.multiple ? optionLabels(step, values) : values.map((value) => optionLabel(step, value))
    if (!labels.length) {
      setValidationError('Devam etmek için en az bir seçenek işaretleyin.')
      return
    }

    setValidationError('')
    appendChatBubble('user', step.multiple ? `Seçilen hizmetler: ${labels.join(', ')}` : labels[0])

    if (quoteState.stepIndex < quoteSteps.length - 1) {
      quoteState.stepIndex += 1
      appendChatBubble('bot', quoteSteps[quoteState.stepIndex].question)
      renderStep()
      return
    }

    quoteState.result = buildQuoteResult(quoteState.answers)
    renderQuoteSummary()
  }

  function renderStepActions(step, values) {
    const actions = document.getElementById('quoteStepActions')
    if (!actions) return

    actions.innerHTML = ''
    if (step.multiple) {
      const note = document.createElement('div')
      note.className = 'quote-selection-note'
      if (!values.length) {
        note.textContent = 'Bir veya birden fazla hizmet seçebilirsiniz.'
      } else if (values.length >= PRICING_CONFIG.bundleDiscount.minServices) {
        note.textContent = `${values.length} hizmet seçildi. %${Math.round(
          100 * PRICING_CONFIG.bundleDiscount.rate
        )} paket indirimi aktif.`
      } else {
        note.textContent = `${values.length} hizmet seçildi. ${
          PRICING_CONFIG.bundleDiscount.minServices
        }+ hizmette otomatik %${Math.round(100 * PRICING_CONFIG.bundleDiscount.rate)} indirim devreye girer.`
      }
      actions.appendChild(note)
    }

    const nextButton = document.createElement('button')
    nextButton.type = 'button'
    nextButton.className = 'btn-gold'
    nextButton.textContent = quoteState.stepIndex === quoteSteps.length - 1 ? 'Teklifi Oluştur' : 'İleri'
    nextButton.addEventListener('click', submitStep)
    actions.appendChild(nextButton)

    if (step.multiple && values.length) {
      const clearButton = document.createElement('button')
      clearButton.type = 'button'
      clearButton.className = 'btn-outline'
      clearButton.textContent = 'Temizle'
      clearButton.addEventListener('click', () => {
        quoteState.answers = { ...quoteState.answers, [step.key]: [] }
        renderStep()
      })
      actions.appendChild(clearButton)
    }
  }

  function renderStep() {
    const summaryCard = document.getElementById('quoteSummaryCard')
    const approvalBox = document.getElementById('quoteApprovalBox')
    const step = quoteSteps[quoteState.stepIndex]
    const options = document.getElementById('quoteOptions')

    if (!(summaryCard && approvalBox && options)) return

    renderProgress()
    summaryCard.classList.remove('active')
    approvalBox.classList.remove('active')
    setValidationError('')

    document.getElementById('quoteStepTag').textContent = step.tag
    document.getElementById('quoteQuestion').textContent = step.question
    document.getElementById('quoteHelper').textContent = step.helper
    options.innerHTML = ''

    const values = selectedValues(step)
    step.options.forEach((option) => {
      const button = document.createElement('button')
      button.type = 'button'
      button.className = 'quote-option'
      button.innerHTML = `<strong>${option.label}</strong><span>${option.detail}</span>`
      if (values.includes(option.value)) button.classList.add('is-selected')

      button.addEventListener('click', () => {
        if (step.multiple) {
          const current = Array.isArray(quoteState.answers[step.key]) ? quoteState.answers[step.key] : []
          const nextValues = current.includes(option.value)
            ? current.filter((value) => value !== option.value)
            : [...current, option.value]
          quoteState.answers = { ...quoteState.answers, [step.key]: nextValues }
          if (nextValues.length) setValidationError('')
        } else {
          quoteState.answers = { ...quoteState.answers, [step.key]: option.value }
          setValidationError('')
        }
        renderStep()
      })

      options.appendChild(button)
    })

    renderStepActions(step, values)
  }

  renderStep()
  appendChatBubble('bot', quoteSteps[0].question)

  function fillDialogFromRecord(record, prefix, ctaButton) {
    if (!record) return false
    document.getElementById(`${prefix}Kicker`).textContent = record.kicker
    document.getElementById(`${prefix}Client`).textContent = record.number ? `${record.number} / ${record.code}` : record.client
    document.getElementById(`${prefix}Title`).textContent = record.title
    document.getElementById(`${prefix}Summary`).textContent = record.summary
    document.getElementById(`${prefix}Story`).textContent = record.story
    document.getElementById(`${prefix}Next`).textContent = record.next
    document.getElementById(`${prefix}Gradient`).style.background = record.gradient

    if (ctaButton && record.title) {
      ctaButton.textContent = `${record.title} İçin Teklif Al`
    }

    const pills = document.getElementById(`${prefix}Pills`)
    pills.innerHTML = ''
    record.pills.forEach((pill) => {
      const element = document.createElement('span')
      element.className = 'portfolio-pill'
      element.textContent = pill
      pills.appendChild(element)
    })

    const stats = document.getElementById(`${prefix}Stats`)
    stats.innerHTML = ''
    record.stats.forEach((stat) => {
      const element = document.createElement('div')
      element.className = 'portfolio-side-stat'
      element.innerHTML = `<div class="portfolio-side-label">${stat.label}</div><div class="portfolio-side-value">${stat.value}</div><div class="portfolio-side-note">${stat.note}</div>`
      stats.appendChild(element)
    })

    const deliverables = document.getElementById(`${prefix}Deliverables`)
    deliverables.innerHTML = ''
    record.deliverables.forEach((item) => {
      const element = document.createElement('li')
      element.textContent = item
      deliverables.appendChild(element)
    })

    const gallery = document.getElementById(`${prefix}Gallery`)
    gallery.innerHTML = ''
    record.gallery.forEach((item) => {
      const element = document.createElement('div')
      element.className = 'portfolio-gallery-cell'
      element.innerHTML = `<strong>${item.title}</strong><span>${item.copy}</span>`
      gallery.appendChild(element)
    })

    return true
  }

  function setupDialog({
    dialogId,
    closeId,
    ctaId,
    triggerSelector,
    dataKey,
    records,
    prefix,
    metricTarget,
  }) {
    const dialog = document.getElementById(dialogId)
    const closeButton = document.getElementById(closeId)
    const ctaButton = document.getElementById(ctaId)
    let lastTrigger = null

    const close = () => {
      if (!dialog) return
      if (typeof dialog.close === 'function' && dialog.open) {
        dialog.close()
      } else {
        dialog.removeAttribute('open')
      }
      document.body.style.overflow = ''
      lastTrigger?.focus()
    }

    const open = (key, trigger) => {
      if (!dialog) return
      const record = records[key]
      if (!fillDialogFromRecord(record, prefix, ctaButton)) return

      if (metricTarget) {
        const metrics = document.getElementById(metricTarget.id)
        metrics.innerHTML = ''
        ;(metricTarget.map[key] || defaultPortfolioMetrics || []).forEach((item) => {
          const element = document.createElement('div')
          element.className = 'metric'
          element.innerHTML = `<span class="metric-value">${item.value}</span><span class="metric-label">${item.label}</span>`
          metrics.appendChild(element)
        })
      }

      lastTrigger = trigger || document.querySelector(`${triggerSelector}[${dataKey}="${key}"]`)
      if (typeof dialog.showModal === 'function') {
        if (!dialog.open) dialog.showModal()
      } else {
        dialog.setAttribute('open', '')
      }
      document.body.style.overflow = 'hidden'
      closeButton?.focus()
    }

    document.querySelectorAll(`${triggerSelector}[${dataKey}]`).forEach((trigger) => {
      const handler = () => open(trigger.getAttribute(dataKey), trigger)
      trigger.addEventListener('click', handler)
      trigger.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return
        event.preventDefault()
        handler()
      })
    })

    document.querySelectorAll(`[data-service-trigger]`).forEach((trigger) => {
      if (dataKey !== 'data-service') return
      trigger.addEventListener('click', () => open(trigger.dataset.serviceTrigger, trigger))
    })

    closeButton?.addEventListener('click', close)
    dialog?.addEventListener('click', (event) => {
      const shell = dialog.querySelector(`.${dialogId.replace('Dialog', '-dialog-shell')}`)
      if (shell && !shell.contains(event.target)) close()
    })
    dialog?.addEventListener('cancel', (event) => {
      event.preventDefault()
      close()
    })
    ctaButton?.addEventListener('click', close)
  }

  setupDialog({
    dialogId: 'serviceDialog',
    closeId: 'serviceDialogClose',
    ctaId: 'serviceDialogCta',
    triggerSelector: '.service-card',
    dataKey: 'data-service',
    records: serviceDetails,
    prefix: 'serviceDialog',
  })

  setupDialog({
    dialogId: 'portfolioDialog',
    closeId: 'portfolioDialogClose',
    ctaId: 'portfolioDialogCta',
    triggerSelector: '.portfolio-card',
    dataKey: 'data-project',
    records: portfolioProjects,
    prefix: 'portfolioDialog',
    metricTarget: { id: 'portfolioDialogMetrics', map: portfolioProjectMetrics },
  })

  document.querySelectorAll('.filter-btn').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach((item) => item.classList.remove('active'))
      button.classList.add('active')
      const filter = button.dataset.filter
      document.querySelectorAll('.portfolio-card').forEach((card) => {
        card.classList.toggle('hidden', filter !== 'all' && card.dataset.category !== filter)
      })
    })
  })

  const beforeAfterBox = document.getElementById('baBox')
  const beforeAfterAfter = document.getElementById('baAfter')
  const beforeAfterLine = document.getElementById('baLine')

  function setBeforeAfter(clientX) {
    if (!(beforeAfterBox && beforeAfterAfter && beforeAfterLine)) return
    const rect = beforeAfterBox.getBoundingClientRect()
    const percent = Math.max(4, Math.min(96, ((clientX - rect.left) / rect.width) * 100))
    beforeAfterLine.style.left = `${percent}%`
    beforeAfterAfter.style.clipPath = `inset(0 ${100 - percent}% 0 0)`
  }

  if (beforeAfterBox && beforeAfterAfter && beforeAfterLine) {
    let dragging = false
    let animated = false

    beforeAfterBox.addEventListener('mousedown', (event) => {
      dragging = true
      setBeforeAfter(event.clientX)
    })
    beforeAfterBox.addEventListener(
      'touchstart',
      (event) => {
        dragging = true
        setBeforeAfter(event.touches[0].clientX)
      },
      { passive: true }
    )

    document.addEventListener('mouseup', () => {
      dragging = false
    })
    document.addEventListener('touchend', () => {
      dragging = false
    })
    document.addEventListener('mousemove', (event) => {
      if (!dragging) return
      setBeforeAfter(event.clientX)
    })
    document.addEventListener(
      'touchmove',
      (event) => {
        if (!dragging) return
        setBeforeAfter(event.touches[0].clientX)
      },
      { passive: true }
    )

    if (!reducedMotion && 'IntersectionObserver' in window) {
      const baObserver = new IntersectionObserver(
        (entries) => {
          if (!entries[0]?.isIntersecting || animated) return
          animated = true
          let frame = 0
          const timer = window.setInterval(() => {
            frame += 1
            const wave = 50 + 40 * Math.sin(0.075 * frame)
            const rect = beforeAfterBox.getBoundingClientRect()
            setBeforeAfter(rect.left + (rect.width * wave) / 100)
            if (frame > 84) window.clearInterval(timer)
          }, 30)
        },
        { threshold: 0.6 }
      )
      baObserver.observe(beforeAfterBox)
    }
  }

  const aboutDeck = document.getElementById('aboutDeck')
  const aboutCards = aboutDeck ? [...aboutDeck.querySelectorAll('.about-card')] : []
  if (aboutDeck && aboutCards.length) {
    const total = aboutCards.length
    aboutDeck.addEventListener('click', () => {
      const lead = aboutDeck.querySelector('.about-card[data-index="0"]')
      if (!lead) return
      lead.classList.add('exit')
      window.setTimeout(() => {
        lead.classList.remove('exit')
        aboutCards.forEach((card) => {
          const nextIndex = (Number(card.getAttribute('data-index') || 0) - 1 + total) % total
          card.setAttribute('data-index', String(nextIndex))
        })
      }, 400)
    })
  }

  const contactForm = document.getElementById('contactForm')
  const contactMessage = document.getElementById('contactFormMessage')

  function setContactMessage(type, text) {
    if (!contactMessage) return
    contactMessage.className = 'form-message'
    contactMessage.textContent = text
    if (type) contactMessage.classList.add(type)
  }

  if (contactForm) {
    contactForm.addEventListener('submit', async (event) => {
      event.preventDefault()
      const submitButton = contactForm.querySelector('.btn-submit')
      const action = contactForm.getAttribute('action') || ''

      if (!action) {
        setContactMessage('error', 'Form bağlantısı şu an eksik görünüyor. Lütfen WhatsApp üzerinden bize ulaşın.')
        return
      }

      submitButton?.setAttribute('disabled', 'disabled')
      setContactMessage('', '')

      try {
        const payload = Object.fromEntries(new FormData(contactForm).entries())
        payload.kaynak = window.location?.pathname || '/'

        const response = await window.fetch(action, {
          method: 'POST',
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        })
        const body = await response.json().catch(() => null)
        if (!response.ok) throw new Error(body?.error || 'Contact request failed')

        contactForm.reset()
        setContactMessage(
          'success',
          body?.message || 'Teşekkürler. Mesajınız bize ulaştı, en kısa sürede size dönüş yapacağız.'
        )
      } catch (_error) {
        setContactMessage(
          'error',
          'Mesaj gönderilirken bir sorun oluştu. Lütfen tekrar deneyin veya WhatsApp üzerinden bize ulaşın.'
        )
      } finally {
        submitButton?.removeAttribute('disabled')
      }
    })
  }

  document.querySelectorAll('[data-sector]').forEach((button) => {
    button.addEventListener('click', () => {
      const sector = button.dataset.sector
      document.querySelectorAll('.sector-btn').forEach((item) => {
        item.classList.remove('active')
        item.setAttribute('aria-pressed', 'false')
      })
      document.querySelectorAll('.sector-panel').forEach((panel) => panel.classList.remove('active'))
      button.classList.add('active')
      button.setAttribute('aria-pressed', 'true')
      document.getElementById(`sector-${sector}`)?.classList.add('active')
    })
  })

  const mobileLayoutQuery = window.matchMedia('(max-width: 768px)')

  function setAccordionState(root, expanded) {
    const trigger = root.querySelector('[data-accordion-trigger]')
    const panel = root.querySelector('[data-accordion-panel]')
    if (!(trigger && panel)) return
    root.classList.toggle('is-open', expanded)
    root.dataset.expanded = String(expanded)
    trigger.setAttribute('aria-expanded', String(expanded))
    panel.hidden = !expanded
  }

  document.querySelectorAll('[data-mobile-accordion]').forEach((root, index) => {
    const trigger = root.querySelector('[data-accordion-trigger]')
    const panel = root.querySelector('[data-accordion-panel]')
    if (!(trigger && panel)) return
    if (!panel.id) panel.id = `mobile-accordion-panel-${index + 1}`
    trigger.setAttribute('aria-controls', panel.id)
    trigger.addEventListener('click', () => {
      if (!mobileLayoutQuery.matches) return
      setAccordionState(root, root.dataset.expanded !== 'true')
    })
  })

  function syncReadMoreBlocks() {
    document.querySelectorAll('[data-mobile-readmore]').forEach((block) => {
      const content = block.querySelector('[data-mobile-readmore-content]')
      const toggle = block.querySelector('[data-mobile-readmore-toggle]')
      if (!(content && toggle)) return

      if (!mobileLayoutQuery.matches) {
        block.classList.add('is-expanded')
        block.classList.remove('is-short')
        toggle.hidden = true
        toggle.textContent = 'Devamını Gör'
        toggle.setAttribute('aria-expanded', 'true')
        return
      }

      const wasExpanded = block.dataset.expanded === 'true'
      block.classList.remove('is-expanded')
      const needsToggle = content.scrollHeight > content.clientHeight + 12

      if (!needsToggle) {
        block.dataset.expanded = 'true'
        block.classList.add('is-short', 'is-expanded')
        toggle.hidden = true
        toggle.setAttribute('aria-expanded', 'true')
        return
      }

      block.classList.remove('is-short')
      block.classList.toggle('is-expanded', wasExpanded)
      toggle.hidden = false
      toggle.textContent = wasExpanded ? 'Daha Az Göster' : 'Devamını Gör'
      toggle.setAttribute('aria-expanded', String(wasExpanded))
    })
  }

  document.querySelectorAll('[data-mobile-readmore-toggle]').forEach((toggle) => {
    toggle.addEventListener('click', () => {
      if (!mobileLayoutQuery.matches) return
      const block = toggle.closest('[data-mobile-readmore]')
      if (!block) return
      const expanded = block.dataset.expanded !== 'true'
      block.dataset.expanded = String(expanded)
      block.classList.toggle('is-expanded', expanded)
      toggle.textContent = expanded ? 'Daha Az Göster' : 'Devamını Gör'
      toggle.setAttribute('aria-expanded', String(expanded))
    })
  })

  function syncMobileExperience() {
    document.querySelectorAll('[data-mobile-accordion]').forEach((root) => {
      if (!mobileLayoutQuery.matches) {
        const trigger = root.querySelector('[data-accordion-trigger]')
        const panel = root.querySelector('[data-accordion-panel]')
        root.classList.add('is-open')
        trigger?.setAttribute('aria-expanded', 'true')
        if (panel) panel.hidden = false
        return
      }
      setAccordionState(root, root.dataset.expanded === 'true')
    })
    syncReadMoreBlocks()
  }

  if (typeof mobileLayoutQuery.addEventListener === 'function') {
    mobileLayoutQuery.addEventListener('change', syncMobileExperience)
  } else if (typeof mobileLayoutQuery.addListener === 'function') {
    mobileLayoutQuery.addListener(syncMobileExperience)
  }

  syncMobileExperience()

  document.querySelector('[data-quote-approve]')?.addEventListener('click', () => {
    if (!quoteState.result) return
    quoteState.approved = true
    const result = quoteState.result
    const message = [
      'Merhaba Veridia, site uzerinden on teklifimi onayladim.',
      `Referans: ${result.reference}`,
      `Hizmetler: ${result.serviceLabels.join(', ')}`,
      `Sektor: ${result.sectorLabel}`,
      `Isletme olcegi: ${result.scaleLabel}`,
      `Hedef: ${result.goalLabel}`,
      `Baslangic zamani: ${result.urgencyLabel}`,
      `Karar modu: ${result.contactLabel}`,
      `Onerilen paket: ${result.packageName}`,
      `Aylik teklif: ${formatCurrency(result.monthly)}`,
      'Devam etmek ve başlangıç planını oluşturmak istiyorum.',
    ].join('\n')

    appendChatBubble('user', 'Teklifi ön onayladım, ekip görüşmesi için hazırım.')
    appendChatBubble('bot', `Harika. ${result.reference} referans koduyla görüşme özeti hazırlandı.`)

    if (typeof window.buildVeridiaWhatsAppUrl === 'function') {
      window.open(window.buildVeridiaWhatsAppUrl(message), '_blank', 'noopener')
      return
    }

    const digits = whatsapp.replace(/\D/g, '')
    const url = /^\d{10,15}$/.test(digits)
      ? `https://wa.me/${digits}?text=${encodeURIComponent(message)}`
      : `https://wa.me/?text=${encodeURIComponent(message)}`
    window.open(url, '_blank', 'noopener')
  })

  document.querySelector('[data-quote-restart]')?.addEventListener('click', () => {
    const chat = document.getElementById('quoteChat')
    quoteState.stepIndex = 0
    quoteState.answers = { service: [] }
    quoteState.result = null
    quoteState.approved = false
    if (chat) {
      chat.innerHTML =
        '<div class="chat-bubble bot">Ön brief yeniden hazır. Yeni kombinasyonu seçin, kapsamı ve tahmini hizmet bedelini tekrar netleştireyim.</div>'
    }
    renderStep()
  })
})(typeof window !== 'undefined' ? window : globalThis)
