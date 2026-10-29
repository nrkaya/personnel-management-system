import unittest
from datetime import date, datetime, timedelta
from flask import session
from app import create_app
from database import db
from models import Kullanici, Personel, Izin, Log, LoginAttempt
from werkzeug.security import generate_password_hash
from utils import validate_password, has_permission, ROLE_HIERARCHY

class EnterpriseSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.admin = Kullanici.query.filter_by(kullanici_adi='admin').first()
        if not self.admin:
            self.admin = Kullanici(
                kullanici_adi='admin',
                sifre_hash=generate_password_hash('Admin123!'),
                rol='Admin',
                ad_soyad='Admin User',
                aktif_mi=True
            )
            db.session.add(self.admin)
        
        self.ik_user = Kullanici(
            kullanici_adi='ik_uzmani',
            sifre_hash=generate_password_hash('Ik123456!'),
            rol='IK',
            ad_soyad='IK Uzmanı',
            aktif_mi=True
        )
        self.mudur_user = Kullanici(
            kullanici_adi='mudur_bey',
            sifre_hash=generate_password_hash('Mudur123!'),
            rol='Mudur',
            ad_soyad='Departman Müdürü',
            aktif_mi=True
        )
        self.muhasebe_user = Kullanici(
            kullanici_adi='muhasebeci',
            sifre_hash=generate_password_hash('Muhasebe123!'),
            rol='Muhasebe',
            ad_soyad='Hesap Uzmanı',
            aktif_mi=True
        )
        db.session.add_all([self.ik_user, self.mudur_user, self.muhasebe_user])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login_as(self, user):
        """Put a valid, versioned session for ``user`` on the test client."""
        with self.client.session_transaction() as sess:
            sess['kullanici_adi'] = user.kullanici_adi
            sess['rol'] = user.rol
            sess['user_id'] = user.id
            sess['oturum_surumu'] = user.oturum_surumu

    def test_password_policy(self):
        """Test password policy enforcement."""
        valid, _ = validate_password("KayaSecure2026!")
        self.assertTrue(valid)

        invalid1, _ = validate_password("short")
        self.assertFalse(invalid1)

        invalid2, _ = validate_password("alllowercase123")
        self.assertFalse(invalid2)

        invalid3, _ = validate_password("ALLUPPERCASE123")
        self.assertFalse(invalid3)

        invalid4, _ = validate_password("NoDigitsHere!")
        self.assertFalse(invalid4)

    def test_rbac_permissions(self):
        """Test RBAC permission matrix for 4 roles."""
        # Admin
        self.assertTrue(has_permission('Admin', 'users'))
        self.assertTrue(has_permission('Admin', 'salary'))
        self.assertTrue(has_permission('Admin', 'trash'))
        self.assertTrue(has_permission('Admin', 'logs'))

        # IK
        self.assertTrue(has_permission('IK', 'add'))
        self.assertTrue(has_permission('IK', 'edit'))
        self.assertTrue(has_permission('IK', 'delete'))
        self.assertTrue(has_permission('IK', 'leaves'))
        self.assertFalse(has_permission('IK', 'users'))

        # Mudur
        self.assertTrue(has_permission('Mudur', 'view'))
        self.assertTrue(has_permission('Mudur', 'leaves'))
        self.assertTrue(has_permission('Mudur', 'export'))
        self.assertFalse(has_permission('Mudur', 'delete'))
        self.assertFalse(has_permission('Mudur', 'users'))

        # Muhasebe
        self.assertTrue(has_permission('Muhasebe', 'view'))
        self.assertTrue(has_permission('Muhasebe', 'salary'))
        self.assertTrue(has_permission('Muhasebe', 'export'))
        self.assertFalse(has_permission('Muhasebe', 'delete'))
        self.assertFalse(has_permission('Muhasebe', 'users'))

    def test_auth_login_and_lockout(self):
        """Test authentication and brute-force lockout."""
        with self.client.session_transaction() as sess:
            sess.clear()
        
        resp = self.client.post('/login', data={'kullanici_adi': 'admin', 'sifre': 'Admin123!'}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        with self.client.session_transaction() as sess:
            sess.clear()
            
        for _ in range(5):
            self.client.post('/login', data={'kullanici_adi': 'ik_uzmani', 'sifre': 'WrongPassword1!'}, follow_redirects=True)

        resp_locked = self.client.post('/login', data={'kullanici_adi': 'ik_uzmani', 'sifre': 'Ik123456!'}, follow_redirects=True)
        self.assertIn("kilitlendi", resp_locked.data.decode('utf-8', errors='ignore'))

    def test_logout_requires_post(self):
        """Logout endpoint must reject GET requests."""
        self._login_as(self.admin)

        # GET should return 405 Method Not Allowed
        resp_get = self.client.get('/logout')
        self.assertEqual(resp_get.status_code, 405)

        # POST should succeed (redirect to login)
        resp_post = self.client.post('/logout', follow_redirects=True)
        self.assertEqual(resp_post.status_code, 200)

    def test_personnel_lifecycle_and_trash(self):
        """Test personnel CRUD, soft-delete, restore, and permanent deletion."""
        p = Personel(
            ad="Mehmet",
            soyad="Kaya",
            departman="Yazılım",
            pozisyon="Senior Developer",
            telefon="0555 444 3322",
            email="mehmet@kaya.com",
            maas=85000.0,
            aktif_mi=True
        )
        db.session.add(p)
        db.session.commit()
        p_id = p.id

        found = Personel.query.filter_by(id=p_id, aktif_mi=True).first()
        self.assertIsNotNone(found)
        self.assertEqual(found.tam_ad, "Mehmet Kaya")

        # Soft Delete
        found.aktif_mi = False
        db.session.commit()

        self.assertIsNone(Personel.query.filter_by(id=p_id, aktif_mi=True).first())
        trash_item = Personel.query.filter_by(id=p_id, aktif_mi=False).first()
        self.assertIsNotNone(trash_item)

        # Restore
        trash_item.aktif_mi = True
        db.session.commit()
        self.assertIsNotNone(Personel.query.filter_by(id=p_id, aktif_mi=True).first())

        # Hard Delete
        db.session.delete(trash_item)
        db.session.commit()
        self.assertIsNone(db.session.get(Personel, p_id))

    def test_leave_management(self):
        """Test leave creation, approval lifecycle, and personnel relation."""
        p = Personel(ad="Ayşe", soyad="Demir", departman="İnsan Kaynakları", aktif_mi=True)
        db.session.add(p)
        db.session.commit()

        izin = Izin(
            personel_id=p.id,
            baslangic=date.today(),
            bitis=date.today() + timedelta(days=5),
            tur="Yıllık İzin",
            durum="Beklemede",
            kullanici_adi="admin"
        )
        db.session.add(izin)
        db.session.commit()

        self.assertEqual(len(p.izinler), 1)
        self.assertEqual(p.izinler[0].durum, "Beklemede")

        p.izinler[0].durum = "Onaylandı"
        db.session.commit()
        self.assertEqual(db.session.get(Izin, izin.id).durum, "Onaylandı")

    def test_rest_api(self):
        """Test RESTful API v1 endpoints and authentication."""
        headers_invalid = {'X-API-KEY': 'wrong-key'}
        headers_valid = {'X-API-KEY': self.app.config['API_KEY']}

        resp_unauth = self.client.get('/api/v1/personeller', headers=headers_invalid)
        self.assertEqual(resp_unauth.status_code, 401)

        resp_get = self.client.get('/api/v1/personeller', headers=headers_valid)
        self.assertEqual(resp_get.status_code, 200)

        payload = {
            'ad': 'Ali',
            'soyad': 'Veli',
            'departman': 'Pazarlama',
            'pozisyon': 'Uzman',
            'maas': 50000
        }
        resp_post = self.client.post('/api/v1/personel', json=payload, headers=headers_valid)
        self.assertEqual(resp_post.status_code, 201)
        res_data = resp_post.get_json()
        new_id = res_data['data']['id']

        resp_single = self.client.get(f'/api/v1/personel/{new_id}', headers=headers_valid)
        self.assertEqual(resp_single.status_code, 200)
        self.assertEqual(resp_single.get_json()['data']['ad'], 'Ali')

        resp_put = self.client.put(f'/api/v1/personel/{new_id}', json={'ad': 'Ali Can'}, headers=headers_valid)
        self.assertEqual(resp_put.status_code, 200)
        self.assertEqual(resp_put.get_json()['data']['ad'], 'Ali Can')

        resp_del = self.client.delete(f'/api/v1/personel/{new_id}', headers=headers_valid)
        self.assertEqual(resp_del.status_code, 200)

        self.assertTrue(Log.query.filter(Log.islem_tipi == 'API Personel Silindi').first())

    def test_endpoint_rbac_and_revoked_account(self):
        """A lower-privilege account cannot reach privileged endpoints by URL."""
        self._login_as(self.muhasebe_user)

        self.assertEqual(self.client.get('/users').status_code, 403)
        self.assertEqual(self.client.get('/trash').status_code, 403)
        self.assertEqual(self.client.post('/users/add', data={
            'kullanici_adi': 'escalation_attempt',
            'sifre': 'VeryStrongPass1!',
            'rol': 'Admin',
        }).status_code, 403)

        self.muhasebe_user.aktif_mi = False
        db.session.commit()
        self.assertEqual(self.client.get('/personeller').status_code, 302)

    def test_api_validation_and_pagination_limits(self):
        headers = {'X-API-KEY': self.app.config['API_KEY']}
        invalid_salary = self.client.post('/api/v1/personel', json={
            'ad': 'Ali', 'soyad': 'Veli', 'maas': 'not-a-number'
        }, headers=headers)
        self.assertEqual(invalid_salary.status_code, 422)

        null_name = self.client.post('/api/v1/personel', json={
            'ad': None, 'soyad': 'Veli'
        }, headers=headers)
        self.assertEqual(null_name.status_code, 422)

        self.assertEqual(
            self.client.get('/api/v1/personeller?page=-1', headers=headers).status_code,
            400,
        )
        self.assertEqual(
            self.client.get('/api/v1/personeller?per_page=1000000', headers=headers).status_code,
            400,
        )

    def test_excel_export(self):
        """Test Excel (.xlsx) export functionality."""
        self._login_as(self.admin)

        p = Personel(ad="Ahmet", soyad="Yıldız", departman="Finans", aktif_mi=True)
        db.session.add(p)
        db.session.commit()

        resp = self.client.get('/export')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_custom_404_page(self):
        """Test custom 404 error page handler."""
        resp = self.client.get('/olmayan-bir-sayfa-404')
        self.assertEqual(resp.status_code, 404)
        self.assertIn("404", resp.data.decode('utf-8', errors='ignore'))

    def test_i18n_translation_and_language_switching(self):
        """Test i18n translation engine and language switching endpoint."""
        from i18n import translate, get_locale

        # Direct translation lookup
        self.assertEqual(translate('app_title', locale='tr'), 'KAYA PTS - Kaya Personel Takip Sistemi (Enterprise)')
        self.assertEqual(translate('app_title', locale='en'), 'KAYA PTS - Kaya Personnel Tracking System (Enterprise)')
        self.assertEqual(translate('nav_dashboard', locale='tr'), 'Gösterge Paneli')
        self.assertEqual(translate('nav_dashboard', locale='en'), 'Dashboard')

        # Language switching via route
        resp = self.client.get('/lang/en', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('lang'), 'en')

        # Switch back to Turkish
        resp_tr = self.client.get('/lang/tr', follow_redirects=True)
        self.assertEqual(resp_tr.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('lang'), 'tr')

if __name__ == '__main__':
    unittest.main()
