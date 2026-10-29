from flask import Blueprint, session, redirect, request, url_for
from utils import safe_redirect_target

lang_bp = Blueprint('lang', __name__)


@lang_bp.route('/set_lang/<lang_code>')
@lang_bp.route('/lang/<lang_code>')
def set_language(lang_code):
    """Switch active interface language."""
    if lang_code in ['tr', 'en']:
        session['lang'] = lang_code

    target = safe_redirect_target(request.args.get('next')) or safe_redirect_target(request.referrer)
    if target:
        return redirect(target)

    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))
