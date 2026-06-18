## Project Motivation

**The Problem**: Traditional learning platforms often lack personalized, hands-on environments and struggle to present complex concepts interactively.  
**Our Solution**: We built a centralized, dynamic platform that integrates interactive quizzes and rich multimedia content, bridging the gap between theory and practice.  
**The Impact**: This enables educators to easily track student progress while empowering students to learn at their own pace through a highly interactive UI.

---

# AI Learning System

This repository contains a full-stack web application for an AI Learning System.  

**Frontend**: Built with Vue.js, Vite, and Pinia.  
**Backend**: Python API built with Flask, SQLAlchemy, and PostgreSQL.

The system is designed to serve AI-related learning content, models, or curriculum modules with an interactive user interface.

---

## Features

**Backend**
- REST API built with Python (Flask)
- PostgreSQL database integration
- Authentication using JWT
- Endpoints for handling user data, courses, or AI model interactions
- Model inference logic / AI service integration

**Frontend**
- Vue.js UI for browsing content, taking quizzes, or running demos
- User authentication pages (login, register)
- Dynamic views for AI learning modules
- State management via Pinia

---

## Prerequisites

Before running locally, ensure you have:

- **Node.js** (v20+ or v22+) & **npm**
- **Python 3.x**
- **PostgreSQL** (running locally or accessible via URL)

---

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/harilexm/AILearningSystem.git
cd AILearningSystem
```

### 2. Backend Setup

The backend is a Flask application located in the `backend` directory.

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:                   # On macOS/Linux:
venv\Scripts\activate           source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
```

Make sure to edit the `.env` file to include your PostgreSQL connection URL and other required keys.

### 3. Database Setup (PostgreSQL)

Before running migrations, make sure your PostgreSQL database exists.

1. Open **pgAdmin** or your `psql` command line.
2. Create an empty database (e.g., `ai_learning_db`).
   - SQL command: `CREATE DATABASE ai_learning_db;`
3. Update the `DATABASE_URL` in your `backend/.env` file to match your credentials. For example:
   `DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/ai_learning_db"`

Once the database is created and the `.env` file is updated, you can run migrations to create the tables.

```bash
# Run database migrations
flask db upgrade

# Optional: Seed the database with sample data (courses, modules, dummy users)
python seed_data.py

# Optional: Create an admin user account
python seed.py

# Run the development server
python run.py
```
The backend API will be available at `http://localhost:5000`.

### 4. Frontend Setup

The frontend is a Vue 3 application built with Vite located in the `frontend` directory.

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```
The frontend application will be accessible at the URL provided by Vite (usually `http://localhost:5173`).
