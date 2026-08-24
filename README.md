# AI Interview Evaluator

A locally-run AI interview evaluation system that generates interview questions from a job description, transcribes spoken answers, and evaluates candidate performance across multiple dimensions.

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

---

## Running the App

You need **3 terminals** running simultaneously.


### Terminal 1 — Backend (from the `backend` folder)

```
cd backend
uvicorn app.main:app --reload
```

Backend runs at: `http://localhost:8000`  
API docs available at: `http://localhost:8000/docs`

### Terminal 2 — Frontend (from the `frontend` folder)

```
cd frontend
python -m http.server 3000
```

Frontend runs at: `http://localhost:3000`
