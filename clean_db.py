"""Clean all data from the database using SQLAlchemy ORM.

After running this script, create a new admin account:
    flask --app app:create_app create-admin
"""

import os
from app import create_app
from database import db
from models import Personel, Izin, Log, LoginAttempt
from utils import log_action


def clean_database():
    """Remove all personnel, leave, and log records."""
    app = create_app('default')
    with app.app_context():
        Izin.query.delete()
        Personel.query.delete()
        Log.query.delete()
        LoginAttempt.query.delete()
        db.session.commit()

        # Clear uploaded avatar images except defaults
        upload_dir = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_dir):
            for f in os.listdir(upload_dir):
                if f not in ('default.png', 'default.svg'):
                    file_path = os.path.join(upload_dir, f)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"Dosya silinemedi {f}: {e}")

        print("Veritabanı ve yüklenen dosyalar başarıyla temizlendi.")
        print("Yeni admin oluşturmak için:")
        print("  flask --app app:create_app create-admin")


if __name__ == '__main__':
    clean_database()
