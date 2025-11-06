import os
import uuid
import datetime
import json
import openai
from functools import wraps 
from collections import Counter
from functools import wraps
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from dotenv import load_dotenv
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from models import db, User, UserRole, Student, Teacher, Course, Module, LearningContent, StudentContentProgress, AssessmentAttempt
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer


# Application Setup
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print("Warning: .env file not found.")
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

#  Database Configuration
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    raise RuntimeError("FATAL ERROR: DATABASE_URL is not set.")
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT Configuration
jwt_secret = os.environ.get('JWT_SECRET_KEY')
if not jwt_secret:
    raise RuntimeError("FATAL ERROR: JWT_SECRET_KEY is not set.")
app.config["JWT_SECRET_KEY"] = jwt_secret
jwt = JWTManager(app)

# --- Initialize Extensions ---
mail = Mail(app)
# We use the JWT_SECRET_KEY as a salt for the serializer for convenience
serializer = URLSafeTimedSerializer(app.config['JWT_SECRET_KEY'])

# --- Mail Configuration ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

# OpenAI Configuration
openai.api_key = os.environ.get('OPENAI_API_KEY')
if not openai.api_key:
    print("Warning: OPENAI_API_KEY is not set. AI features will be disabled.")

# Initialize Extensions
db.init_app(app)
bcrypt = Bcrypt(app)

