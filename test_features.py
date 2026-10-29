import os
import unittest
from app import create_app
from database import db
from models import Personel, Kullanici
from werkzeug.security import generate_password_hash


class FeatureTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.admin = Kullanici(
            kullanici_adi='admin',
            sifre_hash=generate_password_hash('Admin123!'),
            rol='Admin',
            aktif_mi=True,
        )
        db.session.add(self.admin)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess['kullanici_adi'] = 'admin'
            sess['user_id'] = self.admin.id
            sess['oturum_surumu'] = self.admin.oturum_surumu

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_requirements_file(self):
        self.assertTrue(os.path.exists('requirements.txt'), "requirements.txt must exist")
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            reqs = f.read()
        self.assertIn('Flask', reqs)
        self.assertIn('openpyxl', reqs)
        self.assertIn('python-dotenv', reqs)

    def test_custom_404(self):
        res_404 = self.client.get('/non_existent_page_12345')
        self.assertEqual(res_404.status_code, 404, "404 route must return 404 code")
        self.assertIn("404", res_404.get_data(as_text=True))

    def test_pagination_trash_and_restore(self):
        for i in range(1, 26):
            db.session.add(Personel(
                ad=f'TestAd_{i}', soyad=f'TestSoyad_{i}', departman='Yazılım', pozisyon='Mühendis',
                telefon='05550000000', maas=50000, aktif_mi=True,
            ))
        db.session.commit()

        res_p1 = self.client.get('/personeller?page=1')
        self.assertEqual(res_p1.status_code, 200)
        self.assertIn("TestAd_25", res_p1.get_data(as_text=True))  # id desc: newest first
        self.assertEqual(self.client.get('/personeller?page=2').status_code, 200)

        target_id = Personel.query.filter_by(ad='TestAd_1').first().id
        self.assertEqual(self.client.post(f'/delete/{target_id}', follow_redirects=True).status_code, 200)

        res_trash = self.client.get('/trash')
        self.assertEqual(res_trash.status_code, 200)
        self.assertIn("TestAd_1", res_trash.get_data(as_text=True))

        res_restore = self.client.post(f'/personel/restore/{target_id}', follow_redirects=True)
        self.assertEqual(res_restore.status_code, 200)
        self.assertIs(db.session.get(Personel, target_id).aktif_mi, True, "Personnel should be active after restore")


if __name__ == '__main__':
    unittest.main()
