from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from sqlalchemy.orm import selectinload
from database import db
from i18n import _
from models import Izin, Personel
from utils import (
    can_access_personnel, get_active_session_user, log_action, permission_required,
    safe_redirect_target, scope_personnel, utcnow,
)

izin_bp = Blueprint('izin', __name__)

LEAVE_TYPES = {'Yıllık İzin', 'Mazeret İzni', 'Hastalık Raporu', 'Ücretsiz İzin', 'Doğum İzni'}
LEAVE_STATUSES = {'Beklemede', 'Onaylandı', 'Reddedildi'}
MAX_REASON_LENGTH = 1000
PER_PAGE = 30


def _get_visible_leave(id):
    izin = db.get_or_404(Izin, id)
    if izin.personel is None or not can_access_personnel(izin.personel):
        abort(404)
    return izin


@izin_bp.route('/izinler')
@permission_required('view')
def index():
    filter_tur = request.args.get('tur', '').strip()
    filter_durum = request.args.get('durum', '').strip()
    page = max(request.args.get('page', 1, type=int) or 1, 1)

    query = scope_personnel(
        Izin.query.join(Personel).options(selectinload(Izin.personel)).filter(Personel.aktif_mi.is_(True))
    )

    if filter_tur in LEAVE_TYPES:
        query = query.filter(Izin.tur == filter_tur)
    if filter_durum in LEAVE_STATUSES:
        query = query.filter(Izin.durum == filter_durum)

    pagination = query.order_by(Izin.baslangic.desc(), Izin.id.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )

    return render_template(
        'izinler.html',
        izinler=pagination.items,
        pagination=pagination,
        filter_tur=filter_tur,
        filter_durum=filter_durum,
    )

@izin_bp.route('/izin/ekle/<int:personel_id>', methods=['POST'])
@permission_required('leaves')
def ekle(personel_id):
    user = get_active_session_user()
    p = db.get_or_404(Personel, personel_id)
    if not p.aktif_mi or not can_access_personnel(p, user):
        abort(404)
    baslangic_str = request.form.get('baslangic')
    bitis_str = request.form.get('bitis')
    tur = request.form.get('tur', 'Yıllık İzin')
    aciklama = request.form.get('aciklama', '').strip()

    try:
        baslangic = datetime.strptime(baslangic_str, '%Y-%m-%d').date()
        bitis = datetime.strptime(bitis_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash(_('msg_leave_invalid_dates'), 'error')
        return redirect(url_for('personel.profile', id=personel_id))

    if bitis < baslangic:
        flash(_('msg_leave_end_before_start'), 'error')
        return redirect(url_for('personel.profile', id=personel_id))

    if tur not in LEAVE_TYPES:
        flash(_('msg_leave_invalid_type'), 'error')
        return redirect(url_for('personel.profile', id=personel_id))

    if len(aciklama) > MAX_REASON_LENGTH:
        flash(_('msg_field_too_long', field=_('leaves_modal_reason'), max=MAX_REASON_LENGTH), 'error')
        return redirect(url_for('personel.profile', id=personel_id))

    overlaps = Izin.query.filter(
        Izin.personel_id == personel_id,
        Izin.durum.in_(['Beklemede', 'Onaylandı']),
        Izin.baslangic <= bitis,
        Izin.bitis >= baslangic,
    ).first()
    if overlaps:
        flash(_('msg_leave_overlap'), 'error')
        return redirect(url_for('personel.profile', id=personel_id))

    yeni_izin = Izin(
        personel_id=personel_id,
        baslangic=baslangic,
        bitis=bitis,
        tur=tur,
        durum='Beklemede',
        kullanici_adi=user.kullanici_adi,
        aciklama=aciklama or None
    )
    db.session.add(yeni_izin)
    db.session.commit()

    log_action(user.kullanici_adi, 'İzin Talebi Oluşturuldu', f"{p.tam_ad} için {baslangic} - {bitis} arası {tur} talebi oluşturuldu.")
    flash(_('msg_leave_created', name=p.tam_ad, type=_(tur)), 'success')
    return redirect(url_for('personel.profile', id=personel_id))

@izin_bp.route('/izin/durum/<int:id>', methods=['POST'])
@permission_required('leaves')
def durum_guncelle(id):
    user = get_active_session_user()
    izin = _get_visible_leave(id)
    yeni_durum = request.form.get('durum', '')
    back = safe_redirect_target(request.referrer) or url_for('izin.index')
    if yeni_durum not in LEAVE_STATUSES:
        flash(_('msg_leave_invalid_status'), 'error')
        return redirect(back)
    eski_durum = izin.durum
    izin.durum = yeni_durum
    izin.onaylayan_kullanici_adi = user.kullanici_adi
    izin.karar_tarihi = utcnow()
    db.session.commit()

    log_action(user.kullanici_adi, 'İzin Durumu Güncellendi', f"İzin #{id} ({izin.personel.tam_ad}) durumu '{eski_durum}' -> '{yeni_durum}' yapıldı.")
    flash(_('msg_leave_status_updated', status=_(yeni_durum)), 'success')
    return redirect(back)

@izin_bp.route('/izin/sil/<int:id>', methods=['POST'])
@permission_required('leave_delete')
def sil(id):
    user = get_active_session_user()
    izin = _get_visible_leave(id)
    pid = izin.personel_id
    detail = f"{izin.personel.tam_ad} için {izin.baslangic} - {izin.bitis} arası {izin.tur} kaydı silindi (İzin #{id}, durum: {izin.durum})."
    db.session.delete(izin)
    db.session.commit()

    log_action(user.kullanici_adi, 'İzin Silindi', detail)
    flash(_('msg_leave_deleted'), 'success')
    return redirect(url_for('personel.profile', id=pid))