# CUSTOM DECORATOR: Admin-Only Routes
def admin_required():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user_id = get_jwt_identity()
            # Find users roles from database
            user_roles = UserRole.query.filter_by(user_id=current_user_id).all()
            roles = [role.role for role in user_roles]
            # error handling
            if 'administrator' not in roles:
                return jsonify({"error": "Admins only!"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# This decorator is more flexible for routes that teachers OR admins can access.
def roles_required(*roles):
    """Decorator to ensure user has at least one of the specified roles."""
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            user_roles = {r.role for r in user.roles}
            
            if not user_roles.intersection(roles):
                return jsonify({"error": "Access forbidden: insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# API Routes
@app.route('/')
def home():
    return "AI-Powered Learning System Backend is running!"

# AUTHENTICATION ROUTES
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.get_json()
    required_fields = ['username', 'email', 'password', 'firstName', 'lastName']
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({"error": "All fields are required and cannot be empty"}), 400

    try:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
        db.session.add(new_user)
        db.session.flush()
        new_student = Student(user_id=new_user.id, first_name=data['firstName'], last_name=data['lastName'])
        db.session.add(new_student)
        new_role = UserRole(user_id=new_user.id, role='student')
        db.session.add(new_role)
        db.session.commit()
        return jsonify({"message": f"User '{new_user.username}' registered successfully!"}), 201
    except IntegrityError as e:
        db.session.rollback()
        if 'users_username_key' in str(e.orig): return jsonify({"error": "Username already exists"}), 409
        elif 'users_email_key' in str(e.orig): return jsonify({"error": "Email already exists"}), 409
        else: return jsonify({"error": "A database error occurred. Please try again."}), 500
    except Exception as e:
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

@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id_str = get_jwt_identity()
    current_user_id = uuid.UUID(current_user_id_str)
    user = User.query.get(current_user_id)
    if not user: return jsonify({"error": "User not found"}), 404
    return jsonify({"id": str(user.id), "username": user.username, "email": user.email, "roles": [r.role for r in user.roles]}), 200

@app.route('/api/quizzes/<uuid:content_id>', methods=['GET'])
@jwt_required()
def get_quiz_questions(content_id):
    """
    Fetches a quiz for a student, returning only the questions, not the answers.
    """
    content = LearningContent.query.get_or_404(content_id)
    if content.type != 'quiz' or not content.quiz_data:
        return jsonify({"error": "This content is not a valid quiz."}), 404

    # SECURITY: Sanitize the questions, removing the correct answer index to prevent cheating.
    sanitized_questions = []
    for q in content.quiz_data.get('questions', []):
        sanitized_questions.append({
            "id": q.get("id"),
            "text": q.get("text"),
            "options": q.get("options")
        })

    return jsonify({
        "quiz_id": str(content.id),
        "title": content.title,
        "questions": sanitized_questions
    })

# backend/app.py

# --- REPLACE this entire function in your file ---

# backend/app.py

# --- REPLACE this entire function in your file ---

@app.route('/api/quizzes/<uuid:content_id>/submit', methods=['POST'])
@roles_required('student')
def submit_quiz(content_id):
    """
    Receives student answers, grades them, saves the attempt with a correct attempt number, 
    and returns results.
    """
    content = LearningContent.query.get_or_404(content_id)
    if content.type != 'quiz' or not content.quiz_data:
        return jsonify({"error": "This is not a valid quiz."}), 404

    student = Student.query.filter_by(user_id=get_jwt_identity()).first()
    if not student:
        return jsonify({"error": "Student profile required to submit."}), 403

    student_answers = request.get_json().get('answers', {})
    correct_answers = {q['id']: q['correct_answer_index'] for q in content.quiz_data['questions']}
    
    score = 0
    total_questions = len(correct_answers)
    for question_id, correct_index in correct_answers.items():
        if student_answers.get(question_id) is not None and int(student_answers.get(question_id)) == correct_index:
            score += 1
    
    percentage = round((score / total_questions) * 100, 2) if total_questions > 0 else 0

    # --- THIS IS THE FIX ---
    # 1. Count previous attempts for this specific quiz by this student.
    previous_attempts = AssessmentAttempt.query.filter_by(
        student_id=student.id,
        content_id=content_id
    ).count()

    # 2. The new attempt number is the count of previous attempts + 1.
    new_attempt_number = previous_attempts + 1

    # 3. Save the new attempt with the correct attempt number.
    new_attempt = AssessmentAttempt(
        content_id=content_id,
        student_id=student.id,
        attempt_number=new_attempt_number, # <-- Use the calculated number
        score=percentage,
        max_score=100.00,
        answers=student_answers
    )
    db.session.add(new_attempt)
    db.session.commit()

    return jsonify({
        "message": "Quiz submitted successfully!",
        "score": percentage,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "student_answers": student_answers
    })

# ADMIN USER MANAGEMENT API
@app.route('/api/admin/users', methods=['GET'])
@admin_required()
def get_all_users():
    "Admin only: Returns a list of all users."
    users = User.query.all()
    output = []
    for user in users:
        user_data = {'id': str(user.id), 'username': user.username, 'email': user.email, 'roles': [r.role for r in user.roles]}
        if user.student_profile:
            user_data['first_name'] = user.student_profile.first_name
            user_data['last_name'] = user.student_profile.last_name
        elif user.teacher_profile:
            user_data['first_name'] = user.teacher_profile.first_name
            user_data['last_name'] = user.teacher_profile.last_name
        output.append(user_data)
    return jsonify(output), 200

@app.route('/api/admin/users', methods=['POST'])
@admin_required()
def create_user_by_admin():
    "Admin only: Creates a new user (teacher or admin)."
    data = request.get_json()
    required_fields = ['firstName', 'lastName', 'username', 'email', 'password', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    role = data['role']
    if role not in ['teacher', 'administrator']:
        return jsonify({"error": "Invalid role specified."}), 400
    try:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
        db.session.add(new_user)
        db.session.flush()
        new_profile = Teacher(user_id=new_user.id, first_name=data['firstName'], last_name=data['lastName'], title=role.capitalize())
        db.session.add(new_profile)
        new_role = UserRole(user_id=new_user.id, role=role)
        db.session.add(new_role)
        db.session.commit()
        return jsonify({"message": f"{role.capitalize()} '{new_user.username}' created successfully."}), 201
    except IntegrityError as e:
        db.session.rollback()
        if 'users_username_key' in str(e.orig): return jsonify({"error": "Username already exists"}), 409
        if 'users_email_key' in str(e.orig): return jsonify({"error": "Email already exists"}), 409
        return jsonify({"error": "Database error"}), 500

@app.route('/api/admin/users/<uuid:user_id>', methods=['DELETE'])
@admin_required()
def delete_user(user_id):
    "Admin only. Deletes a user by their ID."
    current_user_id = get_jwt_identity()
    if str(user_id) == current_user_id:
        return jsonify({"error": "You cannot delete your own account."}), 403
    user_to_delete = User.query.get(user_id)
    if not user_to_delete:
        return jsonify({"error": "User not found."}), 404
    db.session.delete(user_to_delete)
    db.session.commit()
    return jsonify({"message": f"User '{user_to_delete.username}' has been deleted."}), 200

@app.route('/api/courses', methods=['POST'])
@roles_required('teacher', 'administrator')
def create_course():
    """Creates a new course. Accessible by teachers and admins."""
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({"error": "Title is required"}), 400
    
    current_user_id = get_jwt_identity()
    # Find the teacher profile associated with the logged-in user
    teacher = Teacher.query.filter_by(user_id=current_user_id).first()
    
    new_course = Course(
        title=data['title'],
        description=data.get('description', ''),
        created_by_teacher_id=teacher.id if teacher else None
    )
    db.session.add(new_course)
    db.session.commit()
    return jsonify({"message": "Course created successfully", "course_id": str(new_course.id)}), 201

# --- NEW: UPDATE COURSE ENDPOINT ---

@app.route('/api/courses/<uuid:course_id>', methods=['PUT'])
@roles_required('teacher', 'administrator')
def update_course(course_id):
    """Updates a course's title and description."""
    course = Course.query.get_or_404(course_id)
    data = request.get_json()

    if not data or not data.get('title'):
        return jsonify({"error": "Title is required."}), 400

    # Update the course object with the new data
    course.title = data['title']
    course.description = data.get('description', course.description)
    
    db.session.commit()
    
    return jsonify({"message": f"Course '{course.title}' has been updated."})

@app.route('/api/courses', methods=['GET'])
@jwt_required()
def get_courses():
    """Returns a list of all available courses. Accessible by any logged-in user."""
    courses = Course.query.order_by(Course.title).all()
    # Include teacher's name for display purposes
    output = []
    for c in courses:
        teacher_name = "N/A"
        if c.created_by_teacher_id and c.teacher:
             teacher_name = f"{c.teacher.first_name} {c.teacher.last_name}"
        output.append({"id": str(c.id), "title": c.title, "description": c.description, "author": teacher_name})
    return jsonify(output)

@app.route('/api/courses/<uuid:course_id>', methods=['DELETE'])
@roles_required('teacher', 'administrator')
def delete_course(course_id):
    """Deletes a course and all its nested modules and content."""
    course = Course.query.get_or_404(course_id)
    
    # The 'cascade="all, delete-orphan"' in the models handles the deletion
    # of all child modules and content automatically.
    db.session.delete(course)
    db.session.commit()
    
    return jsonify({"message": f"Course '{course.title}' has been deleted."})

@app.route('/api/modules/<uuid:module_id>', methods=['DELETE'])
@roles_required('teacher', 'administrator')
def delete_module(module_id):
    """Deletes a module and all its nested content."""
    module = Module.query.get_or_404(module_id)
    
    db.session.delete(module)
    db.session.commit()
    
    return jsonify({"message": f"Module '{module.title}' has been deleted."})

@app.route('/api/content/<uuid:content_id>', methods=['DELETE'])
@roles_required('teacher', 'administrator')
def delete_learning_content(content_id):
    """Deletes a single piece of learning content."""
    content = LearningContent.query.get_or_404(content_id)
    
    db.session.delete(content)
    db.session.commit()
    
    return jsonify({"message": f"Content '{content.title}' has been deleted."})

# backend/app.py
# --- REPLACE the old get_course_details function with this one ---

# backend/app.py

# --- REPLACE your existing get_course_details function with this one ---

# backend/app.py

# --- REPLACE your existing get_course_details function with this one ---

# backend/app.py

# --- REPLACE your existing get_course_details function with this one ---

@app.route('/api/courses/<uuid:course_id>', methods=['GET'])
@jwt_required()
def get_course_details(course_id):
    """
    Returns a single course with its structure AND the current student's progress.
    This is the DEFINITIVELY CORRECT version that includes all necessary fields.
    """
    course = Course.query.get_or_404(course_id)
    current_user_id = get_jwt_identity()
    student = Student.query.filter_by(user_id=current_user_id).first()
    
    student_progress = {}
    if student:
        content_ids = [content.id for module in course.modules for content in module.learning_contents]
        if content_ids:
            progress_records = StudentContentProgress.query.filter(
                StudentContentProgress.student_id == student.id,
                StudentContentProgress.content_id.in_(content_ids)
            ).all()
            student_progress = {str(p.content_id): p.status for p in progress_records}

    course_data = {
        "id": str(course.id), 
        "title": course.title, 
        "description": course.description, 
        "modules": []
    }
    
    sorted_modules = sorted(course.modules, key=lambda m: m.module_order)
    
    for module in sorted_modules:
        module_data = {
            "id": str(module.id),
            "title": module.title,
            "description": module.description,
            "order": module.module_order,
            "learning_contents": []
        }
        
        sorted_content = sorted(module.learning_contents, key=lambda c: c.content_order)
        for content in sorted_content:
            content_data = {
                "id": str(content.id),
                "title": content.title,
                "type": content.type,
                "url": content.content_url,
                "body": content.content_body,
                "order": content.content_order,
                "progress_status": student_progress.get(str(content.id), 'not_started')
            }
            module_data["learning_contents"].append(content_data)
        
        course_data["modules"].append(module_data)
        
    return jsonify(course_data)

@app.route('/api/courses/<uuid:course_id>/modules', methods=['POST'])
@roles_required('teacher', 'administrator')
def create_module(course_id):
    """Creates a new module and adds it to a course."""
    course = Course.query.get_or_404(course_id)
    data = request.get_json()
    if not data or not data.get('title') or 'order' not in data:
        return jsonify({"error": "Title and order are required"}), 400
        
    new_module = Module(
        course_id=course.id,
        title=data['title'],
        description=data.get('description', ''),
        module_order=data['order']
    )
    db.session.add(new_module)
    db.session.commit()
    return jsonify({"message": "Module added successfully", "module_id": str(new_module.id)}), 201

# backend/app.py

# --- REPLACE this entire function in your file ---

@app.route('/api/modules/<uuid:module_id>/content', methods=['POST'])
@roles_required('teacher', 'administrator')
def create_learning_content(module_id):
    """Creates new learning content and adds it to a module."""
    module = Module.query.get_or_404(module_id)
    data = request.get_json()
    if not all(k in data for k in ['title', 'type', 'order']):
        return jsonify({"error": "Title, type, and order required"}), 400
    
    # This is the corrected constructor call that includes quiz_data
    new_content = LearningContent(
        module_id=module.id, 
        title=data['title'], 
        type=data['type'], 
        content_order=data['order'], 
        content_url=data.get('url'), 
        content_body=data.get('body'), 
        quiz_data=data.get('quiz_data') # <-- This line was missing from the version I gave you
    )
    
    db.session.add(new_content)
    db.session.commit()
    return jsonify({"message": "Content added", "content_id": str(new_content.id)}), 201

# backend/app.py
# --- ADD THIS NEW ROUTE ---

@app.route('/api/progress/<uuid:content_id>/complete', methods=['POST'])
@jwt_required()
def mark_content_complete(content_id):
    """Marks a piece of learning content as complete for the logged-in student."""
    current_user_id = get_jwt_identity()
    student = Student.query.filter_by(user_id=current_user_id).first()
    
    if not student:
        return jsonify({"error": "Student profile not found for this user."}), 404
        
    # Find if a progress record already exists
    progress_record = StudentContentProgress.query.filter_by(
        student_id=student.id,
        content_id=content_id
    ).first()
    
    if progress_record:
        # Update existing record
        progress_record.status = 'completed'
        progress_record.completed_at = datetime.datetime.utcnow()
        progress_record.last_accessed_at = datetime.datetime.utcnow()
    else:
        # Create a new record
        progress_record = StudentContentProgress(
            student_id=student.id,
            content_id=content_id,
            status='completed',
            completed_at=datetime.datetime.utcnow()
        )
        db.session.add(progress_record)
        
    db.session.commit()
    return jsonify({"message": "Progress updated successfully", "status": "completed"})

# --- NEW TEACHER ANALYTICS API ---

@app.route('/api/courses/<uuid:course_id>/progress', methods=['GET'])
@roles_required('teacher', 'administrator')
def get_course_progress(course_id):
    """
    For a given course, calculates the progress of every student who has started it.
    Accessible by teachers and admins.
    """
    course = Course.query.get_or_404(course_id)
    
    # 1. Get all content IDs for this course to define the scope
    course_content_ids = db.session.query(LearningContent.id).join(Module).filter(Module.course_id == course.id).all()
    # Flatten the list of tuples into a simple list of IDs
    content_ids = [c_id[0] for c_id in course_content_ids]
    
    if not content_ids:
        return jsonify([]) # Return empty list if course has no content

    total_items = len(content_ids)

    # 2. Find all progress records for this course's content
    progress_records = StudentContentProgress.query.filter(
        StudentContentProgress.content_id.in_(content_ids),
        StudentContentProgress.status == 'completed'
    ).all()

    # 3. Aggregate progress by student
    student_progress = {}
    for record in progress_records:
        student_id = record.student_id
        if student_id not in student_progress:
            # Initialize student if not seen before
            student_profile = Student.query.get(student_id)
            student_progress[student_id] = {
                "student_id": str(student_id),
                "student_name": f"{student_profile.first_name} {student_profile.last_name}",
                "completed_count": 0
            }
        student_progress[student_id]["completed_count"] += 1

    # 4. Format the final output with percentages
    output = []
    for student_id, data in student_progress.items():
        data['total_items'] = total_items
        data['percentage'] = round((data['completed_count'] / total_items) * 100, 2)
        output.append(data)
        
    # Sort by student name for a consistent view
    output.sort(key=lambda x: x['student_name'])
    
    return jsonify(output)

@app.route('/api/students/me/recommendations', methods=['GET'])
@roles_required('student')
def get_recommendations():
    """Generates personalized content recommendations for the logged-in student."""
    # 1. Get the student's profile
    student = Student.query.filter_by(user_id=get_jwt_identity()).first()
    if not student:
        return jsonify([]) # Return empty list if no student profile

    # 2. Get the IDs of all content the student has already completed
    completed_progress = StudentContentProgress.query.filter_by(student_id=student.id, status='completed').all()
    completed_content_ids = {p.content_id for p in completed_progress}

    if not completed_content_ids:
        return jsonify([]) # No history, no recommendations

    # 3. Find all tags from the content they have completed
    completed_contents = LearningContent.query.filter(LearningContent.id.in_(completed_content_ids)).all()
    all_tags = []
    for content in completed_contents:
        if content.tags:
            # Split tags by comma, strip whitespace, and convert to lowercase
            all_tags.extend([tag.strip().lower() for tag in content.tags.split(',')])

    if not all_tags:
        return jsonify([]) # No tagged content completed

    # 4. Find the student's top 3 most frequent tags (their "strong topics")
    tag_counts = Counter(all_tags)
    top_tags = {tag for tag, count in tag_counts.most_common(3)}

    # 5. Find uncompleted content that matches these top tags
    # This is a simple but effective way to find relevant content
    recommendation_candidates = LearningContent.query.filter(
        LearningContent.id.notin_(completed_content_ids),
        LearningContent.tags != None
    ).limit(50).all() # Limit initial candidates for performance

    recommendations = []
    for content in recommendation_candidates:
        content_tags = {tag.strip().lower() for tag in content.tags.split(',')}
        # If the content's tags overlap with the student's top tags, it's a good recommendation
        if content_tags.intersection(top_tags):
            recommendations.append({
                "id": str(content.id),
                "title": content.title,
                "type": content.type,
                # Add context for the UI
                "module_title": content.module.title,
                "course_title": content.module.course.title,
                "course_id": str(content.module.course.id)
            })
        if len(recommendations) >= 5: # Limit to a max of 5 recommendations
            break
            
    return jsonify(recommendations)

# backend/app.py
# ... (all existing code) ...

# --- NEW: TEACHER PERFORMANCE ANALYTICS API ---

@app.route('/api/courses/<uuid:course_id>/performance', methods=['GET'])
@roles_required('teacher', 'administrator')
def get_course_performance(course_id):
    """
    For a given course, aggregates all student quiz scores and attempts.
    Accessible by teachers and admins.
    """
    course = Course.query.get_or_404(course_id)
    
    # 1. Find all content items in this course that are quizzes
    course_quiz_ids = [
        content.id for module in course.modules 
        for content in module.learning_contents if content.type == 'quiz'
    ]

    if not course_quiz_ids:
        return jsonify([]) # No quizzes in this course, return empty list

    # 2. Find all assessment attempts for these quizzes
    all_attempts = AssessmentAttempt.query.filter(
        AssessmentAttempt.content_id.in_(course_quiz_ids)
    ).all()

    # 3. Aggregate the data by student for a clean, structured response
    performance_data = {}
    for attempt in all_attempts:
        student_id = attempt.student_id
        
        # If this is the first time we've seen this student, initialize their record
        if student_id not in performance_data:
            performance_data[student_id] = {
                "student_id": str(student_id),
                "student_name": f"{attempt.student.first_name} {attempt.student.last_name}",
                "attempts": [],
                "total_score": 0,
                "attempt_count": 0
            }
        
        # Add the current attempt's details
        performance_data[student_id]['attempts'].append({
            "quiz_id": str(attempt.content_id),
            "quiz_title": attempt.quiz.title,
            "attempt_number": attempt.attempt_number,
            "score": float(attempt.score) # Ensure score is a float
        })
        performance_data[student_id]['total_score'] += attempt.score
        performance_data[student_id]['attempt_count'] += 1
        
    # 4. Calculate average scores and format the final list
    output = []
    for student_id, data in performance_data.items():
        data['average_score'] = round(data['total_score'] / data['attempt_count'], 2)
        # Sort attempts by quiz title and then attempt number
        data['attempts'].sort(key=lambda x: (x['quiz_title'], x['attempt_number']))
        del data['total_score'] # Clean up temporary fields
        del data['attempt_count']
        output.append(data)

    # Sort the final output by student name
    output.sort(key=lambda x: x['student_name'])
    
    return jsonify(output)

# ... (rest of your app.py file)
# --- NEW AI QUIZ GENERATION API ---

@app.route('/api/ai/generate-quiz', methods=['POST'])
@roles_required('teacher', 'administrator')
def generate_quiz_from_article():
    """
    Uses OpenAI's GPT to generate a quiz from a piece of text (article body).
    Accessible by teachers and admins.
    """
    if not openai.api_key:
        return jsonify({"error": "AI service is not configured on the server."}), 503 # 503 Service Unavailable

    data = request.get_json()
    article_text = data.get('text')

    if not article_text or len(article_text) < 100:
        return jsonify({"error": "Article text must be at least 100 characters long to generate a quiz."}), 400

    # This is the "prompt" we send to the AI. It's carefully engineered to ask for a specific JSON format.
    prompt_messages = [
        {
            "role": "system",
            "content": "You are an expert educator and quiz creator. Your task is to generate a structured JSON object for a quiz based on the provided text. The quiz should contain exactly 3 multiple-choice questions. Each question must have a unique 'id', the question 'text', an array of three string 'options', and the 'correct_answer_index' (0, 1, or 2)."
        },
        {
            "role": "user",
            "content": f"Here is the article text: ```{article_text}```"
        }
    ]

    try:
        # Make the API call to OpenAI
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # A model that is good with JSON format
            messages=prompt_messages,
            response_format={ "type": "json_object" }, # Enforce JSON output
            temperature=0.5 # A bit of creativity, but not too much
        )
        
        # Extract the JSON string from the response
        response_content = completion.choices[0].message.content
        # Parse the JSON string into a Python dictionary
        quiz_data = json.loads(response_content)

        # Basic validation of the AI's output
        if 'questions' not in quiz_data or not isinstance(quiz_data['questions'], list):
            raise ValueError("AI response did not contain a valid 'questions' list.")

        # Return the structured quiz_data, ready for our frontend
        return jsonify(quiz_data)

    except json.JSONDecodeError:
        return jsonify({"error": "AI generated an invalid JSON format. Please try again."}), 500
    except Exception as e:
        print(f"An error occurred with the OpenAI API: {e}")
        return jsonify({"error": f"An error occurred while generating the quiz: {e}"}), 500

# --- NEW AI CHATBOT API ---

@app.route('/api/ai/chatbot', methods=['POST'])
@roles_required('student')
def handle_chatbot_query():
    """
    Handles a student's question by sending it to OpenAI's GPT with context from an article.
    """
    if not openai.api_key:
        return jsonify({"error": "AI service is not configured on the server."}), 503

    data = request.get_json()
    question = data.get('question')
    article_text = data.get('context') # The text of the article the student is reading

    if not question:
        return jsonify({"error": "A question is required."}), 400
    if not article_text:
        return jsonify({"error": "Context (the article text) is required."}), 400

    # This is the "prompt engineering" part. We give the AI a persona and strict instructions.
    # This is a simple form of Retrieval-Augmented Generation (RAG).
    system_prompt = (
        "You are a friendly and encouraging tutor named StudyBot. Your role is to help a student "
        "understand an article they are currently reading. Your answers must be based ONLY on the "
        "information provided in the article text. If the answer cannot be found in the article, "
        "you must politely state that you can only answer questions about the provided text. "
        "Do not make up information or answer general knowledge questions."
    )
    
    user_prompt = (
        f"Here is the article text the student is reading:\n--- ARTICLE START ---\n"
        f"{article_text}\n--- ARTICLE END ---\n\n"
        f"Here is the student's question: \"{question}\""
    )

    prompt_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        # Make the API call to OpenAI
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=prompt_messages,
            temperature=0.3, # Low temperature for more factual, less creative answers
            max_tokens=200  # Limit the length of the response
        )
        
        # Extract the text response from the AI
        ai_response = completion.choices[0].message.content

        return jsonify({"answer": ai_response})

    except Exception as e:
        print(f"An error occurred with the OpenAI API (Chatbot): {e}")
        return jsonify({"error": f"An error occurred while communicating with the AI tutor."}), 500

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()

    # SECURITY: Always return a success message to prevent email enumeration
    if user:
        # Generate a secure, timed token (expires in 1 hour)
        token = serializer.dumps(user.email, salt='password-reset-salt')
        # This is the URL to your frontend page
        reset_url = f"http://localhost:5173/reset-password?token={token}"
        print("--- PASSWORD RESET ---")
        print(f"Password reset link for {user.email}: {reset_url}")
        print("----------------------")

        msg = Message(
            "Password Reset Request",
            recipients=[user.email]
        )
        msg.body = f"Hello,\n\nPlease click the following link to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email."
        
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email: {e}")
            # Silently fail for the user, but log it on the server
            pass

    return jsonify({"message": "If an account with that email exists, a password reset link has been sent."})

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('password')

    if not token or not new_password:
        return jsonify({"error": "Token and new password are required."}), 400

    try:
        # Verify the token's signature and that it hasn't expired (3600 seconds = 1 hour)
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        return jsonify({"error": "The password reset link is invalid or has expired."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found."}), 404

    # Update the user's password
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password_hash = hashed_password
    db.session.commit()

    return jsonify({"message": "Your password has been reset successfully."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)