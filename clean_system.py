import os
import glob
from app import create_app
from database import db
from models import Kullanici, Personel, Izin, Log, LoginAttempt
from werkzeug.security import generate_password_hash

def reset_and_clean():
    """Reset all tables and clear uploaded avatars, preserving default admin."""
    app = create_app('default')
    with app.app_context():
        Izin.query.delete()
        Personel.query.delete()
        Log.query.delete()
        LoginAttempt.query.delete()
        Kullanici.query.delete()
        db.session.commit()
        
        admin_user = Kullanici(
            kullanici_adi='admin',
            sifre_hash=generate_password_hash('Admin123!'),
            rol='Admin',
            ad_soyad='System Administrator',
            email='admin@kayapts.com',
            aktif_mi=True
        )
        db.session.add(admin_user)
        db.session.commit()
        
        upload_folder = app.config['UPLOAD_FOLDER']
        for file_path in glob.glob(os.path.join(upload_folder, '*')):
            if not file_path.endswith('default.png'):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

if __name__ == '__main__':
    reset_and_clean()
