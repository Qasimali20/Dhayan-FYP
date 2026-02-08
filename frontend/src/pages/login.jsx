import { useEffect, useState } from "react";
import { login } from "../api/auth";
import { getToken } from "../api/client";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const nav = useNavigate();
  const { user, refreshUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  // ✅ stable redirect (no side effects in render)
  useEffect(() => {
    if (user || getToken()) nav("/dashboard");
  }, [user, nav]);

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      await login(email.trim(), password);
      await refreshUser();          // populate auth context before navigating
      nav("/dashboard");
    } catch (ex) {
      setErr(ex.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="h1">🧠 DHYAN</div>
          <div className="sub">AI-Powered Autism Therapy Platform — Login</div>
        </div>
      </div>

      <div className="panel" style={{ maxWidth: 520 }}>
        <form onSubmit={onSubmit}>
          <div className="row" style={{ marginBottom: 12 }}>
            <input
              className="input"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
            <input
              className="input"
              placeholder="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <div className="row">
            <button className="btn btnPrimary" disabled={loading}>
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </div>

          {err ? <div className="status" style={{ color: "#ffb4b4" }}>{err}</div> : null}

          <div className="auth-links">
            <Link to="/forgot-password">Forgot password?</Link>
            <span className="auth-links-sep">•</span>
            <Link to="/signup">Create an account</Link>
          </div>
        </form>
      </div>
    </div>
  );
}
