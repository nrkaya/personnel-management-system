import os
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
import zipfile
from unittest import mock

import backup_db


class BackupTestCase(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.workdir, 'backups')
        self.upload_dir = os.path.join(self.workdir, 'uploads')
        os.makedirs(self.upload_dir)

    def tearDown(self):
        shutil.rmtree(self.workdir, ignore_errors=True)

    def test_sqlite_backup_copies_data_and_photos(self):
        db_path = os.path.join(self.workdir, 'live.db')
        with sqlite3.connect(db_path) as connection:
            connection.execute('CREATE TABLE personeller (ad TEXT)')
            connection.execute("INSERT INTO personeller VALUES ('Ayşe')")
        connection.close()
        with open(os.path.join(self.upload_dir, 'abc.png'), 'wb') as photo:
            photo.write(b'png-bytes')

        created = backup_db.run_backup(f'sqlite:///{db_path}', self.upload_dir, self.backup_dir)

        self.assertEqual(len(created), 2)
        dump, archive = created
        copy = sqlite3.connect(dump)
        self.assertEqual(copy.execute('SELECT ad FROM personeller').fetchall(), [('Ayşe',)])
        copy.close()
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(zipped.namelist(), ['abc.png'])

    def test_missing_sqlite_file_is_an_error(self):
        with self.assertRaises(backup_db.BackupError):
            backup_db.run_backup('sqlite:///' + os.path.join(self.workdir, 'yok.db'), self.upload_dir, self.backup_dir)

    def test_prune_keeps_newest_backup_sets(self):
        os.makedirs(self.backup_dir)
        for stamp in ('20260101_000000', '20260102_000000', '20260103_000000'):
            # .tar.gz photo archives come from the Docker Compose backup service.
            for suffix in ('.dump', '_uploads.zip', '_uploads.tar.gz'):
                open(os.path.join(self.backup_dir, f'kaya_pts_{stamp}{suffix}'), 'w').close()
        open(os.path.join(self.backup_dir, 'notlarim.txt'), 'w').close()

        backup_db.prune_backups(self.backup_dir, keep=1)

        self.assertEqual(sorted(os.listdir(self.backup_dir)), [
            'kaya_pts_20260103_000000.dump', 'kaya_pts_20260103_000000_uploads.tar.gz',
            'kaya_pts_20260103_000000_uploads.zip', 'notlarim.txt',
        ])

    def test_postgres_without_pg_dump_is_an_error(self):
        with mock.patch('backup_db.shutil.which', return_value=None):
            with self.assertRaises(backup_db.BackupError):
                backup_db.run_backup('postgresql+psycopg://u:p@db:5432/kaya', self.upload_dir, self.backup_dir)

    def test_postgres_password_is_not_on_the_command_line(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        with mock.patch('backup_db.shutil.which', return_value='/usr/bin/pg_dump'), \
                mock.patch('backup_db.subprocess.run', return_value=completed) as run:
            backup_db.run_backup('postgresql+psycopg://kaya:s3cret@db:5433/kaya_pts?sslmode=require',
                                 self.upload_dir, self.backup_dir, include_uploads=False)

        args, kwargs = run.call_args
        command = args[0]
        self.assertNotIn('s3cret', ' '.join(command))
        self.assertIn('--host=db', command)
        self.assertIn('--port=5433', command)
        self.assertIn('--dbname=kaya_pts', command)
        self.assertEqual(kwargs['env']['PGPASSWORD'], 's3cret')
        self.assertEqual(kwargs['env']['PGSSLMODE'], 'require')


if __name__ == '__main__':
    unittest.main()
