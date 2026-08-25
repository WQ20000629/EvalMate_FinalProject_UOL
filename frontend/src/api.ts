import type { Question, EvaluationResult, SentimentResult, SessionResult, ReportSummary } from "./types";

const SERVER_BASE = "http://localhost:8000/api";

async function postRequest<T>(path: string, payload: unknown, multipart = false): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 120000);

  const cfg: RequestInit = { method: "POST", signal: controller.signal };
  if (multipart) {
    cfg.body = payload as BodyInit;
  } else {
    cfg.headers = { "Content-Type": "application/json" };
    cfg.body = JSON.stringify(payload);
  }

  try {
    const resp = await fetch(`${SERVER_BASE}${path}`, cfg);
    clearTimeout(timer);
    if (!resp.ok) {
      const errBody = await resp.json().catch(() => ({ detail: `${resp.status} ${resp.statusText}` }));
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

export function generateQuestions(
  jobDescription: string,
  numQuestions: number,
  questionTypes: string[]
): Promise<Question[]> {
  return postRequest<{ questions: Question[] }>("/generate-questions", {
    job_description: jobDescription,
    num_questions: numQuestions,
    question_types: questionTypes,
  }).then((r) => r.questions);
}

export function transcribeAudio(clip: Blob): Promise<string> {
  const fd = new FormData();
  fd.append("file", clip, "answer.webm");
  return postRequest<{ transcript: string }>("/transcribe", fd, true).then((r) => r.transcript);
}

export function evaluateAnswer(
  question: string,
  transcript: string,
  questionType: string
): Promise<EvaluationResult> {
  return postRequest<EvaluationResult>("/evaluate", {
    question,
    transcript,
    question_type: questionType,
  });
}

export function getSentiment(transcript: string): Promise<SentimentResult> {
  return postRequest<SentimentResult>("/sentiment", { transcript });
}

export function getFinalReport(results: SessionResult[]): Promise<ReportSummary> {
  return postRequest<ReportSummary>("/final-report", { results });
}
