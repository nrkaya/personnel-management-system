from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from database import db, limiter
from i18n import _
from models import Kullanici
from utils import (
    clear_login_attempts, end_user_session, get_active_session_user, log_action,
    login_lock_minutes, login_principal, permission_required, record_login_failure,
    revoke_user_sessions, start_user_session, utcnow, validate_password, verify_password,
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def login():
    if session.get('user_id') and get_active_session_user() is not None:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        kullanici_adi = request.form.get('kullanici_adi', '').strip()
        sifre = request.form.get('sifre', '')

        user = Kullanici.query.filter_by(kullanici_adi=kullanici_adi).first() if kullanici_adi else None
        # Hash before any branching so known and unknown names cost the same.
        password_ok = verify_password(user, sifre)
        principal = login_principal(kullanici_adi, user)
        # Never log what was typed for an unknown name: it is often a password.
        display_name = user.kullanici_adi if user else 'Bilinmeyen'

        lock_minutes = login_lock_minutes(principal)
        if lock_minutes:
            flash(_('msg_login_locked', minutes=lock_minutes), 'error')
            return render_template('login.html', kullanici_adi=kullanici_adi)

        if user and user.aktif_mi and password_ok:
            start_user_session(user)
            user.son_giris_tarihi = utcnow()
            db.session.commit()

            clear_login_attempts(principal)
            log_action(user.kullanici_adi, 'Giriş', 'Sisteme başarıyla giriş yaptı.')
            flash(_('msg_welcome', name=user.ad_soyad or user.kullanici_adi), 'success')
            return redirect(url_for('dashboard.index'))

        log_action(display_name, 'Hatalı Giriş', 'Başarısız giriş denemesi.')
        if record_login_failure(principal, display_name):
            flash(_('msg_login_locked', minutes=login_lock_minutes(principal)), 'error')
        else:
            # The same message for every failure, so it says nothing about
            # whether the username exists or how many tries are left.
            flash(_('msg_login_invalid'), 'error')
        return render_template('login.html', kullanici_adi=kullanici_adi)

    return render_template('login.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    user = get_active_session_user() if session.get('user_id') else None
    if user is not None:
        # Revoke this and every other copy of the session cookie.
        revoke_user_sessions(user)
        db.session.commit()
        log_action(user.kullanici_adi, 'Çıkış', 'Sistemden güvenli çıkış yapıldı.')
    end_user_session()
    flash(_('msg_logout_success'), 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/hesap/sifre', methods=['GET', 'POST'])
@permission_required()
@limiter.limit('10 per minute', methods=['POST'])
def change_password():
    """Let any logged-in user change their own password."""
    user = get_active_session_user()
    if request.method == 'POST':
        mevcut = request.form.get('mevcut_sifre', '')
        yeni = request.form.get('yeni_sifre', '')
        tekrar = request.form.get('yeni_sifre_tekrar', '')

        valid, message = validate_password(yeni)
        if not verify_password(user, mevcut):
            flash(_('msg_current_password_wrong'), 'error')
        elif yeni != tekrar:
            flash(_('msg_passwords_mismatch'), 'error')
        elif yeni == mevcut:
            flash(_('msg_password_must_differ'), 'error')
        elif not valid:
            flash(_('msg_password_insecure', reason=message), 'error')
        else:
            user.sifre_hash = generate_password_hash(yeni)
            # Sign out every other device, then keep this session alive.
            revoke_user_sessions(user)
            db.session.commit()
            start_user_session(user)
            log_action(user.kullanici_adi, 'Şifre Değiştirildi', 'Kullanıcı kendi şifresini değiştirdi; diğer oturumlar kapatıldı.')
            flash(_('msg_password_changed'), 'success')
            return redirect(url_for('dashboard.index'))

    return render_template('account.html')
