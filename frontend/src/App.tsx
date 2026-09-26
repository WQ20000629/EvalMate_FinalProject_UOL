// ------------------------------------------------------------------
// File: frontend/src/App.tsx
// Purpose: Provides the main application wrapper and authentication context.
// ------------------------------------------------------------------

// Provider that shares login state with the whole application.
import { AuthProvider } from "./context/AuthContext";
// Component that displays the current app screen.
import AppContent from "./AppContent";

// Wrap the application so every screen can use the logged-in user.
function App() {
    return (
        <AuthProvider>
            <AppContent />
        </AuthProvider>
    );
}

export default App;
