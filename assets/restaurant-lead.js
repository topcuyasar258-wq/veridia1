!function (root) {
  const document = root.document
  const form = document?.getElementById('restaurantLeadForm')
  const message = document?.getElementById('restaurantLeadFormMessage')
  if (!(form && message)) return

  function setMessage(type, text) {
    message.className = `form-message ${type}`
    message.textContent = text
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    if (!form.reportValidity()) return

    const submitButton = form.querySelector('button[type="submit"]')
    submitButton?.setAttribute('disabled', 'disabled')
    setMessage('', 'Gönderiliyor...')

    try {
      const fields = Object.fromEntries(new FormData(form).entries())
      const payload = {
        ...fields,
        mesaj: 'Restoran veya kafe dijital pazarlama ön analizi talebi.',
        kaynak: root.location?.pathname || '/kafe-restoran-dijital-pazarlama.html',
      }
      const response = await root.fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.error || 'Form gönderilemedi.')
      form.reset()
      setMessage('success', 'Talebiniz alındı. İlk değerlendirme için sizinle iletişime geçeceğiz.')
    } catch (error) {
      setMessage('error', error.message || 'Form gönderilemedi. Lütfen WhatsApp üzerinden bize yazın.')
    } finally {
      submitButton?.removeAttribute('disabled')
    }
  })
}('undefined' != typeof window ? window : globalThis)
