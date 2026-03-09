"""
Seed script to populate the database with sample courses, modules, content, and users.
Run: python seed_data.py
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
from app.extensions import db, bcrypt
from app.models import (
    User, UserRole, Teacher, Student, Course, Module, LearningContent,
    StudentContentProgress, Enrollment
)

def seed():
    app = create_app()
    with app.app_context():
        print("[*] Seeding database...")

        # -- 1. Create Users --
        teacher_user = User.query.filter_by(username='seed_teacher').first()
        if not teacher_user:
            teacher_user = User(username='seed_teacher', email='teacher_seed@example.com',
                                password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'))
            db.session.add(teacher_user)
            db.session.flush()
            db.session.add(UserRole(user_id=teacher_user.id, role='teacher'))
            teacher_profile = Teacher(user_id=teacher_user.id, first_name='Dr. Sarah', last_name='Johnson', title='Professor')
            db.session.add(teacher_profile)
            db.session.commit()
            print("  [OK] Teacher created: teacher_seed@example.com / password123")
        else:
            teacher_profile = Teacher.query.filter_by(user_id=teacher_user.id).first()
            print("  [SKIP] Teacher already exists")

        student_user = User.query.filter_by(username='seed_student').first()
        if not student_user:
            student_user = User(username='seed_student', email='student_seed@example.com',
                                password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'))
            db.session.add(student_user)
            db.session.flush()
            db.session.add(UserRole(user_id=student_user.id, role='student'))
            student_profile = Student(user_id=student_user.id, first_name='Alex', last_name='Smith')
            db.session.add(student_profile)
            db.session.commit()
            print("  [OK] Student created: student_seed@example.com / password123")
        else:
            student_profile = Student.query.filter_by(user_id=student_user.id).first()
            print("  [SKIP] Student already exists")

        # ── 2. Create Courses & Content ──────────────────────────────
        courses_data = [
            {
                "title": "Introduction to Algebra",
                "description": "Master the fundamentals of algebra including variables, equations, and functions.",
                "modules": [
                    {
                        "title": "Variables & Expressions", "order": 1,
                        "contents": [
                            {"title": "What are Variables?", "type": "article", "order": 1, "tags": "algebra,variables,basics,math",
                             "body": "In algebra, a variable is a symbol (usually a letter) that represents an unknown value. Variables allow us to write general formulas and equations. For example, in the expression 2x + 3, 'x' is a variable. Variables are the foundation of all algebraic thinking and are used extensively in equations, functions, and mathematical modeling."},
                            {"title": "Simplifying Expressions", "type": "article", "order": 2, "tags": "algebra,expressions,simplification,math",
                             "body": "Simplifying algebraic expressions means combining like terms and reducing an expression to its simplest form. Like terms have the same variable raised to the same power. For example, 3x + 5x simplifies to 8x. Simplification is a critical skill that makes solving equations much easier."},
                            {"title": "Algebra Basics Quiz", "type": "quiz", "order": 3, "tags": "algebra,variables,quiz",
                             "quiz_data": {"questions": [
                                 {"id": "q1", "text": "What is a variable in algebra?", "options": ["A number", "A symbol representing an unknown value", "An equation"], "correct_answer_index": 1},
                                 {"id": "q2", "text": "Simplify: 3x + 5x", "options": ["8x", "15x", "8x²"], "correct_answer_index": 0},
                                 {"id": "q3", "text": "Which is an algebraic expression?", "options": ["5 + 3 = 8", "2x + 7", "Hello World"], "correct_answer_index": 1}
                             ]}}
                        ]
                    },
                    {
                        "title": "Equations & Solving", "order": 2,
                        "contents": [
                            {"title": "Linear Equations", "type": "article", "order": 1, "tags": "algebra,equations,linear,solving",
                             "body": "A linear equation is an equation where the highest power of the variable is 1. The standard form is ax + b = c. Solving linear equations involves isolating the variable using inverse operations. For example, to solve 2x + 3 = 11, subtract 3 from both sides to get 2x = 8, then divide by 2 to get x = 4."},
                            {"title": "Quadratic Equations", "type": "article", "order": 2, "tags": "algebra,equations,quadratic,advanced",
                             "body": "A quadratic equation has the form ax² + bx + c = 0, where a ≠ 0. Solving quadratic equations can be done through factoring, completing the square, or using the quadratic formula: x = (-b ± √(b²-4ac)) / 2a. The discriminant (b²-4ac) determines the nature of the roots."}
                        ]
                    }
                ]
            },
            {
                "title": "Introduction to Computer Science",
                "description": "Learn the fundamental concepts of computer science and programming.",
                "modules": [
                    {
                        "title": "Programming Basics", "order": 1,
                        "contents": [
                            {"title": "What is Programming?", "type": "article", "order": 1, "tags": "programming,basics,computer-science,intro",
                             "body": "Programming is the process of creating instructions that a computer can follow to perform tasks. Programs are written in programming languages like Python, JavaScript, and Java. Each language has its own syntax and rules, but they all share common concepts like variables, loops, and functions. Programming is a fundamental skill in computer science."},
                            {"title": "Data Types & Variables", "type": "article", "order": 2, "tags": "programming,data-types,variables,python",
                             "body": "In programming, data types define what kind of data can be stored in a variable. Common data types include integers (whole numbers), floats (decimal numbers), strings (text), and booleans (true/false). In Python, you can create a variable simply by assigning a value: name = 'Alice' creates a string variable called name."},
                            {"title": "Programming Basics Quiz", "type": "quiz", "order": 3, "tags": "programming,basics,quiz",
                             "quiz_data": {"questions": [
                                 {"id": "q1", "text": "What is a programming language?", "options": ["A human language", "A set of instructions for computers", "A type of hardware"], "correct_answer_index": 1},
                                 {"id": "q2", "text": "Which is a data type?", "options": ["Variable", "Integer", "Function"], "correct_answer_index": 1},
                                 {"id": "q3", "text": "What does a boolean represent?", "options": ["Text", "True or False", "Decimal numbers"], "correct_answer_index": 1}
                             ]}}
                        ]
                    },
                    {
                        "title": "Control Flow", "order": 2,
                        "contents": [
                            {"title": "If-Else Statements", "type": "article", "order": 1, "tags": "programming,control-flow,conditionals,python",
                             "body": "Conditional statements allow your program to make decisions. The if-else statement checks a condition and executes different blocks of code depending on whether the condition is true or false. For example: if temperature > 30: print('It is hot!') else: print('It is cool!'). You can also chain conditions using elif."},
                            {"title": "Loops in Python", "type": "article", "order": 2, "tags": "programming,loops,iteration,python",
                             "body": "Loops allow you to repeat a block of code multiple times. Python has two main types of loops: 'for' loops (which iterate over a sequence) and 'while' loops (which repeat as long as a condition is true). For example: for i in range(5): print(i) will print numbers 0 through 4."},
                            {"title": "Functions & Modules", "type": "article", "order": 3, "tags": "programming,functions,modules,python,reusability",
                             "body": "Functions are reusable blocks of code that perform a specific task. In Python, you define a function using the 'def' keyword. Functions can accept parameters and return values. Modules are files containing functions that can be imported. Using functions and modules makes code organized, reusable, and easier to debug."}
                        ]
                    }
                ]
            },
            {
                "title": "Introduction to Mathematics",
                "description": "Explore essential mathematical concepts from geometry to statistics.",
                "modules": [
                    {
                        "title": "Geometry Fundamentals", "order": 1,
                        "contents": [
                            {"title": "Shapes and Properties", "type": "article", "order": 1, "tags": "math,geometry,shapes,basics",
                             "body": "Geometry is the study of shapes, sizes, and properties of space. Basic shapes include triangles, rectangles, circles, and polygons. Each shape has specific properties: triangles have 3 sides and angles summing to 180°, rectangles have 4 right angles, and circles are defined by their radius."},
                            {"title": "Area and Perimeter", "type": "article", "order": 2, "tags": "math,geometry,area,perimeter,formulas",
                             "body": "Area measures the space inside a shape, while perimeter measures the distance around it. Key formulas: Rectangle area = length × width, Triangle area = ½ × base × height, Circle area = π × r². Understanding these formulas is essential for solving real-world problems."}
                        ]
                    },
                    {
                        "title": "Statistics Basics", "order": 2,
                        "contents": [
                            {"title": "Mean, Median, Mode", "type": "article", "order": 1, "tags": "math,statistics,mean,median,mode,data-analysis",
                             "body": "Statistics helps us understand data. The mean (average) is found by dividing the sum by the count. The median is the middle value when data is sorted. The mode is the most frequent value. These measures of central tendency each provide different insights into your data set."},
                            {"title": "Probability Basics", "type": "article", "order": 2, "tags": "math,statistics,probability,basics",
                             "body": "Probability measures the likelihood of an event occurring, expressed as a number between 0 and 1. A probability of 0 means impossible, and 1 means certain. The probability of flipping heads on a coin is 0.5 (50%). Probability is fundamental to statistics, machine learning, and decision-making."}
                        ]
                    }
                ]
            }
        ]

        for course_data in courses_data:
            existing = Course.query.filter_by(title=course_data['title']).first()
            if existing:
                print(f"  [SKIP] Course '{course_data['title']}' already exists")
                continue

            course = Course(title=course_data['title'], description=course_data['description'],
                          created_by_teacher_id=teacher_profile.id)
            db.session.add(course)
            db.session.flush()

            for mod_data in course_data['modules']:
                module = Module(course_id=course.id, title=mod_data['title'],
                              module_order=mod_data['order'])
                db.session.add(module)
                db.session.flush()

                for content_data in mod_data['contents']:
                    content = LearningContent(
                        module_id=module.id,
                        title=content_data['title'],
                        type=content_data['type'],
                        content_order=content_data['order'],
                        tags=content_data.get('tags'),
                        content_body=content_data.get('body'),
                        quiz_data=content_data.get('quiz_data')
                    )
                    db.session.add(content)

            db.session.commit()
            print(f"  [OK] Course '{course_data['title']}' created with modules and content")

        # ── 3. Enroll Student & Mark Some Progress ───────────────────
        # Enroll student in the first two courses
        courses = Course.query.limit(2).all()
        for course in courses:
            existing_enr = Enrollment.query.filter_by(student_id=student_profile.id, course_id=course.id).first()
            if not existing_enr:
                db.session.add(Enrollment(student_id=student_profile.id, course_id=course.id))
                print(f"  [OK] Student enrolled in '{course.title}'")

        # Mark some content as completed (so recommendations trigger)
        completed_contents = LearningContent.query.filter(
            LearningContent.tags.isnot(None),
            LearningContent.type.in_(['article', 'video'])
        ).limit(3).all()

        for content in completed_contents:
            existing_prog = StudentContentProgress.query.filter_by(
                student_id=student_profile.id, content_id=content.id
            ).first()
            if not existing_prog:
                db.session.add(StudentContentProgress(
                    student_id=student_profile.id, content_id=content.id, status='completed'
                ))
                print(f"  [OK] Marked '{content.title}' as completed")

        db.session.commit()
        print("\n[*] Seeding complete! You can now log in and see recommendations.")
        print("   Teacher: teacher@example.com / password123")
        print("   Student: student@example.com / password123")

if __name__ == '__main__':
    seed()
