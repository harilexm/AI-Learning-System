import os
import uuid
import datetime
import json
from functools import wraps
from collections import Counter
import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.exc import IntegrityError
from models import (db, User, UserRole, Student, Teacher, Course, Module, LearningContent, StudentContentProgress, AssessmentAttempt)

# Application Setup
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY')
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

# Extensions Initialization
db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['JWT_SECRET_KEY'])

# OpenAI Configuration
openai.api_key = os.environ.get('OPENAI_API_KEY')
if not openai.api_key:
    print("Warning: OPENAI_API_KEY is not set. AI features will be disabled.")

if not app.config['SQLALCHEMY_DATABASE_URI'] or not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("FATAL ERROR: Database URL and JWT Secret Key must be set.")

# Custom Decorators
def roles_required(*roles):
    """Decorator to ensure user has at least one of the specified roles."""
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or not {r.role for r in user.roles}.intersection(roles):
                return jsonify({"error": "Access forbidden: insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# --- Helper Functions ---
def handle_integrity_error(e):
    """Helper to handle common database integrity errors."""
    db.session.rollback()
    if 'users_username_key' in str(e.orig):
        return jsonify({"error": "Username already exists"}), 409
    if 'users_email_key' in str(e.orig):
        return jsonify({"error": "Email already exists"}), 409
    return jsonify({"error": "A database error occurred. Please try again."}), 500

# --- API Routes ---
@app.route('/')
def home():
    return "AI-Powered Learning System Backend is running!"

# --- Authentication Routes ---
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.get_json()
    if not all(data.get(field) for field in ['username', 'email', 'password', 'firstName', 'lastName']):
        return jsonify({"error": "All fields are required and cannot be empty"}), 400

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

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token)
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    email = request.get_json().get('email')
    user = User.query.filter_by(email=email).first()

    if user:
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

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token, new_password = data.get('token'), data.get('password')
    if not token or not new_password:
        return jsonify({"error": "Token and new password are required."}), 400
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        return jsonify({"error": "The password reset link is invalid or has expired."}), 400

    user = User.query.filter_by(email=email).first_or_404()
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()

    return jsonify({"message": "Your password has been reset successfully."})

# --- Profile and User Management ---
@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user = User.query.get_or_404(uuid.UUID(get_jwt_identity()))
    return jsonify({
        "id": str(user.id), 
        "username": user.username, 
        "email": user.email, 
        "roles": [r.role for r in user.roles]
    }), 200

@app.route('/api/profile/change-password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.get_json()
    current_password, new_password = data.get('current_password'), data.get('new_password')
    if not current_password or not new_password:
        return jsonify({"error": "Both current and new passwords are required."}), 400

    user = User.query.get_or_404(uuid.UUID(get_jwt_identity()))
    if not bcrypt.check_password_hash(user.password_hash, current_password):
        return jsonify({"error": "Incorrect current password."}), 401

    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    return jsonify({"message": "Password updated successfully."})

# --- Admin User Management ---
@app.route('/api/admin/users', methods=['GET'])
@roles_required('administrator')
def get_all_users():
    users = User.query.all()
    output = []
    for user in users:
        profile = user.student_profile or user.teacher_profile
        user_data = {
            'id': str(user.id), 'username': user.username, 'email': user.email, 
            'roles': [r.role for r in user.roles],
            'first_name': profile.first_name if profile else None,
            'last_name': profile.last_name if profile else None
        }
        output.append(user_data)
    return jsonify(output), 200

@app.route('/api/admin/users', methods=['POST'])
@roles_required('administrator')
def create_user_by_admin():
    data = request.get_json()
    role = data.get('role')
    if not all(data.get(f) for f in ['firstName', 'lastName', 'username', 'email', 'password', 'role']):
        return jsonify({"error": "Missing required fields"}), 400
    if role not in ['teacher', 'administrator']:
        return jsonify({"error": "Invalid role specified."}), 400
    try:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
        db.session.add(new_user)
        db.session.flush() # Get user ID
        
        profile = Teacher(user_id=new_user.id, first_name=data['firstName'], last_name=data['lastName'], title=role.capitalize())
        user_role = UserRole(user_id=new_user.id, role=role)
        db.session.add_all([profile, user_role])
        db.session.commit()
        return jsonify({"message": f"{role.capitalize()} '{new_user.username}' created successfully."}), 201
    except IntegrityError as e:
        return handle_integrity_error(e)

@app.route('/api/admin/users/<uuid:user_id>', methods=['DELETE'])
@roles_required('administrator')
def delete_user(user_id):
    if str(user_id) == get_jwt_identity():
        return jsonify({"error": "You cannot delete your own account."}), 403
    
    user_to_delete = User.query.get_or_404(user_id)
    username = user_to_delete.username
    db.session.delete(user_to_delete)
    db.session.commit()
    return jsonify({"message": f"User '{username}' has been deleted."})

# --- Course, Module, and Content Management ---
@app.route('/api/courses', methods=['POST'])
@roles_required('teacher', 'administrator')
def create_course():
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({"error": "Title is required"}), 400
    
    teacher = Teacher.query.filter_by(user_id=get_jwt_identity()).first()
    new_course = Course(title=data['title'], description=data.get('description', ''), created_by_teacher_id=teacher.id if teacher else None)
    db.session.add(new_course)
    db.session.commit()
    return jsonify({"message": "Course created successfully", "course_id": str(new_course.id)}), 201

@app.route('/api/courses/<uuid:course_id>', methods=['PUT'])
@roles_required('teacher', 'administrator')
def update_course(course_id):
    course = Course.query.get_or_404(course_id)
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({"error": "Title is required."}), 400
    
    course.title = data['title']
    course.description = data.get('description', course.description)
    db.session.commit()
    return jsonify({"message": f"Course '{course.title}' has been updated."})

@app.route('/api/courses', methods=['GET'])
@jwt_required()
def get_courses():
    courses = Course.query.order_by(Course.title).all()
    output = []
    for c in courses:
        teacher_name = f"{c.teacher.first_name} {c.teacher.last_name}" if c.teacher else "N/A"
        output.append({"id": str(c.id), "title": c.title, "description": c.description, "author": teacher_name})
    return jsonify(output)

@app.route('/api/courses/<uuid:course_id>', methods=['GET'])
@jwt_required()
def get_course_details(course_id):
    course = Course.query.get_or_404(course_id)
    student = Student.query.filter_by(user_id=get_jwt_identity()).first()
    student_progress = {}

    if student:
        content_ids = [content.id for module in course.modules for content in module.learning_contents]
        if content_ids:
            progress_records = StudentContentProgress.query.filter(
                StudentContentProgress.student_id == student.id,
                StudentContentProgress.content_id.in_(content_ids)
            ).all()
            student_progress = {str(p.content_id): p.status for p in progress_records}

    course_data = {"id": str(course.id), "title": course.title, "description": course.description, "modules": []}
    for module in sorted(course.modules, key=lambda m: m.module_order):
        module_data = {"id": str(module.id), "title": module.title, "description": module.description, "order": module.module_order, "learning_contents": []}
        for content in sorted(module.learning_contents, key=lambda c: c.content_order):
            module_data["learning_contents"].append({
                "id": str(content.id), "title": content.title, "type": content.type,
                "url": content.content_url, "body": content.content_body, "order": content.content_order,
                "progress_status": student_progress.get(str(content.id), 'not_started')
            })
        course_data["modules"].append(module_data)
    return jsonify(course_data)

@app.route('/api/courses/<uuid:course_id>', methods=['DELETE'])
@roles_required('teacher', 'administrator')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    title = course.title
    db.session.delete(course)
    db.session.commit()
    return jsonify({"message": f"Course '{title}' has been deleted."})

@app.route('/api/courses/<uuid:course_id>/modules', methods=['POST'])
@roles_required('teacher', 'administrator')
def create_module(course_id):
    data = request.get_json()
    if not all(k in data for k in ['title', 'order']):
        return jsonify({"error": "Title and order are required"}), 400
    
    new_module = Module(course_id=course_id, title=data['title'], description=data.get('description', ''), module_order=data['order'])
    db.session.add(new_module)
    db.session.commit()
    return jsonify({"message": "Module added successfully", "module_id": str(new_module.id)}), 201

@app.route('/api/modules/<uuid:module_id>', methods=['DELETE'])
@roles_required('teacher', 'administrator')
def delete_module(module_id):
    module = Module.query.get_or_404(module_id)
    title = module.title
    db.session.delete(module)
    db.session.commit()
    return jsonify({"message": f"Module '{title}' has been deleted."})

@app.route('/api/modules/<uuid:module_id>/content', methods=['POST'])
@roles_required('teacher', 'administrator')
def create_learning_content(module_id):
    data = request.get_json()
    if not all(k in data for k in ['title', 'type', 'order']):
        return jsonify({"error": "Title, type, and order required"}), 400
    
    new_content = LearningContent(
        module_id=module_id, title=data['title'], type=data['type'], content_order=data['order'],
        content_url=data.get('url'), content_body=data.get('body'), quiz_data=data.get('quiz_data')
    )
    db.session.add(new_content)
    db.session.commit()
    return jsonify({"message": "Content added", "content_id": str(new_content.id)}), 201

@app.route('/api/content/<uuid:content_id>', methods=['DELETE'])
@roles_required('teacher', 'administrator')
def delete_learning_content(content_id):
    content = LearningContent.query.get_or_404(content_id)
    title = content.title
    db.session.delete(content)
    db.session.commit()
    return jsonify({"message": f"Content '{title}' has been deleted."})

# --- Quiz and Progress Routes ---
@app.route('/api/quizzes/<uuid:content_id>', methods=['GET'])
@jwt_required()
def get_quiz_questions(content_id):
    content = LearningContent.query.get_or_404(content_id)
    if content.type != 'quiz' or not content.quiz_data:
        return jsonify({"error": "This content is not a valid quiz."}), 404

    sanitized_questions = [{k: v for k, v in q.items() if k != 'correct_answer_index'} for q in content.quiz_data.get('questions', [])]
    return jsonify({"quiz_id": str(content.id), "title": content.title, "questions": sanitized_questions})

@app.route('/api/quizzes/<uuid:content_id>/submit', methods=['POST'])
@roles_required('student')
def submit_quiz(content_id):
    content = LearningContent.query.get_or_404(content_id)
    if content.type != 'quiz' or not content.quiz_data:
        return jsonify({"error": "This is not a valid quiz."}), 404

    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()
    student_answers = request.get_json().get('answers', {})
    correct_answers = {q['id']: q['correct_answer_index'] for q in content.quiz_data['questions']}
    
    score = sum(1 for q_id, c_idx in correct_answers.items() if int(student_answers.get(q_id, -1)) == c_idx)
    total = len(correct_answers)
    percentage = round((score / total) * 100, 2) if total > 0 else 0

    previous_attempts = AssessmentAttempt.query.filter_by(student_id=student.id, learning_content_id=content_id).count()
    new_attempt = AssessmentAttempt(
        learning_content_id=content_id, student_id=student.id,
        attempt_number=previous_attempts + 1, score=percentage,
        max_score=100.00, answers=student_answers
    )
    db.session.add(new_attempt)
    db.session.commit()
    return jsonify({"message": "Quiz submitted successfully!", "score": percentage, "total_questions": total, "correct_answers": correct_answers, "student_answers": student_answers})

@app.route('/api/progress/<uuid:content_id>/complete', methods=['POST'])
@jwt_required()
def mark_content_complete(content_id):
    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()
    progress_record = StudentContentProgress.query.filter_by(student_id=student.id, content_id=content_id).first()
    
    if progress_record:
        progress_record.status = 'completed'
        progress_record.completed_at = datetime.datetime.utcnow()
    else:
        progress_record = StudentContentProgress(student_id=student.id, content_id=content_id, status='completed')
        db.session.add(progress_record)
        
    db.session.commit()
    return jsonify({"message": "Progress updated successfully", "status": "completed"})

# --- Analytics and AI Routes ---
@app.route('/api/courses/<uuid:course_id>/progress', methods=['GET'])
@roles_required('teacher', 'administrator')
def get_course_progress(course_id):
    content_ids = [c.id for c in LearningContent.query.join(Module).filter(Module.course_id == course_id)]
    if not content_ids: return jsonify([])

    progress_records = StudentContentProgress.query.filter(StudentContentProgress.content_id.in_(content_ids), StudentContentProgress.status == 'completed').all()
    
    student_progress = Counter(record.student_id for record in progress_records)
    output = []
    for student_id, completed_count in student_progress.items():
        student = Student.query.get(student_id)
        output.append({
            "student_id": str(student_id), "student_name": f"{student.first_name} {student.last_name}",
            "completed_count": completed_count, "total_items": len(content_ids),
            "percentage": round((completed_count / len(content_ids)) * 100, 2)
        })
    return jsonify(sorted(output, key=lambda x: x['student_name']))

@app.route('/api/courses/<uuid:course_id>/performance', methods=['GET'])
@roles_required('teacher', 'administrator')
def get_course_performance(course_id):
    quiz_ids = [c.id for m in Course.query.get_or_404(course_id).modules for c in m.learning_contents if c.type == 'quiz']
    if not quiz_ids: return jsonify([])

    attempts = AssessmentAttempt.query.filter(AssessmentAttempt.learning_content_id.in_(quiz_ids)).all()
    performance_data = {}
    for attempt in attempts:
        student_id = attempt.student_id
        if student_id not in performance_data:
            performance_data[student_id] = {
                "student_id": str(student_id), "student_name": f"{attempt.student.first_name} {attempt.student.last_name}",
                "attempts": [], "total_score": 0, "attempt_count": 0
            }
        data = performance_data[student_id]
        data['attempts'].append({"quiz_title": attempt.quiz.title, "attempt_number": attempt.attempt_number, "score": float(attempt.score)})
        data['total_score'] += attempt.score
        data['attempt_count'] += 1
    
    output = []
    for data in performance_data.values():
        data['average_score'] = round(data['total_score'] / data['attempt_count'], 2)
        data['attempts'].sort(key=lambda x: (x['quiz_title'], x['attempt_number']))
        del data['total_score'], data['attempt_count']
        output.append(data)
    
    return jsonify(sorted(output, key=lambda x: x['student_name']))

@app.route('/api/students/me/recommendations', methods=['GET'])
@roles_required('student')
def get_recommendations():
    """Generates personalized content recommendations for the logged-in student."""
    student = Student.query.filter_by(user_id=get_jwt_identity()).first()
    if not student:
        return jsonify([])

    # THIS IS THE CORRECTED LOGIC - RESTORED FROM YOUR ORIGINAL CODE
    completed_progress = StudentContentProgress.query.filter_by(student_id=student.id, status='completed').all()
    completed_content_ids = {p.content_id for p in completed_progress}

    if not completed_content_ids:
        return jsonify([])

    completed_contents = LearningContent.query.filter(LearningContent.id.in_(completed_content_ids), LearningContent.tags.isnot(None)).all()
    all_tags = [tag.strip().lower() for c in completed_contents for tag in c.tags.split(',') if c.tags]
    if not all_tags:
        return jsonify([])

    top_tags = {tag for tag, count in Counter(all_tags).most_common(3)}
    candidates = LearningContent.query.filter(LearningContent.id.notin_(completed_content_ids), LearningContent.tags.isnot(None)).limit(50).all()
    
    recommendations = []
    for content in candidates:
        if content.tags and top_tags.intersection({tag.strip().lower() for tag in content.tags.split(',') }):
            recommendations.append({
                "id": str(content.id), "title": content.title, "type": content.type,
                "course_id": str(content.module.course.id),
                "module_title": content.module.title,
                "course_title": content.module.course.title
            })
        if len(recommendations) >= 5:
            break
            
    return jsonify(recommendations)

@app.route('/api/ai/generate-quiz', methods=['POST'])
@roles_required('teacher', 'administrator')
def generate_quiz_from_article():
    if not openai.api_key: return jsonify({"error": "AI service is not configured."}), 503
    
    article_text = request.get_json().get('text')
    if not article_text or len(article_text) < 100:
        return jsonify({"error": "Article text must be at least 100 characters."}), 400

    prompt = [
        {"role": "system", "content": "You are an expert educator. Generate a JSON object for a quiz with 3 multiple-choice questions from the text. Each question must have a unique 'id', 'text', three 'options', and the 'correct_answer_index' (0, 1, or 2)."},
        {"role": "user", "content": f"Article text: ```{article_text}```"}
    ]
    try:
        completion = openai.chat.completions.create(model="gpt-3.5-turbo-1106", messages=prompt, response_format={"type": "json_object"}, temperature=0.5)
        quiz_data = json.loads(completion.choices[0].message.content)
        if 'questions' not in quiz_data or not isinstance(quiz_data.get('questions'), list):
            raise ValueError("Invalid 'questions' format from AI.")
        return jsonify(quiz_data)
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({"error": f"AI generated invalid data: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An OpenAI API error occurred: {e}"}), 500

@app.route('/api/ai/chatbot', methods=['POST'])
@roles_required('student')
def handle_chatbot_query():
    if not openai.api_key: return jsonify({"error": "AI service is not configured."}), 503

    data = request.get_json()
    question, article_text = data.get('question'), data.get('context')
    if not question or not article_text:
        return jsonify({"error": "Question and context are required."}), 400

    system_prompt = "You are StudyBot, a friendly tutor. Answer questions based ONLY on the provided article. If the answer isn't in the text, politely say so. Do not use outside knowledge."
    user_prompt = f"Article:\n--- START ---\n{article_text}\n--- END ---\n\nStudent's question: \"{question}\""
    
    try:
        completion = openai.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.3, max_tokens=200)
        return jsonify({"answer": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": f"An AI communication error occurred: {e}"}), 500

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)