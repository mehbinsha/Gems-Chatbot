from flask import Flask, send_from_directory
from flask_cors import CORS
from backend.config import Config
from backend.extensions import db, migrate, jwt
from backend.seed import seed_database


def _bootstrap_database() -> None:
    # Keep local setup resilient: create missing tables and seed a default admin once.
    db.create_all()
    seed_database(
        admin_email=Config.DEFAULT_ADMIN_EMAIL,
        admin_password=Config.DEFAULT_ADMIN_PASSWORD,
        intents_json_path=Config.INTENTS_PATH,
    )

def create_app():
    app = Flask(
        __name__,
        static_folder="../frontend",
        static_url_path=""
    )

    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from backend.routes.chat_routes import chat_bp
    from backend.routes.result_routes import result_bp
    from backend.routes.admin_routes import admin_bp
    app.register_blueprint(chat_bp)
    app.register_blueprint(result_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def home():
        return send_from_directory(app.static_folder, "chat_interface.html")

    @app.route("/admin")
    def admin_home():
        return send_from_directory(app.static_folder, "admin.html")

    with app.app_context():
        _bootstrap_database()

    return app
