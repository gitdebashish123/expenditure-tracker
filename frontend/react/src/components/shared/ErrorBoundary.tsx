import { Component, type ReactNode } from "react";

interface Props {
  children:  ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error:    Error | null;
}

/**
 * ErrorBoundary — catches render errors in any child tab component
 *
 * Wraps each tab in DashboardPage so a crash in one tab doesn't
 * take down the whole app. "Try again" resets the error state.
 *
 * Usage:
 *   <ErrorBoundary><QuickAddTab /></ErrorBoundary>
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="p-8 text-center">
          <div className="text-4xl mb-3">⚠️</div>
          <p className="text-sm mb-4" style={{ color: "var(--text-sub)" }}>
            Something went wrong loading this section.
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="text-indigo-400 hover:text-indigo-300 text-sm underline
                       transition-colors"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
