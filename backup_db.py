"""Database backup utility for KAYA PTS.

Creates timestamped SQLite database backups in the backups/ directory.
Designed for personnel data preservation — even deleted personnel records
remain accessible through backups.

Usage:
    python backup_db.py
    python backup_db.py --output custom_backup.db
"""

import os
import shutil
import sys
from datetime import datetime


BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')


def backup_database(output_path=None):
    """Create a timestamped copy of the SQLite database."""
    if not os.path.exists(DATABASE_PATH):
        print(f"HATA: Veritabanı dosyası bulunamadı: {DATABASE_PATH}")
        sys.exit(1)

    os.makedirs(BACKUP_DIR, exist_ok=True)

    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(BACKUP_DIR, f'kaya_pts_backup_{timestamp}.db')

    try:
        shutil.copy2(DATABASE_PATH, output_path)
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Yedekleme başarılı: {output_path}")
        print(f"Dosya boyutu: {size_mb:.2f} MB")
    except OSError as e:
        print(f"HATA: Yedekleme başarısız: {e}")
        sys.exit(1)


def list_backups():
    """List all existing backups."""
    if not os.path.exists(BACKUP_DIR):
        print("Henüz yedek bulunmuyor.")
        return

    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')],
        reverse=True,
    )
    if not backups:
        print("Henüz yedek bulunmuyor.")
        return

    print(f"Toplam {len(backups)} yedek:")
    for name in backups:
        path = os.path.join(BACKUP_DIR, name)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  {name}  ({size_mb:.2f} MB)")


if __name__ == '__main__':
    if '--list' in sys.argv:
        list_backups()
    else:
        custom_output = None
        if '--output' in sys.argv:
            idx = sys.argv.index('--output')
            if idx + 1 < len(sys.argv):
                custom_output = sys.argv[idx + 1]
        backup_database(custom_output)
