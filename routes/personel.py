import io
import math
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, current_app, abort
from sqlalchemy import or_
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from database import db
from models import Personel, Izin
from utils import role_required, has_permission, save_avatar, log_action

personel_bp = Blueprint('personel', __name__)

@personel_bp.route('/personeller')
def index():
    if 'kullanici_adi' not in session:
        return redirect(url_for('auth.login'))

    user_role = session.get('rol', '')
    search_query = request.args.get('q', '').strip()
    filter_dept = request.args.get('departman', '').strip()
    filter_pos = request.args.get('pozisyon', '').strip()
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1
    per_page = 20

    query = Personel.query.filter_by(aktif_mi=True)

    if search_query:
        search_terms = f"%{search_query}%"
        query = query.filter(or_(
            Personel.ad.ilike(search_terms),
            Personel.soyad.ilike(search_terms),
            Personel.telefon.ilike(search_terms),
            Personel.email.ilike(search_terms)
        ))

    if filter_dept:
        query = query.filter(Personel.departman == filter_dept)

    if filter_pos:
        query = query.filter(Personel.pozisyon == filter_pos)

    total_items = query.count()
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
    if page > total_pages:
        page = total_pages

    personeller = query.order_by(Personel.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    departments = [r[0] for r in db.session.query(Personel.departman).filter(
        Personel.aktif_mi == True, Personel.departman.isnot(None), Personel.departman != ''
    ).distinct().all()]

    positions = [r[0] for r in db.session.query(Personel.pozisyon).filter(
        Personel.aktif_mi == True, Personel.pozisyon.isnot(None), Personel.pozisyon != ''
    ).distinct().all()]

    return render_template(
        'index.html',
        personeller=personeller,
        departments=departments,
        positions=positions,
        search_query=search_query,
        filter_dept=filter_dept,
        filter_pos=filter_pos,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        per_page=per_page,
        can_edit=has_permission(user_role, 'edit'),
        can_delete=has_permission(user_role, 'delete'),
        can_add=has_permission(user_role, 'add'),
        can_view_salary=has_permission(user_role, 'salary')
    )

@personel_bp.route('/personel/<int:id>')
def profile(id):
    if 'kullanici_adi' not in session:
        return redirect(url_for('auth.login'))

    user_role = session.get('rol', '')
    p = Personel.query.get_or_404(id)
    if not p.aktif_mi and user_role not in ['Admin', 'IK']:
        flash('Bu personel kaydına erişim izniniz yok.', 'error')
        return redirect(url_for('personel.index'))

    izinler = Izin.query.filter_by(personel_id=id).order_by(Izin.baslangic.desc()).all()

    return render_template(
        'profile.html',
        p=p,
        izinler=izinler,
        can_edit=has_permission(user_role, 'edit'),
        can_delete=has_permission(user_role, 'delete'),
        can_view_salary=has_permission(user_role, 'salary'),
        can_manage_leaves=has_permission(user_role, 'leaves')
    )

@personel_bp.route('/add', methods=['POST'])
@role_required('Admin', 'IK')
def add():
    ad = request.form.get('ad', '').strip()
    soyad = request.form.get('soyad', '').strip()
    departman = request.form.get('departman', '').strip()
    pozisyon = request.form.get('pozisyon', '').strip()
    telefon = request.form.get('telefon', '').strip()
    email = request.form.get('email', '').strip()
    ek_bilgi = request.form.get('ek_bilgi', '').strip()
    maas_str = request.form.get('maas', '0').strip()
    ise_giris_str = request.form.get('ise_giris_tarihi')
    dogum_str = request.form.get('dogum_tarihi')

    try:
        maas = float(maas_str) if maas_str else 0.0
    except ValueError:
        maas = 0.0

    ise_giris = datetime.strptime(ise_giris_str, '%Y-%m-%d').date() if ise_giris_str else date.today()
    dogum_tarihi = datetime.strptime(dogum_str, '%Y-%m-%d').date() if dogum_str else None

    # Handle avatar file upload
    avatar_file = request.files.get('avatar')
    avatar_path = 'default.png'
    if avatar_file and avatar_file.filename != '':
        success, msg, filename = save_avatar(avatar_file, ad, soyad)
        if success:
            avatar_path = filename
        else:
            flash(f"Fotoğraf yüklenemedi: {msg}", 'error')
            return redirect(url_for('personel.index'))

    new_personel = Personel(
        ad=ad,
        soyad=soyad,
        departman=departman,
        pozisyon=pozisyon,
        telefon=telefon,
        email=email,
        ek_bilgi=ek_bilgi,
        maas=maas,
        ise_giris_tarihi=ise_giris,
        dogum_tarihi=dogum_tarihi,
        avatar_path=avatar_path,
        aktif_mi=True
    )
    db.session.add(new_personel)
    db.session.commit()

    log_action(session['kullanici_adi'], 'Personel Eklendi', f"{new_personel.tam_ad} (ID: {new_personel.id}) sisteme eklendi.")
    flash(f'{new_personel.tam_ad} başarıyla eklendi.', 'success')
    return redirect(url_for('personel.index'))

@personel_bp.route('/edit/<int:id>', methods=['POST'])
@role_required('Admin', 'IK')
def edit(id):
    p = Personel.query.get_or_404(id)
    p.ad = request.form.get('ad', p.ad).strip()
    p.soyad = request.form.get('soyad', p.soyad).strip()
    p.departman = request.form.get('departman', p.departman).strip()
    p.pozisyon = request.form.get('pozisyon', p.pozisyon).strip()
    p.telefon = request.form.get('telefon', p.telefon).strip()
    p.email = request.form.get('email', p.email).strip()
    p.ek_bilgi = request.form.get('ek_bilgi', p.ek_bilgi).strip()

    maas_str = request.form.get('maas')
    if maas_str and has_permission(session.get('rol'), 'salary'):
        try:
            p.maas = float(maas_str)
        except ValueError:
            pass

    ise_giris_str = request.form.get('ise_giris_tarihi')
    if ise_giris_str:
        try:
            p.ise_giris_tarihi = datetime.strptime(ise_giris_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    dogum_str = request.form.get('dogum_tarihi')
    if dogum_str:
        try:
            p.dogum_tarihi = datetime.strptime(dogum_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename != '':
        success, msg, filename = save_avatar(avatar_file, p.ad, p.soyad)
        if success:
            p.avatar_path = filename
        else:
            flash(f"Fotoğraf güncellenemedi: {msg}", 'error')
            return redirect(url_for('personel.profile', id=id))

    db.session.commit()
    log_action(session['kullanici_adi'], 'Personel Güncellendi', f"{p.tam_ad} (ID: {p.id}) bilgileri güncellendi.")
    flash(f'{p.tam_ad} bilgileri başarıyla güncellendi.', 'success')
    return redirect(url_for('personel.profile', id=id))

@personel_bp.route('/delete/<int:id>', methods=['POST'])
@role_required('Admin', 'IK')
def delete(id):
    p = Personel.query.get_or_404(id)
    p.aktif_mi = False
    db.session.commit()

    log_action(session['kullanici_adi'], 'Personel Silindi (Çöp Kutusu)', f"{p.tam_ad} (ID: {p.id}) arşive taşındı.")
    flash(f'{p.tam_ad} çöp kutusuna taşındı.', 'success')
    return redirect(url_for('personel.index'))

@personel_bp.route('/trash')
@role_required('Admin', 'IK')
def trash():
    deleted_personnel = Personel.query.filter_by(aktif_mi=False).order_by(Personel.guncellenme_tarihi.desc()).all()
    return render_template('trash.html', personeller=deleted_personnel)

@personel_bp.route('/personel/restore/<int:id>', methods=['POST'])
@role_required('Admin', 'IK')
def restore(id):
    p = Personel.query.get_or_404(id)
    p.aktif_mi = True
    db.session.commit()

    log_action(session['kullanici_adi'], 'Personel Geri Yüklendi', f"{p.tam_ad} (ID: {p.id}) arşivden geri yüklendi.")
    flash(f'{p.tam_ad} başarıyla geri yüklendi.', 'success')
    return redirect(url_for('personel.trash'))

@personel_bp.route('/personel/hard_delete/<int:id>', methods=['POST'])
@role_required('Admin')
def hard_delete(id):
    p = Personel.query.get_or_404(id)
    tam_ad = p.tam_ad
    db.session.delete(p)
    db.session.commit()

    log_action(session['kullanici_adi'], 'Kalıcı Silme', f"{tam_ad} (ID: {id}) sistemden kalıcı olarak silindi.")
    flash(f'{tam_ad} sistemden kalıcı olarak silindi.', 'success')
    return redirect(url_for('personel.trash'))

@personel_bp.route('/export')
def export_excel():
    """Export formatted personnel dataset to Excel (.xlsx)."""
    if 'kullanici_adi' not in session:
        return redirect(url_for('auth.login'))

    user_role = session.get('rol', '')
    can_see_salary = has_permission(user_role, 'salary')

    personeller = Personel.query.filter_by(aktif_mi=True).order_by(Personel.id.asc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Personel Listesi"

    headers = ["ID", "Ad", "Soyad", "Departman", "Pozisyon", "Telefon", "E-Posta", "İşe Giriş Tarihi"]
    if can_see_salary:
        headers.append("Maaş (₺)")

    ws.append(headers)

    header_font = Font(name='Segoe UI', size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="2563EB")
    alignment_center = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = alignment_center
        cell.border = thin_border

    for row_idx, p in enumerate(personeller, start=2):
        row_data = [
            p.id,
            p.ad,
            p.soyad,
            p.departman or '-',
            p.pozisyon or '-',
            p.telefon or '-',
            p.email or '-',
            p.ise_giris_tarihi.strftime('%Y-%m-%d') if p.ise_giris_tarihi else '-'
        ]
        if can_see_salary:
            row_data.append(p.maas)

        ws.append(row_data)
        
        # Zebra striping
        fill_color = "F9FAFB" if row_idx % 2 == 0 else "FFFFFF"
        for col_idx in range(1, len(row_data) + 1):
            c = ws.cell(row=row_idx, column=col_idx)
            c.fill = PatternFill("solid", fgColor=fill_color)
            c.border = thin_border
            if col_idx in [1, 6, 8]:
                c.alignment = alignment_center

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            val_str = str(cell.value or '')
            if len(val_str) > max_length:
                max_length = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_length + 4, 12)

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)

    log_action(session['kullanici_adi'], 'Dışa Aktarma', 'Personel listesi Excel (.xlsx) olarak indirildi.')
    return send_file(
        out,
        download_name=f"KAYA_PTS_Personel_Listesi_{datetime.now().strftime('%Y%m%d')}.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
