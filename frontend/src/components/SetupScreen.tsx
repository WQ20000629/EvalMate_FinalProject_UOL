// ------------------------------------------------------------------
// File: frontend/src/components/SetupScreen.tsx
// Purpose: Collects the job description and interview setup choices.
// ------------------------------------------------------------------

// React state stores the setup form values.
import { useState } from "react";

// Question types the user can choose from, all selected by default.
const ALL_TYPES = ["Behavioural", "Situational", "Motivational", "Technical"];

// Props for SetupScreen: callback that generates questions, and any backend error.
interface SetupScreenProps {
    onGenerate: (
        jobDescription: string,
        numQuestions: number,
        questionTypes: string[],
    ) => void;
    error: string | null;
}

// Let the user enter a job description and choose the interview setup.
export function SetupScreen({ onGenerate, error }: SetupScreenProps) {
    const [jobDescription, setJobDescription] = useState("");
    const [numQuestions, setNumQuestions] = useState(3);
    const [selectedTypes, setSelectedTypes] = useState<string[]>(ALL_TYPES);
    const [localError, setLocalError] = useState<string | null>(null);

    // Add or remove one question type from the selection.
    const toggleType = (type: string) => {
        setSelectedTypes((prev) =>
            prev.includes(type)
                ? prev.filter((t) => t !== type)
                : [...prev, type],
        );
    };

    // Validate the form before asking the backend to generate questions.
    const handleGenerateClick = () => {
        setLocalError(null);
        if (!jobDescription.trim()) {
            setLocalError("Please paste a job description.");
            return;
        }
        if (selectedTypes.length === 0) {
            setLocalError("Select at least one question type.");
            return;
        }
        onGenerate(jobDescription.trim(), numQuestions, selectedTypes);
    };

    const displayError = localError ?? error;

    return (
        <div className="screen">
            <h1>EvalMate</h1>
            <p className="subtitle">
                Paste a job description to generate interview questions.
            </p>

            <textarea
                placeholder="Paste job description here..."
                rows={10}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
            />

            <details className="how-to-use">
                <summary>How to use EvalMate</summary>
                <ol>
                    <li>Paste a job description above, then choose how many questions you want and which types to include.</li>
                    <li>Click <strong>Generate Questions</strong> to get a tailored set of interview questions.</li>
                    <li>For each question, click <strong>Start Recording</strong>, speak your answer, then <strong>Stop Recording</strong>. Your speech is transcribed automatically. You may edit the text or re-record before submitting.</li>
                    <li>A live badge shows whether you're maintaining eye contact with the camera while you answer.</li>
                    <li>After your last answer, view your <strong>Final Report</strong>: scores for Relevance, Content Depth, Clarity &amp; Structure, Confidence Delivery, and Eye Contact, each with written feedback.</li>
                    <li>Log in (top right) to automatically save your sessions and revisit them later from <strong>History</strong>.</li>
                </ol>
            </details>

            <div className="settings-box">
                <div className="settings-row">
                    <label htmlFor="num-questions">Number of Questions</label>
                    <select
                        id="num-questions"
                        value={numQuestions}
                        onChange={(e) =>
                            setNumQuestions(parseInt(e.target.value, 10))
                        }
                    >
                        {[1, 2, 3, 4, 5].map((n) => (
                            <option key={n} value={n}>
                                {n}
                            </option>
                        ))}
                    </select>
                </div>
                <div className="settings-row">
                    <label>Question Types</label>
                    <div className="type-checkboxes">
                        {ALL_TYPES.map((type) => (
                            <label key={type}>
                                <input
                                    type="checkbox"
                                    checked={selectedTypes.includes(type)}
                                    onChange={() => toggleType(type)}
                                />
                                {type}
                            </label>
                        ))}
                    </div>
                </div>
            </div>

            <button onClick={handleGenerateClick}>Generate Questions</button>

            {displayError && <p className="error">{displayError}</p>}
        </div>
    );
}
