// ------------------------------------------------------------------
// File: frontend/src/components/Navbar.tsx
// Purpose: Displays navigation, account actions, and history access.
// ------------------------------------------------------------------

// React state controls whether the login modal is visible.
import { useState } from "react";
// Authentication state and the login form modal.
import { useAuth } from "../context/AuthContext";
import { LoginModal } from "./LoginModal";

// Props for Navbar: callback that opens the history screen.
interface NavbarProps {
    onViewHistory: () => void;
}

// Top navigation bar with account actions and history access.
export function Navbar({ onViewHistory }: NavbarProps) {
    const { user, logout } = useAuth();
    const [showModal, setShowModal] = useState(false);

    return (
        <header className="navbar">
            <div className="navbar-inner">
                <div className="brand">
                    <svg
                        className="brand-mark"
                        viewBox="0 0 200 200"
                        aria-hidden="true"
                    >
                        <circle
                            cx="100"
                            cy="100"
                            r="80"
                            fill="none"
                            stroke="var(--accent-soft)"
                            strokeWidth="18"
                        />
                        <circle
                            cx="100"
                            cy="100"
                            r="80"
                            fill="none"
                            stroke="var(--accent)"
                            strokeWidth="18"
                            strokeLinecap="round"
                            strokeDasharray="420 502"
                            transform="rotate(-90 100 100)"
                        />
                        <path
                            d="M62,104 L88,130 L140,72"
                            fill="none"
                            stroke="var(--heading)"
                            strokeWidth="16"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>
                    <span className="brand-name">EvalMate</span>
                </div>

                <div className="navbar-actions">
                    {user ? (
                        <>
                            <button
                                type="button"
                                className="btn-ghost"
                                onClick={onViewHistory}
                            >
                                History
                            </button>
                            <span className="user-email">{user.email}</span>
                            <button
                                type="button"
                                className="btn-login"
                                onClick={() => logout()}
                            >
                                Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <span className="login-hint">
                                Login to save your progress
                            </span>
                            <button
                                type="button"
                                className="btn-login"
                                onClick={() => setShowModal(true)}
                            >
                                Login
                            </button>
                        </>
                    )}
                </div>
            </div>

            {showModal && <LoginModal onClose={() => setShowModal(false)} />}
        </header>
    );
}
