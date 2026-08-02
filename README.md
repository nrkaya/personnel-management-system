# 🛡️ KAYA PTS — Enterprise Personel Takip ve Yönetim Sistemi

**KAYA PTS (Kaya Personel Takip Sistemi)**; kurumsal şirketlerin insan kaynakları, izin süreçleri, departman analitiği ve bordro/maaş yönetimini en üst düzey güvenlik, modern cam efektli (Glassmorphism) kullanıcı deneyimi ve modüler mimari ile buluşturan yeni nesil kurumsal bir web platformudur.

---

## 🌟 Öne Çıkan Özellikler

- 🏗️ **Modüler Mimari (Flask Blueprints):** 7 bağımsız iş modülü (`auth`, `dashboard`, `personel`, `izin`, `kullanici`, `logs`, `api`).
- 🔐 **Katmanlı Kurumsal Güvenlik:**
  - **CSRF Koruması:** `Flask-WTF` ile tüm form ve AJAX isteklerinde token doğrulaması.
  - **Brute-Force & Rate Limiting:** 5 hatalı giriş denemesinde hesap ve IP adresi **10 dakika otomatik kilitlenir**.
  - **Şifre Güvenlik Politikası:** En az 8 karakter, büyük/küçük harf ve rakam zorunluluğu.
  - **Güvenli Dosya & Avatar Yükleme:** Yalnızca onaylı MIME-türleri (`image/png`, `image/jpeg`, `image/webp`) ve uzantılar kabul edilir, rastgele UUID ile adlandırılarak sunucu güvenliği sağlanır.
  - **Güvenli Oturumlar (Session Security):** `HttpOnly`, `SameSite=Lax`, `PermanentSessionLifetime` (8 saat).
  - **Denetim Logları (Audit Logging):** Kimin, hangi IP ile hangi saatte ne işlem yaptığı veri tabanında değiştirilemez şekilde saklanır.
- 👥 **4 Kademeli Rol ve Yetkilendirme (RBAC):** `Admin`, `IK`, `Müdür`, `Muhasebe`.
- 📊 **Bento Grid Yönetici Paneli:** Chart.js departman dağılım grafikleri, doğum günü kutlamaları ve yaklaşan izin takip widget'ları.
- ⚡ **Yüksek Performanslı Arayüz:** Sayfa başına 10 personel sayfalama (pagination) ve anlık canlı filtreleme/arama motoru.
- 📑 **Kurumsal Excel Raporlama:** `openpyxl` ile biçimlendirilmiş, renkli başlıklı `.xlsx` dışa aktarımı.
- 🌐 **RESTful API v1:** Harici sistem entegrasyonları için `X-API-KEY` korumalı JSON API servisi.
- 🐳 **DevOps & Docker:** Tek komutla ayağa kalkan `Dockerfile` ve `docker-compose.yml` (PostgreSQL desteğiyle).

---

## 👥 4 Kademeli Rol ve Yetki Matrisi (RBAC)

| Yetki / İşlem | 👑 Admin | 💼 İK (İnsan Kaynakları) | 👔 Müdür | 💰 Muhasebe |
| :--- | :---: | :---: | :---: | :---: |
| **Giriş & Dashboard** | ✅ | ✅ | ✅ | ✅ |
| **Personel Listesini Görme** | ✅ | ✅ | ✅ | ✅ |
| **Personel Ekleme / Düzenleme** | ✅ | ✅ | ❌ | ❌ |
| **Personel Silme & Çöp Kutusu** | ✅ | ✅ | ❌ | ❌ |
| **Maaş Bilgilerini Görme** | ✅ | ✅ | ❌ | ✅ |
| **İzin Onaylama / Reddetme** | ✅ | ✅ | ✅ | ❌ |
| **Excel Raporu İndirme** | ✅ | ✅ | ✅ | ✅ |
| **Kullanıcı & Rol Yönetimi** | ✅ | ❌ | ❌ | ❌ |
| **Sistem Denetim Logları** | ✅ | ❌ | ❌ | ❌ |

---

## 🚀 Kurulum ve Çalıştırma

### Yöntem 1: Yerel Olarak Çalıştırma (Geliştirme Modu - SQLite)

1. **Gereksinimler:** Python 3.10+
2. **Sanal Ortamı Başlatın ve Çalıştırın:**
   ```powershell
   # Proje klasörüne geçin
   cd C:\Users\Muhammed\Desktop\personelsistemi

   # Uygulamayı başlatın
   .\venv\Scripts\python app.py
   ```
