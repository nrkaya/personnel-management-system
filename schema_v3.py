"""Deprecated v3 schema migration.

Database migrations are now managed by Alembic / Flask-Migrate.

Usage:
    flask --app app:create_app db upgrade
"""

import sys


def upgrade_v3():
    print("UYARI: Bu betik artık kullanılmamaktadır.")
    print("Veritabanı migration'ları Alembic ile yönetilmektedir.")
    print("")
    print("Kullanım:")
    print("  flask --app app:create_app db upgrade")
    sys.exit(1)


if __name__ == '__main__':
    upgrade_v3()
