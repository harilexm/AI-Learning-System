from getpass import getpass
from app import app, db, bcrypt
from models import User, Teacher, UserRole
from sqlalchemy.exc import IntegrityError

def create_admin():
    with app.app_context():
        try:
            username = input("Enter admin username: ")
            email = input("Enter admin email: ")
            # Check if user already exists
            if User.query.filter((User.username == username) | (User.email == email)).first():
                print("Error: A user with that username or email already exists.")
                return

            password = getpass("Enter admin password: ")
            confirm_password = getpass("Confirm admin password: ")
            if password != confirm_password:
                print("Error: Passwords do not match.")
                return

            # get names
            first_name = input("Enter first name: ")
            last_name = input("Enter last name: ")
            # Hash the password
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            # Create admin
            admin_user = User(
                username=username,
                email=email,
                password_hash=hashed_password
            )
            db.session.add(admin_user)
            db.session.flush() # Get user ID
            # Create the teacher/admin profile
            admin_profile = Teacher(
                user_id=admin_user.id,
                first_name=first_name,
                last_name=last_name,
                title="Administrator"
            )
            db.session.add(admin_profile)
            # Assign the 'administrator' role
            admin_role = UserRole(user_id=admin_user.id, role='administrator')
            db.session.add(admin_role)
            db.session.commit()
            print(f"\n Administrator '{username}' created successfully!")

        except IntegrityError:
            db.session.rollback()
            print("Error: Database integrity error. A user with these details might already exist.")
        except Exception as e:
            db.session.rollback()
            print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    create_admin()