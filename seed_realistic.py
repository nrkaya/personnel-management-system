"""Gerçekçi kurumsal personel verileri oluşturur — 300 kişi."""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from app import create_app
from database import db
from models import Personel

# ── Türk ad/soyad havuzu ──
ERKEK_ADLAR = [
    "Ahmet", "Mehmet", "Ali", "Mustafa", "Hasan", "Hüseyin", "İbrahim",
    "Murat", "Emre", "Burak", "Kemal", "Selim", "Oğuz", "Cem", "Deniz",
    "Barış", "Serkan", "Tolga", "Volkan", "Kaan", "Enes", "Yusuf",
    "Ömer", "Furkan", "Eren", "Onur", "Tuncay", "Erhan", "Gökhan",
    "Levent", "Fikret", "Recep", "Süleyman", "Tarık", "Uğur", "Yasin",
    "Orhan", "Halil", "Cengiz", "Bülent", "Ercan", "Soner", "Osman",
    "Kadir", "Ferhat", "Mert", "Polat", "Utku", "Sinan", "Harun",
]

KADIN_ADLAR = [
    "Ayşe", "Fatma", "Zeynep", "Elif", "Merve", "Esra", "Seda",
    "Büşra", "Gizem", "Derya", "Canan", "Pelin", "Tuğçe", "İrem",
    "Hülya", "Neslihan", "Sibel", "Özlem", "Dilek", "Ebru", "Sevgi",
    "Hatice", "Kübra", "Nur", "Leyla", "Aslı", "Gamze", "Serap",
    "Yasemin", "Emine", "Rabia", "Burcu", "Oya", "Selin", "Rüya",
    "Gül", "Melek", "Nilgün", "Şule", "Vildan", "Dilan", "Berna",
    "Ceyda", "Feride", "Havva", "Meltem", "Tülay", "Müge", "Serpil",
]

SOYADLAR = [
    "Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Yıldırım",
    "Öztürk", "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan",
    "Çetin", "Kara", "Koç", "Kurt", "Özkan", "Şimşek", "Polat",
    "Erdoğan", "Yavuz", "Can", "Acar", "Şen", "Aksoy", "Yalçın",
    "Güler", "Aktaş", "Tekin", "Tunç", "Korkmaz", "Karaca", "Sarı",
    "Güneş", "Kaplan", "Bozkurt", "Taş", "Duman", "Uysal", "Peker",
    "Toprak", "Başaran", "Erdem", "Çakır", "Uçar", "Bulut", "Koçak",
    "Türk", "Ateş", "Karagöz", "Bayrak", "Soylu", "Ergün", "Işık",
]

