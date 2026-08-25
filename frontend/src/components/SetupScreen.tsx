import { useState } from "react";

const ALL_TYPES = ["Behavioural", "Situational", "Motivational", "Technical"];

interface SetupScreenProps {
  onGenerate: (jobDescription: string, numQuestions: number, questionTypes: string[]) => void;
  error: string | null;
}

export function SetupScreen({ onGenerate, error }: SetupScreenProps) {
  const [jobDescription, setJobDescription] = useState("");
  const [numQuestions, setNumQuestions] = useState(3);
  const [selectedTypes, setSelectedTypes] = useState<string[]>(ALL_TYPES);
  const [localError, setLocalError] = useState<string | null>(null);

  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

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
      <h1>AI Interview Evaluator</h1>
      <p className="subtitle">Paste a job description to generate interview questions.</p>

      <textarea
        placeholder="Paste job description here..."
        rows={10}
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
      />

      <div className="settings-box">
        <div className="settings-row">
          <label htmlFor="num-questions">Number of Questions</label>
          <select
            id="num-questions"
            value={numQuestions}
            onChange={(e) => setNumQuestions(parseInt(e.target.value, 10))}
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
