import unittest
from utils import allowed_file
from app import create_app
from models import Personel, Kullanici
from database import db


class SmokeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_allowed_file(self):
        self.assertTrue(allowed_file('avatar.png'), "png should be allowed")
        self.assertTrue(allowed_file('photo.JPG'), "JPG should be allowed")
        self.assertTrue(allowed_file('img.jpeg'), "jpeg should be allowed")
        self.assertTrue(allowed_file('banner.webp'), "webp should be allowed")
        self.assertFalse(allowed_file('script.exe'), "exe must be blocked")
        self.assertFalse(allowed_file('hack.php'), "php must be blocked")
        self.assertFalse(allowed_file('payload.sh'), "sh must be blocked")
        self.assertFalse(allowed_file('noextension'), "no extension must be blocked")

    def test_database_starts_empty(self):
        self.assertEqual(Personel.query.count(), 0)
        self.assertEqual(Kullanici.query.count(), 0)

    def test_login_page(self):
        res = self.app.test_client().get('/login')
        self.assertEqual(res.status_code, 200, "Login page should return 200")


if __name__ == '__main__':
    unittest.main()
