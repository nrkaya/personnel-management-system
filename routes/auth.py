from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from database import db
from models import Kullanici
from utils import log_action, is_account_locked, record_login_failure, clear_login_attempts

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'kullanici_adi' in session:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        kullanici_adi = request.form.get('kullanici_adi', '').strip()
        sifre = request.form.get('sifre', '')

        # Check brute force lockout
        locked, msg = is_account_locked(kullanici_adi)
        if locked:
            flash(msg, 'error')
            return render_template('login.html', kullanici_adi=kullanici_adi)

        user = Kullanici.query.filter_by(kullanici_adi=kullanici_adi).first()

        if user and user.aktif_mi and check_password_hash(user.sifre_hash, sifre):
            session.clear()
            session['kullanici_adi'] = user.kullanici_adi
            session['rol'] = user.rol
            session['user_id'] = user.id
            session.permanent = True
            
            user.son_giris_tarihi = datetime.utcnow()
            db.session.commit()

            clear_login_attempts(kullanici_adi)
            log_action(user.kullanici_adi, 'Giriş', 'Sisteme başarıyla giriş yaptı.')
            flash(f'Hoş geldiniz, {user.kullanici_adi}!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            attempts, max_att = record_login_failure(kullanici_adi)
            kalan = max_att - attempts
            if kalan > 0:
                flash(f'Geçersiz kullanıcı adı veya şifre! (Kalan deneme hakkı: {kalan})', 'error')
            else:
                flash('5 kez hatalı giriş yapıldı! Hesabınız 10 dakika süreyle kilitlenmiştir.', 'error')
                
            log_action(kullanici_adi or 'Bilinmeyen', 'Hatalı Giriş', 'Başarısız giriş denemesi.')
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    user = session.get('kullanici_adi', 'Bilinmeyen')
    log_action(user, 'Çıkış', 'Sistemden güvenli çıkış yapıldı.')
    session.clear()
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('auth.login'))
