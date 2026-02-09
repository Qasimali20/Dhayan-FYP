"""
Memory Match Plugin – Matching Pairs / Card Flip Game
ABA Level 1-3: Visual memory, working memory, pattern recognition.

Mechanics:
  - Grid of face-down cards (pairs of emojis)
  - Child flips two cards at a time; if they match, they stay revealed
  - Adaptive difficulty: more pairs at higher levels
  - Backend tracks the board, flips, and evaluates pair matches

Unlike other games this is multi-step per trial:
  The backend generates a board (one trial = one full board).
  The frontend handles flipping logic client-side, then submits
  final stats (moves, time, pairs_found) when the board is complete.
"""
from __future__ import annotations

import random
from typing import Any, Dict, Optional

from therapy.models import SessionTrial
from therapy.api.games.registry import register

# --- Emoji pools by difficulty ---
EASY_EMOJIS = ["🍎", "🐕", "⭐", "🚗", "🌈", "🐱", "🌻", "🐟"]
MEDIUM_EMOJIS = EASY_EMOJIS + ["🎈", "🦋", "🍕", "🎸", "🐢", "🌙", "🍇", "🚀"]
HARD_EMOJIS = MEDIUM_EMOJIS + ["🦁", "🎯", "🧩", "🎨", "🦄", "🍉", "🔔", "🏀"]


def _pool_for_level(level: int):
    if level <= 1:
        return EASY_EMOJIS
    elif level <= 2:
        return MEDIUM_EMOJIS
    return HARD_EMOJIS


def _num_pairs(level: int) -> int:
    """Number of pairs on the board."""
    if level <= 1:
        return 4   # 4 pairs = 8 cards (4x2 grid)
    elif level <= 2:
        return 6   # 6 pairs = 12 cards (4x3 grid)
    return 8       # 8 pairs = 16 cards (4x4 grid)


@register
class MemoryMatchGame:
    code = "memory_match"
    trial_type = "memory_match"
    game_name = "Memory Match"

    def compute_level(self, session_id: int) -> int:
        completed = SessionTrial.objects.filter(
            session_id=session_id, status="completed"
        )
        total = completed.count()
        if total == 0:
            return 1

        correct = completed.filter(success=True).count()
        accuracy = correct / total

        if accuracy >= 0.85 and total >= 2:
            return 3
        elif accuracy >= 0.65:
            return 2
        return 1

    def build_trial(self, level: int, *, session_id: Optional[int] = None) -> Dict[str, Any]:
        pool = _pool_for_level(level)
        num = _num_pairs(level)

        # Pick random emojis for the pairs
        chosen = random.sample(pool, num)
        # Create pairs (each emoji appears twice)
        cards = []
        for i, emoji in enumerate(chosen):
            cards.append({"id": f"c{i}a", "emoji": emoji, "pair_id": f"p{i}"})
            cards.append({"id": f"c{i}b", "emoji": emoji, "pair_id": f"p{i}"})

        random.shuffle(cards)

        # Compute grid dimensions
        total_cards = len(cards)
        if total_cards <= 8:
            cols = 4
        elif total_cards <= 12:
            cols = 4
        else:
            cols = 4
        rows = total_cards // cols

        # Prompt fading
        if level <= 1:
            prompt = f"Find {num} matching pairs! Flip two cards at a time."
            ai_hint = "Start with corners — they're easier to remember!"
        elif level == 2:
            prompt = f"Match all {num} pairs! Remember where each card is."
            ai_hint = "Try to remember each card position."
        else:
            prompt = f"Match all {num} pairs! How few moves can you use?"
            ai_hint = None

        # Target is the full card layout (for verification)
        pair_map = {c["id"]: c["pair_id"] for c in cards}

        return {
            "prompt": prompt,
            "target": f"{num}_pairs",
            "target_id": f"{num}_pairs",
            "highlight": None,
            "options": [],  # Not used — frontend handles card grid
            "time_limit_ms": num * 15000,  # 15 seconds per pair
            "ai_hint": ai_hint,
            "ai_reason": f"Level {level} memory match with {num} pairs",
            "extra": {
                "level": level,
                "game_type": "memory_match",
                "num_pairs": num,
                "grid_cols": cols,
                "grid_rows": rows,
                "cards": cards,
                "pair_map": pair_map,
            },
        }

    def evaluate(
        self,
        *,
        target: str,
        submit: Dict[str, Any],
        level: int,
        session_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        clicked = submit.get("clicked", "")
        response_time_ms = int(submit.get("response_time_ms", 0))
        timed_out = submit.get("timed_out", False)

        # Parse frontend submission: "pairs:3,moves:8,total:4"
        parts = {}
        for part in clicked.split(","):
            if ":" in part:
                k, v = part.split(":", 1)
                parts[k.strip()] = v.strip()

        pairs_found = int(parts.get("pairs", 0))
        total_pairs = int(parts.get("total", 0)) or 1
        moves = int(parts.get("moves", 0))

        # Success = found all pairs
        completion_ratio = pairs_found / total_pairs
        success = completion_ratio >= 1.0 and not timed_out

        # Score: perfect moves = num_pairs, so efficiency = pairs / moves
        perfect_moves = total_pairs
        if moves > 0:
            efficiency = perfect_moves / moves
        else:
            efficiency = 0

        if success:
            base_score = 10
            if efficiency >= 0.8:
                score = 15  # exceptional memory
            elif efficiency >= 0.5:
                score = 12
            else:
                score = 10
        elif completion_ratio >= 0.5:
            score = 5
        else:
            score = 2 if not timed_out else 0

        # Feedback
        if success and efficiency >= 0.8:
            feedback = "🧠 Amazing memory! You found all pairs with very few moves!"
        elif success:
            feedback = "🌟 Great job! You found all the matching pairs!"
        elif timed_out and completion_ratio >= 0.5:
            feedback = f"⏰ Time's up! You found {pairs_found}/{total_pairs} pairs. Almost there!"
        elif timed_out:
            feedback = f"⏰ Time's up! You found {pairs_found}/{total_pairs} pairs. Keep practicing!"
        else:
            feedback = f"You found {pairs_found}/{total_pairs} pairs. Let's try again!"

        # AI recommendation
        if success and efficiency >= 0.7:
            ai_recommendation = "Increase difficulty — add more pairs."
            ai_reason = "Child has excellent visual memory."
        elif success:
            ai_recommendation = "Maintain current level — child is progressing."
            ai_reason = "Child completed the board but needed extra moves."
        elif timed_out:
            ai_recommendation = "Reduce pairs or increase time."
            ai_reason = "Child ran out of time."
        else:
            ai_recommendation = "Use fewer pairs or provide hints."
            ai_reason = "Child struggled with current difficulty."

        return {
            "success": success,
            "score": score,
            "feedback": feedback,
            "ai_recommendation": ai_recommendation,
            "ai_reason": ai_reason,
            "telemetry": {
                "pairs_found": pairs_found,
                "total_pairs": total_pairs,
                "moves": moves,
                "efficiency": round(efficiency, 2),
                "response_time_ms": response_time_ms,
                "timed_out": timed_out,
                "level": level,
            },
        }
