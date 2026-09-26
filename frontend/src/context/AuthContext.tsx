// ------------------------------------------------------------------
// File: frontend/src/context/AuthContext.tsx
// Purpose: Stores and shares the current user's authentication state.
// ------------------------------------------------------------------

// React tools used to create and share authentication state.
import {
    createContext,
    useContext,
    useEffect,
    useState,
    type ReactNode,
} from "react";
// User type and API functions used by the authentication actions.
import type { User } from "../types";
import { getMe, loginUser, registerUser, logoutUser } from "../api";

// Values made available to components through the auth context.
interface AuthContextValue {
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
}

// Context object, null until AuthProvider supplies a value.
const AuthContext = createContext<AuthContextValue | null>(null);

// Load the current user and provide login, registration, and logout actions.
export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    // Check the existing authentication cookie when the app first loads.
    useEffect(() => {
        getMe()
            .then(setUser)
            .catch(() => setUser(null))
            .finally(() => setLoading(false));
    }, []);

    // Log in and store the returned user.
    async function login(email: string, password: string) {
        const loggedInUser = await loginUser(email, password);
        setUser(loggedInUser);
    }

    // Register the user and store the new account.
    async function register(email: string, password: string) {
        const newUser = await registerUser(email, password);
        setUser(newUser);
    }

    // Log out on the backend and clear the local user.
    async function logout() {
        await logoutUser();
        setUser(null);
    }

    return (
        <AuthContext.Provider
            value={{ user, loading, login, register, logout }}
        >
            {children}
        </AuthContext.Provider>
    );
}

// Read the authentication state from a component.
export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
    return ctx;
}
