"""Database and photo backup utility for KAYA PTS.

Backs up whichever database the application is configured for:
  - SQLite: SQLite's online backup API, safe while the app is running.
  - PostgreSQL: pg_dump in custom format. pg_dump must be installed and at
    least as new as the server's major version.

Personnel photos (uploads/) are personal data that a database dump alone would
not bring back, so they are archived next to each dump.

Usage:
    python backup_db.py                       # back up into backups/
    python backup_db.py --keep 14             # ...and keep only the 14 newest backups
    python backup_db.py --output-dir D:\\yedek
    python backup_db.py --no-uploads          # database only
    python backup_db.py --list

The backup directory can also be set with the BACKUP_DIR environment variable.

Restore:
    SQLite:      stop the app, then copy kaya_pts_<time>.db over database.db
    PostgreSQL:  pg_restore --clean --if-exists --no-owner -d <database URL> kaya_pts_<time>.dump
    Photos:      extract kaya_pts_<time>_uploads.zip into uploads/
"""

import argparse
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BACKUP_DIR = os.environ.get('BACKUP_DIR') or os.path.join(BASE_DIR, 'backups')
PREFIX = 'kaya_pts_'
# kaya_pts_<YYYYmmdd_HHMMSS>.db / .dump / _uploads.zip, plus _uploads.tar.gz
# from the Docker Compose backup service, so both kinds can be listed and pruned.
BACKUP_NAME = re.compile(rf'^{PREFIX}(\d{{8}}_\d{{6}})(\.db|\.dump|_uploads\.zip|_uploads\.tar\.gz)$')


class BackupError(Exception):
    pass


def _backup_sqlite(url, target):
    source_path = url.database
    if not source_path or source_path == ':memory:' or not os.path.isfile(source_path):
        raise BackupError(f'SQLite veritabanı dosyası bulunamadı: {source_path}')
    source = sqlite3.connect(source_path)
    destination = sqlite3.connect(target)
    try:
        # Copies a consistent snapshot even if the app writes meanwhile.
        source.backup(destination)
    finally:
        destination.close()
        source.close()


def _backup_postgres(url, target):
    pg_dump = shutil.which('pg_dump')
    if not pg_dump:
        raise BackupError(
            'pg_dump bulunamadı. PostgreSQL istemci araçlarını kurun (sunucu ile aynı veya '
            'daha yeni ana sürüm) ya da Docker Compose içindeki "backup" servisini kullanın.'
        )
    env = dict(os.environ)
    # The password goes through the environment, not the command line, so it
    # does not show up in process listings.
    if url.password:
        env['PGPASSWORD'] = str(url.password)
    sslmode = url.query.get('sslmode')
    if sslmode:
        env['PGSSLMODE'] = sslmode if isinstance(sslmode, str) else sslmode[0]
    args = [pg_dump, '--format=custom', '--no-owner', f'--file={target}']
    if url.host:
        args.append(f'--host={url.host}')
    if url.port:
        args.append(f'--port={url.port}')
    if url.username:
        args.append(f'--username={url.username}')
    args.append(f'--dbname={url.database}')
    result = subprocess.run(args, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        if os.path.exists(target):
            os.remove(target)
        raise BackupError(f'pg_dump başarısız oldu: {result.stderr.strip()}')


def _archive_uploads(upload_dir, target):
    """Zip every uploaded photo; returns how many files were archived."""
    if not upload_dir or not os.path.isdir(upload_dir):
        return 0
    names = sorted(name for name in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, name)))
    if not names:
        return 0
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.write(os.path.join(upload_dir, name), arcname=name)
    return len(names)


def _backup_sets(backup_dir):
    """Map each backup timestamp to its files, newest first."""
    sets = {}
    if os.path.isdir(backup_dir):
        for name in os.listdir(backup_dir):
            match = BACKUP_NAME.match(name)
            if match:
                sets.setdefault(match.group(1), []).append(name)
    return dict(sorted(sets.items(), reverse=True))


def prune_backups(backup_dir, keep):
    """Delete all but the ``keep`` newest backups; returns the removed file names."""
    removed = []
    for names in list(_backup_sets(backup_dir).values())[keep:]:
        for name in names:
            os.remove(os.path.join(backup_dir, name))
            removed.append(name)
    return removed


def run_backup(database_url, upload_dir, backup_dir, keep=None, include_uploads=True):
    """Back up the database (and photos) into ``backup_dir``; returns the created paths."""
    from sqlalchemy.engine import make_url

    url = make_url(str(database_url))
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    created = []

    if url.get_backend_name() == 'sqlite':
        target = os.path.join(backup_dir, f'{PREFIX}{stamp}.db')
        _backup_sqlite(url, target)
    elif url.get_backend_name() == 'postgresql':
        target = os.path.join(backup_dir, f'{PREFIX}{stamp}.dump')
        _backup_postgres(url, target)
    else:
        raise BackupError(f'Desteklenmeyen veritabanı türü: {url.get_backend_name()}')
    created.append(target)

    if include_uploads:
        archive = os.path.join(backup_dir, f'{PREFIX}{stamp}_uploads.zip')
        if _archive_uploads(upload_dir, archive):
            created.append(archive)

    if keep:
        prune_backups(backup_dir, keep)
    return created


def list_backups(backup_dir):
    sets = _backup_sets(backup_dir)
    if not sets:
        print("Henüz yedek bulunmuyor.")
        return
    print(f"Toplam {len(sets)} yedek ({backup_dir}):")
    for stamp, names in sets.items():
        size_mb = sum(os.path.getsize(os.path.join(backup_dir, name)) for name in names) / (1024 * 1024)
        print(f"  {stamp}  {', '.join(sorted(names))}  ({size_mb:.2f} MB)")


def _app_settings():
    """Read the database URL and upload folder exactly as the app resolves them."""
    sys.path.insert(0, BASE_DIR)
    from app import app
    from database import db

    with app.app_context():
        return db.engine.url, app.config['UPLOAD_FOLDER']


def main(argv=None):
    parser = argparse.ArgumentParser(description='KAYA PTS veritabanı ve fotoğraf yedeği alır.')
    parser.add_argument('--output-dir', default=DEFAULT_BACKUP_DIR, help='Yedeklerin yazılacağı klasör.')
    parser.add_argument('--keep', type=int, help='Yalnızca en yeni N yedeği tut, eskileri sil.')
    parser.add_argument('--no-uploads', action='store_true', help='Personel fotoğraflarını yedekleme.')
    parser.add_argument('--list', action='store_true', help='Mevcut yedekleri listele.')
    args = parser.parse_args(argv)

    if args.list:
        list_backups(args.output_dir)
        return 0
    if args.keep is not None and args.keep < 1:
        parser.error('--keep en az 1 olmalıdır.')

    database_url, upload_dir = _app_settings()
    try:
        created = run_backup(database_url, upload_dir, args.output_dir, args.keep, not args.no_uploads)
    except (BackupError, OSError, sqlite3.Error) as exc:
        print(f"HATA: Yedekleme başarısız: {exc}")
        return 1
    for path in created:
        print(f"Yedek oluşturuldu: {path} ({os.path.getsize(path) / (1024 * 1024):.2f} MB)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
