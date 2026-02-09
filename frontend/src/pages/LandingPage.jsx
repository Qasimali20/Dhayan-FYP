import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const FEATURES = [
  {
    icon: "🧩",
    title: "AI-Powered Games",
    desc: "Adaptive therapy games that adjust difficulty in real-time based on each child's progress and learning patterns.",
  },
  {
    icon: "🗣️",
    title: "Speech Therapy",
    desc: "Record, analyze, and score speech sessions with AI-driven feedback, pronunciation metrics, and therapist scoring.",
  },
  {
    icon: "📊",
    title: "Progress Tracking",
    desc: "Visual dashboards with charts, accuracy trends, and detailed breakdowns for every child and game session.",
  },
  {
    icon: "👨‍⚕️",
    title: "Therapist Console",
    desc: "Manage patients, review session histories, track progress across games, and generate clinical reports.",
  },
  {
    icon: "🎯",
    title: "Adaptive Difficulty",
    desc: "Our neural adaptation engine personalizes every session, adjusting prompts, timing, and complexity per child.",
  },
  {
    icon: "🔒",
    title: "Secure & Private",
    desc: "Role-based access, encrypted data, and HIPAA-aware architecture keep sensitive patient information safe.",
  },
];

const GAMES = [
//   { icon: "👀", name: "Joint Attention", color: "#6366f1" },
  { icon: "🔷", name: "Shape Matching", color: "#10b981" },
  { icon: "🃏", name: "Memory Match", color: "#ec4899" },
  { icon: "🔍", name: "Object Discovery", color: "#f59e0b" },
  { icon: "🧩", name: "Problem Solving", color: "#ef4444" },
  { icon: "🗣️", name: "Speech Therapy", color: "#8b5cf6" },
];

const STATS = [
  { value: "8+", label: "Therapy Games" },
  { value: "AI", label: "Speech Analysis" },
  { value: "Real-time", label: "Adaptation" },
  { value: "Behaviour", label: "Analysis" },
];

