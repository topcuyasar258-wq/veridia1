(function initBlogIndex(root) {
  const topicPills = Array.from(document.querySelectorAll('.topic-pill[data-category]'));
  const blogCards = Array.from(document.querySelectorAll('.blog-card[data-category]'));
  const blogCardHideTimers = new WeakMap();

  if (!topicPills.length || !blogCards.length) {
    return;
  }

  function hideBlogCard(card) {
    if (card.dataset.visibility === 'hidden') {
      return;
    }

    root.clearTimeout(blogCardHideTimers.get(card));
    card.dataset.visibility = 'hiding';
    card.classList.add('is-filtered-out');
    const hideTimer = root.setTimeout(() => {
      card.style.display = 'none';
      card.dataset.visibility = 'hidden';
    }, 320);
    blogCardHideTimers.set(card, hideTimer);
  }

  function showBlogCard(card) {
    if (card.dataset.visibility === 'visible') {
      return;
    }

    root.clearTimeout(blogCardHideTimers.get(card));
    card.style.display = 'flex';
    card.dataset.visibility = 'visible';

    root.requestAnimationFrame(() => {
      card.classList.remove('is-filtered-out');
    });
  }

  function filterBlogCards(category) {
    topicPills.forEach((pill) => {
      pill.classList.toggle('is-active', pill.dataset.category === category);
    });

    blogCards.forEach((card) => {
      const shouldShow = category === 'all' || card.dataset.category === category;
      if (shouldShow) {
        showBlogCard(card);
      } else {
        hideBlogCard(card);
      }
    });
  }

  topicPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      filterBlogCards(pill.dataset.category || 'all');
    });
  });

  blogCards.forEach((card) => {
    card.dataset.visibility = 'visible';
  });

  filterBlogCards('all');
})(typeof window !== 'undefined' ? window : globalThis);
