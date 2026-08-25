import { useState } from "react";
import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { SetupScreen } from "./components/SetupScreen";
import { InterviewScreen } from "./components/InterviewScreen";
import { ReportScreen } from "./components/ReportScreen";
import { LoadingOverlay } from "./components/LoadingOverlay";
import { generateQuestions, evaluateAnswer, getSentiment, getFinalReport } from "./api";
import { fallbackAggregate } from "./reportFallback";
import type { Question, SessionResult, ReportSummary } from "./types";

type Screen = "setup" | "interview" | "report";

function App() {
  const [screen, setScreen] = useState<Screen>("setup");
  const [questionBank, setQuestionBank] = useState<Question[]>([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [sessionResults, setSessionResults] = useState<SessionResult[]>([]);
  const [reportSummary, setReportSummary] = useState<ReportSummary | null>(null);

  const [loading, setLoading] = useState<{ active: boolean; message: string }>({ active: false, message: "" });
  const [setupError, setSetupError] = useState<string | null>(null);
  const [interviewError, setInterviewError] = useState<string | null>(null);

  const handleGenerate = async (jobDescription: string, numQuestions: number, questionTypes: string[]) => {
    setSetupError(null);
    setLoading({ active: true, message: "Generating questions..." });
    try {
      const questions = await generateQuestions(jobDescription, numQuestions, questionTypes);
      setQuestionBank(questions);
      setQuestionIndex(0);
      setSessionResults([]);
      setScreen("interview");
    } catch (e) {
      setSetupError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading({ active: false, message: "" });
    }
  };

  const buildReport = async (results: SessionResult[]) => {
    setLoading({ active: true, message: "Generating final report..." });
    try {
      const summary = await getFinalReport(results);
      setReportSummary(summary);
      setScreen("report");
    } catch {
      setReportSummary(fallbackAggregate(results));
      setScreen("report");
    } finally {
      setLoading({ active: false, message: "" });
    }
  };

  const handleSubmitAnswer = async (transcript: string, eyeContactScore: number | null) => {
    setInterviewError(null);
    const current = questionBank[questionIndex];
    setLoading({ active: true, message: "Evaluating answer..." });
    try {
      const [evaluation, sentiment] = await Promise.all([
        evaluateAnswer(current.question, transcript, current.type),
        getSentiment(transcript),
      ]);

      const newResult: SessionResult = {
        question: current.question,
        question_type: current.type,
        transcript,
        evaluation,
        sentiment,
        eye_contact_score: eyeContactScore,
      };
      const updatedResults = [...sessionResults, newResult];
      setSessionResults(updatedResults);

      const nextIndex = questionIndex + 1;
      if (nextIndex < questionBank.length) {
        setQuestionIndex(nextIndex);
        setLoading({ active: false, message: "" });
      } else {
        await buildReport(updatedResults);
      }
    } catch (e) {
      setInterviewError(e instanceof Error ? `Evaluation failed: ${e.message}` : "Unknown error");
      setLoading({ active: false, message: "" });
    }
  };

  const handleRestart = () => {
    setQuestionBank([]);
    setQuestionIndex(0);
    setSessionResults([]);
    setReportSummary(null);
    setSetupError(null);
    setInterviewError(null);
    setScreen("setup");
  };

  return (
    <div className="app-shell">
      <Navbar />

      <main className="app-main">
        {screen === "setup" && <SetupScreen onGenerate={handleGenerate} error={setupError} />}

        {screen === "interview" && questionBank[questionIndex] && (
          <InterviewScreen
            question={questionBank[questionIndex]}
            questionNumber={questionIndex + 1}
            totalQuestions={questionBank.length}
            onSubmitAnswer={handleSubmitAnswer}
            error={interviewError}
          />
        )}

        {screen === "report" && reportSummary && <ReportScreen summary={reportSummary} onRestart={handleRestart} />}
      </main>

      <Footer />

      <LoadingOverlay visible={loading.active} message={loading.message} />
    </div>
  );
}

export default App;
