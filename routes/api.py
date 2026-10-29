import hmac
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database import csrf, db, limiter
from models import Izin, Kullanici, Personel
from utils import MAX_SALARY, PHONE_PATTERN, log_action

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# API clients authenticate without a browser session, so CSRF does not apply.
csrf.exempt(api_bp)

TEXT_FIELDS = {
    'ad': 100, 'soyad': 100, 'departman': 100, 'pozisyon': 100,
    'telefon': 30, 'email': 120, 'ek_bilgi': 10_000,
}
DATE_FIELDS = {'ise_giris_tarihi', 'dogum_tarihi'}
ALLOWED_FIELDS = set(TEXT_FIELDS) | DATE_FIELDS | {'maas'}
EMAIL_PATTERN = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
# Fields that need an extra scope to read or write, like the web roles.
SALARY_SCOPE = 'personnel:salary'
PERSONAL_SCOPE = 'personnel:personal'
SALARY_FIELDS = {'maas'}
PERSONAL_FIELDS = {'dogum_tarihi', 'ek_bilgi'}


def _configured_api_keys():
    """Load the primary key and optional scoped, rotating integration keys."""
    keys = []
    primary_key = current_app.config.get('API_KEY')
    if primary_key:
        keys.append({
            'name': 'primary',
            'key': primary_key,
            'scopes': {scope.strip() for scope in current_app.config['API_KEY_SCOPES'].split(',') if scope.strip()},
        })

    try:
        extra_keys = json.loads(current_app.config.get('API_KEYS_JSON', '{}'))
    except (TypeError, json.JSONDecodeError):
        current_app.logger.error('API_KEYS_JSON geçerli JSON değil.')
        return keys
    if not isinstance(extra_keys, dict):
        current_app.logger.error('API_KEYS_JSON bir nesne olmalıdır.')
        return keys

    for name, record in extra_keys.items():
        if not isinstance(record, dict) or not isinstance(record.get('key'), str):
            continue
        scopes = record.get('scopes', [])
        if isinstance(scopes, str):
            scopes = [scope.strip() for scope in scopes.split(',')]
        if isinstance(scopes, list):
            keys.append({'name': str(name), 'key': record['key'], 'scopes': set(scopes)})
    return keys


def api_key_required(*required_scopes):
    """Authenticate a constant-time API key comparison and enforce scopes."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            authorization = request.headers.get('Authorization', '')
            bearer_key = authorization[7:] if authorization.startswith('Bearer ') else ''
            supplied_key = request.headers.get('X-API-KEY') or bearer_key
            if not supplied_key:
                return jsonify({'success': False, 'error': 'API anahtarı gerekli.'}), 401

            for record in _configured_api_keys():
                if not hmac.compare_digest(supplied_key, record['key']):
                    continue
                if '*' not in record['scopes'] and not set(required_scopes).issubset(record['scopes']):
                    return jsonify({'success': False, 'error': 'Bu anahtarın gerekli kapsamı yok.'}), 403
                g.api_principal = record['name']
                g.api_scopes = record['scopes']
                return f(*args, **kwargs)
            return jsonify({'success': False, 'error': 'Geçersiz API anahtarı.'}), 401
        return decorated
    return decorator


def _has_scope(scope):
    scopes = getattr(g, 'api_scopes', set())
    return '*' in scopes or scope in scopes


def _serialize(person):
    return person.to_dict(
        include_salary=_has_scope(SALARY_SCOPE),
        include_personal=_has_scope(PERSONAL_SCOPE),
    )


def _forbidden_fields(data):
    """Fields in a write request that the key's scopes do not cover."""
    forbidden = set()
    if not _has_scope(SALARY_SCOPE):
        forbidden |= SALARY_FIELDS & set(data)
    if not _has_scope(PERSONAL_SCOPE):
        forbidden |= PERSONAL_FIELDS & set(data)
    return forbidden


def _scope_error(fields):
    return jsonify({
        'success': False,
        'error': 'Bu anahtarın şu alanlar için kapsamı yok.',
        'fields': sorted(fields),
    }), 403


def _json_object():
    if not request.is_json:
        return None, (jsonify({'success': False, 'error': 'Content-Type application/json olmalıdır.'}), 415)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({'success': False, 'error': 'Geçerli bir JSON nesnesi gönderin.'}), 400)
    return data, None


