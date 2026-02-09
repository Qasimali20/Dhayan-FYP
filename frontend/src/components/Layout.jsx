import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const NAV_ITEMS = [
  { to: "/dashboard", label: "📊 Dashboard" },
  { to: "/therapist", label: "👨‍⚕️ Console" },
  { to: "/games", label: "🎮 Games" },
  { to: "/speech-therapy", label: "🗣️ Speech Therapy" },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const roles = user?.roles || [];
  const displayName = user?.full_name || user?.email || "User";

  return (
    <div className="app-layout">
      {/* Top Navigation */}
      <nav className="top-nav">
        <div className="nav-inner">
          <div className="nav-brand">
            <span className="brand-icon">🧠</span>
            <span className="brand-text">DHYAN</span>
            <span className="brand-sub">Autism Therapy Platform</span>
          </div>

          <div className="nav-links">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `nav-link ${isActive ? "nav-link-active" : ""}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>

          <div className="nav-user">
            <span className="nav-user-name">{displayName}</span>
            {roles.length > 0 && (
              <span className="badge">{roles[0]}</span>
            )}
            <button className="btn btn-sm" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Page Content */}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
