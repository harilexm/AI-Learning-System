import os
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from app import app, db

def wait_for_db():
    """Waits for the database to be ready before proceeding."""
    retries = 10
    delay = 5  # seconds
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set.")

    print("Attempting to connect to the database...")
    
    for i in range(retries):
        try:
            engine = create_engine(db_url)
            engine.connect()
            print("Database connection successful!")
            return
        except OperationalError as e:
            print(f"Database connection failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            
    raise RuntimeError("Could not connect to the database after several retries.")

if __name__ == '__main__':
    with app.app_context():
        # First, wait for the db container to be fully up and running
        wait_for_db()
        
        # Now, create all the tables based on the models
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")