import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ErrorBoundary from "../ErrorBoundary";

function Crash() {
  const x = null;
  return <div>{x.doesNotExist}</div>;
}

function Fine() {
  return <div>Renders fine</div>;
}

describe("ErrorBoundary", () => {
  it("catches a render error and shows a message instead of going blank", () => {
    // React logs the error to console.error even when caught by a boundary
    // (that's expected and correct) -- silence it so the test output stays
    // readable, without hiding the assertion itself.
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <Crash />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Something went wrong/i)).toBeTruthy();
    expect(document.body.textContent.trim().length).toBeGreaterThan(0);

    spy.mockRestore();
  });

  it("renders children normally when nothing throws", () => {
    render(
      <ErrorBoundary>
        <Fine />
      </ErrorBoundary>
    );
    expect(screen.getByText("Renders fine")).toBeTruthy();
  });
});
