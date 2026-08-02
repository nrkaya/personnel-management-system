from flask import Blueprint, render_template, request, session, redirect, url_for
from models import Log
from utils import role_required

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs')
@role_required('Admin')
def index():
    filter_user = request.args.get('user', '').strip()
    filter_type = request.args.get('type', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 30

    query = Log.query

    if filter_user:
        query = query.filter(Log.kullanici_adi.ilike(f"%{filter_user}%"))
    if filter_type:
        query = query.filter(Log.islem_tipi == filter_type)

    logs = query.order_by(Log.tarih_saat.desc()).limit(150).all()

    return render_template(
        'logs.html',
        logs=logs,
        filter_user=filter_user,
        filter_type=filter_type
    )
