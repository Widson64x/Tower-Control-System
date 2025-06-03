from flask import Flask
from .config import Config
from .extensions import db, login_manager
from .routes.auth import auth_bp
from .routes.gestor import gestor_bp
from .routes.feedback import feedback_bp
from .routes.times import times_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(gestor_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(times_bp)

    login_manager.login_view = "auth.login"

    return app

