import Confetti from "./Confetti";
import ProgressRing from "./ProgressRing";
import { useState, useEffect } from "react";

export default function SummaryPanel({ data, lastTrialText }) {
  const [showConfetti, setShowConfetti] = useState(false);

  const accNum =
    typeof data?.accuracy === "string"
      ? parseFloat(data.accuracy)
      : typeof data?.accuracy === "number"
      ? data.accuracy
      : 0;
  const accPct = accNum > 1 ? accNum : Math.round(accNum * 100);
  const isGood = accPct >= 70;

  useEffect(() => {
    if (data && isGood) setShowConfetti(true);
  }, [data]);

  if (!data) return null;

  const heading =
    accPct >= 90
      ? "Outstanding!"
      : accPct >= 70
      ? "Great Job!"
      : accPct >= 50
      ? "Good Effort!"
      : "Keep Practicing!";

  const detailRows = [
    ["Total Trials", data.total_trials ?? "—"],
    ["Correct", data.correct ?? "—"],
    ["Avg Response Time", data.avg_response_time_ms ? `${data.avg_response_time_ms}ms` : "—"],
    ["Level", data.current_level ?? "—"],
  ];

  return (
    <div className="celebration-panel" style={{ marginTop: 16, animation: "feedbackIn .5s var(--ease-out)" }}>
      {showConfetti && <Confetti duration={4000} />}

      <div style={{ textAlign: "center", marginBottom: 16 }}>
        <div style={{ fontSize: 42, marginBottom: 8 }}>
          {accPct >= 90 ? "🏆" : accPct >= 70 ? "🌟" : accPct >= 50 ? "👍" : "💪"}
        </div>
        <div style={{ fontSize: 22, fontWeight: 800 }}>{heading}</div>
        {data.suggestion && (
          <div style={{ color: "var(--muted)", fontSize: 13, marginTop: 6, maxWidth: 360, margin: "6px auto 0" }}>
            {data.suggestion}
          </div>
        )}
      </div>

      {/* Accuracy Ring */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 16 }}>
        <ProgressRing
          value={accPct}
          size={100}
          strokeWidth={9}
          color={accPct >= 80 ? "#10b981" : accPct >= 50 ? "#f59e0b" : "#ef4444"}
        />
      </div>

      {/* Stats row */}
      <div className="stats-grid" style={{ marginBottom: 12 }}>
        {detailRows.map(([k, v]) => (
          <div className="stat-card" key={k} style={{ padding: "10px 8px" }}>
            <div className="stat-value" style={{ fontSize: 18 }}>{v}</div>
            <div className="stat-label">{k}</div>
          </div>
        ))}
      </div>

      {lastTrialText && (
        <div className="badge" style={{ marginTop: 8, textAlign: "center" }}>
          <span>Last Trial:</span>{" "}
          <b style={{ color: "rgba(255,255,255,0.9)" }}>{lastTrialText}</b>
        </div>
      )}
    </div>
  );
}
