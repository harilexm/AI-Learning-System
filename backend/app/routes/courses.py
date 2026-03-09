from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Course, Module, LearningContent, Teacher, Student, StudentContentProgress, Enrollment
from ..utils.decorators import roles_required
import uuid

courses_bp = Blueprint('courses', __name__, url_prefix='/api')

@courses_bp.route('/courses', methods=['POST'])
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

@courses_bp.route('/courses/<uuid:course_id>', methods=['PUT'])
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

@courses_bp.route('/courses', methods=['GET'])
@jwt_required()
def get_courses():
    courses = Course.query.order_by(Course.title).all()
    output = []
    for c in courses:
        teacher_name = f"{c.teacher.first_name} {c.teacher.last_name}" if c.teacher else "N/A"
        output.append({"id": str(c.id), "title": c.title, "description": c.description, "author": teacher_name})
    return jsonify(output)

@courses_bp.route('/courses/<uuid:course_id>', methods=['GET'])
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

@courses_bp.route('/courses/<uuid:course_id>/modules', methods=['POST'])
@roles_required('teacher', 'administrator')
def add_module(course_id):
    course = Course.query.get_or_404(course_id)
    data = request.get_json()
    if not data or not data.get('title') or not data.get('moduleOrder'):
        return jsonify({"error": "Title and module order are required"}), 400
    
    new_module = Module(course_id=course.id, title=data['title'], description=data.get('description'), module_order=data['moduleOrder'])
    db.session.add(new_module)
    db.session.commit()
    return jsonify({"message": f"Module '{new_module.title}' created."}), 201

@courses_bp.route('/modules/<uuid:module_id>/content', methods=['POST'])
@roles_required('teacher', 'administrator')
def add_learning_content(module_id):
    module = Module.query.get_or_404(module_id)
    data = request.get_json()
    
    if not all(data.get(field) for field in ['title', 'type', 'contentOrder']):
        return jsonify({"error": "Title, type, and order are required"}), 400
    
    if data['type'] not in ['video', 'article', 'quiz']:
        return jsonify({"error": "Invalid content type"}), 400

    new_content = LearningContent(
        module_id=module.id, title=data['title'], type=data['type'], content_order=data['contentOrder'],
        content_url=data.get('contentUrl'), content_body=data.get('contentBody'), quiz_data=data.get('quizData'),
        tags=data.get('tags')
    )
    db.session.add(new_content)
    db.session.commit()
    return jsonify({"message": f"{data['type'].capitalize()} added successfully."}), 201

@courses_bp.route('/courses/<uuid:course_id>', methods=['DELETE'])
@roles_required('teacher', 'administrator')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    title = course.title
    db.session.delete(course)
    db.session.commit()
    return jsonify({"message": f"Course '{title}' has been deleted."})

@courses_bp.route('/modules/<uuid:module_id>', methods=['DELETE'])
@roles_required('teacher', 'administrator')
def delete_module(module_id):
    module = Module.query.get_or_404(module_id)
    title = module.title
    db.session.delete(module)
    db.session.commit()
    return jsonify({"message": f"Module '{title}' has been deleted."})

@courses_bp.route('/content/<uuid:content_id>', methods=['DELETE'])
@roles_required('teacher', 'administrator')
def delete_learning_content(content_id):
    content = LearningContent.query.get_or_404(content_id)
    title = content.title
    db.session.delete(content)
    db.session.commit()
    return jsonify({"message": f"Content '{title}' has been deleted."})

@courses_bp.route('/courses/<uuid:course_id>/enroll', methods=['POST'])
@roles_required('student')
def enroll_in_course(course_id):
    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()
    existing = Enrollment.query.filter_by(student_id=student.id, course_id=course_id).first()
    if existing:
        return jsonify({"error": "Already enrolled in this course"}), 409
    try:
        enrollment = Enrollment(student_id=student.id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        return jsonify({"message": "Enrolled successfully"}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to enroll"}), 500

@courses_bp.route('/courses/<uuid:course_id>/enroll', methods=['DELETE'])
@roles_required('student')
def unenroll_from_course(course_id):
    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()
    enrollment = Enrollment.query.filter_by(student_id=student.id, course_id=course_id).first_or_404()
    try:
        db.session.delete(enrollment)
        db.session.commit()
        return jsonify({"message": "Unenrolled successfully"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to unenroll"}), 500

@courses_bp.route('/students/me/enrollments', methods=['GET'])
@roles_required('student')
def get_my_enrollments():
    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    output = []
    for enr in enrollments:
        c = enr.course
        output.append({
            "course_id": str(c.id),
            "title": c.title,
            "description": c.description,
            "enrolled_at": str(enr.enrolled_at)
        })
    return jsonify(output)

@courses_bp.route('/lti/launch', methods=['POST'])
def lti_launch():
    """Handle LTI launch from Moodle/external LMS (Placeholder)."""
    # In a real implementation: validate OAuth/JWT LTI params, create/find user, map course.
    return jsonify({"message": "LTI launch received. Redirecting to platform...", "status": "success"})

@courses_bp.route('/external/import', methods=['POST'])
@roles_required('teacher', 'administrator')
def import_external_content():
    """Import course content from external JSON format."""
    data = request.get_json()
    if not data or 'title' not in data or 'modules' not in data:
        return jsonify({"error": "Invalid format. Must include title and modules list"}), 400
        
    try:
        teacher = Teacher.query.filter_by(user_id=get_jwt_identity()).first()
        course = Course(title=data['title'], description=data.get('description', ''), created_by_teacher_id=teacher.id if teacher else None)
        db.session.add(course)
        db.session.flush()

        for mod_data in data['modules']:
            module = Module(course_id=course.id, title=mod_data['title'], description=mod_data.get('description'), order=mod_data.get('order', 1))
            db.session.add(module)
            db.session.flush()
            
            for content_data in mod_data.get('content', []):
                content = LearningContent(
                    module_id=module.id, 
                    title=content_data['title'],
                    type=content_data['type'], 
                    order=content_data.get('order', 1),
                    body=content_data.get('body'),
                    url=content_data.get('url'),
                    quiz_data=content_data.get('quiz_data'),
                    tags=content_data.get('tags')
                )
                db.session.add(content)

        db.session.commit()
        return jsonify({"message": "Course imported successfully!", "course_id": str(course.id)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Import failed: {str(e)}"}), 500

