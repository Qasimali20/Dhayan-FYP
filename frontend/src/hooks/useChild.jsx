/**
 * Global Child Context — select a child once, use everywhere (games, speech therapy).
 *
 * Provides:
 *   selectedChild   — id string (or "")
 *   childProfile    — full child object from API
 *   children        — full list of children
 *   setSelectedChild(id)
 *   refreshChildren()
 *   ChildSelector   — drop-in <select> component
 */
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { listChildren, createChild } from "../api/patients";

const ChildContext = createContext(null);

export function ChildProvider({ children: reactChildren }) {
  const [children, setChildren] = useState([]);
  const [selectedChild, setSelectedChild] = useState(() => {
    // Restore from sessionStorage so it persists across navigation
    return sessionStorage.getItem("dhyan_selected_child") || "";
  });
  const [loading, setLoading] = useState(true);

  const refreshChildren = useCallback(async () => {
    try {
      const list = await listChildren();
      const arr = Array.isArray(list) ? list : [];
      setChildren(arr);

      // Auto-select first child if nothing is selected
      if (!selectedChild && arr.length > 0) {
        const firstId = String(arr[0].id);
        setSelectedChild(firstId);
        sessionStorage.setItem("dhyan_selected_child", firstId);
      }
    } catch {
      setChildren([]);
    } finally {
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    refreshChildren();
  }, [refreshChildren]);

  // Persist selection
  const selectChild = useCallback((id) => {
    setSelectedChild(id);
    if (id) sessionStorage.setItem("dhyan_selected_child", id);
    else sessionStorage.removeItem("dhyan_selected_child");
  }, []);

  const childProfile = children.find((c) => String(c.id) === String(selectedChild)) || null;

  return (
    <ChildContext.Provider
      value={{
        children,
        selectedChild,
        setSelectedChild: selectChild,
        childProfile,
        refreshChildren,
        loading,
      }}
    >
      {reactChildren}
    </ChildContext.Provider>
  );
}

export function useChild() {
  const ctx = useContext(ChildContext);
  if (!ctx) throw new Error("useChild must be used within ChildProvider");
  return ctx;
}

/**
 * Compact child selector component — drop into any header.
 */
export function ChildSelector({ style = {} }) {
  const { children, selectedChild, setSelectedChild, childProfile, refreshChildren } = useChild();
  const [showAdd, setShowAdd] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newName, setNewName] = useState("");
  const [addError, setAddError] = useState("");

  async function handleAdd(e) {
    e.preventDefault();
    if (!newEmail.trim()) return;
    setAddError("");
    try {
      await createChild({ email: newEmail.trim(), full_name: newName.trim() });
      await refreshChildren();
      setShowAdd(false);
      setNewEmail("");
      setNewName("");
    } catch (ex) {
      setAddError(ex.message || "Failed to add child");
    }
  }

  return (
    <div style={{ ...style }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 13, opacity: 0.7, whiteSpace: "nowrap" }}>👶 Child:</span>
        <select
          className="input"
          value={selectedChild}
          onChange={(e) => setSelectedChild(e.target.value)}
          style={{ minWidth: 160, padding: "6px 10px", fontSize: 13 }}
        >
          <option value="">Select child...</option>
          {children.map((c) => (
            <option key={c.id} value={c.id}>
              {c.full_name || c.user?.full_name || c.user?.email || c.email || `Child #${c.id}`}
            </option>
          ))}
        </select>
        <button
          className="btn"
          style={{ padding: "5px 10px", fontSize: 12 }}
          onClick={() => setShowAdd(!showAdd)}
          title="Add a new child"
        >
          ➕
        </button>
      </div>

      {showAdd && (
        <form
          onSubmit={handleAdd}
          style={{
            display: "flex", gap: 6, marginTop: 6,
            padding: 8, background: "rgba(255,255,255,0.04)", borderRadius: 8,
          }}
        >
          <input className="input" placeholder="Email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} required style={{ flex: 1, padding: "5px 8px", fontSize: 12 }} />
          <input className="input" placeholder="Name" value={newName} onChange={(e) => setNewName(e.target.value)} style={{ flex: 1, padding: "5px 8px", fontSize: 12 }} />
          <button className="btn btnPrimary" type="submit" style={{ padding: "5px 10px", fontSize: 12 }}>Add</button>
        </form>
      )}
      {addError && <div style={{ color: "#f87171", fontSize: 12, marginTop: 4 }}>{addError}</div>}

      {childProfile && (
        <div style={{ fontSize: 12, opacity: 0.6, marginTop: 4 }}>
          Selected: {childProfile.full_name || childProfile.user?.full_name || `#${childProfile.id}`}
        </div>
      )}
    </div>
  );
}
