from flask_sqlalchemy import SQLAlchemy
import uuid
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB, NUMERIC 
import datetime

db = SQLAlchemy()

# roles: user join table from the schema
class UserRole(db.Model):
    __tablename__ = 'user_roles'
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), primary_key=True)
    role = db.Column(ENUM('student', 'teacher', 'administrator', name='role_name'), primary_key=True)
    granted_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

# user model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # define relationships
    roles = db.relationship('UserRole', backref='user', lazy=True, cascade="all, delete-orphan")
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

# studnet Model
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Student {self.first_name} {self.last_name}>'

# Teacher model
class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100)) # e.g., "Professor", "Instructor"
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Teacher {self.first_name} {self.last_name}>'
# new model down here as course, ai system etc

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_by_teacher_id = db.Column(UUID(as_uuid=True), db.ForeignKey('teachers.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationships
    modules = db.relationship('Module', backref='course', lazy=True, cascade="all, delete-orphan")
    teacher = db.relationship('Teacher', backref='courses')
    def __repr__(self):
        return f'<Course {self.title}>'

class Module(db.Model):
    __tablename__ = 'modules'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    module_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationships
    learning_contents = db.relationship('LearningContent', backref='module', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Module {self.title}>'

class LearningContent(db.Model):
    __tablename__ = 'learning_content'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = db.Column(UUID(as_uuid=True), db.ForeignKey('modules.id'), nullable=False)
    type = db.Column(ENUM('video', 'article', 'quiz', 'exercise', 'assignment', name='content_type'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content_url = db.Column(db.Text) # For videos, external links
    content_body = db.Column(db.Text) # For articles, text
    content_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    quiz_data = db.Column(JSONB, nullable=True)
    tags = db.Column(db.String(255), nullable=True) # e.g., "algebra,calculus,intro"
    def __repr__(self):
        return f'<LearningContent {self.title}>'

# --- NEW MODEL (NOW WITH __repr__) ---
# backend/models.py

# --- Find and verify this specific class ---

class AssessmentAttempt(db.Model):
    __tablename__ = 'assessment_attempts'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = db.Column(UUID(as_uuid=True), db.ForeignKey('learning_content.id'), nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    score = db.Column(NUMERIC(5, 2), nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    # --- THIS IS THE CRITICAL LINE ---
    # Ensure this line exists and is correct.
    max_score = db.Column(NUMERIC(5, 2), nullable=False)
    
    answers = db.Column(JSONB, nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref='quiz_attempts')
    quiz = db.relationship('LearningContent', backref='attempts')

    def __repr__(self):
        return f'<AssessmentAttempt student={self.student_id} quiz={self.content_id} score={self.score}>'
# backend/models.py
# ... (all existing imports and models are unchanged) ...

class StudentContentProgress(db.Model):
    __tablename__ = 'student_content_progress'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    content_id = db.Column(UUID(as_uuid=True), db.ForeignKey('learning_content.id'), nullable=False)
    status = db.Column(ENUM('not_started', 'in_progress', 'completed', 'skipped', name='progress_status'), nullable=False, default='not_started')
    started_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))
    last_accessed_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationships for easy access
    student = db.relationship('Student', backref='progress_records')
    learning_content = db.relationship('LearningContent', backref='progress_records')

    def __repr__(self):
        return f'<Progress student={self.student_id} content={self.content_id} status={self.status}>'
    