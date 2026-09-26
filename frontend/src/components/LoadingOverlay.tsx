// ------------------------------------------------------------------
// File: frontend/src/components/LoadingOverlay.tsx
// Purpose: Shows a loading message while the app waits for a request.
// ------------------------------------------------------------------

// Props for LoadingOverlay: whether it is shown and the message to display.
interface LoadingOverlayProps {
    visible: boolean;
    message: string;
}

// Show a loading message while the app waits for a backend call.
export function LoadingOverlay({ visible, message }: LoadingOverlayProps) {
    if (!visible) return null;

    return (
        <div className="loading">
            <div className="spinner" />
            <p>{message}</p>
        </div>
    );
}
