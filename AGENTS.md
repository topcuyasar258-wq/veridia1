# AGENTS.md

Bu repo statik HTML yuzeyleri ile bunlari servis eden yerel bir Python sunucusundan olusur. Sunucu yalnizca dosya servis etmez; ayni zamanda Instagram on analizini yapan API endpoint'lerini, profil gorsel proxy'sini, rate limit davranisini ve snapshot kaydini da yonetir.

## Temel dosyalar

- `server.py`: `ThreadingHTTPServer` tabanli yerel sunucu. Statik dosyalari servis eder, legacy redirect'leri uygular, `POST /api/analyze-instagram`, `POST /api/contact` ve `/api/profile-image` route'larini yonetir, snapshot verilerini SQLite'a yazar.
- `instagram_utils.py`: Instagram analizi icin metrik ve donusum yardimcilari burada tutulur.
- `index.html`: Ana landing sayfasi. Ajans tanitim icerigi, tema/mobil menu davranislari ve sayfa icine gomulu teklif akisi burada.
- `blog.html`: Blog listeleme yuzeyi.
- `blog/`, `seo/`, `reklam/`, `yazilim/`: Servis ve icerik sayfalari. Bu dizinler dogrudan public olarak servis edilir.
- `automation/`: n8n tabanli otomasyon katmani, workflow JSON'lari, form sayfalari ve ilgili dokumantasyon.
- `assets/`: Sayfalarda kullanilan logo ve gorsel dosyalari.
- `.env` / `.env.example`: `APIFY_TOKEN`, `INSTAGRAM_ANALYSIS_ENABLED`, `HOST`, `ALLOWED_ORIGINS` ve benzeri calisma ayarlari.
- `analysis_snapshots.sqlite3`: Analiz gecmisi veritabani. Kaynak kod degil, uygulama verisi.
- `README.md`: Kurulum, calistirma ve otomasyon notlari.

## API ve veri akisi

- Frontend framework kullanmaz; HTML sayfalardaki vanilla JS akislari tamamen istemci tarafinda calisir.
- Sunucu Apify sonucunu normalize eder, metrikleri hesaplar, ozet/insight uretir ve uygun durumlarda `analysis_snapshots.sqlite3` icine snapshot yazar.
- Profil resmi gosterimi icin `/api/profile-image` proxy route'u vardir. Bu davranisi degistirirken izin verilen host kontrolunu koru.
- `POST /api/contact` akisi `CONTACT_FORWARD_URL` tanimliysa istegi upstream'e iletebilir; bu davranisi degistirirken CORS, body limiti ve hata cevabi yuzeyini bozma.
- `ALLOWED_ORIGINS`, `TRUSTED_PROXY_IPS`, rate limit ve security header davranislari `server.py` icinde aktif olarak uygulanir. Bunlara dokunurken sadece UI degil dagitim senaryosunu da dusun.

## Calistirma

- `.env.example` dosyasini `.env` olarak kopyala.
- Gerekli ise `APIFY_TOKEN` degerini gir.
- Instagram analiz endpoint'ini acmak istiyorsan `INSTAGRAM_ANALYSIS_ENABLED=1` kullan.
- `python3 server.py` komutunu calistir.
- Tarayicida `http://127.0.0.1:8000/` adresini ac.

## Dikkat edilmesi gerekenler

- `/` ana landing rotasidir; `/index.html`, `/asdfadsf.html` ve `/veridia-ajans.html` `/` rotasina yonlenir.
- Repo yalnizca tek sayfadan ibaret degil; `blog/`, `seo/`, `reklam/`, `yazilim/` ve birden fazla root seviye HTML sayfasi public yuzeyin parcasi.
- Frontend statik dosya olarak servis ediliyor; framework varmis gibi davranma.
- `index.html` buyuk bir tek dosya; degisiklik yaparken mevcut section id'lerini ve inline script baglantilarini koru.
- `blog.html` ayri bir giris yuzeyi; landing degisiklikleri blog navigasyonunu veya canonical akisi bozmasin.
- `.env` icindeki gizli degerleri commit etme.
- `analysis_snapshots.sqlite3` dosyasini kaynak kod gibi ele alma; migrate etmiyorsan veya veri ihtiyaci yoksa degistirme.
- Apify actor ayarlari `.env` uzerinden degisebilir; mevcut degerleri kod icinden varsayma.
- `automation/` klasoru ayri bir operasyon yuzeyi; landing veya API degisiklikleri bu form/workflow zincirini etkiliyorsa capraz kontrol yap.
- Bir ayrinti repoda net degilse tahmin etme veya bilgi uydurma.
- Eksik veya dogrulanamayan bir ayrinti gerekiyorsa bunu kisa bir notla belirt; yerini doldurmak icin yeni bilgi uydurma.

## Kontrol

- Degisiklikten sonra `python3 server.py` hatasiz aciliyor mu bak.
- Arayuz degistiyse `/`, `/blog.html` ve ilgili servis sayfasi akisini tarayicida kontrol et.
- Analiz akisina dokunulduysa en azindan `/api/analyze-instagram` istemcisinin dogru endpoint'e gittigini ve form/durum alanlarinin bozulmadigini kontrol et.
- Contact veya proxy akisina dokunulduysa `/api/contact` ve `/api/profile-image` davranisinin hata durumlariyla birlikte bozulmadigini kontrol et.
- Apify tarafina dokunulduysa canli test icin gercek `APIFY_TOKEN` gerekir; token yoksa bunu not et, test uydurma.
