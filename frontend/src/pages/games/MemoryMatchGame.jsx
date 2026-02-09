/**
 * MemoryMatchGame – Card-flip matching pairs game.
 * Uses the backend game engine for session/trial tracking,
 * but handles card flip logic entirely on the frontend.
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useChild } from "../../hooks/useChild";
import { startGameSession, nextGameTrial, submitGameTrial } from "../../api/games";
import SummaryPanel from "../../components/summarypanel";

// ── Card component ──────────────────────────────────────────────────────────
function Card({ card, isFlipped, isMatched, onClick, disabled }) {
  return (
    <div
      className={`memory-card ${isFlipped ? "flipped" : ""} ${isMatched ? "matched" : ""}`}
      onClick={() => !disabled && !isFlipped && !isMatched && onClick(card.id)}
    >
      <div className="memory-card-inner">
        <div className="memory-card-front">❓</div>
        <div className="memory-card-back">{card.emoji}</div>
      </div>
    </div>
  );
}

export default function MemoryMatchGamePage() {
  const navigate = useNavigate();
  const { selectedChild } = useChild();

  // Session state
  const [sessionId, setSessionId] = useState(null);
  const [trial, setTrial] = useState(null);
  const [summary, setSummary] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Board state
  const [cards, setCards] = useState([]);
  const [flippedIds, setFlippedIds] = useState([]);
  const [matchedPairs, setMatchedPairs] = useState(new Set());
  const [moves, setMoves] = useState(0);
  const [numPairs, setNumPairs] = useState(0);
  const [gridCols, setGridCols] = useState(4);
  const [lockBoard, setLockBoard] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);

  // Timer
  const [timeLeft, setTimeLeft] = useState(null);
  const timerRef = useRef(null);
  const trialStartRef = useRef(null);
  const trialRef = useRef(null);

  // Keep trial ref updated
  useEffect(() => { trialRef.current = trial; }, [trial]);

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

  // ── Countdown timer ──
  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0) return;
    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          handleTimedOut();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [timeLeft]);

  // ── Check if all pairs matched ──
  useEffect(() => {
    if (numPairs > 0 && matchedPairs.size === numPairs && trial) {
      // All pairs found! Submit success
      handleBoardComplete(true);
    }
  }, [matchedPairs, numPairs, trial]);

  // ── Start session ──
  async function handleStart() {
    if (!selectedChild) {
      setError("Please select a child from the Games page first");
      return;
    }
    setError("");
    setLoading(true);
    setSummary(null);
    try {
      const res = await startGameSession("memory_match", parseInt(selectedChild), 5);
      setSessionId(res.session?.session_id);
      if (res.first_trial && !res.first_trial.detail) {
        setupBoard(res.first_trial);
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

  // ── Setup board from trial data ──
  function setupBoard(trialData) {
    const extra = trialData.extra || {};
    const boardCards = extra.cards || [];
    const pairs = extra.num_pairs || 4;
    const cols = extra.grid_cols || 4;

    setTrial(trialData);
    setCards(boardCards);
    setNumPairs(pairs);
    setGridCols(cols);
    setFlippedIds([]);
    setMatchedPairs(new Set());
    setMoves(0);
    setLockBoard(false);
    setStatus(`Find all ${pairs} pairs!`);
    trialStartRef.current = Date.now();

    // Set timer
    const timeLimitMs = trialData.time_limit_ms || pairs * 15000;
    setTimeLeft(Math.ceil(timeLimitMs / 1000));

    speak(trialData.prompt);
  }

  // ── Handle card click ──
  function handleCardClick(cardId) {
    if (lockBoard || flippedIds.length >= 2) return;

    const newFlipped = [...flippedIds, cardId];
    setFlippedIds(newFlipped);

    if (newFlipped.length === 2) {
      setMoves((m) => m + 1);
      setLockBoard(true);

      const [first, second] = newFlipped;
      const card1 = cards.find((c) => c.id === first);
      const card2 = cards.find((c) => c.id === second);

      if (card1?.pair_id === card2?.pair_id) {
        // Match found!
        speak("Great match!");
        setTimeout(() => {
          setMatchedPairs((prev) => new Set([...prev, card1.pair_id]));
          setFlippedIds([]);
          setLockBoard(false);
        }, 600);
      } else {
        // No match — flip back after delay
        setTimeout(() => {
          setFlippedIds([]);
          setLockBoard(false);
        }, 1000);
      }
    }
  }

  // ── Board complete (all pairs found or timed out) ──
  async function handleBoardComplete(allFound) {
    if (!trialRef.current?.trial_id) return;
    setLockBoard(true);
    setTimeLeft(null);

    const elapsed = Date.now() - (trialStartRef.current || Date.now());
    // Submit as "clicked" value with encoded stats
    const submitValue = `pairs:${matchedPairs.size + (allFound ? 0 : 0)},moves:${moves},total:${numPairs}`;

    setLoading(true);
    try {
      const res = await submitGameTrial(
        "memory_match",
        trialRef.current.trial_id,
        submitValue,
        elapsed,
        false
      );

      setStatus(res.feedback || "Board complete!");
      speak(res.feedback);

      // Wait then load next trial
      setTimeout(async () => {
        if (res.session_completed && res.summary) {
          setSummary(res.summary);
          setTrial(null);
          setCards([]);
          setStatus("Session complete! 🎉");
        } else if (sessionId) {
          try {
            const next = await nextGameTrial("memory_match", sessionId);
            if (next.detail) {
              if (next.summary) setSummary(next.summary);
              setTrial(null);
              setCards([]);
              setStatus("Session complete! 🎉");
            } else {
              setupBoard(next);
            }
          } catch (err) {
            setError(err.message || "Failed to get next trial");
          }
        }
        setLoading(false);
      }, 2000);
    } catch (err) {
      setError(err.message || "Failed to submit");
      setLoading(false);
    }
  }

  // ── Timed out ──
  function handleTimedOut() {
    if (!trialRef.current?.trial_id) return;
    setLockBoard(true);

    const elapsed = Date.now() - (trialStartRef.current || Date.now());
    const submitValue = `pairs:${matchedPairs.size},moves:${moves},total:${numPairs}`;

    setLoading(true);
    submitGameTrial("memory_match", trialRef.current.trial_id, submitValue, elapsed, true)
      .then((res) => {
        setStatus(res.feedback || "⏰ Time's up!");
        speak(res.feedback);

        setTimeout(async () => {
          if (res.session_completed && res.summary) {
            setSummary(res.summary);
            setTrial(null);
            setCards([]);
            setStatus("Session complete! 🎉");
          } else if (sessionId) {
            try {
              const next = await nextGameTrial("memory_match", sessionId);
              if (next.detail) {
                if (next.summary) setSummary(next.summary);
                setTrial(null);
                setCards([]);
                setStatus("Session complete! 🎉");
              } else {
                setupBoard(next);
              }
            } catch {}
          }
          setLoading(false);
        }, 2500);
      })
      .catch((err) => {
        setError(err.message || "Failed to submit");
        setLoading(false);
      });
  }

  // ── Reset ──
  function handleReset() {
    setSessionId(null);
    setTrial(null);
    setSummary(null);
    setCards([]);
    setFlippedIds([]);
    setMatchedPairs(new Set());
    setMoves(0);
    setTimeLeft(null);
    setStatus("");
    setError("");
    setLockBoard(false);
  }

  // ── Render ────────────────────────────────────────────────────────────────
  if (summary) {
    return (
      <div className="container">
        <div className="header">
          <div className="h1">🃏 Memory Match — Complete!</div>
        </div>
        <SummaryPanel data={summary} onBack={() => navigate("/games")} />
        <button className="btn btnPrimary" onClick={handleReset} style={{ marginTop: 16 }}>
          🔄 Play Again
        </button>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="h1">🃏 Memory Match</div>
          <div className="sub">{status || "Flip cards and find matching pairs!"}</div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button
            className={`btn ${voiceEnabled ? "btnPrimary" : ""}`}
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            title="Toggle voice"
          >
            {voiceEnabled ? "🔊" : "🔇"}
          </button>
          {trial && (
            <button className="btn" onClick={handleReset}>
              ✖ Quit
            </button>
          )}
          <button className="btn" onClick={() => navigate("/games")}>
            ← Back
          </button>
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      {!trial && !loading && (
        <div className="panel" style={{ textAlign: "center", padding: 40 }}>
          <div style={{ fontSize: 64, marginBottom: 16 }}>🃏</div>
          <h2>Memory Match</h2>
          <p style={{ color: "#94a3b8", marginBottom: 20 }}>
            Flip cards and find matching pairs! Trains visual memory and concentration.
          </p>
          <button className="btn btnPrimary btn-lg" onClick={handleStart}>
            ▶ Start Game
          </button>
        </div>
      )}

      {loading && !trial && (
        <div className="panel" style={{ textAlign: "center", padding: 40 }}>
          <div className="loader" />
          <p>Loading...</p>
        </div>
      )}

      {trial && cards.length > 0 && (
        <>
          {/* Stats bar */}
          <div
            className="panel"
            style={{
              display: "flex",
              justifyContent: "space-around",
              padding: "12px 20px",
              marginBottom: 16,
            }}
          >
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 12, color: "#94a3b8" }}>Pairs Found</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>
                {matchedPairs.size}/{numPairs}
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 12, color: "#94a3b8" }}>Moves</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{moves}</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 12, color: "#94a3b8" }}>Time Left</div>
              <div
                style={{
                  fontSize: 24,
                  fontWeight: 700,
                  color: timeLeft && timeLeft < 10 ? "#ef4444" : "inherit",
                }}
              >
                {timeLeft != null ? `${timeLeft}s` : "--"}
              </div>
            </div>
          </div>

          {/* Card grid */}
          <div
            className="memory-grid"
            style={{
              display: "grid",
              gridTemplateColumns: `repeat(${gridCols}, 1fr)`,
              gap: 12,
              maxWidth: gridCols * 110,
              margin: "0 auto",
            }}
          >
            {cards.map((card) => (
              <Card
                key={card.id}
                card={card}
                isFlipped={flippedIds.includes(card.id)}
                isMatched={matchedPairs.has(card.pair_id)}
                onClick={handleCardClick}
                disabled={lockBoard || loading}
              />
            ))}
          </div>

          {/* Prompt / hint */}
          {trial.ai_hint && (
            <div
              className="panel"
              style={{
                marginTop: 16,
                padding: "10px 16px",
                textAlign: "center",
                color: "#94a3b8",
                fontSize: 14,
              }}
            >
              💡 {trial.ai_hint}
            </div>
          )}
        </>
      )}
    </div>
  );
}
