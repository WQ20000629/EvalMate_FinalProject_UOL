# EvalMate

A locally-run AI interview evaluation system that generates interview questions from a job description, transcribes spoken answers, and evaluates candidate performance across multiple dimensions. Registered users can save completed interviews and revisit them later from their history.

## How It Works

1. **Paste a job description.** Choose how many questions (1 to 5) and which types to include: Behavioural, Situational, Motivational, Technical.
2. **Questions are generated** from the job description by a local LLM.
3. **Answer each question by voice.** The browser records audio and, at the same time, tracks eye contact via the webcam. Recording can be redone before submitting.
4. **The answer is transcribed** to text, editable before submitting if the transcript isn't quite right.
5. **Each answer is scored** across four dimensions (Relevance, Content Depth, Clarity & Structure, Confidence Delivery) by the LLM, plus sentiment (tone) and eye contact, computed independently.
6. **Scores are combined into one weighted overall score** per answer: the four LLM dimensions at 20% each, sentiment at 10%, eye contact at 10%. If eye-contact data is missing (e.g. webcam access was denied), its weight is redistributed across the other dimensions rather than counted as 0.
7. **A final report** shows the score breakdown and written rationale for every answer.
8. **Logged-in users** have completed sessions saved automatically and can revisit them later from their history. Using the app without an account still works, but the session is not saved.

## Architecture

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript (Vite) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL, via SQLAlchemy + Alembic migrations |
| Auth | JWT (HS256) in an httpOnly cookie, passwords hashed with bcrypt |

**AI models:**

| Task | Model |
|---|---|
| Question generation | `llama3.2:3b` (local, via Ollama) |
| Answer scoring (4 dimensions) | `llama3.2:3b` (local, via Ollama) |
| Speech-to-text | OpenAI Whisper, `small` |
| Sentiment / tone analysis | `cardiffnlp/twitter-roberta-base-sentiment-latest` (HuggingFace) |
| Eye contact tracking | MediaPipe FaceMesh (runs client-side in the browser) |

The two LLM tasks, question generation and scoring, call the same local Ollama server but are otherwise independent. They use different prompts and do not share state. Whisper and the sentiment model run inside the backend process.

## Setup

### 1. Pull the Ollama model

```
ollama pull llama3.2:3b
```

### 2. Install Python dependencies

```
cd backend
pip install -r requirements.txt
```

### 3. Set up PostgreSQL

Create a database and a dedicated login role for the app (via `psql` or pgAdmin):

```sql
CREATE DATABASE interview_evaluator;
CREATE USER interview_app WITH PASSWORD 'pick-a-password';
GRANT ALL PRIVILEGES ON DATABASE interview_evaluator TO interview_app;
```

Then, from `backend/`, copy `.env.example` to `.env` and fill in your actual password and a random secret key:

```
cd backend
copy .env.example .env
```

```
DATABASE_URL=postgresql+psycopg2://interview_app:pick-a-password@localhost:5432/interview_evaluator
JWT_SECRET_KEY=<generate one with: python -c "import secrets; print(secrets.token_hex(32))">
```

`.env` is gitignored, so never commit real credentials.

### 4. Run the database migrations

```
cd backend
alembic upgrade head
```

This creates the `users`, `interview_sessions`, and `session_answers` tables. Run this again after pulling any future change to `backend/app/core/db_models.py`.

### 5. Install frontend dependencies

```
cd frontend
npm install
```

---

## Running the App

You need **2 terminals** running simultaneously, plus Ollama and PostgreSQL running in the background. PostgreSQL runs as a Windows service once installed (check with `Get-Service postgresql*` in PowerShell); Ollama is either the desktop app or `ollama serve` in its own terminal if it isn't already running as a service.

### Terminal 1: Backend (from the `backend` folder)

```
cd backend
uvicorn app.main:app --reload
```

Backend runs at: `http://localhost:8000`  
API docs available at: `http://localhost:8000/docs`

### Terminal 2: Frontend (from the `frontend` folder)

```
cd frontend
npm run dev
```

Frontend runs at: `http://localhost:5173`

The frontend is a React + TypeScript app (Vite). It needs its dev server running via `npm run dev`, not a plain static file server.
