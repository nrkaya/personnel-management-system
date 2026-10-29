from datetime import date, timedelta
from flask import Blueprint, render_template
from sqlalchemy import extract, func
from database import db
from models import Personel, Kullanici, Izin, Log
from utils import get_active_session_user, has_permission, permission_required, scope_personnel

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@permission_required('view')
def index():
    user = get_active_session_user()
    today = date.today()
    next_14_days = today + timedelta(days=14)

    # Head counts and the department chart are aggregates; the lists below name
    # people and therefore follow the user's department scope.
    total_personnel = Personel.query.filter_by(aktif_mi=True).count()
    total_users = Kullanici.query.filter_by(aktif_mi=True).count()

    # Active leaves count
    active_leaves_count = Izin.query.join(Personel).filter(
        Personel.aktif_mi == True,
        Izin.durum == 'Onaylandı',
        Izin.baslangic <= today,
        Izin.bitis >= today
    ).count()

    # Upcoming leaves in 14 days (includes pending and approved)
    upcoming_leaves = scope_personnel(Izin.query.join(Personel).filter(
        Personel.aktif_mi == True,
        Izin.durum.in_(['Onaylandı', 'Beklemede']),
        Izin.baslangic >= today,
        Izin.baslangic <= next_14_days
    ), user).order_by(Izin.baslangic.asc()).limit(5).all()

    # A birthday reveals part of the birth date, which only roles with the
    # 'personal' permission may see. Filter in the database, not in Python.
    birthdays_today = []
    if has_permission(user.rol, 'personal'):
        birthdays_today = scope_personnel(Personel.query.filter(
            Personel.aktif_mi == True,
            Personel.dogum_tarihi.isnot(None),
            extract('month', Personel.dogum_tarihi) == today.month,
            extract('day', Personel.dogum_tarihi) == today.day,
        ), user).all()

    # Department distribution for Chart.js
    dept_stats = db.session.query(
        Personel.departman,
        func.count(Personel.id).label('count')
    ).filter(
        Personel.aktif_mi == True,
        Personel.departman.isnot(None),
        Personel.departman != ''
    ).group_by(Personel.departman).all()

    # The audit trail is restricted to roles that may read the log page.
    recent_logs = []
    if has_permission(user.rol, 'logs'):
        recent_logs = Log.query.order_by(Log.tarih_saat.desc()).limit(6).all()

    return render_template(
        'dashboard.html',
        total_personnel=total_personnel,
        total_users=total_users,
        active_leaves_count=active_leaves_count,
        upcoming_leaves=upcoming_leaves,
        birthdays_today=birthdays_today,
        dept_stats=dept_stats,
        recent_logs=recent_logs
    )
