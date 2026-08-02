import sqlite3
import os
from app import app, get_db

# 1. Requirements.txt check
assert os.path.exists('requirements.txt'), "requirements.txt must exist"
with open('requirements.txt', 'r', encoding='utf-8') as f:
    reqs = f.read()
    assert 'Flask' in reqs and 'openpyxl' in reqs and 'python-dotenv' in reqs
print("[PASS] 1. requirements.txt verified")

client = app.test_client()

# 2. 404 test
res_404 = client.get('/non_existent_page_12345')
assert res_404.status_code == 404, "404 route must return 404 code"
assert "Sayfa Bulunamadı" in res_404.get_data(as_text=True)
print("[PASS] 2. Custom 404 error page verified")

# 3. Pagination & Trash test with admin session
with client.session_transaction() as sess:
    sess['kullanici_adi'] = 'admin'
    sess['rol'] = 'admin'

# Seed 25 test personels
with app.app_context():
    db = get_db()
    for i in range(1, 26):
        db.execute('''
            INSERT INTO Personeller (ad, soyad, departman, pozisyon, telefon, maas, aktif_mi)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (f'TestAd_{i}', f'TestSoyad_{i}', 'Yazılım', 'Mühendis', '05550000000', 50000))
    db.commit()

# Check page 1
res_p1 = client.get('/personeller?page=1')
assert res_p1.status_code == 200
html_p1 = res_p1.get_data(as_text=True)
assert "Toplam <strong>25</strong> personelden" in html_p1
assert "TestAd_25" in html_p1 # id desc: newest first

# Check page 2
res_p2 = client.get('/personeller?page=2')
assert res_p2.status_code == 200
html_p2 = res_p2.get_data(as_text=True)
assert "Sonraki" in html_p2

print("[PASS] 3. Pagination (Page 1 & Page 2) verified")

# 4. Soft delete test
with app.app_context():
    db = get_db()
    target = db.execute('SELECT id FROM Personeller WHERE ad = "TestAd_1"').fetchone()
    target_id = target['id']

res_del = client.post(f'/delete/{target_id}', follow_redirects=True)
assert res_del.status_code == 200

# 5. Trash view test
res_trash = client.get('/trash')
assert res_trash.status_code == 200
html_trash = res_trash.get_data(as_text=True)
assert "TestAd_1" in html_trash
assert "Geri Yükle" in html_trash

print("[PASS] 4. Soft delete to Trash verified")

# 6. Restore test
res_restore = client.post(f'/personel/restore/{target_id}', follow_redirects=True)
assert res_restore.status_code == 200

with app.app_context():
    db = get_db()
    restored = db.execute('SELECT aktif_mi FROM Personeller WHERE id = ?', (target_id,)).fetchone()
    assert restored['aktif_mi'] == 1, "Personnel should be active after restore"

print("[PASS] 5. Restore from Trash verified")

# 7. Clean up test records
with app.app_context():
    db = get_db()
    db.execute('DELETE FROM Personeller WHERE ad LIKE "TestAd_%"')
    db.execute('DELETE FROM Loglar WHERE detay LIKE "%TestAd_%"')
    db.commit()

print("[PASS] 6. Test records cleaned up")
print("[SUCCESS] ALL NEW FEATURES TESTED AND PASSED SUCCESSFULLY!")
