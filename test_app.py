from utils import allowed_file
from app import create_app
from models import Personel, Kullanici
from database import db

assert allowed_file('avatar.png'), "png should be allowed"
assert allowed_file('photo.JPG'), "JPG should be allowed"
assert allowed_file('img.jpeg'), "jpeg should be allowed"
assert allowed_file('banner.webp'), "webp should be allowed"
assert not allowed_file('script.exe'), "exe must be blocked"
assert not allowed_file('hack.php'), "php must be blocked"
assert not allowed_file('payload.sh'), "sh must be blocked"
assert not allowed_file('noextension'), "no extension must be blocked"
print("[TEST] allowed_file tests passed successfully!")

test_app = create_app('testing')
with test_app.app_context():
    db.create_all()
    count = Personel.query.count()
    user_count = Kullanici.query.count()
    print(f"[TEST] Database test passed! Active/Total personnel: {count}, Users: {user_count}")

with test_app.test_client() as client:
    res = client.get('/login')
    assert res.status_code == 200, "Login page should return 200"
    print("[TEST] Web client test passed (login route returns 200)!")

print("[ALL TESTS PASSED]")

