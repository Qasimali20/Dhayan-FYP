/**
 * GenericGame – Reusable game session component.
 * Works with matching, object_discovery, problem_solving, and any future game plugin.
 *
 * Props:
 *   gameCode: string (e.g. "matching", "object_discovery", "problem_solving")
 *   gameName: string (display name)
 *   gameIcon: string (emoji)
 *   trialCount: number (default 10)
 *   multiSelect: boolean (default false — set true for object_discovery)
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { listChildren, createChild } from "../api/patients";
import { startGameSession, nextGameTrial, submitGameTrial, endSession } from "../api/games";
import { useChild } from "../hooks/useChild";
import SummaryPanel from "./summarypanel";

export default function GenericGame({
  gameCode,
  gameName = "Game",
  gameIcon = "🎮",
  trialCount = 10,
  multiSelect = false,
}) {
  const navigate = useNavigate();
  const { selectedChild } = useChild();

  // ── State ──
  const [sessionId, setSessionId] = useState(null);
  const [trial, setTrial] = useState(null);
  const [summary, setSummary] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastResult, setLastResult] = useState(null);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [showFeedback, setShowFeedback] = useState(false);

  const timerRef = useRef(null);
  const trialStartRef = useRef(null);

  // ── TTS ──
  const speak = useCallback(
    (text) => {
      if (!voiceEnabled || !text) return;
      try {
        const u = new SpeechSynthesisUtterance(text.replace(/[^\w\s!?.,']/g, ""));
        u.rate = 0.85;
        u.pitch = 1.1;
        speechSynthesis.cancel();
        speechSynthesis.speak(u);
      } catch {}
    },
    [voiceEnabled]
  );

  // ── Speak prompt on trial change ──
  useEffect(() => {
    if (trial?.prompt) speak(trial.prompt);
  }, [trial, speak]);

  // ── Timer for time limit ──
  useEffect(() => {
    if (!trial?.time_limit_ms || !trial?.trial_id) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      handleSubmit(null, true);
    }, trial.time_limit_ms);
    return () => clearTimeout(timerRef.current);
  }, [trial]);

  // ── Normalize trial from various backend formats ──
  function normalizeTrial(raw) {
    if (!raw || raw.detail) return raw;
    const opts = (raw.options || []).map((o) => {
      if (typeof o === "string") return { id: o, label: o };
      return { id: o.id || o.label || String(o), label: o.label || o.id || String(o) };
    });
    return { ...raw, options: opts };
  }

  // ── Start session ──
  async function handleStart() {
    if (!selectedChild) {
      setError("Please select a child from the Games page first");
      return;
    }
    setError("");
    setLoading(true);
    setSummary(null);
    setLastResult(null);
    setSelectedItems(new Set());
    try {
      const res = await startGameSession(gameCode, parseInt(selectedChild), trialCount);
      setSessionId(res.session?.session_id);
      if (res.first_trial && !res.first_trial.detail) {
        setTrial(normalizeTrial(res.first_trial));
        setStatus("Playing...");
        trialStartRef.current = Date.now();
      } else if (res.summary) {
        setSummary(res.summary);
        setStatus("Session complete");
      }
    } catch (err) {
      setError(err.message || "Failed to start session");
    } finally {
      setLoading(false);
    }
  }

  // ── Submit trial ──
  async function handleSubmit(clickedValue, timedOut = false) {
    if (!trial?.trial_id) return;
    if (timerRef.current) clearTimeout(timerRef.current);

    const elapsed = Date.now() - (trialStartRef.current || Date.now());
    let clicked = clickedValue;

    if (multiSelect && !timedOut) {
      clicked = Array.from(selectedItems).join(",");
    }

    if (!clicked && !timedOut) return;

    setLoading(true);
    setShowFeedback(false);

    try {
      const res = await submitGameTrial(gameCode, trial.trial_id, clicked || "", elapsed, timedOut);
      setLastResult(res);
      setShowFeedback(true);

      // Show feedback briefly then move to next trial
      setTimeout(async () => {
        setShowFeedback(false);
        setSelectedItems(new Set());

        if (res.session_completed && res.summary) {
          setSummary(res.summary);
          setTrial(null);
          setStatus("Session complete!");
        } else if (sessionId) {
          try {
            const next = await nextGameTrial(gameCode, sessionId);
            if (next.detail) {
              if (next.summary) setSummary(next.summary);
              setTrial(null);
              setStatus("Session complete!");
            } else {
              setTrial(normalizeTrial(next));
              setStatus("Playing...");
              trialStartRef.current = Date.now();
            }
          } catch (err) {
            setError(err.message || "Failed to get next trial");
            setTrial(null);
          }
        }
        setLoading(false);
      }, 1500);
    } catch (err) {
      setError(err.message || "Failed to submit");
      setLoading(false);
    }
  }

  // ── Toggle item for multi-select mode ──
  function toggleItem(id) {
    setSelectedItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  // ── Reset / Abandon ──
  async function handleReset() {
    if (sessionId) {
      try { await endSession(sessionId); } catch {}
    }
    setSessionId(null);
    setTrial(null);
    setSummary(null);
    setLastResult(null);
    setStatus("");
    setError("");
    setSelectedItems(new Set());
    setShowFeedback(false);
  }

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="h1">{gameIcon} {gameName}</div>
          <div className="sub">
            {status || "Select a child and start playing"}
          </div>
        </div>
        <div className="row">
          <button
            className={`btn ${voiceEnabled ? "btnPrimary" : ""}`}
            onClick={() => setVoiceEnabled(!voiceEnabled)}
          >
            {voiceEnabled ? "🔊 Voice On" : "🔇 Voice Off"}
          </button>
          {sessionId && (
            <button className="btn" onClick={handleReset}>
              Reset
            </button>
          )}
          <button className="btn" onClick={() => navigate("/games")}>
            ← Back
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: 12 }}>{error}</div>
      )}

      {/* Start Session */}
      {!sessionId && (
        <div className="panel" style={{ marginBottom: 20, textAlign: "center", padding: 32 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>{gameIcon}</div>
          <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>Ready to play {gameName}?</div>
          <div style={{ color: "var(--muted)", fontSize: 13, marginBottom: 20 }}>
            {selectedChild ? "Press start when you're ready!" : "Select a child on the Games page first"}
          </div>
          <button
            className="btn btnPrimary btn-lg"
            onClick={handleStart}
            disabled={loading || !selectedChild}
            style={{ minWidth: 200, fontSize: 16 }}
          >
            {loading ? (
              <><span className="spinner" style={{ width: 18, height: 18, marginRight: 8 }}></span> Starting...</>
            ) : (
              "▶ Start Session"
            )}
          </button>
          {!selectedChild && (
            <div style={{ color: "#f59e0b", fontSize: 13, marginTop: 10 }}>
              Select a child on the Games page first
            </div>
          )}
        </div>
      )}

      {/* Feedback overlay */}
      {showFeedback && lastResult && (
        <div className={`feedback-banner ${lastResult.success ? "feedback-success" : "feedback-fail"}`}>
          <span className="feedback-icon">{lastResult.success ? "✅" : "❌"}</span>
          <span>{lastResult.feedback}</span>
        </div>
      )}

      {/* Trial Display */}
      {trial && !showFeedback && (
        <div>
          <div className="panel" style={{ marginBottom: 14, textAlign: "center" }}>
            <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>
              {trial.prompt}
            </div>
            {trial.extra?.category_label && (
              <div style={{ fontSize: 28, margin: "8px 0" }}>
                {trial.extra.category_label}
                {trial.extra?.correct_count > 0 && (
                  <span style={{ fontSize: 14, color: "var(--muted)", marginLeft: 8 }}>
                    (find {trial.extra.correct_count})
                  </span>
                )}
              </div>
            )}
            {trial.extra?.sequence && (
              <div style={{ fontSize: 32, letterSpacing: 8, margin: "12px 0" }}>
                {trial.extra.sequence.join(" ")}
              </div>
            )}
            {trial.ai_hint && (
              <div style={{ color: "var(--muted)", fontSize: 13, marginTop: 6 }}>
                💡 Hint: {trial.ai_hint}
              </div>
            )}
          </div>

          <div className="grid">
            {(trial.options || []).map((opt) => {
              const isHighlighted = trial.highlight === opt.id;
              const isSelected = multiSelect && selectedItems.has(opt.id);
              return (
                <div
                  key={opt.id}
                  className={`card ${isHighlighted ? "cardHighlight" : ""} ${isSelected ? "cardSelected" : ""} ${loading ? "cardDisabled" : ""}`}
                  onClick={() => {
                    if (loading) return;
                    if (multiSelect) {
                      toggleItem(opt.id);
                    } else {
                      handleSubmit(opt.id);
                    }
                  }}
                >
                  <div style={{ fontSize: 28 }}>{opt.label}</div>
                </div>
              );
            })}
          </div>

          {/* Multi-select submit button */}
          {multiSelect && (
            <div style={{ textAlign: "center", marginTop: 14 }}>
              <button
                className="btn btnPrimary"
                onClick={() => handleSubmit(null)}
                disabled={loading || selectedItems.size === 0}
                style={{ minWidth: 200 }}
              >
                ✅ Submit ({selectedItems.size} selected)
              </button>
            </div>
          )}
        </div>
      )}

      {/* Last result */}
      {lastResult && !showFeedback && !trial && (
        <div className="panel" style={{ marginBottom: 14 }}>
          <div className="row">
            <span className="badge">
              {lastResult.success ? "✅ Correct" : "❌ Incorrect"} — Score: {lastResult.score}/10
            </span>
            {lastResult.ai_recommendation && (
              <span className="sub" style={{ fontSize: 12 }}>
                AI: {lastResult.ai_recommendation}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Summary */}
      {summary && <SummaryPanel data={summary} lastResult={lastResult} />}
    </div>
  );
}
