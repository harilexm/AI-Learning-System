from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from ..models import User

def roles_required(*required_roles):
    """
    Decorator to restrict access to users with specific roles.
    Checks inside the User/UserRole tables.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404

            user_roles = [r.role for r in user.roles]
            if not any(role in user_roles for role in required_roles):
                return jsonify({"error": "Unauthorized access. Insufficient role."}), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
