import os
import json
from flask import session, request, has_request_context

_TRANSLATIONS = {}
_DEFAULT_LOCALE = 'tr'
_SUPPORTED_LOCALES = ['tr', 'en']

def load_translations(directory=None):
    """Load JSON translation dictionaries into memory."""
    global _TRANSLATIONS
    if directory is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        directory = os.path.join(base_dir, 'translations')
        
    _TRANSLATIONS = {}
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                locale = filename[:-5]
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        _TRANSLATIONS[locale] = json.load(f)
                except Exception as e:
                    _TRANSLATIONS[locale] = {}

def get_locale():
    """Determine the active locale from session or request headers."""
    if has_request_context():
        # Check session
        lang = session.get('lang')
        if lang in _SUPPORTED_LOCALES:
            return lang
        
        # Check browser Accept-Language header
        if request.accept_languages:
            best = request.accept_languages.best_match(_SUPPORTED_LOCALES)
            if best:
                return best
                
    return _DEFAULT_LOCALE

def translate(key, default=None, locale=None, **kwargs):
    """Translate a given key into the current or specified locale."""
    if key is None:
        return default if default is not None else ""
        
    if not isinstance(key, str):
        key = str(key)
        
    global _TRANSLATIONS
    if not _TRANSLATIONS:
        load_translations()
        
    if not locale:
        locale = get_locale()
    
    # Lookup in active locale
    text = _TRANSLATIONS.get(locale, {}).get(key)
    
    # Fallback to default locale (Turkish)
    if text is None and locale != _DEFAULT_LOCALE:
        text = _TRANSLATIONS.get(_DEFAULT_LOCALE, {}).get(key)
        
    # Ultimate fallback
    if text is None:
        text = default if default is not None else key
        
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
            
    return text

# Alias for Jinja2 template usage
_ = translate
