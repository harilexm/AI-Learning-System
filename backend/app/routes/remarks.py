from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Teacher, Student, TeacherRemark
from ..utils.decorators import roles_required

remarks_bp = Blueprint('remarks', __name__, url_prefix='/api')

@remarks_bp.route('/teacher/students/<uuid:student_id>/remarks', methods=['POST'])
@roles_required('teacher', 'administrator')
def create_remark(student_id):
    """Teacher sends a remark/feedback/warning to a student."""
    student = Student.query.get_or_404(student_id)
    teacher = Teacher.query.filter_by(user_id=get_jwt_identity()).first()
    if not teacher:
        return jsonify({"error": "Teacher profile not found."}), 404

    data = request.get_json()
    if not data or not data.get('message', '').strip():
        return jsonify({"error": "Message is required."}), 400

    remark_type = data.get('type', 'remark')
    if remark_type not in ['remark', 'encouragement', 'warning']:
        remark_type = 'remark'

    remark = TeacherRemark(
        teacher_id=teacher.id,
        student_id=student.id,
        message=data['message'].strip(),
        type=remark_type
    )
    db.session.add(remark)
    db.session.commit()

    return jsonify({"message": "Remark sent successfully.", "id": str(remark.id)}), 201


@remarks_bp.route('/teacher/students/<uuid:student_id>/remarks', methods=['GET'])
@roles_required('teacher', 'administrator')
def get_student_remarks(student_id):
    """Get all remarks for a specific student (teacher view)."""
    Student.query.get_or_404(student_id)
    remarks = TeacherRemark.query.filter_by(student_id=student_id).order_by(TeacherRemark.created_at.desc()).all()
    
    output = []
    for r in remarks:
        output.append({
            "id": str(r.id),
            "message": r.message,
            "type": r.type,
            "is_read": r.is_read,
            "created_at": r.created_at.strftime("%b %d, %Y %H:%M") if r.created_at else "N/A",
            "teacher_name": f"{r.teacher.first_name} {r.teacher.last_name}" if r.teacher else "Unknown"
        })
    return jsonify(output)


@remarks_bp.route('/students/me/remarks', methods=['GET'])
@roles_required('student')
def get_my_remarks():
    """Student views their own remarks/feedback from teachers."""
    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()
    remarks = TeacherRemark.query.filter_by(student_id=student.id).order_by(TeacherRemark.created_at.desc()).all()
    
    output = []
    for r in remarks:
        output.append({
            "id": str(r.id),
            "message": r.message,
            "type": r.type,
            "is_read": r.is_read,
            "created_at": r.created_at.strftime("%b %d, %Y %H:%M") if r.created_at else "N/A",
            "teacher_name": f"{r.teacher.first_name} {r.teacher.last_name}" if r.teacher else "Unknown"
        })
    
    # Mark all as read
    TeacherRemark.query.filter_by(student_id=student.id, is_read=False).update({"is_read": True})
    db.session.commit()
    
    return jsonify(output)