export default function LandingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      {/* ── Navbar ── */}
      <nav
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 100,
          padding: "14px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          backdropFilter: "blur(20px)",
          background: "rgba(15,17,23,0.88)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 900, color: '#fff',
          }}>D</span>
          <span style={{ fontSize: 20, fontWeight: 800, letterSpacing: "-0.02em" }}>DHYAN</span>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {user ? (
            <button className="btn btnPrimary" onClick={() => navigate("/dashboard")}>
                            Dashboard
            </button>
          ) : (
            <>
              <button className="btn" onClick={() => navigate("/login")}>
                Sign In
              </button>
              <button className="btn btnPrimary" onClick={() => navigate("/signup")}>
                Get Started
              </button>
            </>
          )}
        </div>
      </nav>

      {/* ── Hero ── */}
      <section
        style={{
          paddingTop: 120,
          paddingBottom: 80,
          textAlign: "center",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Background glow */}
        <div
          style={{
            position: "absolute",
            top: "20%",
            left: "50%",
            transform: "translateX(-50%)",
            width: 600,
            height: 600,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)",
            pointerEvents: "none",
          }}
        />

        <div style={{ position: "relative", maxWidth: 720, margin: "0 auto", padding: "0 24px" }}>
          <div
            style={{
              display: "inline-block",
              padding: "6px 16px",
              borderRadius: 20,
              background: "var(--primary-bg)",
              border: "1px solid rgba(99,102,241,0.25)",
              fontSize: 13,
              fontWeight: 600,
              color: "var(--primary-light)",
              marginBottom: 20,
            }}
          >
            🚀 AI-Powered Autism Therapy Platform
          </div>

          <h1
            style={{
              fontSize: "clamp(36px, 6vw, 56px)",
              fontWeight: 900,
              lineHeight: 1.1,
              margin: "0 0 20px 0",
              letterSpacing: "-0.03em",
            }}
          >
            Empowering Children
            <br />
            <span
              style={{
                background: "linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Through Play & AI
            </span>
          </h1>

          <p
            style={{
              fontSize: "clamp(16px, 2.5vw, 19px)",
              color: "var(--text-secondary)",
              lineHeight: 1.6,
              maxWidth: 560,
              margin: "0 auto 32px",
            }}
          >
            DHYAN combines adaptive therapy games, AI-powered speech analysis, and real-time progress
            tracking to support children on the autism spectrum — backed by clinical best practices.
          </p>

          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <button
              className="btn btnPrimary btn-lg"
              style={{ fontSize: 17, padding: "16px 36px" }}
              onClick={() => navigate(user ? "/dashboard" : "/signup")}
            >
              {user ? "Go to Dashboard" : "Get Started Free"} →
            </button>
            <button
              className="btn btn-lg"
              style={{ fontSize: 17, padding: "16px 36px" }}
              onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth" })}
            >
              Learn More ↓
            </button>
          </div>
        </div>
      </section>

      {/* ── Stats Bar ── */}
      <section
        style={{
          maxWidth: 900,
          margin: "0 auto 60px",
          padding: "0 24px",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: 12,
          }}
        >
          {STATS.map((s) => (
            <div
              key={s.label}
              style={{
                textAlign: "center",
                padding: "20px 12px",
                borderRadius: "var(--radius-lg)",
                background: "var(--card)",
                border: "2px solid var(--border)",
              }}
            >
              <div
                style={{
                  fontSize: 28,
                  fontWeight: 900,
                  background: "linear-gradient(135deg, #6366f1, #a78bfa)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                {s.value}
              </div>
              <div style={{ fontSize: 18, color: "var(--muted)", marginTop: 4, fontWeight: 600 }}>
                {s.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section
        id="features"
        style={{
          maxWidth: 1060,
          margin: "0 auto",
          padding: "0 24px 80px",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <h2 style={{ fontSize: 32, fontWeight: 800, margin: "0 0 12px", letterSpacing: "-0.02em" }}>
            Everything You Need
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: 16, maxWidth: 500, margin: "0 auto" }}>
            A complete platform for therapists, parents, and clinicians working with children on the autism spectrum.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: 16,
          }}
        >
          {FEATURES.map((f) => (
            <div
              key={f.title}
              style={{
                padding: 24,
                borderRadius: "var(--radius-xl)",
                background: "var(--card)",
                border: "1px solid var(--border)",
                transition: "all 0.25s var(--ease-out)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--border-hover)";
                e.currentTarget.style.transform = "translateY(-4px)";
                e.currentTarget.style.boxShadow = "var(--shadow-lg)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border)";
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <div style={{ fontSize: 32, marginBottom: 12 }}>{f.icon}</div>
              <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 6 }}>{f.title}</div>
              <div style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                {f.desc}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Games Showcase ── */}
      <section
        style={{
          maxWidth: 900,
          margin: "0 auto",
          padding: "0 24px 80px",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <h2 style={{ fontSize: 28, fontWeight: 800, margin: "0 0 10px" }}>🎮 Therapy Games</h2>
          <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>
            Engaging, adaptive activities designed to build essential skills
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
            gap: 12,
          }}
        >
          {GAMES.map((g) => (
            <div
              key={g.name}
              style={{
                padding: "20px 12px",
                borderRadius: "var(--radius-lg)",
                background: `${g.color}15`,
                border: `1px solid ${g.color}30`,
                textAlign: "center",
                transition: "transform 0.2s var(--ease-out)",
                cursor: "default",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
              onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
            >
              <div style={{ fontSize: 32, marginBottom: 6 }}>{g.icon}</div>
              <div style={{ fontSize: 13, fontWeight: 700 }}>{g.name}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ── */}
      <section
        style={{
          maxWidth: 900,
          margin: "0 auto",
          padding: "0 24px 80px",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <h2 style={{ fontSize: 28, fontWeight: 800, margin: "0 0 10px" }}>How It Works</h2>
          <p style={{ color: "var(--text-secondary)", fontSize: 15 }}>Three simple steps to get started</p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
          {[
            { step: "1", icon: "👶", title: "Add a Child", desc: "Create a profile with basic details and clinical notes." },
            { step: "2", icon: "🎮", title: "Play & Practice", desc: "Choose from adaptive games and speech activities tailored to your child." },
            { step: "3", icon: "📈", title: "Track Progress", desc: "View accuracy trends, session breakdowns, and AI-driven insights." },
          ].map((s) => (
            <div
              key={s.step}
              style={{
                textAlign: "center",
                padding: 24,
                borderRadius: "var(--radius-xl)",
                background: "var(--card)",
                border: "1px solid var(--border)",
                position: "relative",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  top: -14,
                  left: "50%",
                  transform: "translateX(-50%)",
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background: "var(--primary)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 13,
                  fontWeight: 800,
                  color: "#fff",
                }}
              >
                {s.step}
              </div>
              <div style={{ fontSize: 28, marginTop: 12, marginBottom: 4 }}>{s.icon}</div>
              <div style={{ fontSize: 16, fontWeight: 700, marginTop: 16, marginBottom: 6 }}>{s.title}</div>
              <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>{s.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section
        style={{
          maxWidth: 700,
          margin: "0 auto",
          padding: "0 24px 80px",
          textAlign: "center",
        }}
      >
        <div
          style={{
            padding: "48px 32px",
            borderRadius: "var(--radius-2xl)",
            background: "linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.1) 100%)",
            border: "1px solid rgba(99,102,241,0.2)",
          }}
        >
          <h2 style={{ fontSize: 28, fontWeight: 800, margin: "0 0 10px" }}>
            Ready to Make a Difference?
          </h2>
          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: 15,
              marginBottom: 24,
              maxWidth: 440,
              marginLeft: "auto",
              marginRight: "auto",
            }}
          >
            Join therapists and parents using DHYAN to support children's development through AI-powered play.
          </p>
          <button
            className="btn btnPrimary btn-lg"
            style={{ fontSize: 17, padding: "16px 40px" }}
            onClick={() => navigate(user ? "/dashboard" : "/signup")}
          >
            {user ? "Go to Dashboard →" : "Create Free Account →"}
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      {/* <footer
        style={{
          padding: "24px",
          textAlign: "center",
          borderTop: "1px solid var(--border)",
          color: "var(--muted)",
          fontSize: 13,
        }} */}
      {/* > */}
        {/* <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 6 }}> */}
          {/* <span style={{ fontSize: 18 }}>🧠</span>
          <span style={{ fontWeight: 700, color: "var(--text-secondary)" }}>DHYAN</span> */}
        </div>
    //   </footer>
    // </div>
  );
}
