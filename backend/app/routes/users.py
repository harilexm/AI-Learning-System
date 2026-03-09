from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db, bcrypt
from ..models import User, Student, Teacher, LearningProfile, UserRole, Course, AssessmentAttempt, Enrollment, LearningContent, Module
from ..utils.decorators import roles_required
import uuid

users_bp = Blueprint('users', __name__, url_prefix='/api')

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user = User.query.get_or_404(uuid.UUID(get_jwt_identity()))
    return jsonify({
        "id": str(user.id), 
        "username": user.username, 
        "email": user.email, 
        "roles": [r.role for r in user.roles]
    }), 200

@users_bp.route('/profile/change-password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.get_json()
    current_password, new_password = data.get('current_password'), data.get('new_password')
    if not current_password or not new_password:
        return jsonify({"error": "Both current and new passwords are required."}), 400
    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400

    user = User.query.get_or_404(uuid.UUID(get_jwt_identity()))
    if not bcrypt.check_password_hash(user.password_hash, current_password):
        return jsonify({"error": "Incorrect current password."}), 401

    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    return jsonify({"message": "Password updated successfully."})

@users_bp.route('/admin/users', methods=['GET'])
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

@users_bp.route('/admin/users', methods=['POST'])
@roles_required('administrator')
def create_user_by_admin():
    data = request.get_json()
    if not all(data.get(f) for f in ['username', 'email', 'password', 'role']):
        return jsonify({"error": "Missing required fields"}), 400
    if len(data['password']) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400

    try:
        hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], email=data['email'], password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.flush()

        from ..models import UserRole
        role = UserRole(user_id=new_user.id, role=data['role'])
        db.session.add(role)
        
        # Add a dummy profile for simplicity
        if data['role'] == 'teacher':
            profile = Teacher(user_id=new_user.id, first_name=data.get('firstName', 'Teacher'), last_name=data.get('lastName', 'User'))
        else:
            profile = Student(user_id=new_user.id, first_name=data.get('firstName', 'Student'), last_name=data.get('lastName', 'User'))
        db.session.add(profile)

        db.session.commit()
        return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@users_bp.route('/admin/users/<uuid:user_id>', methods=['DELETE'])
@roles_required('administrator')
def delete_user(user_id):
    if str(user_id) == get_jwt_identity():
        return jsonify({"error": "Cannot delete your own account"}), 400
    user = User.query.get_or_404(user_id)
    try:
        from ..models import (DiscussionReply, DiscussionPost, TeacherRemark,
                              ChatHistory, StudyPlan, AssessmentAttempt,
                              StudentContentProgress, Enrollment, LearningProfile)

        # Delete discussion replies and posts by this user
        DiscussionReply.query.filter_by(user_id=user.id).delete()
        # Delete replies on posts owned by this user, then the posts
        for post in DiscussionPost.query.filter_by(user_id=user.id).all():
            DiscussionReply.query.filter_by(post_id=post.id).delete()
        DiscussionPost.query.filter_by(user_id=user.id).delete()

        # If user is a student, clean up student-related records
        if user.student_profile:
            sid = user.student_profile.id
            TeacherRemark.query.filter_by(student_id=sid).delete()
            ChatHistory.query.filter_by(student_id=sid).delete()
            StudyPlan.query.filter_by(student_id=sid).delete()
            AssessmentAttempt.query.filter_by(student_id=sid).delete()
            StudentContentProgress.query.filter_by(student_id=sid).delete()
            Enrollment.query.filter_by(student_id=sid).delete()
            LearningProfile.query.filter_by(student_id=sid).delete()

        # If user is a teacher, clean up teacher-related records
        if user.teacher_profile:
            tid = user.teacher_profile.id
            TeacherRemark.query.filter_by(teacher_id=tid).delete()
            # Unlink courses (set created_by to NULL instead of deleting courses)
            Course.query.filter_by(created_by_teacher_id=tid).update({"created_by_teacher_id": None})

        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete user: {str(e)}"}), 400

@users_bp.route('/students/me/learning-profile', methods=['GET'])
@roles_required('student')
def get_learning_profile():
    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()
    profile = LearningProfile.query.filter_by(student_id=student.id).first()
    if not profile:
        return jsonify({
            "id": None, "primary_goal": None, "learning_style": None, "preferred_pace": "medium"
        })
    return jsonify({
        "id": str(profile.id), "primary_goal": profile.primary_goal,
        "learning_style": profile.learning_style, "preferred_pace": profile.preferred_pace
    })

@users_bp.route('/students/me/learning-profile', methods=['PUT'])
@roles_required('student')
def update_learning_profile():
    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()
    data = request.get_json()
    profile = LearningProfile.query.filter_by(student_id=student.id).first()
    
    if not profile:
        profile = LearningProfile(student_id=student.id)
        db.session.add(profile)
        
    if 'primary_goal' in data: profile.primary_goal = data['primary_goal']
    if 'learning_style' in data: profile.learning_style = data['learning_style']
    if 'preferred_pace' in data: profile.preferred_pace = data['preferred_pace']
    
    try:
        db.session.commit()
        return jsonify({"message": "Learning profile updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update profile"}), 500


@users_bp.route('/admin/system-stats', methods=['GET'])
@roles_required('administrator')
def admin_system_stats():
    """Platform-wide analytics for the admin dashboard."""
    from sqlalchemy import func

    # User counts
    total_users = User.query.count()
    student_count = UserRole.query.filter_by(role='student').count()
    teacher_count = UserRole.query.filter_by(role='teacher').count()
    admin_count = UserRole.query.filter_by(role='administrator').count()

    # Course & content stats
    total_courses = Course.query.count()
    total_content = LearningContent.query.count()

    # Quiz stats
    total_quiz_attempts = AssessmentAttempt.query.count()
    avg_score_result = db.session.query(func.avg(AssessmentAttempt.score)).scalar()
    avg_score = round(float(avg_score_result), 1) if avg_score_result else 0

    # Most popular courses (by enrollment count)
    popular_courses = db.session.query(
        Course.title,
        func.count(Enrollment.id).label('enrollment_count')
    ).join(Enrollment, Enrollment.course_id == Course.id
    ).group_by(Course.title
    ).order_by(func.count(Enrollment.id).desc()
    ).limit(5).all()

    top_courses = [{"title": title, "enrollments": count} for title, count in popular_courses]

    return jsonify({
        "total_users": total_users,
        "student_count": student_count,
        "teacher_count": teacher_count,
        "admin_count": admin_count,
        "total_courses": total_courses,
        "total_content": total_content,
        "total_quiz_attempts": total_quiz_attempts,
        "avg_quiz_score": avg_score,
        "top_courses": top_courses
    })
