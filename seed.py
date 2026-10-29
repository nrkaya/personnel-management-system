"""Seed the database with sample personnel data using SQLAlchemy ORM."""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from app import create_app
from database import db
from models import Personel


def generate_fake_data(count=500):
    """Insert sample personnel records via ORM."""
    app = create_app('default')
    with app.app_context():
        adlar = [
            "Ahmet", "Mehmet", "Ayşe", "Fatma", "Ali", "Veli", "Can", "Canan",
            "Deniz", "Derya", "Emre", "Elif", "Gökhan", "Gizem", "Hasan",
            "Hatice", "İbrahim", "İrem", "Kemal", "Kübra", "Levent", "Leyla",
            "Murat", "Merve", "Nihat", "Nur", "Orhan", "Oya", "Polat", "Pelin",
            "Rıza", "Rüya", "Selim", "Seda", "Tarık", "Tuğçe", "Umut", "Utku",
            "Volkan", "Vildan", "Yasin", "Yasemin", "Zafer", "Zehra",
        ]
        soyadlar = [
            "Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Yıldız", "Yıldırım",
            "Öztürk", "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan",
            "Çetin", "Kara", "Koç", "Kurt", "Özkan", "Şimşek", "Polat", "Öz",
            "Erdoğan", "Yavuz", "Can", "Acar", "Şen", "Aksoy", "Yalçın", "Güler",
        ]
        departmanlar = [
            "Bilişim (IT)", "İnsan Kaynakları", "Muhasebe & Finans", "Pazarlama",
            "Satış", "Lojistik", "Üretim", "Yönetim", "Ar-Ge", "Hukuk",
            "Müşteri Hizmetleri",
        ]
        pozisyonlar = {
            "Bilişim (IT)": ["Yazılım Geliştirici", "Sistem Yöneticisi", "Veri Analisti", "Siber Güvenlik Uzmanı", "IT Müdürü"],
            "İnsan Kaynakları": ["İK Uzmanı", "İşe Alım Sorumlusu", "Eğitim Koordinatörü", "İK Müdürü"],
            "Muhasebe & Finans": ["Muhasebeci", "Finansal Analist", "Bordro Uzmanı", "Finans Direktörü"],
            "Pazarlama": ["Dijital Pazarlama Uzmanı", "İçerik Üreticisi", "Grafik Tasarımcı", "Pazarlama Müdürü"],
            "Satış": ["Satış Temsilcisi", "Bölge Sorumlusu", "Müşteri Temsilcisi", "Satış Müdürü"],
            "Lojistik": ["Lojistik Uzmanı", "Depo Sorumlusu", "Operasyon Yöneticisi"],
            "Üretim": ["Üretim Mühendisi", "Kalite Kontrol Uzmanı", "Vardiya Amiri", "Teknisyen"],
            "Yönetim": ["Genel Müdür", "Genel Müdür Yardımcısı", "Proje Yöneticisi", "Asistan"],
            "Ar-Ge": ["Ar-Ge Mühendisi", "Araştırmacı", "Laborant"],
            "Hukuk": ["Avukat", "Hukuk Danışmanı"],
            "Müşteri Hizmetleri": ["Çağrı Merkezi Temsilcisi", "Müşteri Destek Uzmanı"],
        }

        today = datetime.now()
        inserted = 0

        for _ in range(count):
            ad = random.choice(adlar)
            soyad = random.choice(soyadlar)
            departman = random.choice(departmanlar)
            pozisyon = random.choice(pozisyonlar[departman])
            telefon = f"05{random.randint(3, 5)}{random.randint(0, 9)} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"
            maas = Decimal(random.randint(25, 150) * 1000)
            days_ago = random.randint(0, 3650)
            ise_giris_tarihi = (today - timedelta(days=days_ago)).date()
            ek_bilgi = f"{departman} departmanında {pozisyon} olarak görev yapmaktadır."

            p = Personel(
                ad=ad,
                soyad=soyad,
                departman=departman,
                pozisyon=pozisyon,
                telefon=telefon,
                ek_bilgi=ek_bilgi,
                avatar_path='default.svg',
                ise_giris_tarihi=ise_giris_tarihi,
                maas=maas,
                aktif_mi=True,
            )
            db.session.add(p)
            inserted += 1

        db.session.commit()
        print(f"{inserted} kayıt başarıyla oluşturuldu.")


if __name__ == '__main__':
    generate_fake_data()
