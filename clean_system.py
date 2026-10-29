"""Reset all data tables and clear uploaded avatars.

After running this script, create a new admin account:
    flask --app app:create_app create-admin
"""

import os
import glob
from app import create_app
from database import db
from models import Kullanici, Personel, Izin, Log, LoginAttempt


def reset_and_clean():
    """Reset all tables and clear uploaded avatars.

    Does NOT create a default admin.  Use the CLI command instead:
        flask --app app:create_app create-admin
    """
    app = create_app('default')
    with app.app_context():
        Izin.query.delete()
        Personel.query.delete()
        Log.query.delete()
        LoginAttempt.query.delete()
        Kullanici.query.delete()
        db.session.commit()

        upload_folder = app.config['UPLOAD_FOLDER']
        for file_path in glob.glob(os.path.join(upload_folder, '*')):
            basename = os.path.basename(file_path)
            if basename not in ('default.png', 'default.svg'):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

        print("Tüm veriler temizlendi.")
        print("Yeni admin oluşturmak için:")
        print("  flask --app app:create_app create-admin")


if __name__ == '__main__':
    reset_and_clean()
