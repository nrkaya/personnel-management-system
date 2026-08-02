import os
from app import create_app
from database import db
from models import Personel, Kullanici, Log

# 1. Requirements.txt check
assert os.path.exists('requirements.txt'), "requirements.txt must exist"
with open('requirements.txt', 'r', encoding='utf-8') as f:
    reqs = f.read()
    assert 'Flask' in reqs and 'openpyxl' in reqs and 'python-dotenv' in reqs
print("[PASS] 1. requirements.txt verified")

app = create_app('testing')
client = app.test_client()

with app.app_context():
    db.create_all()

    # 2. 404 test
    res_404 = client.get('/non_existent_page_12345')
    assert res_404.status_code == 404, "404 route must return 404 code"
    assert "404" in res_404.get_data(as_text=True)
    print("[PASS] 2. Custom 404 error page verified")

    # 3. Pagination & Trash test with admin session
    with client.session_transaction() as sess:
        sess['kullanici_adi'] = 'admin'
        sess['rol'] = 'Admin'

    # Seed 25 test personels
    for i in range(1, 26):
        p = Personel(ad=f'TestAd_{i}', soyad=f'TestSoyad_{i}', departman='Yazılım', pozisyon='Mühendis', telefon='05550000000', maas=50000, aktif_mi=True)
        db.session.add(p)
    db.session.commit()

    # Check page 1
    res_p1 = client.get('/personeller?page=1')
    assert res_p1.status_code == 200
    html_p1 = res_p1.get_data(as_text=True)
    assert "TestAd_25" in html_p1 # id desc: newest first

    # Check page 2
    res_p2 = client.get('/personeller?page=2')
    assert res_p2.status_code == 200

    print("[PASS] 3. Pagination (Page 1 & Page 2) verified")

    # 4. Soft delete test
    target = Personel.query.filter_by(ad='TestAd_1').first()
    target_id = target.id

    res_del = client.post(f'/delete/{target_id}', follow_redirects=True)
    assert res_del.status_code == 200

    # 5. Trash view test
    res_trash = client.get('/trash')
    assert res_trash.status_code == 200
    html_trash = res_trash.get_data(as_text=True)
    assert "TestAd_1" in html_trash

    print("[PASS] 4. Soft delete to Trash verified")

    # 6. Restore test
    res_restore = client.post(f'/personel/restore/{target_id}', follow_redirects=True)
    assert res_restore.status_code == 200

    restored = db.session.get(Personel, target_id)
    assert restored.aktif_mi is True, "Personnel should be active after restore"

    print("[PASS] 5. Restore from Trash verified")

    # 7. Clean up test records
    Personel.query.filter(Personel.ad.like('TestAd_%')).delete()
    Log.query.filter(Log.detay.like('%TestAd_%')).delete()
    db.session.commit()

    print("[PASS] 6. Test records cleaned up")
    print("[SUCCESS] ALL NEW FEATURES TESTED AND PASSED SUCCESSFULLY!")

