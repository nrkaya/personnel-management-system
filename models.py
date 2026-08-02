from datetime import datetime
from database import db

class Kullanici(db.Model):
    """User account model with RBAC role."""
    __tablename__ = 'kullanicilar'
    
    id = db.Column(db.Integer, primary_key=True)
    kullanici_adi = db.Column(db.String(80), unique=True, nullable=False, index=True)
    sifre_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='IK', index=True)
    ad_soyad = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    aktif_mi = db.Column(db.Boolean, default=True, nullable=False)
    olusturulma_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    son_giris_tarihi = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Kullanici {self.kullanici_adi} ({self.rol})>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'kullanici_adi': self.kullanici_adi,
            'rol': self.rol,
            'ad_soyad': self.ad_soyad,
            'email': self.email,
            'aktif_mi': self.aktif_mi,
            'olusturulma_tarihi': self.olusturulma_tarihi.strftime('%Y-%m-%d %H:%M:%S') if self.olusturulma_tarihi else None
        }

class Personel(db.Model):
    """Personnel entity model."""
    __tablename__ = 'personeller'
    
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False, index=True)
    soyad = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=True, index=True)
    departman = db.Column(db.String(100), nullable=True, index=True)
    pozisyon = db.Column(db.String(100), nullable=True, index=True)
    telefon = db.Column(db.String(30), nullable=True)
    maas = db.Column(db.Float, default=0.0, nullable=False)
    ise_giris_tarihi = db.Column(db.Date, nullable=True)
    dogum_tarihi = db.Column(db.Date, nullable=True)
    avatar_path = db.Column(db.String(255), default='default.png', nullable=False)
    ek_bilgi = db.Column(db.Text, nullable=True)
    aktif_mi = db.Column(db.Boolean, default=True, nullable=False, index=True)
    olusturulma_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    guncellenme_tarihi = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    izinler = db.relationship('Izin', backref='personel', cascade='all, delete-orphan', lazy=True)

    @property
    def tam_ad(self):
        return f"{self.ad} {self.soyad}"

    def to_dict(self, include_salary=False):
        data = {
            'id': self.id,
            'ad': self.ad,
            'soyad': self.soyad,
            'tam_ad': self.tam_ad,
            'email': self.email,
            'departman': self.departman,
            'pozisyon': self.pozisyon,
            'telefon': self.telefon,
            'ise_giris_tarihi': self.ise_giris_tarihi.strftime('%Y-%m-%d') if self.ise_giris_tarihi else None,
            'dogum_tarihi': self.dogum_tarihi.strftime('%Y-%m-%d') if self.dogum_tarihi else None,
            'avatar_path': self.avatar_path,
            'ek_bilgi': self.ek_bilgi,
            'aktif_mi': self.aktif_mi,
            'olusturulma_tarihi': self.olusturulma_tarihi.strftime('%Y-%m-%d %H:%M:%S') if self.olusturulma_tarihi else None
        }
        if include_salary:
            data['maas'] = self.maas
        return data

class Izin(db.Model):
    """Leave request model."""
    __tablename__ = 'izinler'
    
    id = db.Column(db.Integer, primary_key=True)
    personel_id = db.Column(db.Integer, db.ForeignKey('personeller.id', ondelete='CASCADE'), nullable=False, index=True)
    baslangic = db.Column(db.Date, nullable=False)
    bitis = db.Column(db.Date, nullable=False)
    tur = db.Column(db.String(50), nullable=False, default='Yıllık İzin')
    durum = db.Column(db.String(30), nullable=False, default='Onaylandı')
    kullanici_adi = db.Column(db.String(80), nullable=True)
    eklenme_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    aciklama = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'personel_id': self.personel_id,
            'personel_ad_soyad': self.personel.tam_ad if self.personel else None,
            'baslangic': self.baslangic.strftime('%Y-%m-%d') if self.baslangic else None,
            'bitis': self.bitis.strftime('%Y-%m-%d') if self.bitis else None,
            'tur': self.tur,
            'durum': self.durum,
            'kullanici_adi': self.kullanici_adi,
            'eklenme_tarihi': self.eklenme_tarihi.strftime('%Y-%m-%d %H:%M:%S') if self.eklenme_tarihi else None,
            'aciklama': self.aciklama
        }

class Log(db.Model):
    """Audit log model."""
    __tablename__ = 'loglar'
    
    id = db.Column(db.Integer, primary_key=True)
    kullanici_adi = db.Column(db.String(80), nullable=False, index=True)
    tarih_saat = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    islem_tipi = db.Column(db.String(50), nullable=False, index=True)
    detay = db.Column(db.Text, nullable=True)
    ip_adresi = db.Column(db.String(45), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'kullanici_adi': self.kullanici_adi,
            'tarih_saat': self.tarih_saat.strftime('%Y-%m-%d %H:%M:%S') if self.tarih_saat else None,
            'islem_tipi': self.islem_tipi,
            'detay': self.detay,
            'ip_adresi': self.ip_adresi
        }

class LoginAttempt(db.Model):
    """Brute force tracking model."""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    kullanici_adi = db.Column(db.String(80), nullable=False, index=True)
    ip_adresi = db.Column(db.String(45), nullable=True, index=True)
    deneme_sayisi = db.Column(db.Integer, default=1, nullable=False)
    son_deneme = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    kilitli_mi = db.Column(db.Boolean, default=False, nullable=False)
    kilit_bitis = db.Column(db.DateTime, nullable=True)