# ── Kurumsal birim yapısı ──
# Her birim: (birim_adı, [(ünvan, adet, maaş_min, maaş_max), ...])
KURUM_YAPISI = [
    ("Genel Müdürlük", [
        ("Genel Müdür", 1, 95000, 120000),
        ("Genel Müdür Yardımcısı", 2, 75000, 90000),
        ("Özel Kalem Müdürü", 1, 45000, 55000),
        ("Genel Sekreter", 1, 42000, 52000),
        ("Yönetici Asistanı", 2, 28000, 35000),
    ]),
    ("İnsan Kaynakları Birimi", [
        ("İK Müdürü", 1, 55000, 68000),
        ("İK Müdür Yardımcısı", 1, 42000, 52000),
        ("İK Uzmanı", 4, 32000, 42000),
        ("İşe Alım Sorumlusu", 2, 30000, 38000),
        ("Bordro Uzmanı", 2, 32000, 40000),
        ("Eğitim Koordinatörü", 1, 30000, 38000),
        ("İK Stajyeri", 2, 18000, 22000),
    ]),
    ("Bilgi İşlem Müdürlüğü", [
        ("Bilgi İşlem Müdürü", 1, 60000, 75000),
        ("Bilgi İşlem Müdür Yardımcısı", 1, 48000, 58000),
        ("Sistem Yöneticisi", 3, 38000, 50000),
        ("Ağ ve Güvenlik Uzmanı", 2, 40000, 52000),
        ("Yazılım Geliştirici", 5, 38000, 55000),
        ("Kıdemli Yazılım Geliştirici", 2, 50000, 65000),
        ("Veritabanı Yöneticisi", 2, 40000, 52000),
        ("Teknik Destek Uzmanı", 4, 28000, 36000),
        ("Siber Güvenlik Uzmanı", 2, 42000, 55000),
        ("Veri Analisti", 2, 35000, 45000),
        ("IT Stajyeri", 2, 18000, 22000),
    ]),
    ("Mali İşler Müdürlüğü", [
        ("Mali İşler Müdürü", 1, 55000, 68000),
        ("Mali İşler Müdür Yardımcısı", 1, 42000, 52000),
        ("Muhasebe Uzmanı", 4, 32000, 42000),
        ("Bütçe ve Raporlama Uzmanı", 2, 34000, 44000),
        ("Finans Analisti", 2, 35000, 45000),
        ("Tahsilat Sorumlusu", 2, 28000, 35000),
        ("Muhasebe Memuru", 3, 25000, 32000),
        ("Mali İşler Stajyeri", 1, 18000, 22000),
    ]),
    ("Hukuk Müşavirliği", [
        ("Hukuk Müşaviri", 1, 58000, 72000),
        ("Avukat", 3, 40000, 55000),
        ("Hukuk Danışmanı", 2, 38000, 48000),
        ("İcra ve Takip Uzmanı", 1, 32000, 40000),
        ("Hukuk Büro Memuru", 2, 25000, 32000),
    ]),
    ("Teknik Hizmetler Müdürlüğü", [
        ("Teknik Hizmetler Müdürü", 1, 52000, 65000),
        ("Teknik Müdür Yardımcısı", 1, 40000, 50000),
        ("Makine Mühendisi", 3, 36000, 48000),
        ("Elektrik Mühendisi", 3, 36000, 48000),
        ("İnşaat Mühendisi", 2, 36000, 48000),
        ("Teknik Ressam", 2, 28000, 35000),
        ("Bakım-Onarım Teknisyeni", 5, 26000, 34000),
        ("Elektrik Teknisyeni", 3, 26000, 34000),
        ("Tesisat Teknisyeni", 2, 25000, 32000),
        ("Teknik Şef", 2, 32000, 42000),
    ]),
    ("Satınalma ve Lojistik Müdürlüğü", [
        ("Satınalma Müdürü", 1, 50000, 62000),
        ("Satınalma Müdür Yardımcısı", 1, 38000, 48000),
        ("Satınalma Uzmanı", 3, 30000, 40000),
        ("Lojistik Sorumlusu", 2, 30000, 38000),
        ("Depo Sorumlusu", 2, 26000, 34000),
        ("Ambar Memuru", 3, 23000, 30000),
        ("Taşıma ve Sevkiyat Görevlisi", 3, 22000, 28000),
    ]),
    ("İdari İşler Müdürlüğü", [
        ("İdari İşler Müdürü", 1, 48000, 60000),
        ("İdari İşler Müdür Yardımcısı", 1, 38000, 48000),
        ("İdari İşler Uzmanı", 3, 28000, 36000),
        ("Evrak ve Arşiv Sorumlusu", 2, 24000, 30000),
        ("Santral Görevlisi", 2, 22000, 28000),
        ("Güvenlik Amiri", 1, 28000, 35000),
        ("Güvenlik Görevlisi", 6, 22000, 28000),
        ("Temizlik Hizmetlisi", 4, 20000, 24000),
        ("Şoför", 3, 23000, 29000),
    ]),
    ("Planlama ve Strateji Birimi", [
        ("Strateji Geliştirme Müdürü", 1, 55000, 68000),
        ("Proje Yöneticisi", 3, 40000, 52000),
        ("Kurumsal Planlama Uzmanı", 2, 35000, 45000),
        ("İstatistik Analisti", 2, 32000, 42000),
        ("Performans Değerlendirme Uzmanı", 2, 30000, 40000),
        ("Kalite Yönetim Uzmanı", 2, 32000, 42000),
    ]),
    ("Basın ve Halkla İlişkiler Birimi", [
        ("Basın ve Halkla İlişkiler Müdürü", 1, 48000, 60000),
        ("Kurumsal İletişim Uzmanı", 2, 32000, 42000),
        ("Sosyal Medya Uzmanı", 2, 28000, 38000),
        ("Grafik Tasarımcı", 2, 30000, 40000),
        ("İçerik Editörü", 2, 28000, 36000),
        ("Halkla İlişkiler Sorumlusu", 2, 28000, 36000),
        ("Fotoğrafçı / Kameraman", 1, 26000, 34000),
    ]),
    ("Denetim ve Teftiş Kurulu", [
        ("Başmüfettiş", 1, 58000, 72000),
        ("Müfettiş", 3, 42000, 55000),
        ("İç Denetçi", 3, 40000, 52000),
        ("Denetim Büro Memuru", 2, 25000, 32000),
    ]),
    ("Destek Hizmetleri Birimi", [
        ("Destek Hizmetleri Müdürü", 1, 45000, 56000),
        ("Yemekhane Sorumlusu", 1, 26000, 32000),
        ("Aşçıbaşı", 1, 25000, 30000),
        ("Aşçı", 3, 22000, 27000),
        ("Bahçıvan", 2, 20000, 25000),
        ("Hizmetli", 5, 20000, 24000),
    ]),
]


