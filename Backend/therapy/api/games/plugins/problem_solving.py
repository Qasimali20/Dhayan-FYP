"""
Problem Solving Plugin – Pattern & Puzzle (Executive Function)
ABA Level 6+: Inductive reasoning, pattern completion, sequencing.

Mechanics:
  - Show a sequence with a missing piece (pattern completion)
  - 3-4 options to pick from
  - Adaptive: more complex patterns at higher levels
  - Includes sequence, alternating, and counting patterns
"""
from __future__ import annotations

import random
from typing import Any, Dict, Optional

from therapy.models import SessionTrial
from therapy.api.games.registry import register

# --- Pattern generators ---

PATTERN_SETS = {
    "easy": [
        {"seq": ["🔴", "🔵", "🔴", "🔵"], "answer": "🔴", "distractors": ["🟢", "🟡"], "name": "alternating colors"},
        {"seq": ["⭐", "⭐", "⭐"], "answer": "⭐", "distractors": ["🔵", "❤️"], "name": "repeating stars"},
        {"seq": ["🍎", "🍎", "🍌"], "answer": "🍎", "distractors": ["🍇", "🍊"], "name": "fruit pattern"},
        {"seq": ["🐕", "🐱", "🐕", "🐱"], "answer": "🐕", "distractors": ["🐟", "🐦"], "name": "animal alternating"},
        {"seq": ["🟢", "🟢", "🟢"], "answer": "🟢", "distractors": ["🔴", "🔵"], "name": "same color"},
        {"seq": ["🌙", "☀️", "🌙", "☀️"], "answer": "🌙", "distractors": ["⭐", "☁️"], "name": "day-night pattern"},
        {"seq": ["❤️", "💙", "❤️", "💙"], "answer": "❤️", "distractors": ["💚", "💛"], "name": "heart pattern"},
        {"seq": ["🚗", "🚌", "🚗", "🚌"], "answer": "🚗", "distractors": ["🚂", "✈️"], "name": "vehicle pattern"},
    ],
    "medium": [
        {"seq": ["🔴", "🔵", "🟢", "🔴", "🔵"], "answer": "🟢", "distractors": ["🟡", "🟣", "⚪"], "name": "3-color cycle"},
        {"seq": ["1️⃣", "2️⃣", "3️⃣", "4️⃣"], "answer": "5️⃣", "distractors": ["6️⃣", "3️⃣", "1️⃣"], "name": "counting up"},
        {"seq": ["⬆️", "➡️", "⬇️", "⬅️"], "answer": "⬆️", "distractors": ["↗️", "↘️", "↙️"], "name": "direction cycle"},
        {"seq": ["🌑", "🌓", "🌕", "🌗"], "answer": "🌑", "distractors": ["⭐", "☀️", "☁️"], "name": "moon phases"},
        {"seq": ["🍎", "🍌", "🍇", "🍎", "🍌"], "answer": "🍇", "distractors": ["🍊", "🍒", "🍐"], "name": "fruit cycle 3"},
        {"seq": ["😀", "😢", "😀", "😢"], "answer": "😀", "distractors": ["😡", "😱", "😴"], "name": "emotion pattern"},
    ],
    "hard": [
        {"seq": ["🔴", "🔴", "🔵", "🔴", "🔴", "🔵", "🔴", "🔴"], "answer": "🔵", "distractors": ["🔴", "🟢", "🟡", "🟣"], "name": "AAB pattern"},
        {"seq": ["⭐", "⭐", "🌙", "⭐", "⭐", "🌙", "🌙"], "answer": "⭐", "distractors": ["🌙", "☀️", "💫", "🌟"], "name": "growing pattern"},
        {"seq": ["1️⃣", "3️⃣", "5️⃣", "7️⃣"], "answer": "9️⃣", "distractors": ["8️⃣", "6️⃣", "0️⃣", "2️⃣"], "name": "odd numbers"},
        {"seq": ["🟢", "🟢", "🔵", "🔵", "🟢", "🟢", "🔵"], "answer": "🔵", "distractors": ["🟢", "🔴", "🟡", "🟣"], "name": "AABB repeat"},
        {"seq": ["🐕", "🐱", "🐟", "🐕", "🐱", "🐟", "🐕"], "answer": "🐱", "distractors": ["🐟", "🐦", "🐰", "🐻"], "name": "3-animal cycle"},
    ],
}


