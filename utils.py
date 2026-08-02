import os
import re
import uuid
import mimetypes
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash, request, current_app, abort
from werkzeug.utils import secure_filename
from database import db
from models import Log, LoginAttempt, Kullanici

# Role and permissions matrix (4 core roles)
ROLE_HIERARCHY = {
    'Admin': ['all', 'view', 'add', 'edit', 'delete', 'trash', 'users', 'logs', 'salary', 'leaves', 'export'],
    'IK': ['view', 'add', 'edit', 'delete', 'trash', 'leaves', 'salary', 'export'],
    'Mudur': ['view', 'leaves', 'export'],
    'Muhasebe': ['view', 'salary', 'export']
}

def has_permission(user_role, permission):
    """Check if given role has required permission."""
    if not user_role:
        return False
    perms = ROLE_HIERARCHY.get(user_role, [])
    return 'all' in perms or permission in perms

def role_required(*allowed_roles):
    """Decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'kullanici_adi' not in session:
                flash('Lütfen önce giriş yapınız.', 'error')
                return redirect(url_for('auth.login'))
            
            user_role = session.get('rol', '')
            if user_role not in allowed_roles and 'Admin' not in allowed_roles and user_role != 'Admin':
                flash('Bu işlemi gerçekleştirmek için yetkiniz bulunmamaktadır.', 'error')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_password(password):
    """Enforce strong password policy (min 8 chars, uppercase, lowercase, number)."""
    if len(password) < 8:
        return False, "Şifre en az 8 karakter uzunluğunda olmalıdır."
    if not re.search(r"[A-Z]", password):
        return False, "Şifre en az bir büyük harf (A-Z) içermelidir."
    if not re.search(r"[a-z]", password):
        return False, "Şifre en az bir küçük harf (a-z) içermelidir."
    if not re.search(r"\d", password):
        return False, "Şifre en az bir rakam (0-9) içermelidir."
    return True, "Şifre geçerli."

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is within allowed whitelist."""
    if not filename or '.' not in filename:
        return False
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions

def validate_file_upload(file):
    """Validate file extension and MIME type."""
    if not file or file.filename == '':
        return False, "Dosya seçilmedi.", None

    filename = file.filename
    if '.' not in filename:
        return False, "Geçersiz dosya formatı.", None

    ext = filename.rsplit('.', 1)[1].lower()
    allowed_exts = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})
    if ext not in allowed_exts:
        return False, f"Yalnızca {', '.join(allowed_exts)} uzantılı dosyalar kabul edilir.", None

    mime_type, _ = mimetypes.guess_type(filename)
    allowed_mimes = current_app.config.get('ALLOWED_MIMETYPES', {'image/png', 'image/jpeg', 'image/pjpeg', 'image/webp'})
    if mime_type and mime_type not in allowed_mimes:
        return False, f"Güvensiz dosya tipi tespit edildi: {mime_type}", None

    return True, "Dosya geçerli.", ext

def save_avatar(file, ad, soyad):
    """Securely save avatar with UUID suffix."""
    is_valid, msg, ext = validate_file_upload(file)
    if not is_valid:
        return False, msg, None

    clean_name = secure_filename(f"{ad}_{soyad}")
    unique_filename = f"{clean_name}_{uuid.uuid4().hex[:8]}.{ext}"
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(upload_path)
    return True, "Fotoğraf yüklendi.", unique_filename

def log_action(kullanici_adi, islem_tipi, detay, ip_adresi=None):
    """Record audit log entry in database."""
    try:
        if not ip_adresi and request:
            ip_adresi = request.headers.get('X-Forwarded-For', request.remote_addr)
        new_log = Log(
            kullanici_adi=kullanici_adi,
            islem_tipi=islem_tipi,
            detay=detay,
            ip_adresi=ip_adresi,
            tarih_saat=datetime.utcnow()
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Log error: {e}")

def get_client_ip():
    if request:
        return request.headers.get('X-Forwarded-For', request.remote_addr)
    return '127.0.0.1'

def is_account_locked(kullanici_adi):
    """Check if account or IP is temporarily locked due to failed attempts."""
    ip = get_client_ip()
    attempt = LoginAttempt.query.filter(
        (LoginAttempt.kullanici_adi == kullanici_adi) | (LoginAttempt.ip_adresi == ip)
    ).order_by(LoginAttempt.son_deneme.desc()).first()

    if attempt and attempt.kilitli_mi:
        if attempt.kilit_bitis and datetime.utcnow() < attempt.kilit_bitis:
            kalan_dakika = int((attempt.kilit_bitis - datetime.utcnow()).total_seconds() / 60) + 1
            return True, f"Çok fazla hatalı giriş denemesi! Hesabınız {kalan_dakika} dakika kilitlendi."
        else:
            attempt.kilitli_mi = False
            attempt.deneme_sayisi = 0
            db.session.commit()
            return False, ""
    return False, ""

def record_login_failure(kullanici_adi):
    """Increment failed login attempts and lock if threshold exceeded."""
    ip = get_client_ip()
    max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
    lockout_minutes = current_app.config.get('LOCKOUT_DURATION_MINUTES', 10)

    attempt = LoginAttempt.query.filter_by(kullanici_adi=kullanici_adi, ip_adresi=ip).first()
    if not attempt:
        attempt = LoginAttempt(kullanici_adi=kullanici_adi, ip_adresi=ip, deneme_sayisi=1)
        db.session.add(attempt)
    else:
        attempt.deneme_sayisi += 1
        attempt.son_deneme = datetime.utcnow()

    if attempt.deneme_sayisi >= max_attempts:
        attempt.kilitli_mi = True
        attempt.kilit_bitis = datetime.utcnow() + timedelta(minutes=lockout_minutes)
        log_action(kullanici_adi, 'Güvenlik Uyarısı', f'5 hatalı giriş nedeniyle {lockout_minutes} dakika kilitlendi.')

    db.session.commit()
    return attempt.deneme_sayisi, max_attempts

def clear_login_attempts(kullanici_adi):
    """Clear failed login attempts upon successful authentication."""
    ip = get_client_ip()
    attempts = LoginAttempt.query.filter(
        (LoginAttempt.kullanici_adi == kullanici_adi) | (LoginAttempt.ip_adresi == ip)
    ).all()
    for att in attempts:
        db.session.delete(att)
    db.session.commit()
