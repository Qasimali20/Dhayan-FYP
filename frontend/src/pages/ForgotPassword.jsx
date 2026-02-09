import { useState } from "react";
import { forgotPassword, verifyOtp, resetPassword } from "../api/auth";
import { useNavigate, Link } from "react-router-dom";

const STEP = { EMAIL: 1, OTP: 2, RESET: 3, DONE: 4 };

export default function ForgotPassword() {
  const nav = useNavigate();

  const [step, setStep] = useState(STEP.EMAIL);
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  // Step 1 — request OTP
  async function onRequestOtp(e) {
    e.preventDefault();
    setErr("");
    setMsg("");
    setLoading(true);
    try {
      const data = await forgotPassword(email.trim().toLowerCase());
      setMsg(data.message || "OTP sent to your email.");
      setStep(STEP.OTP);
    } catch (ex) {
      const p = ex.payload;
      if (p?.email) {
        setErr(Array.isArray(p.email) ? p.email.join(", ") : p.email);
      } else {
        setErr(ex.message || "Failed to send OTP");
      }
    } finally {
      setLoading(false);
    }
  }

  // Step 2 — verify OTP
  async function onVerifyOtp(e) {
    e.preventDefault();
    setErr("");
    setMsg("");
    setLoading(true);
    try {
      const data = await verifyOtp(email.trim().toLowerCase(), otp.trim());
      setMsg(data.message || "OTP verified.");
      setStep(STEP.RESET);
    } catch (ex) {
      setErr(ex.payload?.error || ex.message || "Invalid OTP");
    } finally {
      setLoading(false);
    }
  }

  // Step 3 — reset password
  async function onResetPassword(e) {
    e.preventDefault();
    setErr("");
    setMsg("");

    if (password !== password2) {
      setErr("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await resetPassword(email.trim().toLowerCase(), otp.trim(), password, password2);
      setStep(STEP.DONE);
    } catch (ex) {
      const p = ex.payload;
      if (p && typeof p === "object" && !p.error) {
        const msgs = Object.entries(p)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
          .join(" | ");
        setErr(msgs);
      } else {
        setErr(p?.error || ex.message || "Reset failed");
      }
    } finally {
      setLoading(false);
    }
  }

  const subtitle =
    step === STEP.EMAIL  ? "Enter your email to receive a reset code" :
    step === STEP.OTP    ? "Enter the 6-digit OTP sent to your email" :
    step === STEP.RESET  ? "Choose a new password" :
                           "Password reset successful!";

  // Step indicator
  const steps = [1, 2, 3, 4];
  const stepLabels = ["Email", "Verify", "Reset", "Done"];

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
          <div className="auth-brand-sub">{subtitle}</div>
        </div>

        {/* Step indicator */}
        <div style={{ display: "flex", justifyContent: "center", gap: 8, marginBottom: 28 }}>
          {steps.map((s, i) => (
            <div key={s} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 12,
                fontWeight: 700,
                background: step >= s ? "var(--primary)" : "rgba(255,255,255,0.08)",
                color: step >= s ? "#fff" : "var(--muted)",
                transition: "all 0.3s ease",
              }}>
                {step > s ? "✓" : s}
              </div>
              {i < steps.length - 1 && (
                <div style={{
                  width: 24,
                  height: 2,
                  background: step > s ? "var(--primary)" : "var(--border)",
                  borderRadius: 2,
                  transition: "background 0.3s ease",
                }} />
              )}
            </div>
          ))}
        </div>

        {/* ── Step 1: Email ── */}
        {step === STEP.EMAIL && (
          <form onSubmit={onRequestOtp} className="form-stack">
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                className="input full"
                placeholder="you@example.com"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
            <button className="btn btnPrimary btn-lg w-full" disabled={loading}>
              {loading ? <><span className="spinner spinner-sm" style={{ borderTopColor: "#fff" }} /> Sending...</> : "Send OTP"}
            </button>
          </form>
        )}

        {/* ── Step 2: Verify OTP ── */}
        {step === STEP.OTP && (
          <form onSubmit={onVerifyOtp} className="form-stack">
            <div className="form-group">
              <label className="form-label">Verification Code</label>
              <input
                className="input full"
                placeholder="000000"
                maxLength={6}
                required
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                autoComplete="one-time-code"
                style={{ letterSpacing: "0.4em", textAlign: "center", fontSize: 24, fontWeight: 700 }}
              />
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btnPrimary btn-lg" style={{ flex: 1 }} disabled={loading}>
                {loading ? <><span className="spinner spinner-sm" style={{ borderTopColor: "#fff" }} /> Verifying...</> : "Verify OTP"}
              </button>
              <button
                type="button"
                className="btn btn-lg"
                onClick={() => { setStep(STEP.EMAIL); setOtp(""); setErr(""); setMsg(""); }}
              >
                Resend
              </button>
            </div>
          </form>
        )}

        {/* ── Step 3: New password ── */}
        {step === STEP.RESET && (
          <form onSubmit={onResetPassword} className="form-stack">
            <div className="form-group">
              <label className="form-label">New Password</label>
              <input
                className="input full"
                placeholder="Create a strong password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input
                className="input full"
                placeholder="Re-enter your password"
                type="password"
                required
                value={password2}
                onChange={(e) => setPassword2(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <button className="btn btnPrimary btn-lg w-full" disabled={loading}>
              {loading ? <><span className="spinner spinner-sm" style={{ borderTopColor: "#fff" }} /> Resetting...</> : "Reset Password"}
            </button>
          </form>
        )}

        {/* ── Step 4: Done ── */}
        {step === STEP.DONE && (
          <div className="celebration-panel" style={{ padding: "24px 0" }}>
            <div style={{ fontSize: 42, marginBottom: 8 }}>✅</div>
            <div className="celebration-title">Password Reset!</div>
            <div className="celebration-sub">Your password has been updated successfully.</div>
            <button className="btn btnPrimary btn-lg" onClick={() => nav("/login")}>
              Go to Login
            </button>
          </div>
        )}

        {msg && <div className="auth-success" style={{ marginTop: 14 }}>{msg}</div>}
        {err && <div className="auth-error" style={{ marginTop: 14 }}>{err}</div>}

        {step !== STEP.DONE && (
          <div className="auth-links">
            <Link to="/login">Back to Login</Link>
            <span className="auth-links-sep">•</span>
            <Link to="/signup">Create an account</Link>
          </div>
        )}
      </div>
    </div>
  );
}
