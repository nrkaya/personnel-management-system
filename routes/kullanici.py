from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from database import db
from models import Kullanici
from utils import role_required, validate_password, log_action

kullanici_bp = Blueprint('kullanici', __name__)

AVAILABLE_ROLES = ['Admin', 'IK', 'Mudur', 'Muhasebe']

@kullanici_bp.route('/users')
@role_required('Admin')
def index():
    users = Kullanici.query.order_by(Kullanici.id.asc()).all()
    return render_template('users.html', users=users, roles=AVAILABLE_ROLES)

@kullanici_bp.route('/users/add', methods=['POST'])
@role_required('Admin')
def add():
    kullanici_adi = request.form.get('kullanici_adi', '').strip()
    ad_soyad = request.form.get('ad_soyad', '').strip()
    email = request.form.get('email', '').strip()
    sifre = request.form.get('sifre', '')
    rol = request.form.get('rol', 'IK')

    if rol not in AVAILABLE_ROLES:
        rol = 'IK'

    if Kullanici.query.filter_by(kullanici_adi=kullanici_adi).first():
        flash('Bu kullanıcı adı zaten kullanılmaktadır.', 'error')
        return redirect(url_for('kullanici.index'))

    is_valid_pw, pw_msg = validate_password(sifre)
    if not is_valid_pw:
        flash(f'Güvensiz Şifre: {pw_msg}', 'error')
        return redirect(url_for('kullanici.index'))

    new_user = Kullanici(
        kullanici_adi=kullanici_adi,
        ad_soyad=ad_soyad,
        email=email if email else None,
        sifre_hash=generate_password_hash(sifre),
        rol=rol,
        aktif_mi=True
    )
    db.session.add(new_user)
    db.session.commit()

    log_action(session['kullanici_adi'], 'Kullanıcı Eklendi', f"Yeni kullanıcı oluşturuldu: {kullanici_adi} (Rol: {rol})")
    flash(f'{kullanici_adi} kullanıcısı başarıyla eklendi.', 'success')
    return redirect(url_for('kullanici.index'))

@kullanici_bp.route('/users/edit_role/<int:id>', methods=['POST'])
@role_required('Admin')
def edit_role(id):
    user = Kullanici.query.get_or_404(id)
    if user.kullanici_adi == 'admin' and session['kullanici_adi'] != 'admin':
        flash('Ana yönetici hesabı değiştirilemez.', 'error')
        return redirect(url_for('kullanici.index'))

    yeni_rol = request.form.get('rol')
    if yeni_rol in AVAILABLE_ROLES:
        eski_rol = user.rol
        user.rol = yeni_rol
        db.session.commit()
        log_action(session['kullanici_adi'], 'Rol Değiştirildi', f"{user.kullanici_adi} rolü '{eski_rol}' -> '{yeni_rol}' yapıldı.")
        flash(f'{user.kullanici_adi} rolü güncellendi.', 'success')
    return redirect(url_for('kullanici.index'))

@kullanici_bp.route('/users/delete/<int:id>', methods=['POST'])
@role_required('Admin')
def delete(id):
    user = Kullanici.query.get_or_404(id)
    if user.kullanici_adi == 'admin':
        flash('Ana yönetici hesabı silinemez!', 'error')
        return redirect(url_for('kullanici.index'))

    if user.kullanici_adi == session['kullanici_adi']:
        flash('Kendinizi silemezsiniz!', 'error')
        return redirect(url_for('kullanici.index'))

    uname = user.kullanici_adi
    db.session.delete(user)
    db.session.commit()

    log_action(session['kullanici_adi'], 'Kullanıcı Silindi', f"Kullanıcı silindi: {uname} (ID: {id})")
    flash(f'{uname} kullanıcısı silindi.', 'success')
    return redirect(url_for('kullanici.index'))
