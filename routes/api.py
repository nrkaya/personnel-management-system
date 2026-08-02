from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, request, current_app
from database import db, csrf
from models import Personel, Izin, Kullanici, Log

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Exempt API blueprint from CSRF verification
csrf.exempt(api_bp)

def api_key_required(f):
    """Authenticate API requests via X-API-KEY header or Bearer token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY') or request.headers.get('Authorization', '').replace('Bearer ', '')
        expected_key = current_app.config.get('API_KEY', 'kaya-pts-enterprise-api-key-2026')
        
        if not api_key or api_key != expected_key:
            return jsonify({
                'success': False,
                'error': 'Unauthorized: Valid X-API-KEY or Bearer token required.'
            }), 401
        return f(*args, **kwargs)
    return decorated

@api_bp.route('/docs')
def api_docs():
    """RESTful API documentation endpoint."""
    return jsonify({
        'title': 'KAYA PTS Enterprise REST API',
        'version': '1.0.0',
        'description': 'Kaya Personnel Tracking System RESTful Web Services',
        'auth_method': 'Header: X-API-KEY or Authorization: Bearer <API_KEY>',
        'endpoints': [
            {'method': 'GET', 'path': '/api/v1/personeller', 'desc': 'List active personnel (supports search & pagination)'},
            {'method': 'GET', 'path': '/api/v1/personel/<id>', 'desc': 'Get detailed personnel record'},
            {'method': 'POST', 'path': '/api/v1/personel', 'desc': 'Create personnel record (JSON body)'},
            {'method': 'PUT', 'path': '/api/v1/personel/<id>', 'desc': 'Update personnel record'},
            {'method': 'DELETE', 'path': '/api/v1/personel/<id>', 'desc': 'Soft-delete personnel record'},
            {'method': 'GET', 'path': '/api/v1/stats', 'desc': 'Retrieve company personnel and leave metrics'}
        ]
    })

@api_bp.route('/personeller', methods=['GET'])
@api_key_required
def get_personeller():
    q = request.args.get('q', '').strip()
    dept = request.args.get('departman', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Personel.query.filter_by(aktif_mi=True)
    if q:
        search_terms = f"%{q}%"
        query = query.filter((Personel.ad.ilike(search_terms)) | (Personel.soyad.ilike(search_terms)))
    if dept:
        query = query.filter_by(departman=dept)

    total = query.count()
    items = query.order_by(Personel.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'success': True,
        'total': total,
        'page': page,
        'per_page': per_page,
        'data': [p.to_dict(include_salary=True) for p in items]
    })

@api_bp.route('/personel/<int:id>', methods=['GET'])
@api_key_required
def get_personel(id):
    p = Personel.query.filter_by(id=id, aktif_mi=True).first()
    if not p:
        return jsonify({'success': False, 'error': 'Personel not found'}), 404
    return jsonify({'success': True, 'data': p.to_dict(include_salary=True)})

@api_bp.route('/personel', methods=['POST'])
@api_key_required
def create_personel():
    data = request.get_json() or {}
    ad = data.get('ad', '').strip()
    soyad = data.get('soyad', '').strip()
    
    if not ad or not soyad:
        return jsonify({'success': False, 'error': 'First name and last name are required.'}), 400

    new_p = Personel(
        ad=ad,
        soyad=soyad,
        departman=data.get('departman', ''),
        pozisyon=data.get('pozisyon', ''),
        telefon=data.get('telefon', ''),
        email=data.get('email', ''),
        maas=float(data.get('maas', 0)),
        ek_bilgi=data.get('ek_bilgi', ''),
        aktif_mi=True
    )
    db.session.add(new_p)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Personnel created', 'data': new_p.to_dict(include_salary=True)}), 201

@api_bp.route('/personel/<int:id>', methods=['PUT'])
@api_key_required
def update_personel(id):
    p = Personel.query.filter_by(id=id, aktif_mi=True).first()
    if not p:
        return jsonify({'success': False, 'error': 'Personel not found'}), 404

    data = request.get_json() or {}
    if 'ad' in data: p.ad = data['ad']
    if 'soyad' in data: p.soyad = data['soyad']
    if 'departman' in data: p.departman = data['departman']
    if 'pozisyon' in data: p.pozisyon = data['pozisyon']
    if 'telefon' in data: p.telefon = data['telefon']
    if 'email' in data: p.email = data['email']
    if 'maas' in data: p.maas = float(data['maas'])
    if 'ek_bilgi' in data: p.ek_bilgi = data['ek_bilgi']

    db.session.commit()
    return jsonify({'success': True, 'message': 'Personnel updated', 'data': p.to_dict(include_salary=True)})

@api_bp.route('/personel/<int:id>', methods=['DELETE'])
@api_key_required
def delete_personel(id):
    p = Personel.query.filter_by(id=id, aktif_mi=True).first()
    if not p:
        return jsonify({'success': False, 'error': 'Personel not found'}), 404

    p.aktif_mi = False
    db.session.commit()
    return jsonify({'success': True, 'message': 'Personnel soft-deleted'})

@api_bp.route('/stats', methods=['GET'])
@api_key_required
def get_stats():
    total_personnel = Personel.query.filter_by(aktif_mi=True).count()
    total_users = Kullanici.query.filter_by(aktif_mi=True).count()
    total_leaves = Izin.query.count()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_personnel': total_personnel,
            'total_users': total_users,
            'total_leaves': total_leaves
        }
    })
