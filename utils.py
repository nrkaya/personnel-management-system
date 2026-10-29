import hashlib
import hmac
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import wraps
from urllib.parse import urlparse
from flask import session, redirect, url_for, flash, request, current_app, abort, has_request_context
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import false, or_
from werkzeug.security import check_password_hash, generate_password_hash
from database import db
from i18n import _
from models import Log, LoginAttempt, Kullanici, Personel

# Role and permissions matrix (4 core roles). Routes (permission_required) and
# templates read the same table, so a button is shown exactly when its
# endpoint allows the action.
#   personal     -> birth date and dossier notes
#   leave_reason -> free-text leave reasons (may contain health information)
ROLE_HIERARCHY = {
    'Admin': ['all', 'view', 'add', 'edit', 'delete', 'trash', 'hard_delete', 'users', 'logs',
              'salary', 'personal', 'leaves', 'leave_delete', 'leave_reason', 'export'],
    'IK': ['view', 'add', 'edit', 'delete', 'trash', 'leaves', 'leave_delete', 'leave_reason',
           'salary', 'personal', 'export'],
    'Mudur': ['view', 'leaves', 'leave_reason', 'export'],
    'Muhasebe': ['view', 'salary', 'export']
}

IMAGE_FORMATS = {
    'png': 'PNG',
    'jpg': 'JPEG',
    'jpeg': 'JPEG',
    'webp': 'WEBP',
}
DEFAULT_AVATARS = {'default.svg', 'default.png'}
DEFAULT_AVATAR_STATIC = 'img/default-avatar.svg'
EMAIL_PATTERN = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9._-]{3,80}$')
PHONE_PATTERN = re.compile(r'^[0-9+().\s-]*$')
# Largest value that fits Numeric(12, 2).
MAX_SALARY = Decimal('9999999999.99')

_dummy_password_hash = None


def utcnow():
    return datetime.now(timezone.utc)


def as_utc(value):
    """Normalize legacy SQLite timestamps that were stored without tzinfo."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def get_active_session_user():
    """Return the active database user for the current session, if any.

    Roles and account state are read from the database instead of trusting a
    role stored in the signed session cookie, and the session's version must
    match the account's, so logout and password changes revoke old cookies.
    """
    user_id = session.get('user_id')
    # Repeated calls within a request are served from the session's identity map.
    user = db.session.get(Kullanici, user_id) if user_id else None
    if user is None or not user.aktif_mi or session.get('oturum_surumu') != user.oturum_surumu:
        return None
    session['kullanici_adi'] = user.kullanici_adi
    session['rol'] = user.rol
    return user


def start_user_session(user):
    """Replace the session with a fresh one for ``user``, keeping the language."""
    lang = session.get('lang')
    session.clear()
    if lang:
        session['lang'] = lang
    session['user_id'] = user.id
    session['kullanici_adi'] = user.kullanici_adi
    session['rol'] = user.rol
    session['oturum_surumu'] = user.oturum_surumu
    session.permanent = True


def end_user_session():
    """Clear the session but keep the visitor's language choice."""
    lang = session.get('lang')
    session.clear()
    if lang:
        session['lang'] = lang


def revoke_user_sessions(user):
    """Invalidate every session cookie issued for ``user`` so far."""
    user.oturum_surumu = (user.oturum_surumu or 0) + 1


def has_permission(user_role, permission):
    """Check if given role has required permission."""
    if not user_role:
        return False
    perms = ROLE_HIERARCHY.get(user_role, [])
    return 'all' in perms or permission in perms


