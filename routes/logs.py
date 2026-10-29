from flask import Blueprint, render_template, request
from models import Log
from utils import permission_required

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs')
@permission_required('logs')
def index():
    filter_user = request.args.get('user', '').strip()
    filter_type = request.args.get('type', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 30
    if page < 1:
        page = 1

    query = Log.query

    if filter_user:
        query = query.filter(Log.kullanici_adi.ilike(f"%{filter_user}%"))
    if filter_type:
        query = query.filter(Log.islem_tipi == filter_type)

    pagination = query.order_by(Log.tarih_saat.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        'logs.html',
        logs=pagination.items,
        pagination=pagination,
        filter_user=filter_user,
        filter_type=filter_type
    )
