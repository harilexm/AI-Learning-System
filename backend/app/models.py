import uuid
import datetime
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB, NUMERIC
from .extensions import db

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
    title = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Teacher {self.first_name} {self.last_name}>'

# Course model
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_by_teacher_id = db.Column(UUID(as_uuid=True), db.ForeignKey('teachers.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    modules = db.relationship('Module', backref='course', lazy=True, cascade="all, delete-orphan")
    teacher = db.relationship('Teacher', backref='courses')
    
    def __repr__(self):
        return f'<Course {self.title}>'

# Module model
class Module(db.Model):
    __tablename__ = 'modules'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    module_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    learning_contents = db.relationship('LearningContent', backref='module', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Module {self.title}>'
    
# LearningContent model
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

# AssessmentAttempt model
class AssessmentAttempt(db.Model):
    __tablename__ = 'assessment_attempts'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_content_id  = db.Column(UUID(as_uuid=True), db.ForeignKey('learning_content.id'), nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    score = db.Column(NUMERIC(5, 2), nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    max_score = db.Column(NUMERIC(5, 2), nullable=False)
    answers = db.Column(JSONB, nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    student = db.relationship('Student', backref='quiz_attempts')
    quiz = db.relationship('LearningContent', backref='attempts')

    def __repr__(self):
        return f'<AssessmentAttempt student={self.student_id} quiz={self.learning_content_id } score={self.score}>'

# StudentContentProgress model
class StudentContentProgress(db.Model):
    __tablename__ = 'student_content_progress'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    content_id = db.Column(UUID(as_uuid=True), db.ForeignKey('learning_content.id'), nullable=False)
    status = db.Column(ENUM('not_started', 'in_progress', 'completed', 'skipped', name='progress_status'), nullable=False, default='not_started')
    started_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))
    last_accessed_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    student = db.relationship('Student', backref='progress_records')
    learning_content = db.relationship('LearningContent', backref='progress_records')

    def __repr__(self):
        return f'<Progress student={self.student_id} content={self.content_id} status={self.status}>'

# Enrollment model
class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    student = db.relationship('Student', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')

# ChatHistory model
class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    content_id = db.Column(UUID(as_uuid=True), db.ForeignKey('learning_content.id'), nullable=True) # Optional, if tied to specific content
    message = db.Column(db.Text, nullable=False)
    sender = db.Column(ENUM('student', 'bot', name='sender_type'), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    student = db.relationship('Student', backref='chat_messages')

# LearningProfile model
class LearningProfile(db.Model):
    __tablename__ = 'learning_profiles'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False, unique=True)
    primary_goal = db.Column(db.String(255))
    learning_style = db.Column(ENUM('visual', 'auditory', 'reading', 'kinesthetic', name='learning_style_enum'), nullable=True)
    preferred_pace = db.Column(ENUM('slow', 'medium', 'fast', name='pace_enum'), default='medium')
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    student = db.relationship('Student', backref=db.backref('learning_profile', uselist=False))

# StudyPlan model
class StudyPlan(db.Model):
    __tablename__ = 'study_plans'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    generated_plan = db.Column(JSONB, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    student = db.relationship('Student', backref='study_plans')

# TeacherRemark model
class TeacherRemark(db.Model):
    __tablename__ = 'teacher_remarks'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = db.Column(UUID(as_uuid=True), db.ForeignKey('teachers.id'), nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(ENUM('remark', 'encouragement', 'warning', name='remark_type'), nullable=False, default='remark')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    teacher = db.relationship('Teacher', backref='remarks_sent')
    student = db.relationship('Student', backref='remarks_received')

# DiscussionPost model
class DiscussionPost(db.Model):
    __tablename__ = 'discussion_posts'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey('courses.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    user = db.relationship('User', backref='discussion_posts')
    course = db.relationship('Course', backref='discussion_posts')
    replies = db.relationship('DiscussionReply', backref='post', lazy=True, cascade="all, delete-orphan", order_by='DiscussionReply.created_at')

# DiscussionReply model
class DiscussionReply(db.Model):
    __tablename__ = 'discussion_replies'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = db.Column(UUID(as_uuid=True), db.ForeignKey('discussion_posts.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)

    user = db.relationship('User', backref='discussion_replies')