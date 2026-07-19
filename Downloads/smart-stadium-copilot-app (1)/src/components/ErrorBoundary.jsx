import React from "react";
import { P } from "../theme.js";

/**
 * Catches render-time errors in its subtree and shows a recoverable
 * fallback instead of a blank white screen. Class component because
 * error boundaries currently require the class lifecycle API in React.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error("Stadium Copilot error boundary caught:", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div role="alert" className="f-body rounded-xl border p-4 m-4 text-sm"
          style={{ borderColor: P.red, background: "rgba(239,68,68,0.08)", color: P.ice }}>
          <p className="font-semibold mb-1">Something went wrong in this panel.</p>
          <p className="text-xs" style={{ color: P.muted }}>
            The rest of the app should still work. Try refreshing the page.
          </p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="mt-3 f-body text-xs font-semibold rounded-lg px-3 py-1.5"
            style={{ background: P.red, color: "#2A0A0A" }}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
