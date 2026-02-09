import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useChild, ChildSelector } from "../hooks/useChild";

const GAMES = [
  {
    code: "ja",
    path: "/games/ja",
    name: "Joint Attention",
    icon: "👀",
    description: "Practice looking where someone points. Builds shared attention and social engagement skills.",
    color: "rgba(99, 102, 241, 0.25)",
    border: "rgba(99, 102, 241, 0.4)",
    skills: ["Social Engagement", "Shared Attention", "Following Gaze"],
  },
  {
    code: "matching",
    path: "/games/matching",
    name: "Shape Matching",
    icon: "🔷",
    description: "Match identical shapes and objects. Builds visual discrimination and categorization skills.",
    color: "rgba(16, 185, 129, 0.25)",
    border: "rgba(16, 185, 129, 0.4)",
    skills: ["Visual Discrimination", "Matching", "Pattern Recognition"],
  },
  {
    code: "memory_match",
    path: "/games/memory-match",
    name: "Memory Match",
    icon: "🃏",
    description: "Flip cards and find matching pairs! Builds visual memory, concentration, and recall skills.",
    color: "rgba(236, 72, 153, 0.25)",
    border: "rgba(236, 72, 153, 0.4)",
    skills: ["Visual Memory", "Concentration", "Pattern Recall"],
  },
  {
    code: "object_discovery",
    path: "/games/object-discovery",
    name: "Object Discovery",
    icon: "🔍",
    description: "Find and categorize objects by type. Builds receptive language and vocabulary.",
    color: "rgba(245, 158, 11, 0.25)",
    border: "rgba(245, 158, 11, 0.4)",
    skills: ["Receptive Language", "Categorization", "Vocabulary"],
  },
  {
    code: "problem_solving",
    path: "/games/problem-solving",
    name: "Problem Solving",
    icon: "🧩",
    description: "Complete patterns and sequences. Builds logical thinking and executive function.",
    color: "rgba(239, 68, 68, 0.25)",
    border: "rgba(239, 68, 68, 0.4)",
    skills: ["Pattern Logic", "Sequencing", "Executive Function"],
  },
];

export default function GameRouter() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { childProfile } = useChild();

  return (
    <div className="container">
      <div className="header">
        <div>
          <div className="h1">🎮 Therapy Games</div>
          <div className="sub">
            Select a child below, then choose a game. The child stays selected across all games.
          </div>
        </div>
      </div>

      {/* Global Child Selector */}
      <div className="panel" style={{ marginBottom: 20, padding: "12px 16px" }}>
        <ChildSelector />
      </div>

      <div className="game-grid">
        {GAMES.map((game) => (
          <div
            key={game.code}
            className="game-card"
            style={{ background: game.color, borderColor: game.border }}
            onClick={() => navigate(game.path)}
          >
            <div className="game-icon">{game.icon}</div>
            <div className="game-name">{game.name}</div>
            <div className="game-desc">{game.description}</div>
            <div className="game-skills">
              {game.skills.map((s) => (
                <span key={s} className="skill-tag">{s}</span>
              ))}
            </div>
            <button className="btn btnPrimary" style={{ marginTop: 12, width: "100%" }}>
              ▶ Start Game
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
