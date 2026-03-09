from flask import Blueprint, jsonify, request
from collections import Counter
from ..extensions import db
from ..models import LearningContent, Module, StudentContentProgress, Student, Course, AssessmentAttempt, Enrollment, User
from ..utils.decorators import roles_required

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api')

@analytics_bp.route('/courses/<uuid:course_id>/progress', methods=['GET'])
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

@analytics_bp.route('/courses/<uuid:course_id>/performance', methods=['GET'])
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

@analytics_bp.route('/teacher/dashboard-summary', methods=['GET'])
@roles_required('teacher', 'administrator')
def teacher_dashboard_summary():
    from ..ai.gap_analyzer import predict_at_risk
    
    attempts = AssessmentAttempt.query.all()
    avg_score = sum(float(a.score) for a in attempts) / len(attempts) if attempts else 0

    students = Student.query.all()
    at_risk = []
    
    for s in students:
        s_attempts = [a for a in attempts if a.student_id == s.id]
        s_score = sum(float(a.score) for a in s_attempts) / len(s_attempts) if s_attempts else 0
        s_completion = 50
        features = {"avg_score": s_score, "completion_rate": s_completion, "days_inactive": 5}
        risk = predict_at_risk(features)
        # Include email for identification
        user = User.query.get(s.user_id)
        if risk != "low_risk":
            at_risk.append({
                "id": str(s.id),
                "name": f"{s.first_name} {s.last_name}",
                "email": user.email if user else "",
                "risk_level": risk
            })

    recent_activity = []
    for a in sorted(attempts, key=lambda x: x.submitted_at or x.id, reverse=True)[:5]:
        student_name = f"{a.student.first_name} {a.student.last_name}" if a.student else "Unknown"
        student_email = ""
        if a.student:
            user = User.query.get(a.student.user_id)
            student_email = user.email if user else ""
        quiz_title = a.quiz.title if a.quiz else "Unknown"
        date_str = a.submitted_at.strftime("%b %d, %H:%M") if a.submitted_at else "N/A"
        recent_activity.append({
            "student_name": student_name,
            "student_email": student_email,
            "student_id": str(a.student_id),
            "quiz_title": quiz_title,
            "score": float(a.score),
            "date": date_str
        })

    return jsonify({
        "total_students": len(students),
        "total_courses": Course.query.count(),
        "total_quizzes_taken": len(attempts),
        "average_quiz_score": round(avg_score, 1),
        "at_risk_students": at_risk[:5],
        "recent_activity": recent_activity
    })


# ── NEW: Teacher Student List ────────────────────────────────────────
@analytics_bp.route('/teacher/students', methods=['GET'])
@roles_required('teacher', 'administrator')
def get_all_students():
    """List all students with email, enrollment count, avg score, last active."""
    students = Student.query.all()
    output = []
    for s in students:
        user = User.query.get(s.user_id)
        # Get quiz stats
        attempts = AssessmentAttempt.query.filter_by(student_id=s.id).all()
        avg_score = sum(float(a.score) for a in attempts) / len(attempts) if attempts else None
        # Get enrollment count
        enrollment_count = Enrollment.query.filter_by(student_id=s.id).count()
        # Get completion count
        completed = StudentContentProgress.query.filter_by(student_id=s.id, status='completed').count()

        output.append({
            "id": str(s.id),
            "name": f"{s.first_name} {s.last_name}",
            "email": user.email if user else "",
            "enrollment_count": enrollment_count,
            "quizzes_taken": len(attempts),
            "avg_score": round(avg_score, 1) if avg_score is not None else None,
            "completed_items": completed,
            "joined": s.created_at.strftime("%b %d, %Y") if s.created_at else "N/A"
        })
    return jsonify(sorted(output, key=lambda x: x['name']))


# ── NEW: Teacher Student Detail ──────────────────────────────────────
@analytics_bp.route('/teacher/students/<uuid:student_id>', methods=['GET'])
@roles_required('teacher', 'administrator')
def get_student_detail(student_id):
    """Full detail view for a single student: profile, course progress, quiz history."""
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)

    # Course progress
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    course_progress = []
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
            "max_score": float(a.max_score),
            "attempt_number": a.attempt_number,
            "date": a.submitted_at.strftime("%b %d, %Y %H:%M") if a.submitted_at else "N/A"
        })

    # Learning profile
    profile_data = None
    if hasattr(student, 'learning_profile') and student.learning_profile:
        lp = student.learning_profile
        profile_data = {
            "learning_style": lp.learning_style,
            "preferred_pace": lp.preferred_pace,
            "primary_goal": lp.primary_goal
        }

    # Overall stats
    avg_score = sum(float(a.score) for a in attempts) / len(attempts) if attempts else 0

    return jsonify({
        "id": str(student.id),
        "name": f"{student.first_name} {student.last_name}",
        "email": user.email if user else "",
        "joined": student.created_at.strftime("%b %d, %Y") if student.created_at else "N/A",
        "learning_profile": profile_data,
        "overall_avg_score": round(avg_score, 1),
        "total_quizzes": len(attempts),
        "course_progress": course_progress,
        "quiz_history": quiz_history
    })
