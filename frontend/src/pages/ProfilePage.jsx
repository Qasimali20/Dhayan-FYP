import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { updateProfile } from "../api/auth";
import { useToast } from "../hooks/useToast";

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const toast = useToast();

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [phone, setPhone] = useState(user?.phone || "");
  const [saving, setSaving] = useState(false);

  // Track if form is dirty
  const isDirty = fullName !== (user?.full_name || "") || phone !== (user?.phone || "");

  async function handleSaveProfile(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await updateProfile({ full_name: fullName, phone });
      await refreshUser();
      toast.success("Profile updated successfully!");
    } catch (err) {
      toast.error(err.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  }

  const roles = user?.roles || [];
  const roleLabel = roles.map((r) => r.charAt(0).toUpperCase() + r.slice(1)).join(", ") || "User";
  const initial = (user?.full_name || user?.email || "?").charAt(0).toUpperCase();

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="h1">My Profile</div>
          <div className="sub">Manage your account details</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, alignItems: "start" }}>
        {/* Profile Card */}
        <div className="panel" style={{ textAlign: "center", padding: 32 }}>
          {/* Avatar */}
          <div style={{
            width: 80, height: 80, borderRadius: "50%",
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 32, fontWeight: 900, color: "#fff",
            margin: "0 auto 16px",
            boxShadow: "0 8px 24px rgba(99,102,241,0.3)",
          }}>
            {initial}
          </div>

          <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 4 }}>
            {user?.full_name || "No name set"}
          </div>
          <div style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 12 }}>
            {user?.email}
          </div>
          <span className="badge" style={{ fontSize: 12 }}>{roleLabel}</span>

          <div style={{
            marginTop: 20, padding: "14px 0", borderTop: "1px solid var(--border)",
            display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, textAlign: "center",
          }}>
            <div>
              <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>Phone</div>
              <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>{user?.phone || "—"}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>Status</div>
              <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, color: user?.is_active ? "var(--success)" : "var(--danger)" }}>
                {user?.is_active ? "Active" : "Inactive"}
              </div>
            </div>
          </div>
        </div>

        {/* Edit Form */}
        <div className="panel">
          <h3 style={{ margin: "0 0 20px 0", fontSize: 16, fontWeight: 700 }}>Edit Profile</h3>

          <form onSubmit={handleSaveProfile} className="form-stack">
            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                className="input full"
                value={user?.email || ""}
                disabled
                style={{ opacity: 0.5, cursor: "not-allowed" }}
              />
              <span style={{ fontSize: 11, color: "var(--muted)" }}>Email cannot be changed</span>
            </div>

            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                className="input full"
                placeholder="Enter your full name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Phone</label>
              <input
                className="input full"
                placeholder="+1 (555) 123-4567"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Role</label>
              <input
                className="input full"
                value={roleLabel}
                disabled
                style={{ opacity: 0.5, cursor: "not-allowed" }}
              />
            </div>

            <button
              className="btn btnPrimary"
              style={{ marginTop: 8 }}
              disabled={saving || !isDirty}
            >
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </form>
        </div>
      </div>

      {/* Responsive: stack on mobile */}
      <style>{`
        @media (max-width: 768px) {
          .container > div[style*="grid-template-columns"] {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
