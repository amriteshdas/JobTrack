import { Component } from "react";

/**
 * Without this, React's default behavior (since React 18's createRoot) is
 * to unmount the ENTIRE app on any uncaught render error -- leaving a
 * blank white page with no indication anything went wrong. That is almost
 * certainly what's been happening: some component throws during render,
 * there's nothing above it to catch that, so the whole tree disappears.
 *
 * This boundary is deliberately placed once, near the root (see App.jsx),
 * not around every page -- for an app this size, "something broke, here's
 * what and a way back" is more useful than granular per-page boundaries,
 * and it keeps the failure visible instead of silently blank.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Surfaced in the console with the component stack -- this is the
    // actual diagnostic information a blank screen was hiding.
    console.error("Render error caught by ErrorBoundary:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen bg-canvas flex items-center justify-center p-6">
          <div className="max-w-md w-full card p-7 animate-pop">
            <div className="h-10 w-10 rounded-xl bg-red-50 border border-red-200 grid place-items-center text-red-600 mb-3">
              !
            </div>
            <h1 className="font-display text-lg font-bold text-ink-950">Something went wrong</h1>
            <p className="mt-2 text-sm text-ink-500">
              This page hit an error and couldn't render. The details below are also in your
              browser's console (F12 → Console tab).
            </p>
            <pre className="mt-4 text-xs text-red-700 bg-red-50 border border-red-100 rounded-lg p-3 overflow-auto max-h-48 whitespace-pre-wrap">
              {String(this.state.error?.message || this.state.error)}
            </pre>
            <button
              onClick={() => {
                this.setState({ error: null });
                window.location.href = "/";
              }}
              className="btn btn-primary mt-5 w-full"
            >
              Back to home
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
