export default function SummaryPanel({ data, lastTrialText }) {
  if (!data) return null;

  const rows = [
    ["Session ID", data.session_id ?? "—"],
    ["Status", data.status ?? "—"],
    ["Total Trials", data.total_trials ?? "—"],
    ["Completed Trials", data.completed_trials ?? "—"],
    ["Correct", data.correct ?? "—"],
    ["Accuracy", data.accuracy ?? "—"],
    ["Avg Response Time (ms)", data.avg_response_time_ms ?? "—"],
    ["Current Level", data.current_level ?? "—"],
    ["Suggestion", data.suggestion || "—"],
  ];

  return (
    <div className="summary" style={{ marginTop: 16 }}>
      <h3>Session Summary</h3>

      {lastTrialText ? (
        <div className="badge" style={{ marginBottom: 10 }}>
          <span>Last Trial:</span>{" "}
          <b style={{ color: "rgba(255,255,255,0.9)" }}>{lastTrialText}</b>
        </div>
      ) : null}

      <div className="summaryGrid">
        {rows.map(([k, v]) => (
          <div key={k} style={{ display: "contents" }}>
            <div className="k">{k}</div>
            <div className="v">{String(v)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
