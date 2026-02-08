import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { getDashboardStats, getSessionHistory, getChildProgress } from "../api/games";
import { listChildren } from "../api/patients";

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [children, setChildren] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedChild, setSelectedChild] = useState(null);
  const [childProgress, setChildProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      getDashboardStats().catch(() => null),
      listChildren().catch(() => []),
      getSessionHistory({ limit: 10 }).catch(() => []),
    ]).then(([s, c, h]) => {
      setStats(s);
      setChildren(Array.isArray(c) ? c : []);
      setSessions(Array.isArray(h) ? h : []);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!selectedChild) {
      setChildProgress(null);
      return;
    }
    getChildProgress(selectedChild)
      .then(setChildProgress)
      .catch(() => setChildProgress(null));
  }, [selectedChild]);

  if (loading) {
    return (
      <div className="container">
        <div className="h1">Loading Dashboard...</div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="h1">📊 Dashboard</div>
          <div className="sub">Welcome back, {user?.full_name || user?.email}</div>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <StatCard icon="👶" label="Children" value={stats.total_children} />
          <StatCard icon="👨‍⚕️" label="Therapists" value={stats.total_therapists} />
          <StatCard icon="📋" label="Total Sessions" value={stats.total_sessions} />
          <StatCard icon="✅" label="Completed" value={stats.completed_sessions} />
          <StatCard icon="▶️" label="Active" value={stats.active_sessions} />
          <StatCard icon="📅" label="This Week" value={stats.recent_sessions_7d} />
          <StatCard icon="🎯" label="Trials (7d)" value={stats.recent_trials_7d} />
          <StatCard
            icon="📈"
            label="Weekly Accuracy"
            value={`${(stats.weekly_accuracy * 100).toFixed(1)}%`}
          />
        </div>
      )}

      {/* Quick Actions */}
      <div className="panel" style={{ marginTop: 20 }}>
        <h3 style={{ margin: "0 0 12px 0", fontSize: 16 }}>🚀 Quick Actions</h3>
        <div className="row">
          <button className="btn btnPrimary" onClick={() => navigate("/games")}>
            🎮 Start Game Session
          </button>
          <button className="btn" onClick={() => navigate("/therapist")}>
            👨‍⚕️ Therapist Console
          </button>
        </div>
      </div>

      {/* Child Progress */}
      {children.length > 0 && (
        <div className="panel" style={{ marginTop: 20 }}>
          <h3 style={{ margin: "0 0 12px 0", fontSize: 16 }}>👶 Child Progress</h3>
          <div className="row" style={{ marginBottom: 12 }}>
            <select
              className="input"
              value={selectedChild || ""}
              onChange={(e) => setSelectedChild(e.target.value ? parseInt(e.target.value) : null)}
            >
              <option value="">Select a child...</option>
              {children.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name || c.email}
                </option>
              ))}
            </select>
          </div>

          {childProgress && (
            <div>
              <div className="stats-grid" style={{ marginBottom: 16 }}>
                <StatCard icon="📋" label="Sessions" value={childProgress.total_sessions} />
                <StatCard icon="✅" label="Completed" value={childProgress.completed_sessions} />
                <StatCard icon="🎯" label="Total Trials" value={childProgress.total_trials} />
                <StatCard
                  icon="📈"
                  label="Accuracy"
                  value={`${(childProgress.overall_accuracy * 100).toFixed(1)}%`}
                />
              </div>

              {childProgress.game_breakdown?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <h4 style={{ margin: "0 0 8px 0", fontSize: 14, color: "var(--muted)" }}>
                    Game Breakdown
                  </h4>
                  <div className="table-wrapper">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Game</th>
                          <th>Sessions</th>
                          <th>Trials</th>
                          <th>Correct</th>
                          <th>Accuracy</th>
                          <th>Avg RT</th>
                        </tr>
                      </thead>
                      <tbody>
                        {childProgress.game_breakdown.map((g, i) => (
                          <tr key={i}>
                            <td>{g.game.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</td>
                            <td>{g.sessions}</td>
                            <td>{g.total_trials}</td>
                            <td>{g.correct}</td>
                            <td>{(g.accuracy * 100).toFixed(1)}%</td>
                            <td>{g.avg_response_time_ms ? `${g.avg_response_time_ms}ms` : "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Recent Sessions */}
      {sessions.length > 0 && (
        <div className="panel" style={{ marginTop: 20 }}>
          <h3 style={{ margin: "0 0 12px 0", fontSize: 16 }}>📋 Recent Sessions</h3>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Child</th>
                  <th>Game</th>
                  <th>Status</th>
                  <th>Trials</th>
                  <th>Accuracy</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.id}>
                    <td>{s.session_date}</td>
                    <td>{s.child_name}</td>
                    <td>
                      {(s.game_types || [])
                        .map((g) => g.replace(/_/g, " "))
                        .join(", ") || s.title}
                    </td>
                    <td>
                      <span className={`status-badge status-${s.status}`}>
                        {s.status}
                      </span>
                    </td>
                    <td>
                      {s.correct}/{s.total_trials}
                    </td>
                    <td>{(s.accuracy * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
