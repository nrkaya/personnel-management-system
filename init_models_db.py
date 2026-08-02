from app import create_app
from database import db
from models import Kullanici, Personel, Izin, Log, LoginAttempt
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Recreate tables
    db.drop_all()
    db.create_all()
    
    # Default admin user
    admin = Kullanici(
        kullanici_adi='admin',
        sifre_hash=generate_password_hash('Admin123!'),
        rol='Admin',
        ad_soyad='Sistem Yöneticisi',
        email='admin@kayapts.com',
        aktif_mi=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Database initialized successfully with SQLAlchemy models.")
