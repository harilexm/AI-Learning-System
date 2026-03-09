from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import LearningContent, Student, AssessmentAttempt
from ..utils.decorators import roles_required
from flask import current_app
from openai import OpenAI
import json

quizzes_bp = Blueprint('quizzes', __name__, url_prefix='/api')

@quizzes_bp.route('/quizzes/<uuid:content_id>', methods=['GET'])
@jwt_required()
def get_quiz_questions(content_id):
    content = LearningContent.query.get_or_404(content_id)
    if content.type != 'quiz' or not content.quiz_data:
        return jsonify({"error": "This content is not a valid quiz."}), 404

    sanitized_questions = [{k: v for k, v in q.items() if k != 'correct_answer_index'} for q in content.quiz_data.get('questions', [])]
    return jsonify({"quiz_id": str(content.id), "title": content.title, "questions": sanitized_questions})

@quizzes_bp.route('/quizzes/<uuid:content_id>/submit', methods=['POST'])
@roles_required('student')
def submit_quiz(content_id):
    content = LearningContent.query.get_or_404(content_id)
    if content.type != 'quiz' or not content.quiz_data:
        return jsonify({"error": "This is not a valid quiz."}), 404

    student = Student.query.filter_by(user_id=get_jwt_identity()).first_or_404()
    student_answers = request.get_json().get('answers', {})
    correct_answers = {q['id']: q['correct_answer_index'] for q in content.quiz_data['questions']}
    
    score = sum(1 for q_id, c_idx in correct_answers.items() if int(student_answers.get(q_id, -1)) == c_idx)
    total = len(correct_answers)
    percentage = round((score / total) * 100, 2) if total > 0 else 0

    previous_attempts = AssessmentAttempt.query.filter_by(student_id=student.id, learning_content_id=content_id).count()
    new_attempt = AssessmentAttempt(
        learning_content_id=content_id, student_id=student.id,
        attempt_number=previous_attempts + 1, score=percentage,
        max_score=100.00, answers=student_answers
    )
    db.session.add(new_attempt)
    db.session.commit()

    feedback = None
    api_key = current_app.config.get('OPENAI_API_KEY')
    if percentage < 100 and api_key:
        client = OpenAI(api_key=api_key)
        wrong_questions = []
        for q in content.quiz_data['questions']:
            q_id = str(q['id'])
            student_ans_idx = int(student_answers.get(q_id, -1))
            if student_ans_idx != q['correct_answer_index']:
                wrong_questions.append({
                    "question": q['text'],
                    "student_answer": q['options'][student_ans_idx] if student_ans_idx != -1 else "No answer",
                    "correct_answer": q['options'][q['correct_answer_index']]
                })
        
        if wrong_questions:
            try:
                prompt = f"A student took a quiz and got these questions wrong: {json.dumps(wrong_questions)}. Provide a brief, encouraging 1-2 sentence explanation for each correct answer."
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "You are a helpful tutor. Be very concise."}, {"role": "user", "content": prompt}],
                    temperature=0.7, max_tokens=150
                )
                feedback = completion.choices[0].message.content
            except Exception:
                pass

    return jsonify({
        "message": "Quiz submitted successfully!", 
        "score": percentage, 
        "total_questions": total, 
        "correct_answers": correct_answers, 
        "student_answers": student_answers,
        "feedback": feedback
    })
