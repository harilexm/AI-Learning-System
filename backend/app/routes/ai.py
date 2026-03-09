from flask import Blueprint, jsonify, request
from collections import Counter
from flask_jwt_extended import jwt_required, get_jwt_identity
import openai
import json
from ..extensions import db
from ..models import Student, StudentContentProgress, LearningContent, StudyPlan, AssessmentAttempt, ChatHistory, LearningProfile
from ..ai.recommender import get_recommendations as ml_recommend
from ..ai.gap_analyzer import analyze_learning_gaps
from ..utils.decorators import roles_required

ai_bp = Blueprint('ai', __name__, url_prefix='/api')

@ai_bp.route('/students/me/recommendations', methods=['GET'])
@roles_required('student')
def get_recommendations():
    """Generates personalized content recommendations for the logged-in student."""
    student = Student.query.filter_by(user_id=get_jwt_identity()).first()
    if not student:
        return jsonify([])

    completed_progress = StudentContentProgress.query.filter_by(student_id=student.id, status='completed').all()
    completed_content_ids = {p.content_id for p in completed_progress}

    if not completed_content_ids:
        return jsonify([])

    completed_contents = LearningContent.query.filter(LearningContent.id.in_(completed_content_ids), LearningContent.tags.isnot(None)).all()
    completed_titles = [c.title for c in completed_contents]

    candidates = LearningContent.query.filter(LearningContent.id.notin_(completed_content_ids), LearningContent.tags.isnot(None)).limit(50).all()
    
    all_available = []
    for c in candidates:
        all_available.append({
            "id": str(c.id), "title": c.title, "type": c.type, "tags": c.tags,
            "course_id": str(c.module.course.id),
            "module_title": c.module.title,
            "course_title": c.module.course.title
        })
        
    recommended = ml_recommend(completed_titles, all_available)
        
    return jsonify(recommended)

@ai_bp.route('/study-plan', methods=['POST'])
@roles_required('student')
def generate_study_plan():
    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()
    course_id = request.get_json().get('course_id')

    # Gather student's weak topics from quiz results
    attempts = AssessmentAttempt.query.filter_by(student_id=student.id).join(LearningContent).filter(LearningContent.type == 'quiz').all()
    quiz_results = [{"topic": a.quiz.title, "score": float(a.score), "attempts": a.attempt_number} for a in attempts]
    
    weak_topics = [t['topic'] for t in analyze_learning_gaps(quiz_results)]
    profile = LearningProfile.query.filter_by(student_id=student.id).first()

    prompt = f"""Create a 1-week study plan for a student with these characteristics:
    - Learning style: {profile.learning_style if profile else 'visual'}
    - Weak areas: {', '.join(weak_topics) if weak_topics else 'None identified yet'}

    Return a JSON object with format:
    {{"days": [{{"day": 1, "focus": "topic", "activities": ["activity1"], "duration_minutes": 30}}]}}
    """

    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[{"role": "system", "content": "You are an educational planning expert."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        plan_data = json.loads(completion.choices[0].message.content)
        study_plan = StudyPlan(student_id=student.id, title="AI Generated Plan", generated_plan=plan_data)
        db.session.add(study_plan)
        db.session.commit()
        return jsonify(plan_data)
    except Exception as e:
        return jsonify({"error": f"Failed to generate plan: {e}"}), 500

@ai_bp.route('/ai/generate-quiz', methods=['POST'])
@roles_required('teacher', 'administrator')
def generate_quiz_from_article():
    if not openai.api_key: return jsonify({"error": "AI service is not configured."}), 503
    
    article_text = request.get_json().get('text')
    if not article_text or len(article_text) < 100:
        return jsonify({"error": "Article text must be at least 100 characters."}), 400

    prompt = [
        {"role": "system", "content": "You are an expert educator. Generate a JSON object for a quiz with 3 multiple-choice questions from the text. Each question must have a unique 'id', 'text', three 'options', and the 'correct_answer_index' (0, 1, or 2)."},
        {"role": "user", "content": f"Article text: ```{article_text}```"}
    ]
    try:
        completion = openai.chat.completions.create(model="gpt-3.5-turbo-1106", messages=prompt, response_format={"type": "json_object"}, temperature=0.5)
        quiz_data = json.loads(completion.choices[0].message.content)
        if 'questions' not in quiz_data or not isinstance(quiz_data.get('questions'), list):
            raise ValueError("Invalid 'questions' format from AI.")
        return jsonify(quiz_data)
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({"error": f"AI generated invalid data: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An OpenAI API error occurred: {e}"}), 500

@ai_bp.route('/ai/chatbot', methods=['POST'])
@roles_required('student')
def handle_chatbot_query():
    if not openai.api_key: return jsonify({"error": "AI service is not configured."}), 503

    data = request.get_json()
    question, article_text = data.get('question'), data.get('context')
    if not question or not article_text:
        return jsonify({"error": "Question and context are required."}), 400

    system_prompt = "You are StudyBot, a friendly tutor. Answer questions based ONLY on the provided article. If the answer isn't in the text, politely say so. Do not use outside knowledge."
    user_prompt = f"Article:\n--- START ---\n{article_text}\n--- END ---\n"
    
    try:
        student_model = Student.query.filter_by(user_id=get_jwt_identity()).first()
        history = []
        if student_model:
            past_chats = ChatHistory.query.filter_by(student_id=student_model.id).order_by(ChatHistory.timestamp.desc()).limit(6).all()
            for chat in reversed(past_chats):
                role = "user" if chat.sender == 'student' else "assistant"
                history.append({"role": role, "content": chat.message})
                
            db.session.add(ChatHistory(student_id=student_model.id, message=question, sender='student'))
            
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}] + history + [{"role": "user", "content": question}]
        
        completion = openai.chat.completions.create(model="gpt-3.5-turbo", messages=messages, temperature=0.3, max_tokens=200)
        bot_response = completion.choices[0].message.content
        
        if student_model:
            db.session.add(ChatHistory(student_id=student_model.id, message=bot_response, sender='bot'))
            db.session.commit()
            
        return jsonify({"answer": bot_response})
    except Exception as e:
        return jsonify({"error": f"An AI communication error occurred: {e}"}), 500
