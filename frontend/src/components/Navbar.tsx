export function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <span className="brand-name">AI Interview Evaluator</span>
        </div>

        <div className="navbar-actions">
          <span className="login-hint">Login to save your progress</span>
          <button type="button" className="btn-login" title="Coming soon">
            Login
          </button>
        </div>
      </div>
    </header>
  );
}