@register
class ProblemSolvingGame:
    code = "problem_solving"
    trial_type = "problem_solving"
    game_name = "Problem Solving"

    def compute_level(self, session_id: int) -> int:
        completed = SessionTrial.objects.filter(
            session_id=session_id, status="completed"
        )
        total = completed.count()
        if total == 0:
            return 1

        correct = completed.filter(success=True).count()
        accuracy = correct / total

        if accuracy >= 0.80 and total >= 3:
            return 3
        elif accuracy >= 0.55:
            return 2
        return 1

    def build_trial(self, level: int, *, session_id: Optional[int] = None) -> Dict[str, Any]:
        if level <= 1:
            pool = PATTERN_SETS["easy"]
        elif level <= 2:
            pool = PATTERN_SETS["medium"]
        else:
            pool = PATTERN_SETS["hard"]

        pattern = random.choice(pool)

        # Build the display sequence with a blank at the end
        sequence_display = pattern["seq"] + ["❓"]
        answer = pattern["answer"]

        options = [{"id": answer, "label": answer}]
        for d in pattern["distractors"]:
            options.append({"id": d, "label": d})
        random.shuffle(options)

        # Prompt fading — keep instruction text separate from sequence display
        # (sequence is displayed via extra.sequence in the frontend)
        if level <= 1:
            prompt = "Look at the pattern — What comes next?"
            highlight = answer
            ai_hint = f"The pattern is: {pattern['name']}"
        elif level == 2:
            prompt = "What comes next in the pattern?"
            highlight = None
            ai_hint = f"Hint: {pattern['name']}"
        else:
            prompt = "Complete the pattern!"
            highlight = None
            ai_hint = None

        return {
            "prompt": prompt,
            "target": answer,
            "target_id": answer,
            "highlight": highlight,
            "options": options,
            "time_limit_ms": max(8000, 15000 - (level * 2000)),
            "ai_hint": ai_hint,
            "ai_reason": f"Level {level} problem solving – {pattern['name']}",
            "extra": {
                "level": level,
                "pattern_name": pattern["name"],
                "sequence": sequence_display,
                "game_mode": "pattern_completion",
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

        success = (clicked == target) and not timed_out
        score = 10 if success else (3 if clicked == target else 0)

        if success:
            if response_time_ms < 3000:
                feedback = "🧠 Brilliant! You cracked the pattern fast!"
            elif response_time_ms < 6000:
                feedback = "🌟 Great thinking! You found the pattern!"
            else:
                feedback = "✅ Correct! Nice problem solving!"
        elif timed_out:
            feedback = "⏰ Time's up! Look at the pattern carefully."
        else:
            feedback = "🤔 Not quite. Let's try another pattern!"

        if success:
            ai_recommendation = "Increase pattern complexity."
            ai_reason = "Child completed pattern correctly."
        elif timed_out:
            ai_recommendation = "Simplify pattern or increase time limit."
            ai_reason = "Child needed more time to analyze."
        else:
            ai_recommendation = "Use simpler patterns or add visual hints."
            ai_reason = "Child selected wrong pattern continuation."

        return {
            "success": success,
            "score": score,
            "feedback": feedback,
            "ai_recommendation": ai_recommendation,
            "ai_reason": ai_reason,
            "telemetry": {
                "clicked": clicked,
                "target": target,
                "response_time_ms": response_time_ms,
                "timed_out": timed_out,
                "level": level,
            },
        }
