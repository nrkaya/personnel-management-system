from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
csrf = CSRFProtect()
migrate = Migrate(compare_type=True)
limiter = Limiter(key_func=get_remote_address, default_limits=[])
