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
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-icon" style={{
            width: 48, height: 48, borderRadius: 12,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 24, fontWeight: 900, color: '#fff',
          }}>D</div>
          <div className="auth-brand-name">DHYAN</div>
          <div className="auth-brand-sub">AI-Powered Autism Therapy Platform</div>
        </div>

        <form onSubmit={onSubmit} className="form-stack">
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="input full"
              placeholder="you@example.com"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="input full"
              placeholder="Enter your password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          {err && <div className="auth-error">{err}</div>}

          <button className="btn btnPrimary btn-lg w-full" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? (
              <><span className="spinner spinner-sm" style={{ borderTopColor: "#fff" }} /> Signing in...</>
            ) : (
              "Sign In"
            )}
          </button>

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
