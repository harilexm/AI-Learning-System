from flask import Blueprint, request, jsonify
from ..extensions import db, bcrypt, mail, limiter
from ..models import User, Student, UserRole
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def get_serializer():
    return URLSafeTimedSerializer(current_app.config['JWT_SECRET_KEY'])

def handle_integrity_error(e):
    error_info = str(e.orig)
    field = "unknown"
    if "users_username_key" in error_info: field = "Username"
    elif "users_email_key" in error_info: field = "Email"
    db.session.rollback()
    return jsonify({"error": f"{field} already exists. Please choose a different one."}), 409

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("3 per minute")
def register_user():
    data = request.get_json()
    if not all(data.get(field) for field in ['username', 'email', 'password', 'firstName', 'lastName']):
        return jsonify({"error": "All fields are required and cannot be empty"}), 400
    if len(data['password']) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400

    try:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
        db.session.add(new_user)
        db.session.flush() # Flush to get new_user.id

        student_profile = Student(user_id=new_user.id, first_name=data['firstName'], last_name=data['lastName'])
        student_role = UserRole(user_id=new_user.id, role='student')
        db.session.add_all([student_profile, student_role])
        db.session.commit()
        
        return jsonify({"message": f"User '{new_user.username}' registered successfully!"}), 201
    except IntegrityError as e:
        return handle_integrity_error(e)
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An unexpected server error occurred."}), 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login_user():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token)
    
    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.get_json().get('email')
    user = User.query.filter_by(email=email).first()

    if user:
        serializer = get_serializer()
        token = serializer.dumps(user.email, salt='password-reset-salt')
        reset_url = f"http://localhost:5173/reset-password?token={token}"
        msg = Message("Password Reset Request", recipients=[user.email])
        msg.body = f"Please click the following link to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email."
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email: {e}") # Log error but don't expose to user
    
    # SECURITY: Always return a generic success message
    return jsonify({"message": "If an account with that email exists, a password reset link has been sent."})

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token, new_password = data.get('token'), data.get('password')
    if not token or not new_password:
        return jsonify({"error": "Token and new password are required."}), 400
    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400
    try:
        serializer = get_serializer()
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        return jsonify({"error": "The password reset link is invalid or has expired."}), 400

    user = User.query.filter_by(email=email).first_or_404()
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()

    return jsonify({"message": "Your password has been reset successfully."})
