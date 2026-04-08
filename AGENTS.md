# AGENTS.md

Bu repo statik bir landing sayfasi ile onu servis eden yerel bir Python sunucusundan olusur. Sunucu sadece statik dosya servis etmez; ayni zamanda Instagram on analizini yapan API endpoint'lerini ve snapshot kaydini da yonetir.

## Temel dosyalar

- `server.py`: `ThreadingHTTPServer` tabanli yerel sunucu. Statik dosyalari servis eder, `POST /api/analyze-instagram` endpoint'i ile Apify uzerinden analiz yapar, profil gorsel proxy'si sunar ve snapshot verilerini SQLite'a yazar.
- `index.html`: Bilerek cok kisa tutulmus giris noktasi. Kullaniciyi `asdfadsf.html` dosyasina yonlendirir.
- `asdfadsf.html`: Asil landing sayfasi. Ajans tanitim icerigi, tema/mobil menu davranislari ve sayfa icine gomulu Instagram analiz bolumu burada.
- `assets/`: Landing sayfasinda kullanilan logo ve gorsel dosyalari.
- `.env`: `APIFY_TOKEN` basta olmak uzere calisma ayarlari burada tutulur.
- `.env.example`: Ortam degiskenleri icin kopyalanacak ornek dosya.
- `analysis_snapshots.sqlite3`: Analiz gecmisi veritabani. Kaynak kod degil, uygulama verisi.
- `README.md`: Kurulum ve calistirma notlari.

## API ve veri akisi

- Frontend framework kullanmaz; `asdfadsf.html` icindeki vanilla JS analiz istegini dogrudan `/api/analyze-instagram` adresine atar.
- Sunucu Apify sonucunu normalize eder, metrikleri hesaplar, ozet/insight uretir ve uygun durumlarda `analysis_snapshots.sqlite3` icine snapshot yazar.
- Profil resmi gosterimi icin `/api/profile-image` proxy route'u vardir. Bu davranisi degistirirken izin verilen host kontrolunu koru.

## Calistirma

- `.env.example` dosyasini `.env` olarak kopyala.
- Gerekli ise `APIFY_TOKEN` degerini gir.
- `python3 server.py` komutunu calistir.
- Tarayicida `http://127.0.0.1:8000/index.html` adresini ac.

## Dikkat edilmesi gerekenler

- `index.html` bilerek yonlendirme yapiyor; landing akisini degistirmiyorsan bunu bozma.
- Frontend statik dosya olarak servis ediliyor; framework varmis gibi davranma.
- `asdfadsf.html` buyuk bir tek dosya; degisiklik yaparken mevcut section id'lerini, inline script baglantilarini ve analiz alaninin DOM id'lerini koru.
- `.env` icindeki gizli degerleri commit etme.
- `analysis_snapshots.sqlite3` dosyasini kaynak kod gibi ele alma; migrate etmiyorsan veya veri ihtiyaci yoksa degistirme.
- Apify actor ayarlari `.env` uzerinden degisebilir; mevcut degerleri kod icinden varsayma.
- Bir ayrinti repoda net degilse uydurma bilgi ekleme; kisa bir not dus veya belirsizligi oldugu gibi belirt.

## Kontrol

- Degisiklikten sonra `python3 server.py` hatasiz aciliyor mu bak.
- Arayuz degistiyse `index.html` yonlendirmesini ve `asdfadsf.html` akisini tarayicida kontrol et.
- Analiz akisina dokunulduysa en azindan `/api/analyze-instagram` istemcisinin dogru endpoint'e gittigini ve form/durum alanlarinin bozulmadigini kontrol et.
- Apify tarafina dokunulduysa canli test icin gercek `APIFY_TOKEN` gerekir; token yoksa bunu not et, test uydurma.
