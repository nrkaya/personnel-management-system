"""Deprecated compatibility entry point.

Schema creation is now managed by Alembic.  This file intentionally no longer
drops tables or creates a predictable administrator account.
"""

from app import create_app
from database import db


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.session.execute(db.text('SELECT 1'))
    print("Kullanım: flask --app app:create_app db upgrade")
    print("Ardından: flask --app app:create_app create-admin")
