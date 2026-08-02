from flask import Blueprint, session, redirect, request, url_for
from urllib.parse import urlparse

lang_bp = Blueprint('lang', __name__)

@lang_bp.route('/set_lang/<lang_code>')
@lang_bp.route('/lang/<lang_code>')
def set_language(lang_code):
    """Switch active interface language."""
    if lang_code in ['tr', 'en']:
        session['lang'] = lang_code
        
    next_url = request.args.get('next')
    if next_url:
        parsed = urlparse(next_url)
        if not parsed.netloc or parsed.netloc == urlparse(request.url).netloc:
            return redirect(next_url)

    referrer = request.referrer
    if referrer:
        parsed_ref = urlparse(referrer)
        parsed_req = urlparse(request.url)
        if parsed_ref.netloc == '' or parsed_ref.netloc == parsed_req.netloc:
            return redirect(referrer)
            
    if session.get('kullanici_adi'):
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

