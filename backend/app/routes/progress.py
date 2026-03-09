from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
from ..extensions import db
from ..models import Student, StudentContentProgress, Enrollment, Course, AssessmentAttempt
from ..utils.decorators import roles_required

progress_bp = Blueprint('progress', __name__, url_prefix='/api')

@progress_bp.route('/progress/<uuid:content_id>/complete', methods=['POST'])
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


@progress_bp.route('/students/me/history', methods=['GET'])
@roles_required('student')
def get_my_history():
    """Comprehensive learning history for the logged-in student."""
    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()

    # Course progress
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    course_progress = []
    total_completed = 0
    for enr in enrollments:
        course = Course.query.get(enr.course_id)
        if not course:
            continue
        total_content = sum(len(m.learning_contents) for m in course.modules)
        content_ids = [c.id for m in course.modules for c in m.learning_contents]
        completed = StudentContentProgress.query.filter(
            StudentContentProgress.student_id == student.id,
            StudentContentProgress.content_id.in_(content_ids),
            StudentContentProgress.status == 'completed'
        ).count() if content_ids else 0
        total_completed += completed
        course_progress.append({
            "course_id": str(course.id),
            "course_title": course.title,
            "total_items": total_content,
            "completed_items": completed,
            "percentage": round((completed / total_content) * 100, 1) if total_content > 0 else 0
        })

    # Quiz history
    attempts = AssessmentAttempt.query.filter_by(student_id=student.id).order_by(AssessmentAttempt.submitted_at.desc()).all()
    quiz_history = []
    for a in attempts:
        quiz_history.append({
            "quiz_title": a.quiz.title if a.quiz else "Unknown",
            "score": float(a.score),
            "attempt_number": a.attempt_number,
            "date": a.submitted_at.strftime("%b %d, %Y %H:%M") if a.submitted_at else "N/A"
        })

    avg_score = sum(float(a.score) for a in attempts) / len(attempts) if attempts else 0

    return jsonify({
        "courses_enrolled": len(enrollments),
        "content_completed": total_completed,
        "quizzes_taken": len(attempts),
        "avg_score": round(avg_score, 1),
        "course_progress": course_progress,
        "quiz_history": quiz_history
    })