def permission_required(*permissions):
    """Require a logged-in, active user whose role grants every permission.

    Called without arguments it only requires a valid login.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                return redirect(url_for('auth.login'))

            user = get_active_session_user()
            if user is None:
                end_user_session()
                flash(_('msg_session_invalid'), 'error')
                return redirect(url_for('auth.login'))

            if not all(has_permission(user.rol, permission) for permission in permissions):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def manager_department_missing(user):
    """A department manager sees nobody until a department is assigned."""
    return user is not None and user.rol == 'Mudur' and not user.departman


def scope_personnel(query, user=None):
    """Limit a query that selects or joins Personel to the records ``user`` may see.

    Department managers ('Mudur') are restricted to their own department; every
    other role works company-wide.
    """
    if user is None:
        user = get_active_session_user()
    if user is None or manager_department_missing(user):
        return query.filter(false())
    if user.rol == 'Mudur':
        return query.filter(Personel.departman == user.departman)
    return query


def can_access_personnel(personel, user=None):
    """Object-level counterpart of :func:`scope_personnel`."""
    if user is None:
        user = get_active_session_user()
    if user is None or manager_department_missing(user):
        return False
    if user.rol == 'Mudur':
        return personel.departman == user.departman
    return True


def validate_password(password):
    """Enforce a practical password policy for newly-created accounts."""
    if len(password) < 12:
        return False, _('msg_pw_min_length')
    if not re.search(r"[A-Z]", password):
        return False, _('msg_pw_uppercase')
    if not re.search(r"[a-z]", password):
        return False, _('msg_pw_lowercase')
    if not re.search(r"\d", password):
        return False, _('msg_pw_digit')
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, _('msg_pw_special')
    return True, _('msg_pw_valid')


def validate_email(email):
    """Allow an omitted email but reject malformed addresses."""
    return not email or bool(EMAIL_PATTERN.fullmatch(email))


def verify_password(user, password):
    """Check a password, spending the same hashing work for unknown users.

    Skipping the hash for a username that does not exist would let response
    times reveal which usernames are real.
    """
    global _dummy_password_hash
    if user is None:
        if _dummy_password_hash is None:
            _dummy_password_hash = generate_password_hash(uuid.uuid4().hex)
        check_password_hash(_dummy_password_hash, password)
        return False
    return check_password_hash(user.sifre_hash, password)


def safe_redirect_target(target):
    """Return a same-origin path for ``target``, or None for anything else."""
    if not target:
        return None
    # Browsers treat backslashes like slashes, so '/\\evil.com' means '//evil.com'.
    parsed = urlparse(target.strip().replace('\\', '/'))
    if parsed.scheme and parsed.scheme not in ('http', 'https'):
        return None
    if parsed.netloc and parsed.netloc != request.host:
        return None
    path = parsed.path or '/'
    if not path.startswith('/') or path.startswith('//'):
        return None
    return f'{path}?{parsed.query}' if parsed.query else path


def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is within allowed whitelist."""
    if not filename or '.' not in filename:
        return False
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions

def validate_file_upload(file):
    """Validate an image by decoding its bytes, not by trusting its filename."""
    if not file or file.filename == '':
        return False, _('msg_file_missing'), None

    filename = file.filename
    if '.' not in filename:
        return False, _('msg_file_invalid_format'), None

    ext = filename.rsplit('.', 1)[1].lower()
    allowed_exts = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})
    if ext not in allowed_exts:
        return False, _('msg_file_allowed_types', types=', '.join(sorted(allowed_exts))), None

    try:
        file.stream.seek(0)
        with Image.open(file.stream) as image:
            detected_format = (image.format or '').upper()
            width, height = image.size
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        return False, _('msg_file_not_image'), None
    finally:
        file.stream.seek(0)

    if detected_format != IMAGE_FORMATS[ext]:
        return False, _('msg_file_type_mismatch'), None

    if width * height > current_app.config['MAX_IMAGE_PIXELS']:
        return False, _('msg_file_too_many_pixels'), None

    return True, _('msg_file_valid'), ext

def save_avatar(file):
    """Re-encode an uploaded photo under a random name that reveals nothing."""
    is_valid, msg, ext = validate_file_upload(file)
    if not is_valid:
        return False, msg, None

    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    try:
        file.stream.seek(0)
        with Image.open(file.stream) as image:
            image = ImageOps.exif_transpose(image)
            if ext in {'jpg', 'jpeg'} and image.mode not in {'RGB', 'L'}:
                image = image.convert('RGB')
            image.save(upload_path, format=IMAGE_FORMATS[ext], optimize=True)
    except (UnidentifiedImageError, OSError, ValueError):
        return False, _('msg_file_processing_failed'), None
    return True, _('msg_file_uploaded'), unique_filename


def _is_generated_avatar(filename):
    return bool(filename) and filename not in DEFAULT_AVATARS and os.path.basename(filename) == filename


def avatar_file_path(filename):
    """Return the stored path of an uploaded avatar, or None if there is none."""
    if not _is_generated_avatar(filename):
        return None
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(path):
        return path

    legacy_path = os.path.join(current_app.config['LEGACY_UPLOAD_FOLDER'], filename)
    if not os.path.isfile(legacy_path):
        return None
    # Photos uploaded before uploads left the public static folder are moved
    # on first use, so they stop being reachable without a login.
    try:
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.replace(legacy_path, path)
        return path
    except OSError:
        current_app.logger.warning('Eski avatar taşınamadı: %s', filename)
        return legacy_path


