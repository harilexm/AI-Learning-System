from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import DiscussionPost, DiscussionReply, Course, User, UserRole
from ..utils.decorators import roles_required
import uuid

discussions_bp = Blueprint('discussions', __name__, url_prefix='/api')


@discussions_bp.route('/teacher/discussions', methods=['GET'])
@roles_required('teacher', 'administrator')
def get_teacher_discussions():
    """Get all recent discussion posts across all courses for teacher dashboard.
    Highlights unanswered posts (no reply from a teacher/admin)."""
    posts = DiscussionPost.query.order_by(DiscussionPost.created_at.desc()).limit(20).all()

    output = []
    for p in posts:
        user = User.query.get(p.user_id)
        roles = [r.role for r in user.roles] if user else []
        role_label = 'Teacher' if 'teacher' in roles else ('Admin' if 'administrator' in roles else 'Student')
        course = Course.query.get(p.course_id)

        # Check if any teacher/admin has replied
        has_teacher_reply = False
        for r in p.replies:
            reply_user = User.query.get(r.user_id)
            if reply_user:
                reply_roles = [rr.role for rr in reply_user.roles]
                if 'teacher' in reply_roles or 'administrator' in reply_roles:
                    has_teacher_reply = True
                    break

        output.append({
            "id": str(p.id),
            "title": p.title,
            "body": p.body[:150] + ('...' if len(p.body) > 150 else ''),
            "author": user.username if user else "Unknown",
            "author_role": role_label,
            "course_title": course.title if course else "Unknown",
            "course_id": str(p.course_id),
            "reply_count": len(p.replies),
            "answered": has_teacher_reply,
            "created_at": p.created_at.strftime("%b %d, %Y %H:%M") if p.created_at else "N/A"
        })
    return jsonify(output)


@discussions_bp.route('/courses/<uuid:course_id>/discussions', methods=['GET'])
@jwt_required()
def get_discussions(course_id):
    """Get all discussion posts for a course, with reply counts."""
    Course.query.get_or_404(course_id)
    posts = DiscussionPost.query.filter_by(course_id=course_id).order_by(DiscussionPost.created_at.desc()).all()

    output = []
    for p in posts:
        user = User.query.get(p.user_id)
        # Determine role display
        roles = [r.role for r in user.roles] if user else []
        role_label = 'Teacher' if 'teacher' in roles else ('Admin' if 'administrator' in roles else 'Student')

        output.append({
            "id": str(p.id),
            "title": p.title,
            "body": p.body,
            "author": user.username if user else "Unknown",
            "author_role": role_label,
            "reply_count": len(p.replies),
            "created_at": p.created_at.strftime("%b %d, %Y %H:%M") if p.created_at else "N/A"
        })
    return jsonify(output)


@discussions_bp.route('/courses/<uuid:course_id>/discussions', methods=['POST'])
@jwt_required()
def create_discussion(course_id):
    """Create a new discussion post in a course."""
    Course.query.get_or_404(course_id)
    data = request.get_json()

    if not data or not data.get('title', '').strip() or not data.get('body', '').strip():
        return jsonify({"error": "Title and body are required."}), 400

    post = DiscussionPost(
        course_id=course_id,
        user_id=uuid.UUID(get_jwt_identity()),
        title=data['title'].strip(),
        body=data['body'].strip()
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({"message": "Discussion posted!", "id": str(post.id)}), 201


@discussions_bp.route('/discussions/<uuid:post_id>', methods=['GET'])
@jwt_required()
def get_discussion_detail(post_id):
    """Get a single discussion post with all its replies."""
    post = DiscussionPost.query.get_or_404(post_id)
    user = User.query.get(post.user_id)
    roles = [r.role for r in user.roles] if user else []
    role_label = 'Teacher' if 'teacher' in roles else ('Admin' if 'administrator' in roles else 'Student')

    replies = []
    for r in post.replies:
        reply_user = User.query.get(r.user_id)
        reply_roles = [rr.role for rr in reply_user.roles] if reply_user else []
        reply_role = 'Teacher' if 'teacher' in reply_roles else ('Admin' if 'administrator' in reply_roles else 'Student')
        replies.append({
            "id": str(r.id),
            "body": r.body,
            "author": reply_user.username if reply_user else "Unknown",
            "author_role": reply_role,
            "created_at": r.created_at.strftime("%b %d, %Y %H:%M") if r.created_at else "N/A"
        })

    return jsonify({
        "id": str(post.id),
        "title": post.title,
        "body": post.body,
        "author": user.username if user else "Unknown",
        "author_role": role_label,
        "course_id": str(post.course_id),
        "created_at": post.created_at.strftime("%b %d, %Y %H:%M") if post.created_at else "N/A",
        "replies": replies
    })


@discussions_bp.route('/discussions/<uuid:post_id>/replies', methods=['POST'])
@jwt_required()
def create_reply(post_id):
    """Reply to a discussion post."""
    DiscussionPost.query.get_or_404(post_id)
    data = request.get_json()

    if not data or not data.get('body', '').strip():
        return jsonify({"error": "Reply body is required."}), 400

    reply = DiscussionReply(
        post_id=post_id,
        user_id=uuid.UUID(get_jwt_identity()),
        body=data['body'].strip()
    )
    db.session.add(reply)
    db.session.commit()
    return jsonify({"message": "Reply posted!", "id": str(reply.id)}), 201
