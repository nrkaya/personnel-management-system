from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from database import db
from models import Izin, Personel
from utils import role_required, has_permission, log_action

izin_bp = Blueprint('izin', __name__)

@izin_bp.route('/izinler')
def index():
    if 'kullanici_adi' not in session:
        return redirect(url_for('auth.login'))

    user_role = session.get('rol', '')
    filter_tur = request.args.get('tur', '').strip()
    filter_durum = request.args.get('durum', '').strip()

    query = Izin.query.join(Personel)

    if filter_tur:
        query = query.filter(Izin.tur == filter_tur)
    if filter_durum:
        query = query.filter(Izin.durum == filter_durum)

    izinler = query.order_by(Izin.baslangic.desc()).all()

    return render_template(
        'izinler.html',
        izinler=izinler,
        filter_tur=filter_tur,
        filter_durum=filter_durum,
        can_manage=has_permission(user_role, 'leaves')
    )

@izin_bp.route('/izin/ekle/<int:personel_id>', methods=['POST'])
@role_required('Admin', 'IK', 'Mudur')
def ekle(personel_id):
    p = Personel.query.get_or_404(personel_id)
    baslangic_str = request.form.get('baslangic')
    bitis_str = request.form.get('bitis')
    tur = request.form.get('tur', 'Yıllık İzin')
    aciklama = request.form.get('aciklama', '').strip()

    try:
        baslangic = datetime.strptime(baslangic_str, '%Y-%m-%d').date()
        bitis = datetime.strptime(bitis_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Geçersiz tarih aralığı girdiniz.', 'error')
        return redirect(url_for('personel.profile', id=personel_id))

    if bitis < baslangic:
        flash('Bitiş tarihi başlangıç tarihinden önce olamaz.', 'error')
        return redirect(url_for('personel.profile', id=personel_id))

    yeni_izin = Izin(
        personel_id=personel_id,
        baslangic=baslangic,
        bitis=bitis,
        tur=tur,
        durum='Onaylandı',
        kullanici_adi=session['kullanici_adi'],
        aciklama=aciklama
    )
    db.session.add(yeni_izin)
    db.session.commit()

    log_action(session['kullanici_adi'], 'İzin Eklendi', f"{p.tam_ad} için {baslangic} - {bitis} arası {tur} eklendi.")
    flash(f'{p.tam_ad} için {tur} başarıyla kaydedildi.', 'success')
    return redirect(url_for('personel.profile', id=personel_id))

@izin_bp.route('/izin/durum/<int:id>', methods=['POST'])
@role_required('Admin', 'IK', 'Mudur')
def durum_guncelle(id):
    izin = Izin.query.get_or_404(id)
    yeni_durum = request.form.get('durum', 'Onaylandı')
    izin.durum = yeni_durum
    db.session.commit()

    log_action(session['kullanici_adi'], 'İzin Durumu Güncellendi', f"İzin #{id} durumu '{yeni_durum}' yapıldı.")
    flash(f'İzin durumu {yeni_durum} olarak güncellendi.', 'success')
    return redirect(request.referrer or url_for('izin.index'))

@izin_bp.route('/izin/sil/<int:id>', methods=['POST'])
@role_required('Admin', 'IK')
def sil(id):
    izin = Izin.query.get_or_404(id)
    pid = izin.personel_id
    db.session.delete(izin)
    db.session.commit()

    log_action(session['kullanici_adi'], 'İzin Silindi', f"İzin kaydı silindi (ID: {id})")
    flash('İzin kaydı silindi.', 'success')
    return redirect(url_for('personel.profile', id=pid))
