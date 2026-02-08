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

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="h1">DHYAN</div>
          <div className="sub">Therapy Assistant — {subtitle}</div>
        </div>
      </div>

      <div className="panel" style={{ maxWidth: 520 }}>

        {/* ── Step 1: Email ── */}
        {step === STEP.EMAIL && (
          <form onSubmit={onRequestOtp}>
            <div className="form-stack">
              <input
                className="input full"
                placeholder="Email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
            <div className="row" style={{ marginTop: 14 }}>
              <button className="btn btnPrimary" disabled={loading}>
                {loading ? "Sending..." : "Send OTP"}
              </button>
            </div>
          </form>
        )}

        {/* ── Step 2: Verify OTP ── */}
        {step === STEP.OTP && (
          <form onSubmit={onVerifyOtp}>
            <div className="form-stack">
              <input
                className="input full"
                placeholder="6-digit OTP"
                maxLength={6}
                required
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                autoComplete="one-time-code"
                style={{ letterSpacing: "0.4em", textAlign: "center", fontSize: 22 }}
              />
            </div>
            <div className="row" style={{ marginTop: 14 }}>
              <button className="btn btnPrimary" disabled={loading}>
                {loading ? "Verifying..." : "Verify OTP"}
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => { setStep(STEP.EMAIL); setOtp(""); setErr(""); setMsg(""); }}
              >
                Resend
              </button>
            </div>
          </form>
        )}

        {/* ── Step 3: New password ── */}
        {step === STEP.RESET && (
          <form onSubmit={onResetPassword}>
            <div className="form-stack">
              <input
                className="input full"
                placeholder="New Password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
              />
              <input
                className="input full"
                placeholder="Confirm New Password"
                type="password"
                required
                value={password2}
                onChange={(e) => setPassword2(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <div className="row" style={{ marginTop: 14 }}>
              <button className="btn btnPrimary" disabled={loading}>
                {loading ? "Resetting..." : "Reset Password"}
              </button>
            </div>
          </form>
        )}

        {/* ── Step 4: Done ── */}
        {step === STEP.DONE && (
          <div style={{ textAlign: "center", padding: "20px 0" }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
            <p style={{ color: "#6ee7b7", fontSize: 16, marginBottom: 18 }}>
              Password reset successfully!
            </p>
            <button className="btn btnPrimary" onClick={() => nav("/login")}>
              Go to Login
            </button>
          </div>
        )}

        {msg ? <div className="status" style={{ color: "#6ee7b7" }}>{msg}</div> : null}
        {err ? <div className="status" style={{ color: "#ffb4b4" }}>{err}</div> : null}

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