def generate_phone():
    operator = random.choice(["530", "531", "532", "533", "534", "535",
                               "536", "537", "538", "539", "540", "541",
                               "542", "543", "544", "545", "546", "505",
                               "506", "507", "551", "552", "553", "554"])
    return f"0{operator} {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}"


def generate_email(ad, soyad, domain="kayapts.com.tr"):
    ad_clean = ad.lower().replace("ı", "i").replace("ö", "o").replace("ü", "u") \
                  .replace("ş", "s").replace("ç", "c").replace("ğ", "g") \
                  .replace("İ", "i").replace("â", "a")
    soyad_clean = soyad.lower().replace("ı", "i").replace("ö", "o").replace("ü", "u") \
                       .replace("ş", "s").replace("ç", "c").replace("ğ", "g") \
                       .replace("İ", "i").replace("â", "a")
    suffix = random.randint(1, 99) if random.random() < 0.3 else ""
    return f"{ad_clean}.{soyad_clean}{suffix}@{domain}"


def generate_birth_date(pozisyon):
    """Yaşı pozisyona göre ayarla — müdürler daha yaşlı olur."""
    today = datetime.now()
    if "Müdür" in pozisyon or "Müşavir" in pozisyon or "Başmüfettiş" in pozisyon or "Genel" in pozisyon:
        min_age, max_age = 40, 58
    elif "Yardımcısı" in pozisyon or "Avukat" in pozisyon or "Müfettiş" in pozisyon or "Kıdemli" in pozisyon:
        min_age, max_age = 35, 52
    elif "Uzman" in pozisyon or "Mühendis" in pozisyon or "Sorumlu" in pozisyon or "Şef" in pozisyon:
        min_age, max_age = 28, 45
    elif "Stajyer" in pozisyon:
        min_age, max_age = 20, 25
    else:
        min_age, max_age = 24, 50
    age = random.randint(min_age, max_age)
    birth = today - timedelta(days=age * 365 + random.randint(0, 364))
    return birth.date()


