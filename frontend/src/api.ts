// ------------------------------------------------------------------
// File: frontend/src/api.ts
// Purpose: Sends requests from the frontend to the backend API.
// ------------------------------------------------------------------

// Types describe the data sent to and returned from the backend.
import type {
    Question,
    EvaluationResult,
    SentimentResult,
    SessionResult,
    ReportSummary,
    User,
    SessionSummary,
} from "./types";

// Base URL used by all frontend requests.
const SERVER_BASE = "http://localhost:8000/api";

// Send a request, handle errors, and stop requests that take too long.
async function request<T>(path: string, cfg: RequestInit): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 120000);

    try {
        const resp = await fetch(`${SERVER_BASE}${path}`, {
            ...cfg,
            credentials: "include",
            signal: controller.signal,
        });
        clearTimeout(timer);
        if (!resp.ok) {
            const errBody = await resp
                .json()
                .catch(() => ({ detail: `${resp.status} ${resp.statusText}` }));
            throw new Error(errBody.detail || "Unknown error");
        }
        return resp.json() as Promise<T>;
    } catch (e) {
        clearTimeout(timer);
        if (e instanceof Error && e.name === "AbortError") {
            throw new Error("Request timed out. Ollama may be overloaded.");
        }
        throw e;
    }
}

// Send a request without a request body.
function getRequest<T>(path: string): Promise<T> {
    return request<T>(path, { method: "GET" });
}

// Send either JSON data or a file form.
function postRequest<T>(
    path: string,
    payload: unknown,
    multipart = false,
): Promise<T> {
    const cfg: RequestInit = { method: "POST" };
    if (multipart) {
        cfg.body = payload as BodyInit;
    } else {
        cfg.headers = { "Content-Type": "application/json" };
        cfg.body = JSON.stringify(payload);
    }
    return request<T>(path, cfg);
}

// Generate interview questions from a job description.
export function generateQuestions(
    jobDescription: string,
    numQuestions: number,
    questionTypes: string[],
): Promise<Question[]> {
    return postRequest<{ questions: Question[] }>("/generate-questions", {
        job_description: jobDescription,
        num_questions: numQuestions,
        question_types: questionTypes,
    }).then((r) => r.questions);
}

// Upload a recorded audio clip and return its transcript.
export function transcribeAudio(clip: Blob): Promise<string> {
    const fd = new FormData();
    fd.append("file", clip, "answer.webm");
    return postRequest<{ transcript: string }>("/transcribe", fd, true).then(
        (r) => r.transcript,
    );
}

// Send one answer to the rubric evaluator.
export function evaluateAnswer(
    question: string,
    transcript: string,
    questionType: string,
): Promise<EvaluationResult> {
    return postRequest<EvaluationResult>("/evaluate", {
        question,
        transcript,
        question_type: questionType,
    });
}

// Ask the backend to classify the tone of a transcript.
export function getSentiment(transcript: string): Promise<SentimentResult> {
    return postRequest<SentimentResult>("/sentiment", { transcript });
}

// Request the complete report for the current interview.
export function getFinalReport(
    results: SessionResult[],
    jobDescription: string,
): Promise<ReportSummary> {
    return postRequest<ReportSummary>("/final-report", {
        results,
        job_description: jobDescription,
    });
}

// Authentication requests.

// Create a new user account.
export function registerUser(email: string, password: string): Promise<User> {
    return postRequest<User>("/auth/register", { email, password });
}

// Log in an existing user.
export function loginUser(email: string, password: string): Promise<User> {
    return postRequest<User>("/auth/login", { email, password });
}

// Clear the authentication cookie on the backend.
export function logoutUser(): Promise<{ status: string }> {
    return postRequest<{ status: string }>("/auth/logout", {});
}

// Check whether a user is already logged in.
export function getMe(): Promise<User> {
    return getRequest<User>("/auth/me");
}

// Saved interview history requests.

// Get saved sessions for the current user.
export function listSessions(): Promise<SessionSummary[]> {
    return getRequest<SessionSummary[]>("/sessions");
}

// Get the full report for one saved session.
export function getSession(id: number): Promise<ReportSummary> {
    return getRequest<ReportSummary>(`/sessions/${id}`);
}
