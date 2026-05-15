import React, { useEffect, useState } from "react";
import "./App.css";

const API_URL = "https://smartpick-ai.onrender.com";

function App() {
  const [fixtures, setFixtures] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [source, setSource] = useState("");
  const [history, setHistory] = useState([]);
  const [adminStats, setAdminStats] = useState(null);

  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");

  const [authForm, setAuthForm] = useState({
    username: "",
    email: "",
    password: "",
  });

  useEffect(() => {
    const savedUser = localStorage.getItem("smartpick_user");

    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }

    fetchFixtures();
    fetchHistory();
    fetchAdminStats();
  }, []);

  function handleAuthChange(event) {
    setAuthForm({
      ...authForm,
      [event.target.name]: event.target.value,
    });
  }

  async function handleAuthSubmit(event) {
    event.preventDefault();

    const endpoint =
      authMode === "login"
        ? "/auth/login"
        : "/auth/register";

    const payload =
      authMode === "login"
        ? {
            email: authForm.email,
            password: authForm.password,
          }
        : authForm;

    try {
      const response = await fetch(
        `${API_URL}${endpoint}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (data.error) {
        alert(data.error);
        return;
      }

      if (data.access_token) {
        localStorage.setItem(
          "smartpick_token",
          data.access_token
        );
      }

      localStorage.setItem(
        "smartpick_user",
        JSON.stringify(data.user)
      );

      setUser(data.user);

      setAuthForm({
        username: "",
        email: "",
        password: "",
      });

      fetchAdminStats();
    } catch (error) {
      console.error(error);
      alert("Authentication failed.");
    }
  }

  function logout() {
    localStorage.removeItem("smartpick_token");
    localStorage.removeItem("smartpick_user");

    setUser(null);
  }

  async function fetchAdminStats() {
    try {
      const response = await fetch(
        `${API_URL}/admin/stats`
      );

      const data = await response.json();

      setAdminStats(data);
    } catch (error) {
      console.error(error);
    }
  }

  async function fetchHistory() {
    try {
      const response = await fetch(
        `${API_URL}/predictions/history`
      );

      const data = await response.json();

      setHistory(data.predictions || []);
    } catch (error) {
      console.error(error);
    }
  }

  async function clearHistory() {
    try {
      await fetch(
        `${API_URL}/predictions/clear`,
        {
          method: "DELETE",
        }
      );

      setHistory([]);

      fetchAdminStats();
    } catch (error) {
      console.error(error);

      alert("Could not clear prediction history.");
    }
  }

  async function markPrediction(id, isCorrect) {
    try {
      await fetch(
        `${API_URL}/predictions/${id}/result`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            result: isCorrect ? "won" : "lost",
            is_correct: isCorrect,
          }),
        }
      );

      fetchHistory();
      fetchAdminStats();
    } catch (error) {
      console.error(error);

      alert("Could not update prediction result.");
    }
  }

  async function fetchFixtures() {
    setLoading(true);
    setPrediction(null);

    try {
      const response = await fetch(
        `${API_URL}/fixtures/upcoming`
      );

      const data = await response.json();

      setSource(data.source || "unknown");
      setFixtures(data.fixtures || []);
    } catch (error) {
      console.error(error);

      alert("Could not load fixtures.");
    }

    setLoading(false);
  }

  async function getSafePick(home, away) {
    setLoading(true);

    const matchName = `${home} vs ${away}`;

    setSelectedMatch(matchName);

    try {
      const response = await fetch(
        `${API_URL}/safe-pick?home_team=${encodeURIComponent(
          home
        )}&away_team=${encodeURIComponent(away)}`
      );

      const data = await response.json();

      setPrediction(data);

      if (!data.error) {
        fetchHistory();
        fetchAdminStats();
      }
    } catch (error) {
      console.error(error);

      alert("Could not get safe pick.");
    }

    setLoading(false);
  }

  return (
    <div className="app">
      <header className="hero">
        <h1 className="glow-title">
          SmartPick AI
        </h1>

        <div className="hero-info">
          <p>
            AI-powered safe football prediction
            insights.
          </p>

          <div className="live-badge">
            LIVE AI ANALYSIS
          </div>
        </div>

        <button onClick={fetchFixtures}>
          Refresh Fixtures
        </button>
      </header>

      {!user && (
        <section className="section auth-box">
          <h2>
            {authMode === "login"
              ? "Login"
              : "Create Account"}
          </h2>

          <form
            onSubmit={handleAuthSubmit}
            className="auth-form"
          >
            {authMode === "register" && (
              <input
                type="text"
                name="username"
                placeholder="Username"
                value={authForm.username}
                onChange={handleAuthChange}
                required
              />
            )}

            <input
              type="email"
              name="email"
              placeholder="Email"
              value={authForm.email}
              onChange={handleAuthChange}
              required
            />

            <input
              type="password"
              name="password"
              placeholder="Password"
              value={authForm.password}
              onChange={handleAuthChange}
              required
            />

            <button type="submit">
              {authMode === "login"
                ? "Login"
                : "Register"}
            </button>
          </form>

          <button
            className="secondary-btn"
            onClick={() =>
              setAuthMode(
                authMode === "login"
                  ? "register"
                  : "login"
              )
            }
          >
            Switch to{" "}
            {authMode === "login"
              ? "Register"
              : "Login"}
          </button>
        </section>
      )}

      {user && (
        <section className="section user-bar">
          <div>
            <h2>
              Welcome, {user.username}
            </h2>

            <p>{user.email}</p>
          </div>

          <button onClick={logout}>
            Logout
          </button>
        </section>
      )}

      {adminStats && (
        <section className="section admin-dashboard">
          <h2>Admin Dashboard</h2>

          <div className="admin-grid">
            <div className="admin-card">
              <span>Total Users</span>

              <h3>
                {adminStats.total_users}
              </h3>
            </div>

            <div className="admin-card">
              <span>
                Total Predictions
              </span>

              <h3>
                {adminStats.total_predictions}
              </h3>
            </div>

            <div className="admin-card">
              <span>Accuracy</span>

              <h3>
                {adminStats.accuracy}%
              </h3>
            </div>

            <div className="admin-card">
              <span>Correct</span>

              <h3>
                {
                  adminStats.correct_predictions
                }
              </h3>
            </div>

            <div className="admin-card">
              <span>Incorrect</span>

              <h3>
                {
                  adminStats.incorrect_predictions
                }
              </h3>
            </div>
          </div>
        </section>
      )}

      <section className="section">
        <h2>Safe Pick Mode: ON</h2>

        <p>
          The app only recommends picks that pass
          strict confidence filters.
        </p>

        {source && (
          <p>
            Data source:{" "}
            <strong>{source}</strong>
          </p>
        )}
      </section>

      <section className="section">
        <h2>Upcoming Fixtures</h2>

        {loading && <p>Loading...</p>}

        <div className="fixtures">
          {fixtures
            .slice(0, 20)
            .map((match) => (
              <div
                className="fixture-card"
                key={match.fixture_id}
              >
                <p className="league">
                  {match.league}
                </p>

                <div className="teams">
                  <div className="team">
                    <img
                      src={match.home_logo}
                      alt={match.home}
                      className="team-logo"
                    />

                    <span>
                      {match.home}
                    </span>
                  </div>

                  <div className="vs">
                    VS
                  </div>

                  <div className="team">
                    <img
                      src={match.away_logo}
                      alt={match.away}
                      className="team-logo"
                    />

                    <span>
                      {match.away}
                    </span>
                  </div>
                </div>

                <p>
                  {new Date(
                    match.date
                  ).toLocaleString()}
                </p>

                <button
                  onClick={() =>
                    getSafePick(
                      match.home,
                      match.away
                    )
                  }
                >
                  Get Safe Pick
                </button>
              </div>
            ))}
        </div>
      </section>

      {prediction &&
        prediction.error && (
          <section className="section prediction-box">
            <h2>
              No Safe Pick Available
            </h2>

            <p>{prediction.error}</p>

            <p>{prediction.message}</p>
          </section>
        )}

      {prediction &&
        !prediction.error && (
          <section className="section prediction-box">
            <h2>
              Prediction Result
            </h2>

            <p className="match-name">
              {selectedMatch}
            </p>

            <div className="best-pick">
              <p>
                {prediction.is_safe_pick
                  ? "SAFE PICK"
                  : "RISKY PICK"}
              </p>

              <h3>
                {prediction.best_pick.pick}
              </h3>

              <h1>
                {
                  prediction.best_pick
                    .confidence
                }
                %
              </h1>

              <span>
                {
                  prediction.best_pick
                    .market
                }
              </span>

              <div className="confidence-bar">
                <div
                  className="confidence-fill"
                  style={{
                    width: `${prediction.best_pick.confidence}%`,
                  }}
                ></div>
              </div>

              <p>
                Risk: {prediction.risk}
              </p>
            </div>

            <h3>AI Score Engine</h3>

            <div className="ai-scores">
              <div className="score-card">
                <h4>Attack</h4>

                <p>
                  {
                    prediction.ai_scores
                      .attack_rating
                  }
                  %
                </p>
              </div>

              <div className="score-card">
                <h4>Defense</h4>

                <p>
                  {
                    prediction.ai_scores
                      .defense_rating
                  }
                  %
                </p>
              </div>

              <div className="score-card">
                <h4>Momentum</h4>

                <p>
                  {
                    prediction.ai_scores
                      .momentum_rating
                  }
                  %
                </p>
              </div>

              <div className="score-card">
                <h4>Safety</h4>

                <p>
                  {
                    prediction.ai_scores
                      .safety_score
                  }
                  %
                </p>
              </div>
            </div>

            <h3>AI Match Summary</h3>

            {prediction.ai_summary.map(
              (item, index) => (
                <div
                  className="ranking"
                  key={index}
                >
                  <span>{item}</span>
                </div>
              )
            )}

            <h3>Market Ranking</h3>

            {prediction.all_predictions.map(
              (item, index) => (
                <div
                  className="ranking"
                  key={index}
                >
                  <span>
                    {item.pick} (
                    {item.risk} risk)
                  </span>

                  <strong>
                    {item.confidence}%
                  </strong>
                </div>
              )
            )}

            <p className="disclaimer">
              {prediction.disclaimer}
            </p>
          </section>
        )}

      {history.length > 0 && (
        <section className="section">
          <div className="history-header">
            <h2>
              Prediction Database
              History
            </h2>

            <button
              className="clear-history-btn"
              onClick={clearHistory}
            >
              Clear History
            </button>
          </div>

          {history.map((item) => (
            <div
              className="history-card"
              key={item.id}
            >
              <div>
                <strong>
                  {item.match_name}
                </strong>

                <p>{item.pick}</p>

                <small>
                  {item.market} •{" "}
                  {item.risk} risk •{" "}
                  {item.result}
                </small>

                <div className="result-buttons">
                  <button
                    onClick={() =>
                      markPrediction(
                        item.id,
                        true
                      )
                    }
                  >
                    Mark Won
                  </button>

                  <button
                    className="danger-btn"
                    onClick={() =>
                      markPrediction(
                        item.id,
                        false
                      )
                    }
                  >
                    Mark Lost
                  </button>
                </div>
              </div>

              <h3>
                {item.confidence}%
              </h3>
            </div>
          ))}
        </section>
      )}

      <section className="section legal-section">
        <h2>
          Responsible Use & Legal
          Disclaimer
        </h2>

        <p>
          SmartPick AI provides football
          prediction insights for
          informational and entertainment
          purposes only.
        </p>

        <p>
          Predictions are based on
          statistics, trends, and
          probability models. They are not
          guaranteed outcomes.
        </p>

        <p>
          SmartPick AI is not a betting
          company, bookmaker, financial
          adviser, or gambling service.
        </p>

        <p>
          Users are responsible for their
          own decisions. Never bet money
          you cannot afford to lose.
        </p>

        <p>
          If gambling causes stress,
          financial problems, or loss of
          control, seek help from a
          responsible gambling support
          service.
        </p>
      </section>

      <footer>
        SmartPick AI provides
        statistical predictions only.
        Predictions are not guaranteed.
      </footer>
    </div>
  );
}

export default App;