def _validate_personnel(data, partial=False):
    """Return normalized data and field errors instead of unhandled 500s."""
    errors, clean = {}, {}
    unknown_fields = set(data) - ALLOWED_FIELDS
    if unknown_fields:
        errors['fields'] = f"Desteklenmeyen alanlar: {', '.join(sorted(unknown_fields))}"

    for field, max_length in TEXT_FIELDS.items():
        required = field in {'ad', 'soyad'} and not partial
        if field not in data:
            if required:
                errors[field] = 'Bu alan zorunludur.'
            continue
        value = data[field]
        if not isinstance(value, str):
            errors[field] = 'Metin olmalıdır.'
            continue
        value = value.strip()
        if required and not value:
            errors[field] = 'Bu alan boş olamaz.'
        elif len(value) > max_length:
            errors[field] = f'En fazla {max_length} karakter olabilir.'
        elif field == 'email' and value and not EMAIL_PATTERN.fullmatch(value):
            errors[field] = 'Geçerli bir e-posta adresi olmalıdır.'
        elif field == 'telefon' and not PHONE_PATTERN.fullmatch(value):
            errors[field] = 'Yalnızca rakam, boşluk ve + ( ) . - karakterleri kullanılabilir.'
        else:
            clean[field] = value or None

    if 'maas' in data:
        try:
            salary = Decimal(str(data['maas'])).quantize(Decimal('0.01'))
            if not salary.is_finite() or salary < 0 or salary > MAX_SALARY:
                raise InvalidOperation
            clean['maas'] = salary
        except (InvalidOperation, ValueError, TypeError):
            errors['maas'] = f'0 ile {MAX_SALARY} arasında, iki ondalıklı bir tutar olmalıdır.'

    for field in DATE_FIELDS:
        if field not in data:
            continue
        value = data[field]
        if value in (None, ''):
            clean[field] = None
            continue
        if not isinstance(value, str):
            errors[field] = 'YYYY-AA-GG biçiminde bir tarih olmalıdır.'
            continue
        try:
            clean[field] = datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            errors[field] = 'YYYY-AA-GG biçiminde geçerli bir tarih olmalıdır.'
    if clean.get('dogum_tarihi') and clean['dogum_tarihi'] > date.today():
        errors['dogum_tarihi'] = 'Doğum tarihi gelecekte olamaz.'
    return clean, errors


def _commit_or_error():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Veri bütünlüğü kuralı ihlal edildi.'}), 409
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('API veritabanı işlemi başarısız oldu.')
        return jsonify({'success': False, 'error': 'Veri kaydedilemedi.'}), 500
    return None


def _audit(action, detail):
    log_action(f"API:{getattr(g, 'api_principal', 'unknown')}", action, detail)


@api_bp.route('/docs')
@limiter.limit('30 per minute')
@api_key_required('stats:read')
def api_docs():
    return jsonify({
        'title': 'KAYA PTS Enterprise REST API',
        'version': '1.1.0',
        'authentication': 'X-API-KEY or Authorization: Bearer <key>',
        'scopes': {
            'personnel:read': ['GET /personeller', 'GET /personel/<id>'],
            'personnel:write': ['POST /personel', 'PUT /personel/<id>', 'DELETE /personel/<id>'],
            SALARY_SCOPE: ['maas alanını okuma ve yazma'],
            PERSONAL_SCOPE: ['dogum_tarihi ve ek_bilgi alanlarını okuma ve yazma'],
            'stats:read': ['GET /stats', 'GET /docs'],
        },
        'pagination': {'page': '1 or greater', 'per_page': f"1-{current_app.config['MAX_API_PAGE_SIZE']}"},
    })


