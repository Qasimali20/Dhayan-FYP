import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="container" style={{ textAlign: "center", padding: "120px 0" }}>
        <div className="spinner" style={{ width: 36, height: 36, margin: "0 auto 16px" }}></div>
        <div style={{ fontSize: 15, color: "var(--text-secondary)" }}>Authenticating...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
