from flask import Flask, redirect, url_for
from .config import Config
from .extensions import db, login_manager
from .routes.auth import auth_bp
from .routes.home import home_bp
from .routes.employees import funcionarios_bp
from .routes.times import times_bp
from .routes.promocoes import promocoes_bp


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
    app.register_blueprint(home_bp)
    app.register_blueprint(funcionarios_bp)
    app.register_blueprint(times_bp)
    app.register_blueprint(promocoes_bp)

    login_manager.login_view = "auth.login"

    # Adicione esta rota:
    @app.route("/")
    def index():
        return redirect(url_for("home.home"))
    
    return app

