(function attachQuotePricing(root, factory) {
  const api = factory();
  root.VeridiaQuotePricing = api;

  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  }
})(typeof window !== 'undefined' ? window : globalThis, function createQuotePricingApi() {
  const PRICING_CONFIG = Object.freeze({
    unitPrice: 1000,
    minimumPrice: 15000,
    serviceBasePoints: Object.freeze({
      branding: 25,
      social: 30,
      performance: 25,
      content: 40,
      influencer: 20,
    }),
    sectorMultipliers: Object.freeze({
      standard: 1.0,
      creative: 1.2,
      tech: 1.3,
      beauty: 1.4,
    }),
    scaleMultipliers: Object.freeze({
      small: 0.8,
      medium: 1.0,
      enterprise: 1.4,
    }),
    urgencyMultipliers: Object.freeze({
      planning: 1.0,
      week: 1.1,
      immediate: 1.25,
    }),
    bundleDiscount: Object.freeze({
      minServices: 3,
      rate: 0.15,
    }),
    rounding: Object.freeze({
      smallIncrement: 500,
      largeIncrement: 1000,
      largeQuoteThreshold: 50000,
    }),
    labels: Object.freeze({
      services: Object.freeze({
        branding: 'Marka Stratejisi',
        social: 'Sosyal Medya Yönetimi',
        performance: 'Reklam Kampanyaları',
        content: 'İçerik Üretimi',
        influencer: 'Influencer Pazarlama',
      }),
      sectors: Object.freeze({
        standard: 'Standart Sektörler',
        creative: 'Kreatif / Moda',
        tech: 'Teknoloji / SaaS',
        beauty: 'Sağlık / Güzellik',
      }),
      scales: Object.freeze({
        small: 'Küçük Ölçekli',
        medium: 'Orta Ölçekli',
        enterprise: 'Büyük / Kurumsal',
      }),
      urgencies: Object.freeze({
        planning: 'Planlama Aşaması',
        week: 'Bu hafta içinde',
        immediate: '48 saat içinde',
      }),
    }),
  });

  function mergeNested(defaultValue, overrideValue) {
    return {
      ...defaultValue,
      ...(overrideValue || {}),
    };
  }

  function createConfig(overrides = {}) {
    return {
      ...PRICING_CONFIG,
      ...overrides,
      serviceBasePoints: mergeNested(PRICING_CONFIG.serviceBasePoints, overrides.serviceBasePoints),
      sectorMultipliers: mergeNested(PRICING_CONFIG.sectorMultipliers, overrides.sectorMultipliers),
      scaleMultipliers: mergeNested(PRICING_CONFIG.scaleMultipliers, overrides.scaleMultipliers),
      urgencyMultipliers: mergeNested(PRICING_CONFIG.urgencyMultipliers, overrides.urgencyMultipliers),
      bundleDiscount: mergeNested(PRICING_CONFIG.bundleDiscount, overrides.bundleDiscount),
      rounding: mergeNested(PRICING_CONFIG.rounding, overrides.rounding),
      labels: {
        ...PRICING_CONFIG.labels,
        ...(overrides.labels || {}),
        services: mergeNested(PRICING_CONFIG.labels.services, overrides.labels && overrides.labels.services),
        sectors: mergeNested(PRICING_CONFIG.labels.sectors, overrides.labels && overrides.labels.sectors),
        scales: mergeNested(PRICING_CONFIG.labels.scales, overrides.labels && overrides.labels.scales),
        urgencies: mergeNested(PRICING_CONFIG.labels.urgencies, overrides.labels && overrides.labels.urgencies),
      },
    };
  }

  function uniqueValues(values) {
    return [...new Set((Array.isArray(values) ? values : []).filter(Boolean))];
  }

  function getLookupValue(lookup, key, label) {
    const value = lookup[key];

    if (value === undefined) {
      throw new Error(`Unknown ${label}: ${key}`);
    }

    return value;
  }

  function roundUpToIncrement(value, increment) {
    if (!Number.isFinite(value) || value <= 0) {
      return 0;
    }

    return Math.ceil(value / increment) * increment;
  }

  function roundPrice(value, rounding = PRICING_CONFIG.rounding) {
    const increment = value >= rounding.largeQuoteThreshold
      ? rounding.largeIncrement
      : rounding.smallIncrement;

    return roundUpToIncrement(value, increment);
  }

  function formatTryCurrency(value) {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      maximumFractionDigits: 0,
    }).format(Number(value || 0));
  }

  function formatMultiplier(value) {
    return `x${Number(value || 0).toFixed(2).replace('.', ',')}`;
  }

  function getPackageName(services, labels) {
    const selectedLabels = services.map((service) => labels[service] || service);

    if (selectedLabels.length === 1) {
      return `${selectedLabels[0]} Paketi`;
    }

    if (selectedLabels.length === 2) {
      return `${selectedLabels.join(' + ')} Kombinasyonu`;
    }

    return 'Entegre Büyüme Paketi';
  }

  function calculateQuickQuote(selection, overrides = {}) {
    const config = createConfig(overrides);
    const services = uniqueValues(selection.services);

    if (!services.length) {
      throw new Error('At least one service must be selected.');
    }

    const sector = selection.sector;
    const scale = selection.scale;
    const urgency = selection.urgency;
    const unitPrice = Number.isFinite(selection.unitPrice) ? selection.unitPrice : config.unitPrice;

    const basePoints = services.reduce((total, service) => {
      return total + getLookupValue(config.serviceBasePoints, service, 'service');
    }, 0);

    const sectorMultiplier = getLookupValue(config.sectorMultipliers, sector, 'sector');
    const scaleMultiplier = getLookupValue(config.scaleMultipliers, scale, 'scale');
    const urgencyMultiplier = getLookupValue(config.urgencyMultipliers, urgency, 'urgency');

    const baseAfterSector = basePoints * sectorMultiplier;
    const baseAfterScale = baseAfterSector * scaleMultiplier;
    const scoreAfterUrgency = baseAfterScale * urgencyMultiplier;
    const subtotalBeforeDiscount = Math.round(scoreAfterUrgency * unitPrice);
    const discountRate = services.length >= config.bundleDiscount.minServices ? config.bundleDiscount.rate : 0;
    const discountAmount = Math.round(subtotalBeforeDiscount * discountRate);
    const priceAfterDiscount = subtotalBeforeDiscount - discountAmount;
    const minimumApplied = priceAfterDiscount < config.minimumPrice;
    const priceBeforeRounding = minimumApplied ? config.minimumPrice : priceAfterDiscount;
    const finalPrice = roundPrice(priceBeforeRounding, config.rounding);
    const roundingIncrement = priceBeforeRounding >= config.rounding.largeQuoteThreshold
      ? config.rounding.largeIncrement
      : config.rounding.smallIncrement;

    return {
      services,
      serviceCount: services.length,
      serviceLabels: services.map((service) => config.labels.services[service] || service),
      sector,
      sectorLabel: config.labels.sectors[sector] || sector,
      scale,
      scaleLabel: config.labels.scales[scale] || scale,
      urgency,
      urgencyLabel: config.labels.urgencies[urgency] || urgency,
      packageName: getPackageName(services, config.labels.services),
      unitPrice,
      basePoints,
      sectorMultiplier,
      scaleMultiplier,
      urgencyMultiplier,
      baseAfterSector,
      baseAfterScale,
      scoreAfterUrgency,
      subtotalBeforeDiscount,
      discountRate,
      discountAmount,
      priceAfterDiscount,
      minimumPrice: config.minimumPrice,
      minimumApplied,
      priceBeforeRounding,
      finalPrice,
      roundingIncrement,
      roundingDifference: finalPrice - priceBeforeRounding,
    };
  }

  function buildWhyThisPriceText(quote) {
    const serviceText = quote.serviceLabels.join(', ');
    const sentences = [
      `Bu fiyat; seçtiğiniz ${serviceText.toLowerCase()} hizmetleri, sektörünüzün zorluk seviyesi, işinizin büyüklüğü ve ne kadar hızlı başlamak istediğiniz dikkate alınarak hesaplandı.`,
    ];

    if (quote.discountRate > 0) {
      sentences.push(`${quote.serviceCount} hizmet seçtiğiniz için otomatik %${Math.round(quote.discountRate * 100)} paket indirimi uygulandı.`);
    }

    if (quote.minimumApplied) {
      sentences.push(`Hesap çıkan tutar çok düşük kaldığı için minimum başlangıç bedeli olan ${formatTryCurrency(quote.minimumPrice)} esas alındı.`);
    }

    if (quote.roundingDifference > 0) {
      sentences.push(`Fiyat, daha temiz ve anlaşılır görünmesi için yuvarlandı.`);
    }

    return sentences.join(' ');
  }

  return {
    PRICING_CONFIG,
    calculateQuickQuote,
    buildWhyThisPriceText,
    formatMultiplier,
    formatTryCurrency,
    getPackageName,
    roundPrice,
  };
});
