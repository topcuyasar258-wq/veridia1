(function initHomepage(root) {
  const doc = root.document;
  const prefersReducedMotion = root.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!prefersReducedMotion) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    doc.querySelectorAll('.reveal').forEach((element) => revealObserver.observe(element));
  } else {
    doc.querySelectorAll('.reveal').forEach((element) => element.classList.add('visible'));
  }

  function runCounter(element) {
    const target = Number(element.dataset.target || 0);
    const divide = element.dataset.divide ? Number(element.dataset.divide) : 1;
    const suffix = element.dataset.suffix || '';
    let start = null;

    function step(timestamp) {
      if (start === null) {
        start = timestamp;
      }

      const progress = Math.min((timestamp - start) / 1800, 1);
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      const value = (target * easedProgress) / divide;
      element.textContent = divide > 1 ? `${value.toFixed(1)}${suffix}` : `${Math.floor(value)}${suffix}`;

      if (progress < 1) {
        root.requestAnimationFrame(step);
      }
    }

    root.requestAnimationFrame(step);
  }

  const ticker = doc.querySelector('.stats-ticker');
  if (ticker && !prefersReducedMotion) {
    const tickerObserver = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting) {
        doc.querySelectorAll('.ticker-number').forEach(runCounter);
        tickerObserver.disconnect();
      }
    }, { threshold: 0.5 });

    tickerObserver.observe(ticker);
  } else {
    doc.querySelectorAll('.ticker-number').forEach((element) => {
      const target = Number(element.dataset.target || 0);
      const divide = element.dataset.divide ? Number(element.dataset.divide) : 1;
      const suffix = element.dataset.suffix || '';
      const value = divide > 1 ? (target / divide).toFixed(1) : target;
      element.textContent = `${value}${suffix}`;
    });
  }

  const siteConfig = root.VERIDIA_CONFIG;
  const quotePricingApi = root.VeridiaQuotePricing;
  const quoteSteps = root.quoteSteps;
  const serviceDetails = root.serviceDetails;
  const portfolioProjects = root.portfolioProjects;
  const portfolioProjectMetrics = root.portfolioProjectMetrics;
  const defaultPortfolioMetrics = root.defaultPortfolioMetrics;

  if (!siteConfig || !quotePricingApi || !Array.isArray(quoteSteps) || !serviceDetails || !portfolioProjects) {
    return;
  }

  const {
    PRICING_CONFIG,
    calculateQuickQuote,
    buildWhyThisPriceText,
    formatMultiplier,
    formatTryCurrency,
  } = quotePricingApi;

  const whatsappPhone = siteConfig.whatsapp || '';
  const quoteServiceDeliverables = {
    branding: 'Marka konumlandırması, mesaj mimarisi ve stratejik yön çerçevesi',
    strategy: 'Marka konumlandırması, mesaj mimarisi ve stratejik yön çerçevesi',
    social: 'Sosyal medya planı, yayın ritmi ve topluluk yönetimi sistemi',
    performance: 'Reklam kampanyası kurulumu, optimizasyonu ve performans takibi',
    content: 'İçerik üretimi, kreatif adaptasyon ve format planlaması',
    pr: 'Basın görünürlüğü, duyuru planı ve marka güveni oluşturan iletişim yönetimi',
    influencer: 'Influencer eşleşmesi, brief süreci ve yayın koordinasyonu',
  };

  const quoteState = {
    stepIndex: 0,
    answers: {
      service: [],
    },
    result: null,
    approved: false,
  };

  function formatCurrency(value) {
    return formatTryCurrency(value);
  }

  function createQuoteProgress() {
    const wrap = doc.getElementById('quoteProgress');
    if (!wrap) {
      return;
    }

    wrap.innerHTML = '';
    quoteSteps.forEach((_, index) => {
      const dot = doc.createElement('div');
      dot.className = 'quote-progress-dot';
      if (index < quoteState.stepIndex) {
        dot.classList.add('done');
      }
      if (index === quoteState.stepIndex) {
        dot.classList.add('active');
      }
      dot.innerHTML = '<span></span>';
      wrap.appendChild(dot);
    });
  }

  function pushQuoteMessage(role, text) {
    const chat = doc.getElementById('quoteChat');
    if (!chat) {
      return;
    }

    const bubble = doc.createElement('div');
    bubble.className = `chat-bubble ${role}`;
    bubble.textContent = text;
    chat.appendChild(bubble);
    chat.scrollTop = chat.scrollHeight;
  }

  function getOptionText(step, value) {
    const found = step.options.find((option) => option.value === value);
    return found ? found.label : value;
  }

  function getOptionTexts(step, values) {
    const normalizedValues = Array.isArray(values) ? [...new Set(values)] : [];
    return normalizedValues.map((value) => getOptionText(step, value)).filter(Boolean);
  }

  function getSelectedQuoteValues(step) {
    if (step.multiple) {
      return Array.isArray(quoteState.answers[step.key]) ? [...new Set(quoteState.answers[step.key])] : [];
    }

    return quoteState.answers[step.key] ? [quoteState.answers[step.key]] : [];
  }

  function setQuoteValidationError(message = '') {
    const errorNode = doc.getElementById('quoteValidationError');
    if (!errorNode) {
      return;
    }

    errorNode.textContent = message;
    errorNode.classList.toggle('active', Boolean(message));
  }

  function confirmQuoteStep() {
    const step = quoteSteps[quoteState.stepIndex];
    const selectedValues = getSelectedQuoteValues(step);
    const selectedLabels = step.multiple
      ? getOptionTexts(step, selectedValues)
      : selectedValues.map((value) => getOptionText(step, value));

    if (selectedLabels.length === 0) {
      setQuoteValidationError('Devam etmek için en az bir seçenek işaretleyin.');
      return;
    }

    setQuoteValidationError('');
    advanceQuoteFlow(step.multiple ? `Seçilen hizmetler: ${selectedLabels.join(', ')}` : selectedLabels[0]);
  }

  function renderQuoteStepActions(step) {
    const actionsWrap = doc.getElementById('quoteStepActions');
    if (!actionsWrap) {
      return;
    }

    actionsWrap.innerHTML = '';
    const selectedValues = getSelectedQuoteValues(step);

    if (step.multiple) {
      const selectionNote = doc.createElement('div');
      selectionNote.className = 'quote-selection-note';

      if (selectedValues.length === 0) {
        selectionNote.textContent = 'Bir veya birden fazla hizmet seçebilirsiniz.';
      } else if (selectedValues.length >= PRICING_CONFIG.bundleDiscount.minServices) {
        selectionNote.textContent = `${selectedValues.length} hizmet seçildi. %${Math.round(PRICING_CONFIG.bundleDiscount.rate * 100)} paket indirimi aktif.`;
      } else {
        selectionNote.textContent = `${selectedValues.length} hizmet seçildi. ${PRICING_CONFIG.bundleDiscount.minServices}+ hizmette otomatik %${Math.round(PRICING_CONFIG.bundleDiscount.rate * 100)} indirim devreye girer.`;
      }

      actionsWrap.appendChild(selectionNote);
    }

    const continueButton = doc.createElement('button');
    continueButton.type = 'button';
    continueButton.className = 'btn-gold';
    continueButton.textContent = quoteState.stepIndex === quoteSteps.length - 1 ? 'Teklifi Oluştur' : 'İleri';
    continueButton.addEventListener('click', confirmQuoteStep);
    actionsWrap.appendChild(continueButton);

    if (step.multiple && selectedValues.length > 0) {
      const clearButton = doc.createElement('button');
      clearButton.type = 'button';
      clearButton.className = 'btn-outline';
      clearButton.textContent = 'Temizle';
      clearButton.addEventListener('click', () => {
        quoteState.answers = {
          ...quoteState.answers,
          [step.key]: [],
        };
        renderQuoteStep();
      });
      actionsWrap.appendChild(clearButton);
    }
  }

  function renderQuoteStep() {
    const summary = doc.getElementById('quoteSummaryCard');
    const approval = doc.getElementById('quoteApprovalBox');
    const step = quoteSteps[quoteState.stepIndex];
    const optionsWrap = doc.getElementById('quoteOptions');
    const stepTag = doc.getElementById('quoteStepTag');
    const question = doc.getElementById('quoteQuestion');
    const helper = doc.getElementById('quoteHelper');

    if (!summary || !approval || !optionsWrap || !stepTag || !question || !helper) {
      return;
    }

    createQuoteProgress();
    summary.classList.remove('active');
    approval.classList.remove('active');
    setQuoteValidationError('');

    stepTag.textContent = step.tag;
    question.textContent = step.question;
    helper.textContent = step.helper;
    optionsWrap.innerHTML = '';

    const selectedValues = getSelectedQuoteValues(step);

    step.options.forEach((option) => {
      const button = doc.createElement('button');
      button.type = 'button';
      button.className = 'quote-option';
      button.innerHTML = `<strong>${option.label}</strong><span>${option.detail}</span>`;
      if (selectedValues.includes(option.value)) {
        button.classList.add('is-selected');
      }

      button.addEventListener('click', () => {
        if (step.multiple) {
          toggleQuoteService(option.value);
          return;
        }

        selectQuoteOption(option);
      });

      optionsWrap.appendChild(button);
    });

    renderQuoteStepActions(step);
  }

  function toggleQuoteService(serviceValue) {
    const step = quoteSteps[quoteState.stepIndex];
    const currentValues = Array.isArray(quoteState.answers[step.key]) ? quoteState.answers[step.key] : [];
    const nextValues = currentValues.includes(serviceValue)
      ? currentValues.filter((value) => value !== serviceValue)
      : [...currentValues, serviceValue];

    quoteState.answers = {
      ...quoteState.answers,
      [step.key]: nextValues,
    };

    if (nextValues.length > 0) {
      setQuoteValidationError('');
    }

    renderQuoteStep();
  }

  function advanceQuoteFlow(userMessage) {
    if (userMessage) {
      pushQuoteMessage('user', userMessage);
    }

    if (quoteState.stepIndex < quoteSteps.length - 1) {
      quoteState.stepIndex += 1;
      pushQuoteMessage('bot', quoteSteps[quoteState.stepIndex].question);
      renderQuoteStep();
      return;
    }

    quoteState.result = buildQuoteResult(quoteState.answers);
    renderQuoteResult();
  }

  function selectQuoteOption(option) {
    const step = quoteSteps[quoteState.stepIndex];
    quoteState.answers = {
      ...quoteState.answers,
      [step.key]: option.value,
    };

    setQuoteValidationError('');
    renderQuoteStep();
  }

  function buildQuotePricingNote(pricing) {
    const noteParts = [
      `Hizmet toplamı: ${pricing.basePoints} puan`,
      `Sektör etkisi: ${formatMultiplier(pricing.sectorMultiplier)}`,
      `İş büyüklüğü: ${formatMultiplier(pricing.scaleMultiplier)}`,
      `Başlangıç hızı: ${formatMultiplier(pricing.urgencyMultiplier)}`,
      `Puan başı bedel: ${formatCurrency(pricing.unitPrice)}`,
    ];

    let note = `${noteParts.join(' • ')}. Ara hesap ${formatCurrency(pricing.subtotalBeforeDiscount)} oldu.`;

    if (pricing.discountAmount > 0) {
      note += ` Paket indirimi olarak ${formatCurrency(pricing.discountAmount)} düşüldü.`;
    }

    if (pricing.minimumApplied) {
      note += ` Minimum başlangıç bedeli olarak ${formatCurrency(pricing.minimumPrice)} baz alındı.`;
    }

    note += ` Son fiyat ${formatCurrency(pricing.finalPrice)} olarak belirlendi.`;
    return note;
  }

  function buildQuoteResult(answers) {
    const pricing = calculateQuickQuote({
      services: answers.service,
      sector: answers.sector,
      scale: answers.scale,
      urgency: answers.urgency,
    });

    const selectedServices = Array.isArray(answers.service) ? answers.service : [];
    const deliverables = selectedServices
      .map((serviceKey) => quoteServiceDeliverables[serviceKey])
      .filter(Boolean);

    if (selectedServices.length >= PRICING_CONFIG.bundleDiscount.minServices) {
      deliverables.push('Tek ekip gibi çalışan koordinasyon ve tek raporlama katmanı');
    }

    const reference = `VER-${new Date().toISOString().slice(2, 10).replace(/-/g, '')}-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
    const rangeText = pricing.discountRate > 0
      ? `%${Math.round(pricing.discountRate * 100)} paket indirimi dahil aylık başlangıç hizmet bedeli.`
      : 'Seçilen kapsam için aylık başlangıç hizmet bedeli.';

    return {
      packageName: pricing.packageName,
      monthly: pricing.finalPrice,
      reference,
      rangeText: pricing.minimumApplied ? `${rangeText} Minimum teklif koruması uygulandı.` : rangeText,
      whyThisPrice: buildWhyThisPriceText(pricing),
      pricingNote: buildQuotePricingNote(pricing),
      serviceLabels: getOptionTexts(quoteSteps[0], answers.service),
      sectorLabel: getOptionText(quoteSteps[1], answers.sector),
      scaleLabel: getOptionText(quoteSteps[2], answers.scale),
      goalLabel: getOptionText(quoteSteps[3], answers.goal),
      urgencyLabel: getOptionText(quoteSteps[4], answers.urgency),
      contactLabel: getOptionText(quoteSteps[5], answers.contactMode),
      contactMode: answers.contactMode,
      deliverables,
      breakdown: [
        { label: 'Hizmet toplamı', value: `${pricing.basePoints} puan` },
        { label: 'Sektör etkisi', value: formatMultiplier(pricing.sectorMultiplier) },
        { label: 'İş büyüklüğü etkisi', value: formatMultiplier(pricing.scaleMultiplier) },
        { label: 'Başlangıç hızı etkisi', value: formatMultiplier(pricing.urgencyMultiplier) },
        { label: 'Puan başı bedel', value: formatCurrency(pricing.unitPrice) },
        { label: 'Ara hesap', value: formatCurrency(pricing.subtotalBeforeDiscount) },
        ...(pricing.discountAmount > 0 ? [{
          label: `Paket indirimi (%${Math.round(pricing.discountRate * 100)})`,
          value: `-${formatCurrency(pricing.discountAmount)}`,
        }] : []),
        ...(pricing.minimumApplied ? [{
          label: 'Minimum başlangıç bedeli',
          value: formatCurrency(pricing.minimumPrice),
        }] : []),
        { label: 'Son aylık teklif', value: formatCurrency(pricing.finalPrice) },
      ],
    };
  }

  function renderQuoteResult() {
    const result = quoteState.result;
    if (!result) {
      return;
    }

    createQuoteProgress();
    doc.querySelectorAll('.quote-progress-dot').forEach((dot) => dot.classList.add('done'));
    doc.getElementById('quoteStepTag').textContent = 'Teklif Hazır';
    doc.getElementById('quoteQuestion').textContent = 'Ön teklifiniz oluşturuldu.';
    doc.getElementById('quoteHelper').textContent = 'Kapsam özetini inceleyin, uygunsa ön onay verip görüşme özetini açın.';
    doc.getElementById('quoteOptions').innerHTML = '';
    doc.getElementById('quoteStepActions').innerHTML = '';
    doc.getElementById('quotePackageName').textContent = result.packageName;
    doc.getElementById('quotePrice').innerHTML = `${formatCurrency(result.monthly)} <small>/ aylık</small>`;
    doc.getElementById('quoteRange').textContent = result.rangeText;
    doc.getElementById('quoteReadiness').textContent = result.whyThisPrice;
    doc.getElementById('quoteAiNote').textContent = result.pricingNote;
    doc.getElementById('quoteReference').textContent = `Referans kodu: ${result.reference}`;
    doc.getElementById('quoteSummaryCard').classList.add('active');
    doc.getElementById('quoteApprovalBox').classList.add('active');

    const breakdown = doc.getElementById('quoteBreakdown');
    breakdown.innerHTML = '';
    result.breakdown.forEach((item) => {
      const row = doc.createElement('li');
      row.innerHTML = `<span>${item.label}</span><strong>${item.value}</strong>`;
      breakdown.appendChild(row);
    });

    const deliverables = doc.getElementById('quoteDeliverables');
    deliverables.innerHTML = '';
    result.deliverables.forEach((item) => {
      const row = doc.createElement('li');
      row.textContent = item;
      deliverables.appendChild(row);
    });

    pushQuoteMessage('bot', `${result.packageName} hazır. Tahmini aylık başlangıç fiyatı ${formatCurrency(result.monthly)} seviyesinde. Hazırsanız görüşme özetini WhatsApp'ta açabilirsiniz.`);
    root.localStorage.setItem('veridia-latest-quote', JSON.stringify({ answers: quoteState.answers, result }));
  }

  function restartQuoteFlow() {
    const chat = doc.getElementById('quoteChat');
    quoteState.stepIndex = 0;
    quoteState.answers = { service: [] };
    quoteState.result = null;
    quoteState.approved = false;

    if (chat) {
      chat.innerHTML = '<div class="chat-bubble bot">Ön brief yeniden hazır. Yeni kombinasyonu seçin, kapsamı ve tahmini hizmet bedelini tekrar netleştireyim.</div>';
    }

    renderQuoteStep();
  }

  function buildWhatsAppUrl(text) {
    if (typeof root.buildVeridiaWhatsAppUrl === 'function') {
      return root.buildVeridiaWhatsAppUrl(text);
    }

    const cleanPhone = whatsappPhone.replace(/\D/g, '');
    if (/^\d{10,15}$/.test(cleanPhone)) {
      return `https://wa.me/${cleanPhone}?text=${encodeURIComponent(text)}`;
    }

    return `https://wa.me/?text=${encodeURIComponent(text)}`;
  }

  function approveQuote() {
    if (!quoteState.result) {
      return;
    }

    quoteState.approved = true;
    const result = quoteState.result;
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
    ].join('\n');

    pushQuoteMessage('user', 'Teklifi ön onayladım, ekip görüşmesi için hazırım.');
    pushQuoteMessage('bot', `Harika. ${result.reference} referans koduyla görüşme özeti hazırlandı.`);
    root.open(buildWhatsAppUrl(message), '_blank', 'noopener');
  }

  renderQuoteStep();
  pushQuoteMessage('bot', quoteSteps[0].question);

  function selectSector(sectorId, trigger) {
    doc.querySelectorAll('.sector-btn').forEach((button) => {
      button.classList.remove('active');
      button.setAttribute('aria-pressed', 'false');
    });

    doc.querySelectorAll('.sector-panel').forEach((panel) => panel.classList.remove('active'));
    trigger.classList.add('active');
    trigger.setAttribute('aria-pressed', 'true');
    doc.getElementById(`sector-${sectorId}`)?.classList.add('active');
  }

  const serviceDialog = doc.getElementById('serviceDialog');
  const serviceDialogClose = doc.getElementById('serviceDialogClose');
  const serviceDialogCta = doc.getElementById('serviceDialogCta');
  let lastServiceTrigger = null;

  function renderServiceDetail(serviceId) {
    const service = serviceDetails[serviceId];
    if (!service) {
      return false;
    }

    doc.getElementById('serviceDialogKicker').textContent = service.kicker;
    doc.getElementById('serviceDialogClient').textContent = `${service.number} / ${service.code}`;
    doc.getElementById('serviceDialogTitle').textContent = service.title;
    doc.getElementById('serviceDialogSummary').textContent = service.summary;
    doc.getElementById('serviceDialogStory').textContent = service.story;
    doc.getElementById('serviceDialogNext').textContent = service.next;
    doc.getElementById('serviceDialogGradient').style.background = service.gradient;
    serviceDialogCta.textContent = `${service.title} İçin Teklif Al`;

    const pills = doc.getElementById('serviceDialogPills');
    pills.innerHTML = '';
    service.pills.forEach((item) => {
      const pill = doc.createElement('span');
      pill.className = 'portfolio-pill';
      pill.textContent = item;
      pills.appendChild(pill);
    });

    const stats = doc.getElementById('serviceDialogStats');
    stats.innerHTML = '';
    service.stats.forEach((item) => {
      const block = doc.createElement('div');
      block.className = 'portfolio-side-stat';
      block.innerHTML = `<div class="portfolio-side-label">${item.label}</div><div class="portfolio-side-value">${item.value}</div><div class="portfolio-side-note">${item.note}</div>`;
      stats.appendChild(block);
    });

    const deliverables = doc.getElementById('serviceDialogDeliverables');
    deliverables.innerHTML = '';
    service.deliverables.forEach((item) => {
      const row = doc.createElement('li');
      row.textContent = item;
      deliverables.appendChild(row);
    });

    const gallery = doc.getElementById('serviceDialogGallery');
    gallery.innerHTML = '';
    service.gallery.forEach((item) => {
      const cell = doc.createElement('div');
      cell.className = 'portfolio-gallery-cell';
      cell.innerHTML = `<strong>${item.title}</strong><span>${item.copy}</span>`;
      gallery.appendChild(cell);
    });

    return true;
  }

  function openServiceDialog(serviceId, trigger) {
    if (!serviceDialog || !serviceDialogClose || !renderServiceDetail(serviceId)) {
      return;
    }

    lastServiceTrigger = trigger || doc.querySelector(`.service-card[data-service="${serviceId}"]`);
    if (typeof serviceDialog.showModal === 'function') {
      if (!serviceDialog.open) {
        serviceDialog.showModal();
      }
    } else {
      serviceDialog.setAttribute('open', '');
    }

    doc.body.style.overflow = 'hidden';
    serviceDialogClose.focus();
  }

  function closeServiceDialog() {
    if (!serviceDialog) {
      return;
    }

    if (typeof serviceDialog.close === 'function' && serviceDialog.open) {
      serviceDialog.close();
    } else {
      serviceDialog.removeAttribute('open');
    }

    doc.body.style.overflow = '';
    lastServiceTrigger?.focus();
  }

  doc.querySelectorAll('.service-card[data-service]').forEach((card) => {
    card.addEventListener('click', () => openServiceDialog(card.dataset.service, card));
    card.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openServiceDialog(card.dataset.service, card);
      }
    });
  });

  doc.querySelectorAll('[data-service-trigger]').forEach((button) => {
    button.addEventListener('click', () => openServiceDialog(button.dataset.serviceTrigger, button));
  });

  serviceDialogClose?.addEventListener('click', closeServiceDialog);
  serviceDialog?.addEventListener('click', (event) => {
    const shell = serviceDialog.querySelector('.service-dialog-shell');
    if (shell && !shell.contains(event.target)) {
      closeServiceDialog();
    }
  });
  serviceDialog?.addEventListener('cancel', (event) => {
    event.preventDefault();
    closeServiceDialog();
  });
  serviceDialogCta?.addEventListener('click', closeServiceDialog);

  doc.querySelectorAll('.filter-btn').forEach((button) => {
    button.addEventListener('click', () => {
      doc.querySelectorAll('.filter-btn').forEach((item) => item.classList.remove('active'));
      button.classList.add('active');
      const filter = button.dataset.filter;
      doc.querySelectorAll('.portfolio-card').forEach((card) => {
        card.classList.toggle('hidden', filter !== 'all' && card.dataset.category !== filter);
      });
    });
  });

  const portfolioDialog = doc.getElementById('portfolioDialog');
  const portfolioDialogClose = doc.getElementById('portfolioDialogClose');
  const portfolioDialogCta = doc.getElementById('portfolioDialogCta');
  let lastPortfolioTrigger = null;

  function renderPortfolioProject(projectId) {
    const project = portfolioProjects[projectId];
    if (!project) {
      return false;
    }

    doc.getElementById('portfolioDialogKicker').textContent = project.kicker;
    doc.getElementById('portfolioDialogClient').textContent = project.client;
    doc.getElementById('portfolioDialogTitle').textContent = project.title;
    doc.getElementById('portfolioDialogSummary').textContent = project.summary;
    doc.getElementById('portfolioDialogStory').textContent = project.story;
    doc.getElementById('portfolioDialogNext').textContent = project.next;
    doc.getElementById('portfolioDialogGradient').style.background = project.gradient;

    const pills = doc.getElementById('portfolioDialogPills');
    pills.innerHTML = '';
    project.pills.forEach((item) => {
      const pill = doc.createElement('span');
      pill.className = 'portfolio-pill';
      pill.textContent = item;
      pills.appendChild(pill);
    });

    const stats = doc.getElementById('portfolioDialogStats');
    stats.innerHTML = '';
    project.stats.forEach((item) => {
      const block = doc.createElement('div');
      block.className = 'portfolio-side-stat';
      block.innerHTML = `<div class="portfolio-side-label">${item.label}</div><div class="portfolio-side-value">${item.value}</div><div class="portfolio-side-note">${item.note}</div>`;
      stats.appendChild(block);
    });

    const metrics = doc.getElementById('portfolioDialogMetrics');
    metrics.innerHTML = '';
    (portfolioProjectMetrics[projectId] || defaultPortfolioMetrics || []).forEach((item) => {
      const metric = doc.createElement('div');
      metric.className = 'metric';
      metric.innerHTML = `<span class="metric-value">${item.value}</span><span class="metric-label">${item.label}</span>`;
      metrics.appendChild(metric);
    });

    const deliverables = doc.getElementById('portfolioDialogDeliverables');
    deliverables.innerHTML = '';
    project.deliverables.forEach((item) => {
      const row = doc.createElement('li');
      row.textContent = item;
      deliverables.appendChild(row);
    });

    const gallery = doc.getElementById('portfolioDialogGallery');
    gallery.innerHTML = '';
    project.gallery.forEach((item) => {
      const cell = doc.createElement('div');
      cell.className = 'portfolio-gallery-cell';
      cell.innerHTML = `<strong>${item.title}</strong><span>${item.copy}</span>`;
      gallery.appendChild(cell);
    });

    return true;
  }

  function openPortfolioDialog(projectId, trigger) {
    if (!portfolioDialog || !portfolioDialogClose || !renderPortfolioProject(projectId)) {
      return;
    }

    lastPortfolioTrigger = trigger || doc.querySelector(`.portfolio-card[data-project="${projectId}"]`);
    if (typeof portfolioDialog.showModal === 'function') {
      if (!portfolioDialog.open) {
        portfolioDialog.showModal();
      }
    } else {
      portfolioDialog.setAttribute('open', '');
    }

    doc.body.style.overflow = 'hidden';
    portfolioDialogClose.focus();
  }

  function closePortfolioDialog() {
    if (!portfolioDialog) {
      return;
    }

    if (typeof portfolioDialog.close === 'function' && portfolioDialog.open) {
      portfolioDialog.close();
    } else {
      portfolioDialog.removeAttribute('open');
    }

    doc.body.style.overflow = '';
    lastPortfolioTrigger?.focus();
  }

  doc.querySelectorAll('.portfolio-card[data-project]').forEach((card) => {
    card.addEventListener('click', () => openPortfolioDialog(card.dataset.project, card));
    card.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openPortfolioDialog(card.dataset.project, card);
      }
    });
  });

  portfolioDialogClose?.addEventListener('click', closePortfolioDialog);
  portfolioDialog?.addEventListener('click', (event) => {
    const shell = portfolioDialog.querySelector('.portfolio-dialog-shell');
    if (shell && !shell.contains(event.target)) {
      closePortfolioDialog();
    }
  });
  portfolioDialog?.addEventListener('cancel', (event) => {
    event.preventDefault();
    closePortfolioDialog();
  });
  portfolioDialogCta?.addEventListener('click', closePortfolioDialog);

  const baBox = doc.getElementById('baBox');
  const baAfter = doc.getElementById('baAfter');
  const baLine = doc.getElementById('baLine');
  let dragging = false;
  let demoDone = false;

  function setBeforeAfterPosition(clientX) {
    if (!baBox || !baAfter || !baLine) {
      return;
    }

    const rect = baBox.getBoundingClientRect();
    const percent = Math.max(4, Math.min(96, ((clientX - rect.left) / rect.width) * 100));
    baLine.style.left = `${percent}%`;
    baAfter.style.clipPath = `inset(0 ${100 - percent}% 0 0)`;
  }

  if (baBox && baAfter && baLine) {
    baBox.addEventListener('mousedown', (event) => {
      dragging = true;
      setBeforeAfterPosition(event.clientX);
    });
    baBox.addEventListener('touchstart', (event) => {
      dragging = true;
      setBeforeAfterPosition(event.touches[0].clientX);
    }, { passive: true });
    doc.addEventListener('mouseup', () => { dragging = false; });
    doc.addEventListener('touchend', () => { dragging = false; });
    doc.addEventListener('mousemove', (event) => {
      if (dragging) {
        setBeforeAfterPosition(event.clientX);
      }
    });
    doc.addEventListener('touchmove', (event) => {
      if (dragging) {
        setBeforeAfterPosition(event.touches[0].clientX);
      }
    }, { passive: true });

    if (!prefersReducedMotion) {
      const beforeAfterObserver = new IntersectionObserver((entries) => {
        if (entries[0]?.isIntersecting && !demoDone) {
          demoDone = true;
          let tick = 0;
          const interval = root.setInterval(() => {
            tick += 1;
            const percent = 50 + Math.sin(tick * 0.075) * 40;
            const rect = baBox.getBoundingClientRect();
            setBeforeAfterPosition(rect.left + (rect.width * percent) / 100);
            if (tick > 84) {
              root.clearInterval(interval);
            }
          }, 30);
        }
      }, { threshold: 0.6 });

      beforeAfterObserver.observe(baBox);
    }
  }

  const aboutDeck = doc.getElementById('aboutDeck');
  const aboutCards = aboutDeck ? aboutDeck.querySelectorAll('.about-card') : [];

  if (aboutDeck && aboutCards.length > 0) {
    const totalCards = aboutCards.length;
    aboutDeck.addEventListener('click', () => {
      const topCard = aboutDeck.querySelector('.about-card[data-index="0"]');
      if (!topCard) {
        return;
      }

      topCard.classList.add('exit');
      root.setTimeout(() => {
        topCard.classList.remove('exit');
        aboutCards.forEach((card) => {
          const index = Number(card.getAttribute('data-index') || 0);
          const nextIndex = (index - 1 + totalCards) % totalCards;
          card.setAttribute('data-index', String(nextIndex));
        });
      }, 400);
    });
  }

  const contactForm = doc.getElementById('contactForm');
  const contactFormMessage = doc.getElementById('contactFormMessage');

  function setContactFormMessage(type, text) {
    if (!contactFormMessage) {
      return;
    }

    contactFormMessage.className = 'form-message';
    contactFormMessage.textContent = text;
    if (type) {
      contactFormMessage.classList.add(type);
    }
  }

  if (contactForm) {
    contactForm.addEventListener('submit', async (event) => {
      event.preventDefault();

      const submitButton = contactForm.querySelector('.btn-submit');
      const action = contactForm.getAttribute('action') || '';

      if (action.includes('FORM_ID_BURAYA')) {
        setContactFormMessage('error', "Form kurulumu henüz tamamlanmadı. Lütfen Formspree form ID'sini ekleyin.");
        return;
      }

      submitButton?.setAttribute('disabled', 'disabled');
      setContactFormMessage('', '');

      try {
        const response = await root.fetch(action, {
          method: 'POST',
          headers: {
            Accept: 'application/json',
          },
          body: new root.FormData(contactForm),
        });

        if (!response.ok) {
          throw new Error('Formspree request failed');
        }

        contactForm.reset();
        setContactFormMessage('success', 'Teşekkürler. Mesajınız bize ulaştı, en kısa sürede size dönüş yapacağız.');
      } catch (error) {
        setContactFormMessage('error', 'Mesaj gönderilirken bir sorun oluştu. Lütfen tekrar deneyin veya WhatsApp üzerinden bize ulaşın.');
      } finally {
        submitButton?.removeAttribute('disabled');
      }
    });
  }

  doc.querySelectorAll('[data-sector]').forEach((button) => {
    button.addEventListener('click', () => selectSector(button.dataset.sector, button));
  });

  doc.querySelector('[data-quote-approve]')?.addEventListener('click', approveQuote);
  doc.querySelector('[data-quote-restart]')?.addEventListener('click', restartQuoteFlow);
})(typeof window !== 'undefined' ? window : globalThis);
