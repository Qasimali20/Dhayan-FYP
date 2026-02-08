import { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { listChildren, createChild } from "../api/patients";
import { getSessionHistory, getChildProgress } from "../api/games";

export default function TherapistConsole() {
  const { user } = useAuth();

  const [children, setChildren] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selectedChild, setSelectedChild] = useState(null);
  const [childProgress, setChildProgress] = useState(null);
  const [showAddChild, setShowAddChild] = useState(false);
  const [loading, setLoading] = useState(true);

  // Add child form
  const [newChild, setNewChild] = useState({
    email: "", full_name: "", date_of_birth: "", gender: "unknown",
    diagnosis_notes: "",
  });
  const [addError, setAddError] = useState("");
  const [addLoading, setAddLoading] = useState(false);

  // Session filters
  const [statusFilter, setStatusFilter] = useState("");
  const [gameFilter, setGameFilter] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [c, s] = await Promise.all([
        listChildren().catch(() => []),
        getSessionHistory({ limit: 50 }).catch(() => []),
      ]);
      setChildren(Array.isArray(c) ? c : []);
      setSessions(Array.isArray(s) ? s : []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!selectedChild) {
      setChildProgress(null);
      return;
    }
    getChildProgress(selectedChild)
      .then(setChildProgress)
      .catch(() => setChildProgress(null));
  }, [selectedChild]);

  async function handleAddChild(e) {
    e.preventDefault();
    setAddError("");
    setAddLoading(true);
    try {
      await createChild(newChild);
      setShowAddChild(false);
      setNewChild({ email: "", full_name: "", date_of_birth: "", gender: "unknown", diagnosis_notes: "" });
      loadData();
    } catch (err) {
      setAddError(err.message || "Failed to add child");
    } finally {
      setAddLoading(false);
    }
  }

  // Filter sessions
  const filteredSessions = sessions.filter((s) => {
    if (statusFilter && s.status !== statusFilter) return false;
    if (gameFilter && !(s.game_types || []).includes(gameFilter)) return false;
    if (selectedChild && s.child_id !== selectedChild) return false;
    return true;
  });

  if (loading) {
    return <div className="container"><div className="h1">Loading Console...</div></div>;
  }

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="h1">👨‍⚕️ Therapist Console</div>
          <div className="sub">Manage patients, review sessions, track progress</div>
        </div>
        <button className="btn btnPrimary" onClick={() => setShowAddChild(!showAddChild)}>
          {showAddChild ? "Cancel" : "➕ Add Child"}
        </button>
      </div>

      {/* Add Child Form */}
      {showAddChild && (
        <div className="panel" style={{ marginBottom: 20 }}>
          <h3 style={{ margin: "0 0 12px 0", fontSize: 16 }}>Add New Child</h3>
          <form onSubmit={handleAddChild} className="form-stack">
            <div className="form-row">
              <input
                className="input full"
                placeholder="Child's email"
                value={newChild.email}
                onChange={(e) => setNewChild({ ...newChild, email: e.target.value })}
                required
              />
              <input
                className="input full"
                placeholder="Full name"
                value={newChild.full_name}
                onChange={(e) => setNewChild({ ...newChild, full_name: e.target.value })}
              />
            </div>
            <div className="form-row">
              <input
                className="input full"
                type="date"
                placeholder="Date of birth"
                value={newChild.date_of_birth}
                onChange={(e) => setNewChild({ ...newChild, date_of_birth: e.target.value })}
              />
              <select
                className="input full"
                value={newChild.gender}
                onChange={(e) => setNewChild({ ...newChild, gender: e.target.value })}
              >
                <option value="unknown">Gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <textarea
              className="input full"
              placeholder="Diagnosis notes (optional)"
              value={newChild.diagnosis_notes}
              onChange={(e) => setNewChild({ ...newChild, diagnosis_notes: e.target.value })}
              rows={3}
            />
            {addError && <div style={{ color: "#f87171", fontSize: 14 }}>{addError}</div>}
            <button className="btn btnPrimary" disabled={addLoading}>
              {addLoading ? "Adding..." : "Add Child"}
            </button>
          </form>
        </div>
      )}

      {/* Children List */}
      <div className="panel" style={{ marginBottom: 20 }}>
        <h3 style={{ margin: "0 0 12px 0", fontSize: 16 }}>👶 Children ({children.length})</h3>
        {children.length === 0 ? (
          <p className="sub">No children assigned yet. Add a child to get started.</p>
        ) : (
          <div className="children-grid">
            {children.map((c) => (
              <div
                key={c.id}
                className={`child-card ${selectedChild === c.id ? "child-card-active" : ""}`}
                onClick={() => setSelectedChild(selectedChild === c.id ? null : c.id)}
              >
                <div className="child-avatar">👶</div>
                <div className="child-info">
                  <div className="child-name">{c.full_name || c.email}</div>
                  <div className="child-meta">
                    {c.date_of_birth && <span>DOB: {c.date_of_birth}</span>}
                    {c.gender && c.gender !== "unknown" && <span> · {c.gender}</span>}
                  </div>
                  {c.diagnosis_notes && (
                    <div className="child-diagnosis">{c.diagnosis_notes}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Child Progress Panel */}
      {childProgress && (
        <div className="panel" style={{ marginBottom: 20 }}>
          <h3 style={{ margin: "0 0 12px 0", fontSize: 16 }}>
            📈 Progress: {childProgress.child_name}
          </h3>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{childProgress.total_sessions}</div>
              <div className="stat-label">Sessions</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{childProgress.completed_sessions}</div>
              <div className="stat-label">Completed</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{childProgress.total_trials}</div>
              <div className="stat-label">Trials</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{(childProgress.overall_accuracy * 100).toFixed(1)}%</div>
              <div className="stat-label">Accuracy</div>
            </div>
          </div>

          {childProgress.game_breakdown?.length > 0 && (
            <div className="table-wrapper" style={{ marginTop: 12 }}>
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
          )}

          {childProgress.recent_sessions?.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h4 style={{ margin: "0 0 8px 0", fontSize: 14, color: "var(--muted)" }}>
                Recent Sessions
              </h4>
              {childProgress.recent_sessions.map((s, i) => (
                <div key={i} className="session-row">
                  <span className="session-date">{s.date}</span>
                  <span className="session-title">{s.title}</span>
                  <span className={`status-badge status-${s.status}`}>{s.status}</span>
                  <span className="session-score">{s.correct}/{s.total_trials}</span>
                  <span className={`accuracy-badge ${s.accuracy >= 0.8 ? "acc-high" : s.accuracy >= 0.5 ? "acc-mid" : "acc-low"}`}>
                    {(s.accuracy * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Session History with Filters */}
      <div className="panel">
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
          <h3 style={{ margin: 0, fontSize: 16 }}>📋 Session History</h3>
          <div className="row">
            <select className="input" style={{ minWidth: 120 }} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="in_progress">In Progress</option>
              <option value="draft">Draft</option>
            </select>
            <select className="input" style={{ minWidth: 140 }} value={gameFilter} onChange={(e) => setGameFilter(e.target.value)}>
              <option value="">All Games</option>
              <option value="joint_attention">Joint Attention</option>
              <option value="matching">Matching</option>
              <option value="object_discovery">Object Discovery</option>
              <option value="problem_solving">Problem Solving</option>
            </select>
          </div>
        </div>

        {filteredSessions.length === 0 ? (
          <p className="sub">No sessions found.</p>
        ) : (
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
                {filteredSessions.map((s) => (
                  <tr key={s.id}>
                    <td>{s.session_date}</td>
                    <td>{s.child_name}</td>
                    <td>{(s.game_types || []).map((g) => g.replace(/_/g, " ")).join(", ") || s.title}</td>
                    <td><span className={`status-badge status-${s.status}`}>{s.status}</span></td>
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
        )}
      </div>
    </div>
  );
}
