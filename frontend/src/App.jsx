import React, { useState } from "react";

const suggestions = [
  "A 5-day trip to Tokyo in April, with a mid-range budget",
  "A weekend in Paris for two, including flights and hotels",
  "A family-friendly beach trip from New York this summer",
];

export default function App() {
  const [query, setQuery] = useState("");
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setPlan(null);
    setIsLoading(true);

    try {
      const response = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: query }),
      });

      let data;
      try {
        data = await response.json();
      } catch {
        throw new Error(
          `The API returned an invalid response (HTTP ${response.status}). Make sure the FastAPI backend is running at http://localhost:8000.`,
        );
      }

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "The travel plan could not be created. Please try again.",
        );
      }

      setPlan(data);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not connect to the travel planner.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="TripMate home">
          <span className="brand-mark" aria-hidden="true">
            T
          </span>
          <span>TripMate</span>
        </a>
        <span className="topbar-note">Your next trip starts here</span>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">TRAVEL, THOUGHTFULLY PLANNED</p>
          <h1>Where would you like to go?</h1>
          <p className="hero-description">
            Tell us what you have in mind. TripMate will bring together flight
            ideas, places to stay, and a practical itinerary.
          </p>
        </div>

        <form className="planner-card" onSubmit={handleSubmit}>
          <label htmlFor="trip-query">Describe your trip</label>
          <textarea
            id="trip-query"
            name="trip-query"
            rows="4"
            maxLength="2000"
            placeholder="For example: Plan a 5-day trip to Tokyo for two in April, with a moderate budget..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            required
          />
          <div className="form-footer">
            <span className="character-count">{query.length}/2000</span>
            <button type="submit" disabled={isLoading || !query.trim()}>
              {isLoading ? (
                <>
                  <span className="spinner" aria-hidden="true" />
                  Planning your trip...
                </>
              ) : (
                <>
                  Plan my trip
                  <span aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>
        </form>

        <div className="suggestions" aria-label="Example trip requests">
          <span>Need an idea?</span>
          {suggestions.map((suggestion) => (
            <button
              className="suggestion"
              key={suggestion}
              onClick={() => setQuery(suggestion)}
              type="button"
            >
              {suggestion}
            </button>
          ))}
        </div>

        {error && (
          <div className="notice error-notice" role="alert">
            <strong>We couldn&apos;t make that plan.</strong>
            <span>{error}</span>
          </div>
        )}

        {isLoading && (
          <p className="loading-note" role="status">
            Gathering ideas and putting your itinerary together. This can take
            a little while.
          </p>
        )}

        {plan && (
          <section className="plan-card" aria-live="polite">
            <div className="plan-heading">
              <div>
                <p className="eyebrow">MADE FOR YOUR TRIP</p>
                <h2>Your travel plan</h2>
              </div>
              <span className="plan-icon" aria-hidden="true">
                ✦
              </span>
            </div>
            <div className="plan-answer">{plan.answer}</div>
          </section>
        )}
      </section>

      <footer className="page-footer">
        Travel details are suggestions. Confirm prices and availability before
        booking.
      </footer>
    </main>
  );
}
