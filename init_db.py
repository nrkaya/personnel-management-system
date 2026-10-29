"""Deprecated legacy initializer.

Database schema is now managed by Alembic migrations.
Admin user creation uses the interactive CLI command.

Usage:
    flask --app app:create_app db upgrade
    flask --app app:create_app create-admin
"""

import sys


def init_db():
    print("UYARI: Bu betik artık kullanılmamaktadır.")
    print("Veritabanı şeması Alembic ile yönetilmektedir.")
    print("")
    print("Kullanım:")
    print("  flask --app app:create_app db upgrade")
    print("  flask --app app:create_app create-admin")
    sys.exit(1)


if __name__ == '__main__':
    init_db()