@api_bp.route('/personeller', methods=['GET'])
@limiter.limit('120 per minute')
@api_key_required('personnel:read')
def get_personeller():
    q = request.args.get('q', '').strip()
    department = request.args.get('departman', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    maximum = current_app.config['MAX_API_PAGE_SIZE']
    if page is None or page < 1 or per_page is None or not 1 <= per_page <= maximum:
        return jsonify({'success': False, 'error': f'page en az 1, per_page ise 1-{maximum} arasında olmalıdır.'}), 400

    query = Personel.query.filter_by(aktif_mi=True)
    if q:
        search_terms = f"%{q}%"
        query = query.filter((Personel.ad.ilike(search_terms)) | (Personel.soyad.ilike(search_terms)))
    if department:
        query = query.filter_by(departman=department)
    total = query.count()
    items = query.order_by(Personel.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        'success': True,
        'meta': {'total': total, 'page': page, 'per_page': per_page},
        'data': [_serialize(person) for person in items],
    })


@api_bp.route('/personel/<int:id>', methods=['GET'])
@limiter.limit('120 per minute')
@api_key_required('personnel:read')
def get_personel(id):
    person = Personel.query.filter_by(id=id, aktif_mi=True).first()
    if not person:
        return jsonify({'success': False, 'error': 'Personel bulunamadı.'}), 404
    return jsonify({'success': True, 'data': _serialize(person)})


@api_bp.route('/personel', methods=['POST'])
@limiter.limit('30 per minute')
@api_key_required('personnel:write')
def create_personel():
    data, error = _json_object()
    if error:
        return error
    forbidden = _forbidden_fields(data)
    if forbidden:
        return _scope_error(forbidden)
    clean, errors = _validate_personnel(data)
    if errors:
        return jsonify({'success': False, 'error': 'Doğrulama başarısız.', 'fields': errors}), 422
    person = Personel(**clean, aktif_mi=True)
    db.session.add(person)
    error = _commit_or_error()
    if error:
        return error
    _audit('API Personel Eklendi', f'Personel #{person.id} oluşturuldu.')
    return jsonify({'success': True, 'message': 'Personel oluşturuldu.', 'data': _serialize(person)}), 201


@api_bp.route('/personel/<int:id>', methods=['PUT'])
@limiter.limit('60 per minute')
@api_key_required('personnel:write')
def update_personel(id):
    person = Personel.query.filter_by(id=id, aktif_mi=True).first()
    if not person:
        return jsonify({'success': False, 'error': 'Personel bulunamadı.'}), 404
    data, error = _json_object()
    if error:
        return error
    if not data:
        return jsonify({'success': False, 'error': 'Güncellenecek en az bir alan gönderin.'}), 400
    forbidden = _forbidden_fields(data)
    if forbidden:
        return _scope_error(forbidden)
    clean, errors = _validate_personnel(data, partial=True)
    if errors:
        return jsonify({'success': False, 'error': 'Doğrulama başarısız.', 'fields': errors}), 422
    for field, value in clean.items():
        setattr(person, field, value)
    error = _commit_or_error()
    if error:
        return error
    _audit('API Personel Güncellendi', f'Personel #{person.id} güncellendi.')
    return jsonify({'success': True, 'message': 'Personel güncellendi.', 'data': _serialize(person)})


@api_bp.route('/personel/<int:id>', methods=['DELETE'])
@limiter.limit('30 per minute')
@api_key_required('personnel:write')
def delete_personel(id):
    person = Personel.query.filter_by(id=id, aktif_mi=True).first()
    if not person:
        return jsonify({'success': False, 'error': 'Personel bulunamadı.'}), 404
    person.aktif_mi = False
    error = _commit_or_error()
    if error:
        return error
    _audit('API Personel Silindi', f'Personel #{person.id} arşive taşındı.')
    return jsonify({'success': True, 'message': 'Personel arşive taşındı.'})


@api_bp.route('/stats', methods=['GET'])
@limiter.limit('120 per minute')
@api_key_required('stats:read')
def get_stats():
    today = date.today()
    # Same rule as the dashboard: leaves of archived personnel do not count.
    active_leaves = Izin.query.join(Personel).filter(
        Personel.aktif_mi.is_(True),
        Izin.durum == 'Onaylandı', Izin.baslangic <= today, Izin.bitis >= today
    ).count()
    return jsonify({
        'success': True,
        'data': {
            'toplam_aktif_personel': Personel.query.filter_by(aktif_mi=True).count(),
            'toplam_kullanici': Kullanici.query.filter_by(aktif_mi=True).count(),
            'aktif_izindekiler': active_leaves,
        },
    })