def avatar_url(personel):
    """URL for a personnel photo; uploaded photos go through a login-protected route."""
    if personel is None or not _is_generated_avatar(personel.avatar_filename):
        return url_for('static', filename=DEFAULT_AVATAR_STATIC)
    return url_for('personel.avatar', id=personel.id)


def remove_avatar(filename):
    """Delete only a generated upload; never accept a path from user input."""
    if not _is_generated_avatar(filename):
        return
    for folder in (current_app.config['UPLOAD_FOLDER'], current_app.config['LEGACY_UPLOAD_FOLDER']):
        path = os.path.join(folder, filename)
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            current_app.logger.warning('Eski avatar silinemedi: %s', filename)

def log_action(kullanici_adi, islem_tipi, detay, ip_adresi=None, commit=True):
    """Record audit log entry in database."""
    try:
        if not ip_adresi and has_request_context():
            ip_adresi = request.remote_addr
        new_log = Log(
            kullanici_adi=(kullanici_adi or 'Bilinmeyen')[:80],
            islem_tipi=islem_tipi[:50],
            detay=detay,
            ip_adresi=ip_adresi,
            tarih_saat=utcnow()
        )
        db.session.add(new_log)
        if commit:
            db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Denetim kaydı yazılamadı.')

def get_client_ip():
    if has_request_context():
        # ProxyFix normalizes remote_addr only when explicitly configured.
        return request.remote_addr
    return '127.0.0.1'


def login_principal(username, user):
    """Name the brute-force bucket for a login attempt.

    Unknown usernames get a keyed hash so they are counted exactly like real
    accounts (the counters reveal nothing about which names exist) without
    storing what was typed, which is sometimes a password.
    """
    if user is not None:
        return user.kullanici_adi
    digest = hmac.new(
        current_app.config['SECRET_KEY'].encode('utf-8'),
        username.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    return f'?{digest[:40]}'


def login_lock_minutes(principal):
    """Minutes left on a lock for this account or this client IP, else 0."""
    ip = get_client_ip()
    now = utcnow()
    locked_rows = LoginAttempt.query.filter(
        LoginAttempt.kilitli_mi.is_(True),
        or_(LoginAttempt.kullanici_adi == principal, LoginAttempt.ip_adresi == ip),
    ).all()
    lock_ends = [as_utc(row.kilit_bitis) for row in locked_rows if row.kilit_bitis is not None]
    active = [end for end in lock_ends if end > now]
    if not active:
        return 0
    return int((max(active) - now).total_seconds() // 60) + 1


def record_login_failure(principal, display_name):
    """Count a failed login for (principal, IP); lock it at the threshold.

    Returns True when this failure triggered a lock.
    """
    ip = get_client_ip()
    now = utcnow()
    max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
    lockout = timedelta(minutes=current_app.config.get('LOCKOUT_DURATION_MINUTES', 10))

    attempt = LoginAttempt.query.filter_by(kullanici_adi=principal, ip_adresi=ip).first()
    if attempt is None:
        attempt = LoginAttempt(kullanici_adi=principal, ip_adresi=ip, deneme_sayisi=0)
        db.session.add(attempt)
    else:
        lock_expired = attempt.kilitli_mi and (
            attempt.kilit_bitis is None or as_utc(attempt.kilit_bitis) <= now
        )
        quiet = attempt.son_deneme is not None and now - as_utc(attempt.son_deneme) > lockout
        if lock_expired or quiet:
            # An expired lock or a quiet period starts a fresh counting window.
            attempt.deneme_sayisi = 0
            attempt.kilitli_mi = False
            attempt.kilit_bitis = None

    attempt.deneme_sayisi += 1
    attempt.son_deneme = now
    locked = attempt.deneme_sayisi >= max_attempts
    if locked:
        attempt.kilitli_mi = True
        attempt.kilit_bitis = now + lockout
        db.session.add(Log(
            kullanici_adi=display_name[:80],
            islem_tipi='Güvenlik Uyarısı',
            detay=f'{max_attempts} hatalı giriş nedeniyle {lockout.seconds // 60} dakika kilitlendi.',
            ip_adresi=ip,
            tarih_saat=now,
        ))

    db.session.commit()
    return locked

def clear_login_attempts(principal):
    """Clear this client's failed attempts for an account after it logs in.

    Only the (account, IP) pair is reset: logging into one account must not
    wipe the counters an attacker built up against another account.
    """
    LoginAttempt.query.filter_by(kullanici_adi=principal, ip_adresi=get_client_ip()).delete()
    db.session.commit()
