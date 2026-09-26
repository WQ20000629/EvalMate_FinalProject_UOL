// ------------------------------------------------------------------
// File: frontend/src/main.tsx
// Purpose: Starts the React application and connects it to the HTML root.
// ------------------------------------------------------------------

// React functions used to start the application.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Global styles and the root component.
import "./index.css";
import App from "./App.tsx";

// Mount the React app inside the root element from index.html.
// ref: https://vite.dev/guide/
createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <App />
    </StrictMode>,
);
