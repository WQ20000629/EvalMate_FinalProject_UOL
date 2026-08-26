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

### 3. Install frontend dependencies

```
cd frontend
npm install
```

---

## Running the App

You need **2 terminals** running simultaneously, plus Ollama running in the background (the desktop app, or `ollama serve` in its own terminal if it isn't already running as a service).

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
npm run dev
```

Frontend runs at: `http://localhost:5173`

The frontend is a React + TypeScript app (Vite) — it needs its dev server running via `npm run dev`, not a plain static file server.
