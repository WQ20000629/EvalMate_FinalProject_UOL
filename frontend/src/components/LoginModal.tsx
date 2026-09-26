// ------------------------------------------------------------------
// File: frontend/src/components/LoginModal.tsx
// Purpose: Provides the login and account registration form.
// ------------------------------------------------------------------

// React state stores the form values and submission status.
import { useState } from "react";
// Authentication actions used by the form.
import { useAuth } from "../context/AuthContext";

// Props for LoginModal: callback that closes the modal.
interface LoginModalProps {
    onClose: () => void;
}

// Modal that handles both login and account creation.
export function LoginModal({ onClose }: LoginModalProps) {
    const { login, register } = useAuth();
    const [mode, setMode] = useState<"login" | "register">("login");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    // Validate the form and call the selected authentication action.
    const handleSubmit = async () => {
        setError(null);
        if (!email.trim() || !password) {
            setError("Enter an email and password.");
            return;
        }
        setSubmitting(true);
        try {
            if (mode === "login") {
                await login(email.trim(), password);
            } else {
                await register(email.trim(), password);
            }
            onClose();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Something went wrong.");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-card" onClick={(e) => e.stopPropagation()}>
                <div className="modal-tabs">
                    <button
                        type="button"
                        className={`modal-tab ${mode === "login" ? "active" : ""}`}
                        onClick={() => {
                            setMode("login");
                            setError(null);
                        }}
                    >
                        Log in
                    </button>
                    <button
                        type="button"
                        className={`modal-tab ${mode === "register" ? "active" : ""}`}
                        onClick={() => {
                            setMode("register");
                            setError(null);
                        }}
                    >
                        Sign up
                    </button>
                </div>

                <label className="modal-label" htmlFor="auth-email">
                    Email
                </label>
                <input
                    id="auth-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                />

                <label className="modal-label" htmlFor="auth-password">
                    Password
                </label>
                <input
                    id="auth-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={
                        mode === "register"
                            ? "At least 8 characters"
                            : "••••••••"
                    }
                    onKeyDown={(e) => {
                        if (e.key === "Enter") handleSubmit();
                    }}
                />

                {error && <p className="error">{error}</p>}

                <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={submitting}
                >
                    {submitting
                        ? "Please wait..."
                        : mode === "login"
                          ? "Log in"
                          : "Create account"}
                </button>
            </div>
        </div>
    );
}