3. **Tarayıcıdan Açın:**
   👉 **`http://127.0.0.1:5000`**
4. **Varsayılan Yönetici Girişi:**
   - **Kullanıcı Adı:** `admin`
   - **Şifre:** `Admin123!`

---

### Yöntem 2: Docker & PostgreSQL ile Çalıştırma (Production Modu)

```bash
docker-compose up --build -d
```
> Web uygulaması ve PostgreSQL veritabanı otomatik olarak ayağa kalkar (`http://localhost:5000`).

---

## 🌐 RESTful API v1 Dokümantasyonu

Tüm API uç noktaları `X-API-KEY` başlığı ile korunmaktadır.  
**Varsayılan API Key:** `kaya-pts-enterprise-api-key-2026`

### 1. İstatistikleri Getir
* **GET** `/api/v1/stats`
* **Başlıklar:** `X-API-KEY: kaya-pts-enterprise-api-key-2026`
* **Örnek Yanıt:**
  ```json
  {
    "success": true,
    "data": {
      "toplam_aktif_personel": 45,
      "toplam_kullanici": 4,
      "aktif_izindekiler": 2
    }
  }
  ```

### 2. Personelleri Listele
* **GET** `/api/v1/personeller?sayfa=1&limit=20&ara=Ahmet&departman=Yazılım`
* **Başlıklar:** `X-API-KEY: kaya-pts-enterprise-api-key-2026`

### 3. Yeni Personel Ekle
* **POST** `/api/v1/personel`
* **Body (JSON):**
  ```json
  {
    "ad": "Mehmet",
    "soyad": "Kaya",
    "departman": "Yazılım",
    "pozisyon": "Senior Backend Developer",
    "telefon": "0555 123 4567",
    "email": "mehmet@kayapts.com",
    "maas": 95000
  }
  ```

### 4. Personel Güncelle
* **PUT** `/api/v1/personel/<id>`
* **Body (JSON):** `{"maas": 105000, "pozisyon": "Lead Developer"}`

### 5. Personel Sil (Soft Delete)
* **DELETE** `/api/v1/personel/<id>`

---

## 🧪 Otomatik Testler

Proje bünyesindeki tüm kimlik doğrulama, brute-force kilitlenmesi, şifre politikası, RBAC yetkileri, CRUD, Excel çıktısı ve API testlerini çalıştırmak için:

```powershell
.\venv\Scripts\python -m unittest test_enterprise.py
```
> **Test Sonucu:** `Ran 8 tests -> OK (%100 Başarı)`

---

## 📁 Proje Dosya Yapısı

```
personelsistemi/
├── app.py                  # Application Factory (create_app)
├── config.py               # Development, Production, Testing ayarları
├── database.py             # SQLAlchemy & CSRF Protect instance
├── models.py               # ORM Tabloları (Kullanici, Personel, Izin, Log, LoginAttempt)
├── utils.py                # RBAC decorator, Rate Limit, Dosya/Şifre doğrulama
├── test_enterprise.py      # Otomatik test paketi
├── clean_system.py         # Sistem sıfırlama ve temizlik scripti
├── routes/
│   ├── auth.py             # Giriş, Çıkış, Rate Limit
│   ├── dashboard.py        # Bento Grid, İstatistikler
│   ├── personel.py         # CRUD, Canlı Arama, Sayfalama, Excel
│   ├── izin.py             # İzin onaylama iş akışı
│   ├── kullanici.py        # 4 Kademeli Rol ve Kullanıcı Yönetimi
│   ├── logs.py             # Denetim / Audit Logları
│   └── api.py              # RESTful API v1
├── templates/              # Cam efektli (Glassmorphism) Jinja2 şablonları
├── static/
│   ├── css/style.css       # Kurumsal koyu tema, Bento Grid CSS
│   └── js/main.js          # Canlı arama, Toast bildirimleri
├── Dockerfile              # Production Docker image
├── docker-compose.yml      # PostgreSQL + Web container
├── requirements.txt        # Python kütüphane bağımlılıkları
└── README.md               # Proje dokümantasyonu
```

---
*© 2026 KAYA PTS — Kurumsal Personel Takip Sistemi. Tüm Hakları Saklıdır.*
