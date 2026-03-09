import os
from flask import Flask
from flask_cors import CORS
import openai
from .config import Config
from .extensions import db, bcrypt, jwt, mail, migrate, limiter

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.validate()

    cors_origin = os.environ.get("CORS_ORIGIN", "http://localhost:5173")
    CORS(app, resources={r"/*": {"origins": cors_origin}})

    # Initialize OpenAI API key
    openai.api_key = app.config.get('OPENAI_API_KEY')

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Register blueprints (will be implemented next)
    from .routes import register_blueprints
    register_blueprints(app)

    return app
