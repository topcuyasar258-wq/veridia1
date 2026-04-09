const test = require('node:test');
const assert = require('node:assert/strict');

const {
  calculateQuickQuote,
  roundPrice,
  formatTryCurrency,
} = require('../assets/quote-pricing.js');

test('calculates a baseline quote from the configured formula', () => {
  const quote = calculateQuickQuote({
    services: ['branding'],
    sector: 'standard',
    scale: 'medium',
    urgency: 'planning',
  });

  assert.equal(quote.basePoints, 25);
  assert.equal(quote.subtotalBeforeDiscount, 25000);
  assert.equal(quote.discountRate, 0);
  assert.equal(quote.finalPrice, 25000);
});

test('applies the 15% bundle discount when three or more services are selected', () => {
  const quote = calculateQuickQuote({
    services: ['branding', 'social', 'content'],
    sector: 'standard',
    scale: 'medium',
    urgency: 'planning',
  });

  assert.equal(quote.basePoints, 95);
  assert.equal(quote.subtotalBeforeDiscount, 95000);
  assert.equal(quote.discountRate, 0.15);
  assert.equal(quote.discountAmount, 14250);
  assert.equal(quote.priceAfterDiscount, 80750);
  assert.equal(quote.finalPrice, 81000);
});

test('respects the minimum price after discount when the unit price is lowered', () => {
  const quote = calculateQuickQuote(
    {
      services: ['influencer'],
      sector: 'standard',
      scale: 'small',
      urgency: 'planning',
    },
    {
      unitPrice: 500,
    }
  );

  assert.equal(quote.subtotalBeforeDiscount, 8000);
  assert.equal(quote.minimumApplied, true);
  assert.equal(quote.finalPrice, 15000);
});

test('rounds smaller quotes up to the next clean 500 TL step', () => {
  assert.equal(roundPrice(34200), 34500);
});

test('formats Turkish lira values without decimals', () => {
  assert.equal(formatTryCurrency(34500), '₺34.500');
});
