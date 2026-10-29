from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from database import db
from i18n import _
from models import Kullanici, LoginAttempt, Personel
from utils import (
    USERNAME_PATTERN, get_active_session_user, log_action, permission_required,
    revoke_user_sessions, validate_email, validate_password,
)

kullanici_bp = Blueprint('kullanici', __name__)

AVAILABLE_ROLES = ['Admin', 'IK', 'Mudur', 'Muhasebe']


def _department_choices():
    rows = db.session.query(Personel.departman).filter(
        Personel.departman.isnot(None), Personel.departman != ''
    ).distinct().order_by(Personel.departman).all()
    return [row[0] for row in rows]


def _active_admin_count():
    return Kullanici.query.filter_by(rol='Admin', aktif_mi=True).count()


def _clean_account_fields(form, rol):
    """Validate the editable account fields shared by the add and edit forms."""
    ad_soyad = form.get('ad_soyad', '').strip()
    email = form.get('email', '').strip()
    departman = form.get('departman', '').strip()
    if len(ad_soyad) > 120:
        raise ValueError(_('msg_fullname_too_long'))
    if len(email) > 120 or not validate_email(email):
        raise ValueError(_('msg_invalid_email'))
    if len(departman) > 100:
        raise ValueError(_('msg_field_too_long', field=_('users_field_department'), max=100))
    if rol == 'Mudur' and not departman:
        raise ValueError(_('msg_manager_needs_department'))
    # Only department managers are scoped; keep the field empty for others.
    return ad_soyad or None, email or None, (departman if rol == 'Mudur' else None)


@kullanici_bp.route('/users')
@permission_required('users')
def index():
    users = Kullanici.query.order_by(Kullanici.id.asc()).all()
    return render_template('users.html', users=users, roles=AVAILABLE_ROLES, departments=_department_choices())

@kullanici_bp.route('/users/add', methods=['POST'])
@permission_required('users')
def add():
    actor = get_active_session_user()
    kullanici_adi = request.form.get('kullanici_adi', '').strip()
    sifre = request.form.get('sifre', '')
    rol = request.form.get('rol', '')

    if rol not in AVAILABLE_ROLES:
        flash(_('msg_invalid_role'), 'error')
        return redirect(url_for('kullanici.index'))
    if not USERNAME_PATTERN.fullmatch(kullanici_adi):
        flash(_('msg_invalid_username'), 'error')
        return redirect(url_for('kullanici.index'))
    try:
        ad_soyad, email, departman = _clean_account_fields(request.form, rol)
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('kullanici.index'))
    if Kullanici.query.filter_by(kullanici_adi=kullanici_adi).first():
        flash(_('msg_username_taken'), 'error')
        return redirect(url_for('kullanici.index'))

    is_valid_pw, pw_msg = validate_password(sifre)
    if not is_valid_pw:
        flash(_('msg_password_insecure', reason=pw_msg), 'error')
        return redirect(url_for('kullanici.index'))

    new_user = Kullanici(
        kullanici_adi=kullanici_adi,
        ad_soyad=ad_soyad,
        email=email,
        departman=departman,
        sifre_hash=generate_password_hash(sifre),
        rol=rol,
        aktif_mi=True
    )
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(_('msg_username_or_email_taken'), 'error')
        return redirect(url_for('kullanici.index'))

    detail = f"Yeni kullanıcı oluşturuldu: {kullanici_adi} (Rol: {rol}"
    detail += f", Departman: {departman})" if departman else ")"
    log_action(actor.kullanici_adi, 'Kullanıcı Eklendi', detail)
    flash(_('msg_user_added', name=kullanici_adi), 'success')
    return redirect(url_for('kullanici.index'))

