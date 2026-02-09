import { useEffect, useMemo, useRef, useState } from "react";
import { clearToken, getToken } from "../api/client";
import { useNavigate } from "react-router-dom";
import {
  startSession as apiStartSession,
  nextTrial as apiNextTrial,
  submitTrial as apiSubmitTrial,
  summary as apiSummary,
} from "../api/ja";
import { useChild } from "../hooks/useChild";

import OptionCard from "../components/OptionCard";
import SummaryPanel from "../components/summarypanel";

export default function JaGame() {
  const nav = useNavigate();
  const { selectedChild: childId } = useChild();

  const [sessionId, setSessionId] = useState(null);
  const [trialId, setTrialId] = useState(null);

  // trial shape:
  // {
  //   prompt, options:[string|obj], highlight:<id|string|null>, level, time_limit_ms,
  //   target? (debug), tts_text? (optional)
  // }
  const [trial, setTrial] = useState(null);
  const [statusText, setStatusText] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [completed, setCompleted] = useState(false);

  const [summary, setSummary] = useState(null);
  const [lastTrialText, setLastTrialText] = useState(null);

  // timing
  const trialStartRef = useRef(null);

  // voice
  const [voiceEnabled, setVoiceEnabled] = useState(false);

  // ✅ stable auth redirect
  useEffect(() => {
    if (!getToken()) nav("/login");
  }, [nav]);

  // ── Fetch children on mount ──
  // (now handled by global ChildProvider)

  const canClick = useMemo(() => {
    return !!trialId && !!trial && !submitting && !completed;
  }, [trialId, trial, submitting, completed]);

  function logout() {
    clearToken();
    nav("/login");
  }

  function resetRunState() {
    setSessionId(null);
    setTrialId(null);
    setTrial(null);
    setStatusText("");
    setSubmitting(false);
    setCompleted(false);
    setSummary(null);
    setLastTrialText(null);
    trialStartRef.current = null;
  }

  function normalizeTrialPayload(t) {
    // Backend might return {detail:"No more..."} or normal trial payload
    if (!t || t.detail) return t;

    return {
      trial_id: t.trial_id,
      prompt: t.prompt || "",
      options: t.options || [],
      // highlight should be id (string) if using objects, otherwise option label
      highlight: t.highlight ?? null,
      level: t.level || 1,
      time_limit_ms: t.time_limit_ms || 10000,
      target: t.target || null, // debug only
      tts_text: t.tts_text || null, // optional (future backend tts)
    };
  }

  // --- TTS (Web Speech API fallback, reliable) ---
  function speakText(text) {
    try {
      if (!text) return;
      if (!("speechSynthesis" in window)) return;

      const u = new SpeechSynthesisUtterance(text);
      u.rate = 0.92;
      u.pitch = 1.05;
      u.lang = "en-US";

      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    } catch {
      // ignore
    }
  }

  async function enableVoice() {
    // Browsers require a user gesture to unlock audio.
    // WebSpeech typically works after a click; we still do a safe call.
    setVoiceEnabled(true);
    setStatusText("Voice enabled.");
    if (trial?.tts_text || trial?.prompt) speakText(trial.tts_text || trial.prompt);
  }

  useEffect(() => {
    // auto speak whenever trial changes (if enabled)
    if (voiceEnabled && !completed && trial?.prompt) {
      const text = trial.tts_text || trial.prompt;
      speakText(text);
    }
  }, [voiceEnabled, trial, completed]);

  // --- FLOW: Start -> auto first trial ---
  async function begin() {
    setStatusText("");
    setSummary(null);
    setLastTrialText(null);
    setCompleted(false);
    setTrial(null);
    setTrialId(null);

    const cid = parseInt(childId, 10);
    if (!cid) {
      setStatusText("Please select a child first.");
      return;
    }

    try {
      setStatusText("Starting session...");

      /**
       * Expected backend:
       * {
       *   session: {session_id, trials_planned, time_limit_ms},
       *   first_trial: { trial_id, prompt, options, highlight, level, time_limit_ms, ... }
       *   OR first_trial: { detail: "No more planned trials", summary?: {...} }
       *   summary?: {...} (optional)
       * }
       */
      const res = await apiStartSession(cid, 10);

      const sid = res?.session?.session_id ?? res?.session_id;
      if (!sid) {
        setStatusText("Start failed: session_id missing.");
        return;
      }
      setSessionId(sid);

      // Edge case: backend ended instantly
      if (res?.summary) {
        setCompleted(true);
        setSummary(res.summary);
        setStatusText("Session completed. Summary below.");
        return;
      }

      // ✅ auto first trial
      const ft = normalizeTrialPayload(res?.first_trial);
      if (ft?.detail && String(ft.detail).toLowerCase().includes("no more")) {
        const s = ft.summary ? ft.summary : await apiSummary(sid);
        setCompleted(true);
        setSummary(s);
        setStatusText("Session completed. Summary below.");
        return;
      }

      if (!ft?.trial_id) {
        setStatusText("Session started, but no trial returned.");
        return;
      }

      setTrialId(ft.trial_id);
      setTrial({
        prompt: ft.prompt,
        options: ft.options,
        highlight: ft.highlight,
        level: ft.level,
        time_limit_ms: ft.time_limit_ms,
        target: ft.target,
        tts_text: ft.tts_text,
      });
      trialStartRef.current = performance.now();
      setStatusText(`Session started: ${sid}`);
    } catch (e) {
      setStatusText(`Error: ${e.message}`);
    }
  }

  // --- FLOW: Next Trial ---
  async function loadNext(sid = sessionId) {
    if (!sid || completed) return;

    try {
      setStatusText("Loading next trial...");
      const t = await apiNextTrial(sid);

      if (t?.detail && String(t.detail).toLowerCase().includes("no more")) {
        const s = t.summary ? t.summary : await apiSummary(sid);
        setCompleted(true);
        setTrial(null);
        setTrialId(null);
        setSummary(s);
        setStatusText("Session completed. Summary below.");
        return;
      }

      const nt = normalizeTrialPayload(t);
      if (!nt?.trial_id) {
        setStatusText("No trial returned.");
        return;
      }

      setTrialId(nt.trial_id);
      setTrial({
        prompt: nt.prompt,
        options: nt.options,
        highlight: nt.highlight,
        level: nt.level,
        time_limit_ms: nt.time_limit_ms,
        target: nt.target,
        tts_text: nt.tts_text,
      });

      trialStartRef.current = performance.now();
      setStatusText("");
    } catch (e) {
      setStatusText(`Error: ${e.message}`);
    }
  }

  // --- SUBMIT ---
  async function onPick(opt) {
    if (!canClick) return;

    const clicked = typeof opt === "string" ? opt : opt?.id;
    if (!clicked) return;

    const start = trialStartRef.current ?? performance.now();
    const rt = Math.floor(performance.now() - start);
    const timedOut = rt > (trial?.time_limit_ms || 10000);

    setSubmitting(true);

    try {
      const resp = await apiSubmitTrial(trialId, clicked, rt, timedOut);

      const ok = resp.success ? "Correct" : "Wrong";
      const last = `${ok} | RT=${rt}ms | Clicked=${clicked}${
        trial?.target ? ` | Target=${trial.target}` : ""
      }`;
      setLastTrialText(last);

      // If backend indicates completion, show summary immediately
      if (resp?.session_completed) {
        const s = resp.summary ? resp.summary : sessionId ? await apiSummary(sessionId) : null;

        setCompleted(true);
        setTrial(null);
        setTrialId(null);
        setSummary(s);
        setStatusText("✅ Session completed. Summary below.");
        return;
      }

      // normal flow -> auto next
      setStatusText(last);
      setTimeout(() => loadNext(), 250);
    } catch (e) {
      setStatusText(`Error: ${e.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  async function manualSummary() {
    if (!sessionId) return;
    try {
      setCompleted(true);
      setTrial(null);
      setTrialId(null);

      const s = await apiSummary(sessionId);
      setSummary(s);
      setStatusText("Showing summary...");
    } catch (e) {
      setStatusText(`Error: ${e.message}`);
    }
  }

  const headingText = useMemo(() => {
    if (completed) return "Session completed.";
    if (trial?.prompt) return trial.prompt;
    if (sessionId) return "Loading…";
    // return "Enter Child ID and press Start.";
  }, [completed, trial, sessionId]);

  return (
    <div className="container">
      <div className="header">
        <div>
          {/* <div className="h1">Look Where I Point</div> */}
          <div className="sub">Joint Attention • AI-assisted session</div>
        </div>

        <div className="row" style={{ gap: 10 }}>
          <button className="btn" onClick={manualSummary} disabled={!sessionId}>
            Summary
          </button>

          <button className="btn" onClick={voiceEnabled ? () => speakText(trial?.tts_text || trial?.prompt) : enableVoice} disabled={completed}>
            {voiceEnabled ? "🔊 Speak" : "🔇 Enable Voice"}
          </button>

          {/* <button className="btn" onClick={logout}>
            Logout
          </button> */}
        </div>
      </div>

      <div className="panel">
        {/* ── Start controls ── */}
        <div className="row" style={{ marginBottom: 12 }}>
          {!childId && (
            <div style={{ color: "#f59e0b", fontSize: 13 }}>
                            Select a child on the Games page first
            </div>
          )}
        </div>

        <div className="row">

          <button className="btn btnPrimary" onClick={begin} disabled={submitting}>
            {submitting ? "Working..." : "Start Session"}
          </button>

          {/* Debug only (normally auto-advances) */}
          <button
            className="btn"
            onClick={() => loadNext()}
            disabled={!sessionId || completed || submitting}
            title="Debug only (normally auto-advances)"
          >
            Next Trial
          </button>

          <button className="btn" onClick={resetRunState}>
            Reset
          </button>

          {sessionId ? (
            <span className="badge">
              Session: <b style={{ color: "rgba(255,255,255,0.92)" }}>{sessionId}</b>
            </span>
          ) : null}

          {trial?.level ? (
            <span className="badge">
              Level: <b style={{ color: "rgba(255,255,255,0.92)" }}>{trial.level}</b>
            </span>
          ) : null}
        </div>

        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 28, fontWeight: 900, letterSpacing: "-0.02em" }}>
            {headingText}
          </div>
          <div className="status">{statusText}</div>
        </div>

        {/* OPTIONS GRID */}
        {!completed && trial?.options?.length ? (
          <div className="grid">
            {trial.options.map((opt, i) => {
              const id = typeof opt === "string" ? opt : opt?.id;
              const key = id ? `${id}-${i}` : `opt-${i}`;

              return (
                <OptionCard
                  key={key}
                  option={opt}
                  highlight={!!id && trial.highlight === id}
                  disabled={!canClick}
                  onClick={onPick}
                />
              );
            })}
          </div>
        ) : null}

        <SummaryPanel data={summary} lastTrialText={lastTrialText} />

        {completed ? (
          <div className="row" style={{ marginTop: 14 }}>
            <button className="btn btnPrimary" onClick={begin}>
              Start New Session
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
