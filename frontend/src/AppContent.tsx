// ------------------------------------------------------------------
// File: frontend/src/AppContent.tsx
// Purpose: Controls the main screens and the current interview workflow.
// ------------------------------------------------------------------

// React state stores the current screen and interview data.
import { useState } from "react";
// Shared layout and screen components.
import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { SetupScreen } from "./components/SetupScreen";
import { InterviewScreen } from "./components/InterviewScreen";
import { ReportScreen } from "./components/ReportScreen";
import { HistoryScreen } from "./components/HistoryScreen";
import { LoadingOverlay } from "./components/LoadingOverlay";
import {
    generateQuestions,
    evaluateAnswer,
    getSentiment,
    getFinalReport,
    getSession,
} from "./api";
import { fallbackAggregate } from "./reportFallback";
import type { Question, SessionResult, ReportSummary } from "./types";

// The screens the app can show.
type Screen ="setup" | "interview" | "report" | "history";

// Keep the main navigation and interview state in one component.
function AppContent() {
    const [screen, setScreen] = useState<Screen>("setup");
    const [jobDescription, setJobDescription] = useState("");
    const [questionBank, setQuestionBank] = useState<Question[]>([]);
    const [questionIndex, setQuestionIndex] = useState(0);
    const [sessionResults, setSessionResults] = useState<SessionResult[]>([]);
    const [reportSummary, setReportSummary] = useState<ReportSummary | null>(
        null,
    );
    const [viewingHistorical, setViewingHistorical] = useState(false);

    const [loading, setLoading] = useState<{
        active: boolean;
        message: string;
    }>({ active: false, message: "" });
    const [setupError, setSetupError] = useState<string | null>(null);
    const [interviewError, setInterviewError] = useState<string | null>(null);
    const [historyError, setHistoryError] = useState<string | null>(null);

    // Ask the backend for questions based on the selected setup.
    const handleGenerate = async (
        jd: string,
        numQuestions: number,
        questionTypes: string[],
    ) => {
        setSetupError(null);
        setLoading({ active: true, message: "Generating questions..." });
        try {
            const questions = await generateQuestions(
                jd,
                numQuestions,
                questionTypes,
            );
            setJobDescription(jd);
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

    // Request the final report after all answers have been submitted.
    const buildReport = async (results: SessionResult[]) => {
        setLoading({ active: true, message: "Generating final report..." });
        try {
            const summary = await getFinalReport(results, jobDescription);
            setReportSummary(summary);
            setViewingHistorical(false);
            setScreen("report");
        } catch {
            // Work out the report in the browser if the backend call fails.
            setReportSummary(fallbackAggregate(results));
            setViewingHistorical(false);
            setScreen("report");
        } finally {
            setLoading({ active: false, message: "" });
        }
    };

    // Send one transcript for evaluation and move to the next question.
    const handleSubmitAnswer = async (
        transcript: string,
        eyeContactScore: number | null,
    ) => {
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

            // Go to the next question, or build the report after the last one.
            const nextIndex = questionIndex + 1;
            if (nextIndex < questionBank.length) {
                setQuestionIndex(nextIndex);
                setLoading({ active: false, message: "" });
            } else {
                await buildReport(updatedResults);
            }
        } catch (e) {
            setInterviewError(
                e instanceof Error
                    ? `Evaluation failed: ${e.message}`
                    : "Unknown error",
            );
            setLoading({ active: false, message: "" });
        }
    };

    // Clear the current interview and return to the setup screen.
    const handleRestart = () => {
        setQuestionBank([]);
        setQuestionIndex(0);
        setSessionResults([]);
        setReportSummary(null);
        setSetupError(null);
        setInterviewError(null);
        setScreen("setup");
    };

    // Open the history screen and clear any old history error.
    const handleViewHistory = () => {
        setHistoryError(null);
        setScreen("history");
    };

    // Load a saved session and display its report.
    const handleSelectSession = async (id: number) => {
        setLoading({ active: true, message: "Loading session..." });
        try {
            const summary = await getSession(id);
            setReportSummary(summary);
            setViewingHistorical(true);
            setScreen("report");
        } catch (e) {
            setHistoryError(
                e instanceof Error ? e.message : "Failed to load session.",
            );
        } finally {
            setLoading({ active: false, message: "" });
        }
    };

    return (
        <div className="app-shell">
            <Navbar onViewHistory={handleViewHistory} />

            <main className="app-main">
                {screen === "setup" && (
                    <SetupScreen
                        onGenerate={handleGenerate}
                        error={setupError}
                    />
                )}

                {screen === "interview" && questionBank[questionIndex] && (
                    <InterviewScreen
                        question={questionBank[questionIndex]}
                        questionNumber={questionIndex + 1}
                        totalQuestions={questionBank.length}
                        onSubmitAnswer={handleSubmitAnswer}
                        error={interviewError}
                    />
                )}

                {screen === "report" && reportSummary && (
                    <ReportScreen
                        summary={reportSummary}
                        onRestart={
                            viewingHistorical
                                ? () => setScreen("history")
                                : handleRestart
                        }
                        restartLabel={
                            viewingHistorical ? "Back to History" : "Start Over"
                        }
                    />
                )}

                {screen === "history" && (
                    <>
                        {historyError && (
                            <p className="error">{historyError}</p>
                        )}
                        <HistoryScreen
                            onSelectSession={handleSelectSession}
                            onNewInterview={handleRestart}
                        />
                    </>
                )}
            </main>

            <Footer />

            <LoadingOverlay
                visible={loading.active}
                message={loading.message}
            />
        </div>
    );
}

export default AppContent;
