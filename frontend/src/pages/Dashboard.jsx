import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { getDashboardStats, getSessionHistory, getChildProgress } from "../api/games";
import { listChildren } from "../api/patients";
import { SkeletonStatCards, SkeletonTable } from "../components/Skeleton";
import ProgressRing from "../components/ProgressRing";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

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
        <div className="header">
          <div>
            <div className="h1">Dashboard</div>
            <div className="sub">Loading your data...</div>
          </div>
        </div>
        <SkeletonStatCards count={4} />
        <SkeletonTable rows={4} cols={5} />
      </div>
    );
  }

  // Prepare chart data from game breakdown
  const chartData = childProgress?.game_breakdown?.map((g) => ({
    name: g.game.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    accuracy: Math.round(g.accuracy * 100),
    sessions: g.sessions,
    trials: g.total_trials,
  })) || [];

  // Session trend (last 10 sessions as area chart)
  const trendData = [...sessions].reverse().map((s, i) => ({
    idx: i + 1,
    accuracy: Math.round(s.accuracy * 100),
    trials: s.total_trials,
  }));

  const weeklyAcc = stats ? Math.round(stats.weekly_accuracy * 100) : 0;

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="h1">Dashboard</div>
          <div className="sub">Welcome back, {user?.full_name || user?.email}</div>
        </div>
        <div className="row">
          <button className="btn btnPrimary" onClick={() => navigate("/games")}>
            🎮 Start Game
          </button>
          <button className="btn" onClick={() => navigate("/therapist")}>
            📊 Console
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <StatCard icon="👶" label="Children" value={stats.total_children} accent="primary" />
          <StatCard icon="📋" label="Total Sessions" value={stats.total_sessions} accent="success" />
          <StatCard icon="✅" label="Completed" value={stats.completed_sessions} accent="warning" />
          <StatCard icon="🎯" label="Trials (7d)" value={stats.recent_trials_7d} accent="danger" />
        </div>
      )}

      {/* Accuracy + Recent Overview */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
          {/* Weekly Accuracy Ring */}
          <div className="panel" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24 }}>
            <ProgressRing
              value={weeklyAcc}
              size={120}
              strokeWidth={10}
              color={weeklyAcc >= 80 ? "#10b981" : weeklyAcc >= 50 ? "#f59e0b" : "#ef4444"}
            />
            <div style={{ marginTop: 12, fontWeight: 700, fontSize: 15 }}>Weekly Accuracy</div>
            <div style={{ color: "var(--muted)", fontSize: 13 }}>{stats.recent_sessions_7d} sessions this week</div>
          </div>

          {/* Session Trend */}
          {trendData.length > 1 ? (
            <div className="chart-container">
              <div className="chart-title">📈 Session Accuracy Trend</div>
              <ResponsiveContainer width="100%" height={160}>
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="accGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="idx" hide />
                  <YAxis domain={[0, 100]} hide />
                  <Tooltip
                    contentStyle={{ background: "#161922", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 13 }}
                    labelStyle={{ display: "none" }}
                    formatter={(v) => [`${v}%`, "Accuracy"]}
                  />
                  <Area type="monotone" dataKey="accuracy" stroke="#6366f1" fill="url(#accGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="panel" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
              <div className="empty-state" style={{ padding: 16 }}>
                <div className="empty-state-icon" style={{ fontSize: 36 }}>📈</div>
                <div className="empty-state-desc">Play more sessions to see trends</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Child Progress */}
      {children.length > 0 && (
        <div className="panel" style={{ marginTop: 20 }}>
          <h3 style={{ margin: "0 0 12px 0", fontSize: 16 }}>Child Progress</h3>
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
                <StatCard label="Sessions" value={childProgress.total_sessions} />
                <StatCard label="Completed" value={childProgress.completed_sessions} />
                <StatCard label="Total Trials" value={childProgress.total_trials} />
                <div className="stat-card" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                  <ProgressRing
                    value={Math.round(childProgress.overall_accuracy * 100)}
                    size={64}
                    strokeWidth={6}
                    color={childProgress.overall_accuracy >= 0.8 ? "#10b981" : childProgress.overall_accuracy >= 0.5 ? "#f59e0b" : "#ef4444"}
                  />
                  <div className="stat-label" style={{ marginTop: 6 }}>Accuracy</div>
                </div>
              </div>

              {/* Game Breakdown Chart */}
              {chartData.length > 0 && (
                <div className="chart-container">
                  <div className="chart-title">🎮 Game Breakdown</div>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={chartData} barSize={32}>
                      <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ background: "#161922", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 13 }}
                        formatter={(v, name) => [name === "accuracy" ? `${v}%` : v, name === "accuracy" ? "Accuracy" : "Sessions"]}
                      />
                      <Bar dataKey="accuracy" fill="#6366f1" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {childProgress.game_breakdown?.length > 0 && (
                <div style={{ marginTop: 12 }}>
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
                            <td style={{ fontWeight: 600 }}>{g.game.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</td>
                            <td>{g.sessions}</td>
                            <td>{g.total_trials}</td>
                            <td>{g.correct}</td>
                            <td>
                              <span className={`accuracy-badge ${g.accuracy >= 0.8 ? "acc-high" : g.accuracy >= 0.5 ? "acc-mid" : "acc-low"}`}>
                                {(g.accuracy * 100).toFixed(0)}%
                              </span>
                            </td>
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
      {sessions.length > 0 ? (
        <div className="panel" style={{ marginTop: 20 }}>
          <h3 style={{ margin: "0 0 12px 0", fontSize: 16 }}>Recent Sessions</h3>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Child</th>
                  <th>Game</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>Accuracy</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.id}>
                    <td>{s.session_date}</td>
                    <td style={{ fontWeight: 600 }}>{s.child_name}</td>
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
                    <td>{s.correct}/{s.total_trials}</td>
                    <td>
                      <span className={`accuracy-badge ${s.accuracy >= 0.8 ? "acc-high" : s.accuracy >= 0.5 ? "acc-mid" : "acc-low"}`}>
                        {(s.accuracy * 100).toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="panel" style={{ marginTop: 20 }}>
          <div className="empty-state">
            <div className="empty-state-icon" style={{ fontSize: 36 }}>🎮</div>
            <div className="empty-state-title">No Sessions Yet</div>
            <div className="empty-state-desc">Start a game session to see your progress here.</div>
            <button className="btn btnPrimary" onClick={() => navigate("/games")}>🎮 Play Now</button>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, accent }) {
  return (
    <div className={`stat-card ${accent ? `stat-card-${accent}` : ""}`}>
      {icon && <div style={{ fontSize: 22, marginBottom: 4 }}>{icon}</div>}
      <div className="stat-value">{value ?? 0}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
