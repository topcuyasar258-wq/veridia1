;(function () {
  try {
    if (window.localStorage.getItem('veridia-theme') === 'light') {
      document.documentElement.dataset.theme = 'light'
    }
  } catch (_error) {
    // Theme preference is optional; ignore storage failures.
  }
})()
