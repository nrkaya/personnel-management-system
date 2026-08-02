from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, session, redirect, url_for
from sqlalchemy import func
from database import db
from models import Personel, Kullanici, Izin, Log

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def index():
    if 'kullanici_adi' not in session:
        return redirect(url_for('auth.login'))
        
    today = date.today()
    next_14_days = today + timedelta(days=14)
    
    total_personnel = Personel.query.filter_by(aktif_mi=True).count()
    total_users = Kullanici.query.filter_by(aktif_mi=True).count()
    
    # Active leaves count
    active_leaves_count = Izin.query.join(Personel).filter(
        Personel.aktif_mi == True,
        Izin.durum == 'Onaylandı',
        Izin.baslangic <= today,
        Izin.bitis >= today
    ).count()

    # Upcoming leaves in 14 days
    upcoming_leaves = Izin.query.join(Personel).filter(
        Personel.aktif_mi == True,
        Izin.durum == 'Onaylandı',
        Izin.baslangic > today,
        Izin.baslangic <= next_14_days
    ).order_by(Izin.baslangic.asc()).limit(5).all()

    # Birthdays today (DB-agnostic filter)
    all_with_birthday = Personel.query.filter(
        Personel.aktif_mi == True,
        Personel.dogum_tarihi.isnot(None)
    ).all()
    birthdays_today = [
        p for p in all_with_birthday 
        if p.dogum_tarihi and p.dogum_tarihi.month == today.month and p.dogum_tarihi.day == today.day
    ]

    # Department distribution for Chart.js
    dept_stats = db.session.query(
        Personel.departman,
        func.count(Personel.id).label('count')
    ).filter(
        Personel.aktif_mi == True,
        Personel.departman.isnot(None),
        Personel.departman != ''
    ).group_by(Personel.departman).all()

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
