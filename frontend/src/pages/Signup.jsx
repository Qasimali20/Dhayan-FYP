import { useState } from "react";
import { signup } from "../api/auth";
import { useNavigate, Link } from "react-router-dom";

export default function Signup() {
  const nav = useNavigate();

  const [form, setForm] = useState({
    email: "",
    full_name: "",
    phone: "",
    password: "",
    password2: "",
    role: "parent",
  });
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");

    if (form.password !== form.password2) {
      setErr("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await signup(form);
      nav("/login", { state: { msg: "Account created! Please sign in." } });
    } catch (ex) {
      // try to show field-level errors
      const p = ex.payload;
      if (p && typeof p === "object") {
        const msgs = Object.entries(p)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
          .join(" | ");
        setErr(msgs);
      } else {
        setErr(ex.message || "Signup failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="h1">DHYAN</div>
          <div className="sub">Therapy Assistant — Create Account</div>
        </div>
      </div>

      <div className="panel" style={{ maxWidth: 520 }}>
        <form onSubmit={onSubmit}>
          <div className="form-stack">
            <input
              className="input full"
              placeholder="Email"
              type="email"
              required
              value={form.email}
              onChange={set("email")}
              autoComplete="email"
            />
            <input
              className="input full"
              placeholder="Full Name"
              value={form.full_name}
              onChange={set("full_name")}
              autoComplete="name"
            />
            <input
              className="input full"
              placeholder="Phone (optional)"
              value={form.phone}
              onChange={set("phone")}
              autoComplete="tel"
            />

            <select
              className="input full"
              value={form.role}
              onChange={set("role")}
            >
              <option value="parent">Parent</option>
              <option value="therapist">Therapist</option>
            </select>

            <input
              className="input full"
              placeholder="Password"
              type="password"
              required
              value={form.password}
              onChange={set("password")}
              autoComplete="new-password"
            />
            <input
              className="input full"
              placeholder="Confirm Password"
              type="password"
              required
              value={form.password2}
              onChange={set("password2")}
              autoComplete="new-password"
            />
          </div>

          <div className="row" style={{ marginTop: 14 }}>
            <button className="btn btnPrimary" disabled={loading}>
              {loading ? "Creating account..." : "Sign Up"}
            </button>
          </div>

          {err ? (
            <div className="status" style={{ color: "#ffb4b4" }}>{err}</div>
          ) : null}

          <div className="auth-links">
            <Link to="/login">Already have an account? Sign in</Link>
          </div>
        </form>
      </div>
    </div>
  );
}