def generate_hire_date(pozisyon):
    """Kıdeme göre işe giriş tarihi."""
    today = datetime.now()
    if "Genel Müdür" == pozisyon:
        min_years, max_years = 8, 20
    elif "Müdür" in pozisyon or "Müşavir" in pozisyon or "Başmüfettiş" in pozisyon:
        min_years, max_years = 5, 18
    elif "Yardımcısı" in pozisyon or "Kıdemli" in pozisyon:
        min_years, max_years = 4, 15
    elif "Stajyer" in pozisyon:
        min_years, max_years = 0, 1
    elif "Uzman" in pozisyon or "Mühendis" in pozisyon:
        min_years, max_years = 1, 10
    else:
        min_years, max_years = 0, 12
    years = random.randint(min_years, max_years)
    hire = today - timedelta(days=years * 365 + random.randint(0, 364))
    return hire.date()


def seed():
    app = create_app('default')
    with app.app_context():
        records = []
        used_emails = set()

        for birim_adi, pozisyonlar in KURUM_YAPISI:
            for pozisyon, adet, maas_min, maas_max in pozisyonlar:
                for _ in range(adet):
                    cinsiyet = random.choice(["E", "K"])
                    ad = random.choice(ERKEK_ADLAR if cinsiyet == "E" else KADIN_ADLAR)
                    soyad = random.choice(SOYADLAR)

                    email = generate_email(ad, soyad)
                    attempt = 0
                    while email in used_emails and attempt < 10:
                        email = generate_email(ad, soyad)
                        attempt += 1
                    used_emails.add(email)

                    maas = Decimal(random.randint(maas_min, maas_max))
                    # Yuvarlama: 500'ün katlarına
                    maas = Decimal(int(maas / 500) * 500)

                    ek_bilgi_parts = [f"{birim_adi} bünyesinde {pozisyon} olarak görev yapmaktadır."]
                    if "Müdür" in pozisyon and "Yardımcısı" not in pozisyon:
                        ek_bilgi_parts.append("Birim yönetimi ve koordinasyondan sorumludur.")
                    elif "Stajyer" in pozisyon:
                        ek_bilgi_parts.append("Üniversite staj programı kapsamında görevlendirilmiştir.")

                    records.append(Personel(
                        ad=ad,
                        soyad=soyad,
                        departman=birim_adi,
                        pozisyon=pozisyon,
                        telefon=generate_phone(),
                        email=email,
                        maas=maas,
                        ise_giris_tarihi=generate_hire_date(pozisyon),
                        dogum_tarihi=generate_birth_date(pozisyon),
                        avatar_path='default.svg',
                        ek_bilgi=" ".join(ek_bilgi_parts),
                        aktif_mi=True,
                    ))

        # Tam 300'e tamamla (yapıdan ~295 civarı çıkıyor)
        while len(records) < 300:
            birim_adi, pozisyonlar_list = random.choice(KURUM_YAPISI)
            pozisyon, _, maas_min, maas_max = random.choice(pozisyonlar_list)
            cinsiyet = random.choice(["E", "K"])
            ad = random.choice(ERKEK_ADLAR if cinsiyet == "E" else KADIN_ADLAR)
            soyad = random.choice(SOYADLAR)
            email = generate_email(ad, soyad)
            while email in used_emails:
                email = generate_email(ad, soyad)
            used_emails.add(email)
            maas = Decimal(int(random.randint(maas_min, maas_max) / 500) * 500)

            records.append(Personel(
                ad=ad,
                soyad=soyad,
                departman=birim_adi,
                pozisyon=pozisyon,
                telefon=generate_phone(),
                email=email,
                maas=maas,
                ise_giris_tarihi=generate_hire_date(pozisyon),
                dogum_tarihi=generate_birth_date(pozisyon),
                avatar_path='default.svg',
                ek_bilgi=f"{birim_adi} bünyesinde {pozisyon} olarak görev yapmaktadır.",
                aktif_mi=True,
            ))

        db.session.add_all(records)
        db.session.commit()

        print(f"[OK] {len(records)} personel kaydi basariyla olusturuldu!")
        print()
        print("Birim dağılımı:")
        for birim_adi, pozisyonlar_list in KURUM_YAPISI:
            count = sum(1 for r in records if r.departman == birim_adi)
            print(f"  {birim_adi}: {count} kişi")


if __name__ == '__main__':
    seed()
