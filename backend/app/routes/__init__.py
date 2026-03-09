from flask import jsonify

def register_blueprints(app):
    from .auth import auth_bp
    from .users import users_bp
    from .courses import courses_bp
    from .quizzes import quizzes_bp
    from .progress import progress_bp
    from .analytics import analytics_bp
    from .ai import ai_bp
    from .remarks import remarks_bp
    from .discussions import discussions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(remarks_bp)
    app.register_blueprint(discussions_bp)

    @app.route('/')
    def index():
        return jsonify({"message": "AI-Powered Learning System Backend is running!", "status": "active"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"error": "Too many requests. Please wait and try again."}), 429
