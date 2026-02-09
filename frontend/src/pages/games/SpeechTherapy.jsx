import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { useChild } from "../../hooks/useChild";
import { getToken } from "../../api/client";
import {
  getSpeechActivities,
  startSpeechSession,
  uploadSpeechAudio,
  getSpeechAnalysis,
  scoreSpeechTrial,
  getSpeechSessionSummary,
} from "../../api/speech";

// ─── Constants ──────────────────────────────────────────────────────────────

const PROMPT_LEVEL_LABELS = [
  "L0 — Full Model",
  "L1 — Partial Model",
  "L2 — Gestural/Visual",
  "L3 — Independent",
];

const PROMPT_LEVEL_SHORT = ["Full Model", "Partial", "Visual", "Independent"];

const SEVERITY_COLORS = {
  info: "#10b981",
  warning: "#f59e0b",
  concern: "#ef4444",
};

const CATEGORY_ICONS = {
  repetition: "🗣️",
  picture_naming: "🖼️",
  questions: "❓",
  story_retell: "📖",
  category_naming: "🧠",
};

// ─── TTS Hook ────────────────────────────────────────────────────────────────

function useTextToSpeech() {
  const [enabled, setEnabled] = useState(true);
  const [speaking, setSpeaking] = useState(false);
  const supported = typeof window !== "undefined" && "speechSynthesis" in window;

  const speak = useCallback(
    (text, opts = {}) => {
      if (!supported || !text) return;
      try {
        window.speechSynthesis.cancel();
        const cleaned = text.replace(/[^\w\s!?.,'":\-()]/g, "");
        const u = new SpeechSynthesisUtterance(cleaned);
        u.rate = opts.rate ?? 0.85;
        u.pitch = opts.pitch ?? 1.1;
        u.lang = opts.lang ?? "en-US";
        u.volume = opts.volume ?? 1.0;

        // Try to pick a child-friendly voice
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(
          (v) => v.lang.startsWith("en") && v.name.toLowerCase().includes("female")
        );
        if (preferred) u.voice = preferred;

        u.onstart = () => setSpeaking(true);
        u.onend = () => setSpeaking(false);
        u.onerror = () => setSpeaking(false);

        window.speechSynthesis.speak(u);
      } catch {
        setSpeaking(false);
      }
    },
    [supported]
  );

  const stop = useCallback(() => {
    if (supported) window.speechSynthesis.cancel();
    setSpeaking(false);
  }, [supported]);

  return { speak, stop, speaking, enabled, setEnabled, supported };
}

// ─── Component ──────────────────────────────────────────────────────────────

export default function SpeechTherapy() {
  const nav = useNavigate();
  const { user } = useAuth();
  const { selectedChild, childProfile } = useChild();
  const tts = useTextToSpeech();
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Setup state
  const [activities, setActivities] = useState([]);
  const [selectedActivity, setSelectedActivity] = useState("");
  const [trialsPlanned, setTrialsPlanned] = useState(5);
  const [promptLevel, setPromptLevel] = useState(0);

  // Session state
  const [session, setSession] = useState(null);
  const [currentTrialIndex, setCurrentTrialIndex] = useState(0);
  const [phase, setPhase] = useState("setup");

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);

  // Analysis state
  const [analysis, setAnalysis] = useState(null);
  const [analysisPolling, setAnalysisPolling] = useState(false);

  // Summary state
  const [summary, setSummary] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Auth guard
  useEffect(() => {
    if (!getToken()) nav("/login");
  }, [nav]);

  // Load activities
  useEffect(() => {
    async function load() {
      try {
        const a = await getSpeechActivities();
        setActivities(Array.isArray(a) ? a : []);
      } catch {}
    }
    load();
  }, []);

  // Recording timer
  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => setRecordingTime((t) => t + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  // ─── Derived ─────────────────────────────────────────────────────────

  const currentTrial = session?.trials?.[currentTrialIndex];
  const currentActivity = activities.find((a) => a.id === Number(selectedActivity));

  // ─── TTS: auto-speak prompt when trial becomes active ────────────────

  useEffect(() => {
    if (phase === "active" && currentTrial && tts.enabled) {
      const text = currentTrial.prompt || currentTrial.target_text || "";
      if (text) {
        const timer = setTimeout(() => tts.speak(text), 400);
        return () => clearTimeout(timer);
      }
    }
  }, [phase, currentTrialIndex, currentTrial, tts.enabled]); // eslint-disable-line

  // ─── Handlers ─────────────────────────────────────────────────────────

  async function handleStartSession() {
    if (!selectedChild) {
      setError("Select a child on the Games page first");
      return;
    }
    if (!selectedActivity) {
      setError("Select an activity");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await startSpeechSession({
        child_id: Number(selectedChild),
        activity_id: Number(selectedActivity),
        trials_planned: trialsPlanned,
        prompt_level: promptLevel,
      });
      setSession(res);
      setCurrentTrialIndex(0);
      setPhase("active");
    } catch (e) {
      setError(e.message || "Failed to start session");
    } finally {
      setLoading(false);
    }
  }

  async function handleStartRecording() {
    setError("");
    setAudioBlob(null);
    setAudioUrl(null);
    setRecordingTime(0);
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((t) => t.stop());
        setPhase("processing");
      };

      recorder.start(250);
      setIsRecording(true);
      setPhase("recording");
    } catch (e) {
      setError("Microphone access denied. Please allow microphone permissions.");
    }
  }

  function handleStopRecording() {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }

  async function handleUploadAndAnalyze() {
    if (!audioBlob || !currentTrial) return;
    setLoading(true);
    setError("");
    setAnalysis(null);

    try {
      const file = new File([audioBlob], `trial_${currentTrial.trial_id}.webm`, {
        type: "audio/webm",
      });
      await uploadSpeechAudio(currentTrial.trial_id, file, recordingTime * 1000);

      setAnalysisPolling(true);
      let attempts = 0;
      const maxAttempts = 30;

      const poll = setInterval(async () => {
        attempts++;
        try {
          const res = await getSpeechAnalysis(currentTrial.trial_id);
          if (
            res.analysis?.processing_status === "done" ||
            res.analysis?.processing_status === "failed"
          ) {
            clearInterval(poll);
            setAnalysis(res);
            setAnalysisPolling(false);
            setPhase("scoring");
            setLoading(false);
          }
        } catch {}
        if (attempts >= maxAttempts) {
          clearInterval(poll);
          setAnalysisPolling(false);
          setPhase("scoring");
          setLoading(false);
        }
      }, 2000);
    } catch (e) {
      setError(e.message || "Upload failed");
      setLoading(false);
    }
  }

  async function handleScore(score) {
    if (!currentTrial) return;
    setLoading(true);
    try {
      const res = await scoreSpeechTrial(currentTrial.trial_id, { score });

      if (res.session_complete || currentTrialIndex >= session.trials.length - 1) {
        const sum = await getSpeechSessionSummary(session.session_id);
        setSummary(sum);
        setPhase("summary");
      } else {
        setCurrentTrialIndex((i) => i + 1);
        setAudioBlob(null);
        setAudioUrl(null);
        setAnalysis(null);
        setRecordingTime(0);
        setPhase("active");
      }
    } catch (e) {
      setError(e.message || "Scoring failed");
    } finally {
      setLoading(false);
    }
  }

  function handleNewSession() {
    tts.stop();
    setSession(null);
    setSummary(null);
    setAnalysis(null);
    setAudioBlob(null);
    setAudioUrl(null);
    setCurrentTrialIndex(0);
    setPhase("setup");
    setError("");
  }

  const progressPct = session
    ? Math.round(((currentTrialIndex + (phase === "scoring" ? 1 : 0)) / session.trials.length) * 100)
    : 0;

  // ─── Render ───────────────────────────────────────────────────────────

  return (
    <div className="container">
      {/* Header */}
      <div className="header">
        <div>
          <div className="h1">🗣️ Speech Therapy</div>
          <div className="sub">
            AI-powered speech analysis with voice prompts for children
          </div>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <button
            className={`btn ${tts.enabled ? "btnPrimary" : ""}`}
            onClick={() => tts.setEnabled(!tts.enabled)}
            title={tts.enabled ? "Voice prompts ON" : "Voice prompts OFF"}
          >
            {tts.enabled ? "🔊 Voice On" : "🔇 Voice Off"}
          </button>
          {session && (
            <button className="btn" onClick={handleNewSession}>
              🔄 Reset
            </button>
          )}
          <button className="btn" onClick={() => nav("/dashboard")}>
            ← Back
          </button>
        </div>
      </div>

      {/* Child Info Bar */}
      {childProfile && (
        <div style={{
          padding: "8px 16px", borderRadius: 8, marginBottom: 12,
          background: "rgba(99,102,241,0.1)", display: "flex", alignItems: "center", gap: 8,
          fontSize: 13,
        }}>
          <span>👶</span>
          <strong>{childProfile.full_name || childProfile.user?.full_name || `Child #${childProfile.id}`}</strong>
          {session && (
            <>
              <span style={{ opacity: 0.4 }}>|</span>
              <span>{session.activity?.name}</span>
              <span style={{ opacity: 0.4 }}>|</span>
              <span>Prompt {PROMPT_LEVEL_SHORT[promptLevel]}</span>
            </>
          )}
        </div>
      )}

      {error && (
        <div className="panel" style={{ background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.3)", padding: "10px 16px" }}>
          <p style={{ color: "#ef4444", margin: 0 }}>⚠️ {error}</p>
        </div>
      )}

      {/* ══════════ SETUP PHASE ══════════ */}
      {phase === "setup" && (
        <div className="panel" style={{ maxWidth: 680 }}>
          <h3 style={{ margin: "0 0 16px 0" }}>📋 Session Setup</h3>

          {!selectedChild && (
            <div style={{
              padding: 12, marginBottom: 16, borderRadius: 8,
              background: "rgba(245,158,11,0.12)", border: "1px solid rgba(245,158,11,0.3)",
              color: "#f59e0b", fontSize: 14,
            }}>
              ⚠️ Please select a child from the <strong>Games</strong> page first.
            </div>
          )}

          {/* Activity Grid */}
          <label className="sub" style={{ display: "block", marginBottom: 8 }}>Choose Activity</label>
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))",
            gap: 8, marginBottom: 16,
          }}>
            {activities.map((a) => {
              const isSelected = String(a.id) === String(selectedActivity);
              const icon = CATEGORY_ICONS[a.category] || "🎯";
              return (
                <div
                  key={a.id}
                  onClick={() => setSelectedActivity(String(a.id))}
                  style={{
                    padding: "12px 10px", borderRadius: 10, cursor: "pointer",
                    background: isSelected ? "rgba(99,102,241,0.25)" : "rgba(255,255,255,0.04)",
                    border: isSelected ? "2px solid rgba(99,102,241,0.6)" : "2px solid transparent",
                    textAlign: "center", transition: "all 0.15s",
                  }}
                >
                  <div style={{ fontSize: 26, marginBottom: 4 }}>{icon}</div>
                  <div style={{ fontSize: 12, fontWeight: 600, lineHeight: 1.3 }}>{a.name}</div>
                  <div style={{ fontSize: 10, opacity: 0.5, marginTop: 2 }}>L{a.difficulty_level}</div>
                </div>
              );
            })}
          </div>

          {/* Settings Row */}
          <div className="row" style={{ gap: 12, marginBottom: 16 }}>
            <div style={{ flex: 1 }}>
              <label className="sub" style={{ display: "block", marginBottom: 4 }}>Trials</label>
              <input
                className="input"
                type="number"
                min={1} max={20}
                value={trialsPlanned}
                onChange={(e) => setTrialsPlanned(Number(e.target.value))}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label className="sub" style={{ display: "block", marginBottom: 4 }}>Prompt Level</label>
              <select
                className="input"
                value={promptLevel}
                onChange={(e) => setPromptLevel(Number(e.target.value))}
              >
                {PROMPT_LEVEL_LABELS.map((label, i) => (
                  <option key={i} value={i}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Activity Detail Preview */}
          {currentActivity && (
            <div style={{
              padding: 14, background: "rgba(99,102,241,0.08)", borderRadius: 10,
              marginBottom: 16, borderLeft: "3px solid rgba(99,102,241,0.5)",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <span style={{ fontSize: 22 }}>{CATEGORY_ICONS[currentActivity.category] || "🎯"}</span>
                <strong>{currentActivity.name}</strong>
              </div>
              <p style={{ margin: "4px 0 0", fontSize: 13, opacity: 0.8, lineHeight: 1.5 }}>
                {currentActivity.description}
              </p>
              {currentActivity.prompt_levels?.[promptLevel] && (
                <p style={{ margin: "6px 0 0", fontSize: 12, color: "#818cf8" }}>
                  📌 {currentActivity.prompt_levels[promptLevel].instruction}
                </p>
              )}
            </div>
          )}

          <button
            className="btn btnPrimary"
            style={{ width: "100%", padding: "14px", fontSize: 16 }}
            onClick={handleStartSession}
            disabled={loading || !selectedChild || !selectedActivity}
          >
            {loading ? "Starting..." : "▶ Start Speech Session"}
          </button>
        </div>
      )}

      {/* ══════════ ACTIVE / RECORDING PHASE ══════════ */}
      {(phase === "active" || phase === "recording") && session && currentTrial && (
        <div className="panel" style={{ maxWidth: 620 }}>
          {/* Progress Bar */}
          <div style={{
            height: 4, borderRadius: 2, background: "rgba(255,255,255,0.08)",
            marginBottom: 16, overflow: "hidden",
          }}>
            <div style={{
              height: "100%", width: `${progressPct}%`,
              background: "linear-gradient(90deg, #6366f1, #8b5cf6)",
              transition: "width 0.3s",
            }} />
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ margin: 0 }}>
              Trial {currentTrialIndex + 1} / {session.trials.length}
            </h3>
            <span className="sub" style={{ fontSize: 12 }}>
              {session.activity?.name} • {PROMPT_LEVEL_SHORT[promptLevel]}
            </span>
          </div>

          {/* Prompt Card */}
          <div style={{
            padding: "28px 20px", borderRadius: 14,
            background: "linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.1) 100%)",
            border: "1px solid rgba(99,102,241,0.2)",
            textAlign: "center", marginBottom: 16, position: "relative",
          }}>
            {/* Speak button */}
            <button
              onClick={() => tts.speak(currentTrial.prompt || currentTrial.target_text)}
              style={{
                position: "absolute", top: 10, right: 10,
                background: tts.speaking ? "rgba(99,102,241,0.4)" : "rgba(255,255,255,0.08)",
                border: "none", borderRadius: 8, padding: "6px 10px", cursor: "pointer",
                color: "#e2e8f0", fontSize: 16,
                animation: tts.speaking ? "pulse 1s infinite" : "none",
              }}
              title="Speak prompt aloud"
            >
              {tts.speaking ? "🔊" : "🔈"}
            </button>

            <div style={{ fontSize: 22, fontWeight: 600, marginBottom: 8, lineHeight: 1.4 }}>
              {currentTrial.prompt || session.activity?.name}
            </div>
            {currentTrial.target_text && (
              <div style={{
                fontSize: 32, fontWeight: 700,
                background: "linear-gradient(135deg, #818cf8, #a78bfa)",
                WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
                marginTop: 4,
              }}>
                "{currentTrial.target_text}"
              </div>
            )}
          </div>

          {/* Recording Controls */}
          {phase === "active" && (
            <button
              className="btn btnPrimary"
              style={{
                width: "100%", padding: "16px", fontSize: 18,
                display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
              }}
              onClick={handleStartRecording}
            >
              🎙️ Start Recording
            </button>
          )}

          {phase === "recording" && (
            <div style={{ textAlign: "center" }}>
              <div style={{
                width: 80, height: 80, borderRadius: "50%", margin: "0 auto 16px",
                background: "rgba(239,68,68,0.2)", border: "3px solid rgba(239,68,68,0.6)",
                display: "flex", alignItems: "center", justifyContent: "center",
                animation: "pulse 1.5s ease-in-out infinite",
              }}>
                <span style={{ fontSize: 36 }}>🎙️</span>
              </div>
              <div style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>
                {recordingTime}s
              </div>
              <div style={{ fontSize: 13, opacity: 0.6, marginBottom: 16 }}>Recording...</div>
              <button
                className="btn"
                style={{
                  width: "100%", padding: "14px", fontSize: 16,
                  background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.4)",
                }}
                onClick={handleStopRecording}
              >
                ⏹️ Stop Recording
              </button>
            </div>
          )}
        </div>
      )}

      {/* ══════════ PROCESSING / REVIEW PHASE ══════════ */}
      {phase === "processing" && (
        <div className="panel" style={{ maxWidth: 620, textAlign: "center" }}>
          <h3 style={{ marginBottom: 16 }}>🎧 Review Recording</h3>

          {audioUrl && (
            <audio controls src={audioUrl} style={{ width: "100%", marginBottom: 16 }} />
          )}

          <div style={{ display: "flex", gap: 12 }}>
            <button
              className="btn"
              style={{ flex: 1, background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)" }}
              onClick={() => { setPhase("active"); setAudioBlob(null); setAudioUrl(null); }}
            >
              🔄 Re-record
            </button>
            <button
              className="btn btnPrimary"
              style={{ flex: 1 }}
              onClick={handleUploadAndAnalyze}
              disabled={loading}
            >
              {loading ? "⏳ Analyzing..." : "📤 Upload & Analyze"}
            </button>
          </div>
        </div>
      )}

      {/* ══════════ SCORING PHASE — Results ══════════ */}
      {phase === "scoring" && (
        <div className="panel" style={{ maxWidth: 720 }}>
          <div style={{
            height: 4, borderRadius: 2, background: "rgba(255,255,255,0.08)",
            marginBottom: 16, overflow: "hidden",
          }}>
            <div style={{
              height: "100%", width: `${progressPct}%`,
              background: "linear-gradient(90deg, #6366f1, #8b5cf6)",
              transition: "width 0.3s",
            }} />
          </div>

          <h3 style={{ marginBottom: 16 }}>
            📊 Trial {currentTrialIndex + 1} Results
          </h3>

          {audioUrl && (
            <audio controls src={audioUrl} style={{ width: "100%", marginBottom: 12 }} />
          )}

          {/* Transcript */}
          {analysis?.analysis && (
            <div style={{ marginBottom: 16 }}>
              <label className="sub" style={{ display: "block", marginBottom: 6 }}>Transcript</label>
              <div style={{
                padding: "14px 16px", borderRadius: 10,
                background: "rgba(255,255,255,0.05)",
                fontSize: 17, lineHeight: 1.5,
                fontStyle: analysis.analysis.transcript_text ? "normal" : "italic",
                borderLeft: "3px solid rgba(99,102,241,0.5)",
              }}>
                {analysis.analysis.transcript_text || "No speech detected"}
              </div>
              {analysis.analysis.transcript_text && (
                <button
                  className="btn"
                  style={{ marginTop: 6, padding: "4px 12px", fontSize: 12 }}
                  onClick={() => tts.speak(analysis.analysis.transcript_text)}
                >
                  🔊 Play Back Transcript
                </button>
              )}
            </div>
          )}

          {/* Speech Metrics */}
          {analysis?.analysis?.features_json && (
            <div style={{ marginBottom: 16 }}>
              <label className="sub" style={{ display: "block", marginBottom: 8 }}>Speech Metrics</label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                <MetricCard label="Words" value={analysis.analysis.features_json.word_count || 0} />
                <MetricCard label="Speech Rate" value={`${Math.round(analysis.analysis.features_json.estimated_speech_rate_wpm || 0)} wpm`} />
                <MetricCard label="Pause Ratio" value={`${Math.round((analysis.analysis.features_json.pause_ratio || 0) * 100)}%`} />
                <MetricCard label="Duration" value={`${((analysis.analysis.features_json.duration_ms || 0) / 1000).toFixed(1)}s`} />
                <MetricCard label="Pauses" value={analysis.analysis.features_json.pause_count || 0} />
                <MetricCard label="Latency" value={`${((analysis.analysis.features_json.response_latency_ms || 0) / 1000).toFixed(1)}s`} />
              </div>
            </div>
          )}

          {/* Target Score */}
          {analysis?.analysis?.target_score_json?.keyword_match !== undefined && (
            <div style={{ marginBottom: 16 }}>
              <label className="sub" style={{ display: "block", marginBottom: 8 }}>Target Match</label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                <MetricCard
                  label="Keyword Match"
                  value={`${Math.round(analysis.analysis.target_score_json.keyword_match * 100)}%`}
                  color={analysis.analysis.target_score_json.keyword_match >= 0.8 ? "#10b981" : "#f59e0b"}
                />
                <MetricCard
                  label="Similarity"
                  value={`${Math.round(analysis.analysis.target_score_json.text_similarity * 100)}%`}
                />
                <MetricCard
                  label="Exact Match"
                  value={analysis.analysis.target_score_json.exact_match ? "✅" : "❌"}
                />
              </div>
              {analysis.analysis.target_score_json.missing_keywords?.length > 0 && (
                <div style={{ marginTop: 8, fontSize: 13, color: "#f59e0b" }}>
                  Missing: {analysis.analysis.target_score_json.missing_keywords.join(", ")}
                </div>
              )}
            </div>
          )}

          {/* AI Feedback */}
          {analysis?.analysis?.feedback_json?.suggestions?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <label className="sub" style={{ display: "block", marginBottom: 8 }}>
                💡 AI Suggestions
                <span style={{
                  marginLeft: 8, padding: "2px 8px", borderRadius: 12, fontSize: 11,
                  background: (SEVERITY_COLORS[analysis.analysis.feedback_json.severity] || "#10b981") + "30",
                  color: SEVERITY_COLORS[analysis.analysis.feedback_json.severity] || "#10b981",
                }}>
                  {analysis.analysis.feedback_json.severity}
                </span>
              </label>
              {analysis.analysis.feedback_json.suggestions.map((s, i) => (
                <div key={i} style={{
                  padding: 12, marginBottom: 6, borderRadius: 10,
                  background: "rgba(255,255,255,0.03)",
                  borderLeft: "3px solid #818cf8",
                }}>
                  <div style={{ fontSize: 14, fontWeight: 500 }}>{s.message}</div>
                  {s.action && (
                    <div style={{ fontSize: 12, marginTop: 6, opacity: 0.65 }}>
                      👉 {s.action}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Therapist Scoring */}
          <div style={{ marginTop: 16 }}>
            <label className="sub" style={{ display: "block", marginBottom: 8 }}>Therapist Score</label>
            <div style={{ display: "flex", gap: 10 }}>
              {[
                { score: "success", label: "✅ Success", bg: "16,185,129" },
                { score: "partial", label: "⚡ Partial", bg: "245,158,11" },
                { score: "fail", label: "❌ Fail", bg: "239,68,68" },
              ].map(({ score, label, bg }) => (
                <button
                  key={score}
                  className="btn"
                  style={{
                    flex: 1, padding: 14, fontSize: 16,
                    background: `rgba(${bg},0.12)`, border: `1px solid rgba(${bg},0.35)`,
                  }}
                  onClick={() => handleScore(score)}
                  disabled={loading}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ══════════ SUMMARY PHASE ══════════ */}
      {phase === "summary" && summary && (
        <div className="panel" style={{ maxWidth: 640 }}>
          <h3 style={{ margin: "0 0 16px 0" }}>📋 Session Summary</h3>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
            <MetricCard label="Total Trials" value={summary.total_completed} />
            <MetricCard label="Correct" value={summary.correct} color="#10b981" />
            <MetricCard
              label="Accuracy"
              value={`${Math.round((summary.accuracy || 0) * 100)}%`}
              color={summary.accuracy >= 0.7 ? "#10b981" : summary.accuracy >= 0.4 ? "#f59e0b" : "#ef4444"}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            {summary.trials?.map((t, i) => (
              <div key={t.trial_id} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "10px 12px", borderRadius: 8, marginBottom: 4,
                background: "rgba(255,255,255,0.03)",
              }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>Trial {i + 1}</span>
                <span style={{ fontSize: 12, opacity: 0.6, flex: 1, margin: "0 12px", textAlign: "center" }}>
                  {t.target_text || "—"}
                </span>
                <span style={{ fontSize: 12, opacity: 0.6, flex: 1, textAlign: "center" }}>
                  {t.transcript || "—"}
                </span>
                <span style={{
                  padding: "3px 12px", borderRadius: 12, fontSize: 12, fontWeight: 500,
                  background:
                    t.therapist_score === "success" ? "rgba(16,185,129,0.2)" :
                    t.therapist_score === "partial" ? "rgba(245,158,11,0.2)" :
                    "rgba(239,68,68,0.2)",
                  color:
                    t.therapist_score === "success" ? "#10b981" :
                    t.therapist_score === "partial" ? "#f59e0b" :
                    "#ef4444",
                }}>
                  {t.therapist_score || t.status}
                </span>
              </div>
            ))}
          </div>

          <button
            className="btn btnPrimary"
            style={{ width: "100%", padding: "14px", fontSize: 16 }}
            onClick={handleNewSession}
          >
            🔄 Start New Session
          </button>
        </div>
      )}

      {/* Analysis Loading Indicator */}
      {analysisPolling && (
        <div style={{
          position: "fixed", bottom: 20, right: 20, padding: "12px 20px",
          background: "rgba(99,102,241,0.95)", borderRadius: 12, color: "#fff",
          fontSize: 14, fontWeight: 500, boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
        }}>
          ⏳ Analyzing speech...
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }) {
  return (
    <div style={{
      padding: 12, borderRadius: 10, textAlign: "center",
      background: "rgba(255,255,255,0.04)",
    }}>
      <div style={{ fontSize: 22, fontWeight: 700, color: color || "#e2e8f0" }}>
        {value}
      </div>
      <div style={{ fontSize: 11, opacity: 0.55, marginTop: 2 }}>{label}</div>
    </div>
  );
}
