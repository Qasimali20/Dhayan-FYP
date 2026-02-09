/* Reusable skeleton loader components */

export function SkeletonCard({ height = 100 }) {
  return (
    <div
      className="skeleton skeleton-card"
      style={{ height }}
    />
  );
}

export function SkeletonText({ width = "80%", height = 14 }) {
  return (
    <div
      className="skeleton"
      style={{ height, width, borderRadius: 6 }}
    />
  );
}

export function SkeletonStatCards({ count = 4 }) {
  return (
    <div className="stats-grid">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="stat-card" style={{ padding: "20px 16px" }}>
          <div className="skeleton" style={{ width: 32, height: 32, borderRadius: "50%", margin: "0 auto 8px" }} />
          <div className="skeleton" style={{ width: "50%", height: 24, margin: "0 auto 6px", borderRadius: 6 }} />
          <div className="skeleton" style={{ width: "70%", height: 12, margin: "0 auto", borderRadius: 4 }} />
        </div>
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 6 }) {
  return (
    <div className="panel" style={{ marginTop: 20 }}>
      <div className="skeleton" style={{ width: 160, height: 20, marginBottom: 16, borderRadius: 6 }} />
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} style={{ display: "flex", gap: 12, alignItems: "center" }}>
            {Array.from({ length: cols }).map((_, j) => (
              <div
                key={j}
                className="skeleton"
                style={{
                  flex: j === 0 ? "0 0 90px" : 1,
                  height: 14,
                  borderRadius: 4,
                }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function LoadingScreen({ message = "Loading..." }) {
  return (
    <div className="loading-screen">
      <div className="spinner spinner-lg" />
      <span>{message}</span>
    </div>
  );
}
