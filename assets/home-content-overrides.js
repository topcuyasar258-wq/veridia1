(function (window) {
  const serviceDetails = {
    "marka-stratejisi": {
      number: "01",
      code: "WEB FLOW",
      kicker: "Dönüşüm Odaklı Yüzey",
      title: "Web Tasarım",
      summary: "Kurumsal web sitesi ve landing page yapısını yalnızca estetik için değil, daha fazla teklif ve başvuru üretmek için kurguluyoruz.",
      story: "Web tasarım tarafında mesele sadece güzel görünen bir arayüz değil; ilk ekranda ne söylediğiniz, hangi güven sinyallerini gösterdiğiniz ve kullanıcıyı hangi aksiyona taşıdığınızdır. Bu nedenle mesaj, CTA ve sayfa akışını aynı karar sisteminde ele alıyoruz.",
      pills: ["Kurumsal Site", "Landing Page", "CTA Kurgusu", "Mobil Deneyim"],
      stats: [
        { label: "Odak", value: "Dönüşüm", note: "Web sitesi yalnızca vitrin değil, teklif ve başvuru toplayan bir yapı haline gelir." },
        { label: "Çıktı", value: "Net", note: "Hero mesajı, güven blokları ve form akışı aynı hedefe bağlanır." },
        { label: "Tempo", value: "2-4 Hafta", note: "Kapsama göre hızlı kurulum veya revizyon sprintiyle ilerler." }
      ],
      deliverables: [
        "Ana sayfa, hizmet sayfaları ve teklif akışı kurgusu",
        "Hero mesajı, güven blokları ve CTA hiyerarşisi",
        "Mobil kullanım ve form başlatma akışı önerileri",
        "SEO ve reklam trafiğine uygun landing page mantığı"
      ],
      gallery: [
        { title: "Ana Sayfa", copy: "İlk ekranda ne yaptığınız ve neden tercih edilmeniz gerektiği netleşir." },
        { title: "CTA Akışı", copy: "WhatsApp, form ve teklif alanları kullanıcıyı yormadan görünür hale gelir." },
        { title: "Güven Katmanı", copy: "Referans, süreç ve teslim mantığı karar vermeyi kolaylaştırır." }
      ],
      next: "Web tasarım tarafı doğru kurulduğunda SEO, reklam ve sosyal medya trafiği aynı yüzeyde daha verimli çalışır.",
      gradient: "linear-gradient(135deg, rgba(96,176,255,0.88), rgba(61,26,74,0.92))"
    },
    "sosyal-medya": {
      number: "02",
      code: "SEO MAP",
      kicker: "Google Görünürlüğü",
      title: "SEO Danışmanlığı",
      summary: "Teknik altyapı, sayfa dili ve arama niyetini aynı çatı altında düzenleyerek Google'da daha doğru sorgularda görünmenizi sağlıyoruz.",
      story: "SEO tarafında yalnızca anahtar kelime listesi vermiyoruz. Teknik yapı, indekslenme mantığı, başlıklar, iç linkleme ve hizmet sayfalarının arama niyetine uyumu birlikte ele alındığında görünürlük daha sürdürülebilir hale geliyor.",
      pills: ["Teknik SEO", "İç SEO", "Hizmet Sayfaları", "İç Linkleme"],
      stats: [
        { label: "Odak", value: "Görünürlük", note: "Site, gerçekten müşteri getirebilecek aramalarda daha görünür hale gelir." },
        { label: "Yapı", value: "Bütünsel", note: "Teknik SEO, sayfa dili ve içerik kümeleri birlikte ele alınır." },
        { label: "Tempo", value: "Aşamalı", note: "Quick win fırsatları öne alınır, sonrasında düzenli iyileştirme yapılır." }
      ],
      deliverables: [
        "Teknik SEO kontrolü ve öncelik listesi",
        "Başlık, meta ve H1 uyum önerileri",
        "Hizmet sayfası ve blog cluster planı",
        "Google görünürlüğü için uygulanabilir yol haritası"
      ],
      gallery: [
        { title: "Teknik Tespit", copy: "Görünürlüğü sessizce düşüren teknik sorunlar görünür hale gelir." },
        { title: "Sayfa Dili", copy: "Başlık, açıklama ve içerik dili arama niyetine daha iyi oturur." },
        { title: "Cluster Yapısı", copy: "Blog ile hizmet sayfaları aynı otorite akışında çalışır." }
      ],
      next: "SEO danışmanlığı doğru uygulandığında hem organik trafik artar hem de hizmet sayfalarının dönüşüm kalitesi yükselir.",
      gradient: "linear-gradient(135deg, rgba(92,214,185,0.84), rgba(18,20,24,0.95))"
    },
    "reklam-kampanyalari": {
      number: "03",
      code: "ADS INTENT",
      kicker: "Arama Niyeti ve Talep",
      title: "Google Ads Yönetimi",
      summary: "Google Ads kampanyalarını anahtar kelime, reklam metni ve açılış sayfası uyumuyla birlikte kurgulayarak daha nitelikli başvuru topluyoruz.",
      story: "Sadece kampanya açıp sonucu beklemiyoruz. Arama niyetini katmanlara ayırıyor, gereksiz sorguları temizliyor, reklam metinlerini teklif cümlesiyle hizalıyor ve landing page tarafını aynı doğrultuda düzenliyoruz.",
      pills: ["Search Ads", "Anahtar Kelime", "Landing Page", "Dönüşüm Takibi"],
      stats: [
        { label: "Odak", value: "Lead", note: "Tıklama hacmi yerine daha nitelikli form ve başvuru kalitesi merkeze alınır." },
        { label: "Test", value: "Sürekli", note: "Reklam metni, teklif açısı ve sorgu eşleşmeleri düzenli optimize edilir." },
        { label: "Kontrol", value: "Canlı", note: "Bütçe ve performans sinyalleri düzenli okunur, kör harcama engellenir." }
      ],
      deliverables: [
        "Arama niyetine göre kampanya ve anahtar kelime yapısı",
        "Reklam metni, teklif açısı ve CTA planı",
        "Landing page mesaj uyumu önerileri",
        "Haftalık optimizasyon ve bütçe raporlaması"
      ],
      gallery: [
        { title: "Search Yapısı", copy: "Arama terimleri niyet seviyesine göre daha temiz katmanlara ayrılır." },
        { title: "Reklam Metni", copy: "Başlık ve açıklamalar teklif cümlesiyle daha net hizalanır." },
        { title: "Sayfa Uyumu", copy: "Reklam sözü ile sayfa deneyimi arasındaki kopukluk kapatılır." }
      ],
      next: "Google Ads tarafı en iyi sonucu, net bir teklif ve güçlü bir açılış sayfasıyla birlikte çalıştığında verir.",
      gradient: "linear-gradient(135deg, rgba(216,171,83,0.88), rgba(28,28,30,0.94))"
    },
    "icerik-uretimi": {
      number: "04",
      code: "SOCIAL LOOP",
      kicker: "İçerik ve Topluluk",
      title: "Sosyal Medya Yönetimi",
      summary: "Sosyal medyayı sadece paylaşım takvimi olarak değil, güven oluşturan, hatırlanan ve teklif akışını besleyen bir sistem olarak yönetiyoruz.",
      story: "Burada amaç yalnızca gönderi paylaşmak değil; markanın akış içinde tanınır hale gelmesini sağlamak. İçerik planı, topluluk yönetimi, yorum ve DM tonu ile aylık performans okumalarını aynı editoryal sistemde topluyoruz.",
      pills: ["İçerik Planı", "Yayın Takvimi", "Topluluk Yönetimi", "Raporlama"],
      stats: [
        { label: "Ritim", value: "Sürekli", note: "Marka kampanya dönemi dışında da düzenli ve güven veren şekilde görünür kalır." },
        { label: "Format", value: "Çoklu", note: "Reels, carousel, story ve sabit gönderiler aynı sistemde planlanır." },
        { label: "Takip", value: "Aylık", note: "Neyin çalıştığı okunur ve sonraki ayın içerik planı buna göre şekillenir." }
      ],
      deliverables: [
        "Aylık içerik planı ve yayın takvimi",
        "Platform bazlı format önerileri",
        "Yorum, DM ve topluluk tonu",
        "Performans raporu ve sonraki ay optimizasyonları"
      ],
      gallery: [
        { title: "İçerik Akışı", copy: "Ne zaman, ne paylaşılacağı ve hangi mesajın öne çıkacağı netleşir." },
        { title: "Topluluk", copy: "Yorum ve DM tarafı marka tonuyla daha tutarlı hale gelir." },
        { title: "Marka Hafızası", copy: "Tekrarlayan ama sıkıcı olmayan bir görünürlük sistemi kurulur." }
      ],
      next: "Sosyal medya yönetimi düzenli çalıştığında reklam kreatifleri ve marka güveni de aynı anda güçlenir.",
      gradient: "linear-gradient(135deg, rgba(197,106,132,0.9), rgba(61,26,74,0.92))"
    },
    "halkla-iliskiler": {
      number: "05",
      code: "BRAND KIT",
      kicker: "Marka Görünümü",
      title: "Kurumsal Kimlik",
      summary: "Logo, renk, tipografi ve sunum dilini bir araya getirerek markanızı daha güven veren ve daha tutarlı bir görünüme taşıyoruz.",
      story: "Kurumsal kimlik tarafında hedef yalnızca estetik bir görünüm değil; markanın dijitalde ve basılı yüzeylerde daha net algılanmasını sağlamaktır. Logo sistemi, renk dili, tipografi ve temel kullanım kuralları aynı marka mantığında toplanır.",
      pills: ["Logo Sistemi", "Renk Dili", "Tipografi", "Kullanım Rehberi"],
      stats: [
        { label: "Odak", value: "Güven", note: "Marka ilk bakışta daha düzenli ve profesyonel görünür." },
        { label: "Çıktı", value: "Net", note: "Sunum, sosyal medya ve teklif dosyaları aynı kimlikte birleşir." },
        { label: "Tempo", value: "2-3 Hafta", note: "Kapsama göre hızlı bir kimlik iyileştirme süreci uygulanır." }
      ],
      deliverables: [
        "Logo ailesi, renk sistemi ve tipografi yönü",
        "Temel marka kullanım kuralları",
        "Sunum, sosyal medya ve teklif dosyası görünümü",
        "Ton of voice ve görsel tutarlılık önerileri"
      ],
      gallery: [
        { title: "Logo Ailesi", copy: "Ana imza, ikincil logo ve temel kullanım varyasyonları netleşir." },
        { title: "Sunum Dili", copy: "Teklif dosyaları ve kurumsal sunumlar daha güçlü görünür." },
        { title: "Dijital Tutarlılık", copy: "Site, sosyal medya ve basılı işler aynı hissi vermeye başlar." }
      ],
      next: "Kurumsal kimlik doğru kurulduğunda web sitesi ve reklam dili de çok daha güven verici görünür.",
      gradient: "linear-gradient(135deg, rgba(158,132,255,0.88), rgba(28,28,30,0.94))"
    },
    "influencer-pazarlama": {
      number: "06",
      code: "SHOP FLOW",
      kicker: "Satış Odaklı Mağaza",
      title: "E-Ticaret Sitesi",
      summary: "Ürün, kategori, sepet ve ödeme akışını sadeleştirerek ziyaretçiyi daha hızlı satın almaya yaklaştıran e-ticaret yapıları kuruyoruz.",
      story: "E-ticaret tarafında mesele sadece ürün listelemek değil; kullanıcıyı daha az eforla doğru ürüne, sepet aşamasına ve ödeme ekranına taşımaktır. Kategori yapısı, ürün sayfası dili ve güven blokları aynı akışta düşünülür.",
      pills: ["Kategori Yapısı", "Ürün Sayfası", "Sepet Akışı", "Checkout"],
      stats: [
        { label: "Odak", value: "Satış", note: "Mağaza yapısı kullanıcıyı daha hızlı sepete ve ödemeye yaklaştırır." },
        { label: "Zemin", value: "Mobil", note: "Mobil alışveriş deneyimi ve güven alanları önceliklendirilir." },
        { label: "Model", value: "Dönüşüm", note: "Kampanya ve reklam trafiğine daha uygun mağaza akışı kurulur." }
      ],
      deliverables: [
        "Kategori ve ürün sayfası yapısı",
        "Sepet ve ödeme akışı iyileştirmeleri",
        "Mobil alışveriş deneyimi ve güven blokları",
        "Kampanya ve reklam trafiğine uygun mağaza kurgusu"
      ],
      gallery: [
        { title: "Kategori Hiyerarşisi", copy: "Kullanıcının ürünü daha hızlı bulacağı sade bir yapı kurulur." },
        { title: "Ürün Sayfası", copy: "Ürün açıklaması, görseller ve güven unsurları karar vermeyi kolaylaştırır." },
        { title: "Sepet Akışı", copy: "Terk etmeyi azaltan daha temiz bir ödeme süreci tasarlanır." }
      ],
      next: "E-ticaret sitesi doğru kurulduğunda reklam trafiği ve organik trafik aynı mağazada daha yüksek dönüşüme döner.",
      gradient: "linear-gradient(135deg, rgba(255,134,112,0.9), rgba(107,26,42,0.9))"
    }
  };

  const quoteSteps = [
    {
      key: "service",
      tag: "Adım 1 / 6",
      question: "Hangi hizmet için teklif oluşturuyoruz?",
      multiple: true,
      helper: "En yakın ihtiyacınızı seçin; sistem kalan detayları buna göre adapte eder.",
      options: [
        { value: "strategy", label: "Web Tasarım", detail: "Kurumsal site ve landing page kurgusu." },
        { value: "social", label: "SEO Danışmanlığı", detail: "Teknik ve içerik SEO odaklı görünürlük planı." },
        { value: "performance", label: "Google Ads Yönetimi", detail: "Lead ve satış odaklı reklam yönetimi." },
        { value: "content", label: "Sosyal Medya Yönetimi", detail: "İçerik planı ve topluluk yönetimi." },
        ]
    },
    {
      key: "sector",
      tag: "Adım 2 / 6",
      question: "Hangi sektördesiniz?",
      helper: "Her sektörün rekabet yoğunluğu ve edinim maliyeti başlangıç planını etkileyebilir.",
      options: [
        { value: "saas", label: "Teknoloji / SaaS", detail: "B2B ve abonelik odaklı modeller." },
        { value: "ecommerce", label: "E-Ticaret / Perakende", detail: "Ürün satışı ve mağaza yönetimi." },
        { value: "service", label: "Hizmet / Kurumsal", detail: "Danışmanlık, sağlık, eğitim ve profesyonel hizmetler." },
        { value: "lifestyle", label: "Lifestyle / Mekan", detail: "Kafe, restoran, güzellik veya yaşam markaları." }
      ]
    },
    {
      key: "scale",
      tag: "Adım 3 / 6",
      question: "İşletme veya bütçe ölçeğiniz nedir?",
      helper: "Kapsamın derinliği ve operasyonel yük bu ölçeğe göre değişir.",
      options: [
        { value: "early", label: "Erken Aşama / Butik", detail: "Hızlı başlangıç ve temel sistem kurulumu." },
        { value: "growth", label: "Büyüme Odaklı / Orta", detail: "Düzenli optimizasyon ve hacim artışı." },
        { value: "enterprise", label: "Kurumsal / Büyük", detail: "Daha yoğun yönetim ve çoklu akış ihtiyacı." }
      ]
    },
    {
      key: "goal",
      tag: "Adım 4 / 6",
      question: "Öncelikli hedefiniz ne?",
      helper: "Bu alan fiyatı değil, ilk görüşmenin kapsam ve öncelik çerçevesini belirler.",
      options: [
        { value: "lead", label: "Lead / Başvuru", detail: "Form, DM, randevu veya teklif talebi akışı." },
        { value: "sales", label: "Direkt Satış", detail: "E-ticaret, kampanya dönüşümü ve ROAS takibi." },
        { value: "awareness", label: "Marka Bilinirliği", detail: "Görünürlük, erişim ve güven oluşturma." },
        { value: "launch", label: "Lansman", detail: "Yeni marka, ürün veya hizmet çıkışı." }
      ]
    },
    {
      key: "urgency",
      tag: "Adım 5 / 6",
      question: "Ne kadar hızlı başlamak istiyorsunuz?",
      helper: "Aciliyet düzeyi, başlangıç sprintinin yoğunluğunu ve teklif katsayısını etkiler.",
      options: [
        { value: "planning", label: "Planlama Aşaması", detail: "Henüz karşılaştırma ve bütçe netleştirme safhası." },
        { value: "week", label: "Bu Hafta İçinde", detail: "Standart hızlı başlangıç temposu." },
        { value: "immediate", label: "48 Saat İçinde", detail: "Hızlı onboarding ve öncelikli planlama gerekir." }
      ]
    },
    {
      key: "contactMode",
      tag: "Adım 6 / 6",
      question: "İlk görüşmede bizi nasıl konumlayalım?",
      helper: "Bu seçim fiyatı değiştirmez; ilk mesaj özetinin tonunu düzenler.",
      options: [
        { value: "decision", label: "Karar Verici", detail: "Teklif ve başlangıç takvimiyle direkt ilerleyelim." },
        { value: "team", label: "Takımla Değerlendiriyorum", detail: "Karşılaştırmalı ve daha açıklayıcı özet verelim." },
        { value: "collecting", label: "Fiyat Topluyorum", detail: "Kısa, net ve kapsam odaklı ilerleyelim." },
        { value: "custom", label: "Özel Senaryo", detail: "Daha esnek kapsam ve özel çözüm vurgusu yapalım." }
      ]
    }
  ];

  if (window.serviceDetails) {
    Object.assign(window.serviceDetails, serviceDetails);
  } else {
    window.serviceDetails = serviceDetails;
  }

  window.quoteSteps = quoteSteps;

  if (window.VeridiaQuotePricing && typeof window.VeridiaQuotePricing.calculateQuickQuote === "function") {
    const pricingApi = window.VeridiaQuotePricing;
    const serviceLabelOverrides = {
      branding: "Web Tasarım",
      strategy: "Web Tasarım",
      social: "SEO Danışmanlığı",
      performance: "Google Ads Yönetimi",
      content: "Sosyal Medya Yönetimi",
    };

    const originalCalculateQuickQuote = pricingApi.calculateQuickQuote.bind(pricingApi);

    pricingApi.calculateQuickQuote = function calculateQuickQuoteWithOverrides(input, overrides = {}) {
      const mergedLabels = {
        ...(overrides.labels || {}),
        services: {
          ...((overrides.labels && overrides.labels.services) || {}),
          ...serviceLabelOverrides,
        },
      };

      return originalCalculateQuickQuote(input, {
        ...overrides,
        labels: mergedLabels,
      });
    };
  }
})(window);