@kullanici_bp.route('/users/edit/<int:id>', methods=['POST'])
@permission_required('users')
def edit(id):
    actor = get_active_session_user()
    user = db.get_or_404(Kullanici, id)
    yeni_rol = request.form.get('rol', user.rol)
    aktif_mi = request.form.get('aktif_mi') == '1'

    if user.id == actor.id:
        # Admins cannot demote or disable themselves; the form locks these fields.
        yeni_rol, aktif_mi = user.rol, True
    if yeni_rol not in AVAILABLE_ROLES:
        flash(_('msg_invalid_role'), 'error')
        return redirect(url_for('kullanici.index'))
    removes_admin = user.rol == 'Admin' and user.aktif_mi and (yeni_rol != 'Admin' or not aktif_mi)
    if removes_admin and _active_admin_count() <= 1:
        flash(_('msg_last_admin'), 'error')
        return redirect(url_for('kullanici.index'))
    try:
        ad_soyad, email, departman = _clean_account_fields(request.form, yeni_rol)
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('kullanici.index'))

    changes = []
    if yeni_rol != user.rol:
        changes.append(f"rol '{user.rol}' -> '{yeni_rol}'")
    if departman != user.departman:
        changes.append(f"departman '{user.departman or '-'}' -> '{departman or '-'}'")
    if aktif_mi != user.aktif_mi:
        changes.append('aktif edildi' if aktif_mi else 'pasif edildi')
    if ad_soyad != user.ad_soyad or email != user.email:
        changes.append('iletişim bilgileri güncellendi')

    if user.aktif_mi and not aktif_mi:
        revoke_user_sessions(user)
    user.rol = yeni_rol
    user.departman = departman
    user.aktif_mi = aktif_mi
    user.ad_soyad = ad_soyad
    user.email = email
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(_('msg_username_or_email_taken'), 'error')
        return redirect(url_for('kullanici.index'))

    if changes:
        log_action(actor.kullanici_adi, 'Kullanıcı Güncellendi', f"{user.kullanici_adi}: {', '.join(changes)}.")
    flash(_('msg_user_updated', name=user.kullanici_adi), 'success')
    return redirect(url_for('kullanici.index'))

@kullanici_bp.route('/users/reset_password/<int:id>', methods=['POST'])
@permission_required('users')
def reset_password(id):
    actor = get_active_session_user()
    user = db.get_or_404(Kullanici, id)
    if user.id == actor.id:
        flash(_('msg_use_account_page'), 'error')
        return redirect(url_for('auth.change_password'))

    sifre = request.form.get('sifre', '')
    if sifre != request.form.get('sifre_tekrar', ''):
        flash(_('msg_passwords_mismatch'), 'error')
        return redirect(url_for('kullanici.index'))
    is_valid_pw, pw_msg = validate_password(sifre)
    if not is_valid_pw:
        flash(_('msg_password_insecure', reason=pw_msg), 'error')
        return redirect(url_for('kullanici.index'))

    user.sifre_hash = generate_password_hash(sifre)
    revoke_user_sessions(user)
    # A reset also lifts any brute-force lock on the account.
    LoginAttempt.query.filter_by(kullanici_adi=user.kullanici_adi).delete()
    db.session.commit()

    log_action(actor.kullanici_adi, 'Şifre Sıfırlandı', f"{user.kullanici_adi} kullanıcısının şifresi sıfırlandı; açık oturumları kapatıldı.")
    flash(_('msg_password_reset', name=user.kullanici_adi), 'success')
    return redirect(url_for('kullanici.index'))

@kullanici_bp.route('/users/delete/<int:id>', methods=['POST'])
@permission_required('users')
def delete(id):
    actor = get_active_session_user()
    user = db.get_or_404(Kullanici, id)
    if user.id == actor.id:
        flash(_('msg_cannot_delete_self'), 'error')
        return redirect(url_for('kullanici.index'))

    if user.rol == 'Admin' and user.aktif_mi and _active_admin_count() <= 1:
        flash(_('msg_last_admin'), 'error')
        return redirect(url_for('kullanici.index'))

    uname = user.kullanici_adi
    db.session.delete(user)
    LoginAttempt.query.filter_by(kullanici_adi=uname).delete()
    db.session.commit()

    log_action(actor.kullanici_adi, 'Kullanıcı Silindi', f"Kullanıcı silindi: {uname} (ID: {id})")
    flash(_('msg_user_deleted', name=uname), 'success')
    return redirect(url_for('kullanici.index'))
