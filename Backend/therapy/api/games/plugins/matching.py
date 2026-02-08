"""
Matching Game Plugin – Shape / Emoji Matching (Visual Discrimination)
ABA Level 1: Visual discrimination, matching identical items.

Mechanics:
  - Show a target emoji/shape
  - 3-4 options; child picks the matching one
  - Adaptive difficulty: more distractors, similar shapes at higher levels
  - Prompt fading via ABA hierarchy
"""
from __future__ import annotations

import random
from typing import Any, Dict, Optional

from therapy.models import SessionTrial
from therapy.api.games.registry import register

# --- Stimulus pools ---
EASY_ITEMS = [
    {"id": "apple",   "label": "🍎 Apple",   "category": "fruit"},
    {"id": "banana",  "label": "🍌 Banana",  "category": "fruit"},
    {"id": "car",     "label": "🚗 Car",     "category": "vehicle"},
    {"id": "dog",     "label": "🐕 Dog",     "category": "animal"},
    {"id": "cat",     "label": "🐱 Cat",     "category": "animal"},
    {"id": "star",    "label": "⭐ Star",    "category": "shape"},
    {"id": "heart",   "label": "❤️ Heart",   "category": "shape"},
    {"id": "sun",     "label": "☀️ Sun",     "category": "nature"},
    {"id": "moon",    "label": "🌙 Moon",    "category": "nature"},
    {"id": "fish",    "label": "🐟 Fish",    "category": "animal"},
    {"id": "bird",    "label": "🐦 Bird",    "category": "animal"},
    {"id": "tree",    "label": "🌳 Tree",    "category": "nature"},
]

MEDIUM_ITEMS = EASY_ITEMS + [
    {"id": "grape",    "label": "🍇 Grape",    "category": "fruit"},
    {"id": "orange",   "label": "🍊 Orange",   "category": "fruit"},
    {"id": "bus",      "label": "🚌 Bus",      "category": "vehicle"},
    {"id": "truck",    "label": "🚛 Truck",    "category": "vehicle"},
    {"id": "rabbit",   "label": "🐰 Rabbit",   "category": "animal"},
    {"id": "bear",     "label": "🐻 Bear",     "category": "animal"},
    {"id": "circle",   "label": "🔵 Circle",   "category": "shape"},
    {"id": "triangle", "label": "🔺 Triangle", "category": "shape"},
]

HARD_ITEMS = MEDIUM_ITEMS + [
    {"id": "cherry",    "label": "🍒 Cherry",    "category": "fruit"},
    {"id": "pear",      "label": "🍐 Pear",      "category": "fruit"},
    {"id": "ambulance", "label": "🚑 Ambulance", "category": "vehicle"},
    {"id": "helicopter","label": "🚁 Helicopter","category": "vehicle"},
    {"id": "penguin",   "label": "🐧 Penguin",   "category": "animal"},
    {"id": "dolphin",   "label": "🐬 Dolphin",   "category": "animal"},
    {"id": "diamond",   "label": "💎 Diamond",   "category": "shape"},
    {"id": "square",    "label": "🟦 Square",    "category": "shape"},
]


def _pool_for_level(level: int):
    if level <= 1:
        return EASY_ITEMS
    elif level <= 2:
        return MEDIUM_ITEMS
    return HARD_ITEMS


def _num_options(level: int) -> int:
    if level <= 1:
        return 3
    elif level <= 2:
        return 4
    return 5


@register
class MatchingGame:
    code = "matching"
    trial_type = "matching"
    game_name = "Shape Matching"

    def compute_level(self, session_id: int) -> int:
        completed = SessionTrial.objects.filter(
            session_id=session_id, status="completed"
        )
        total = completed.count()
        if total == 0:
            return 1

        correct = completed.filter(success=True).count()
        accuracy = correct / total

        if accuracy >= 0.85 and total >= 3:
            return 3
        elif accuracy >= 0.65:
            return 2
        return 1

    def build_trial(self, level: int, *, session_id: Optional[int] = None) -> Dict[str, Any]:
        pool = _pool_for_level(level)
        n_opts = _num_options(level)

        target_item = random.choice(pool)
        distractors = [i for i in pool if i["id"] != target_item["id"]]
        random.shuffle(distractors)
        distractor_items = distractors[: n_opts - 1]

        options = [target_item] + distractor_items
        random.shuffle(options)

        # Prompt fading
        if level <= 1:
            prompt = f"Find the {target_item['label']}! Can you match it?"
            highlight = target_item["id"]
            ai_hint = f"Look for the {target_item['label']}"
        elif level == 2:
            prompt = f"Find the {target_item['label']}!"
            highlight = None
            ai_hint = f"Which one is the {target_item['label']}?"
        else:
            prompt = f"Can you find the {target_item['label']}?"
            highlight = None
            ai_hint = None

        return {
            "prompt": prompt,
            "target": target_item["id"],
            "target_id": target_item["id"],
            "highlight": highlight,
            "options": [{"id": o["id"], "label": o["label"]} for o in options],
            "time_limit_ms": max(6000, 12000 - (level * 2000)),
            "ai_hint": ai_hint,
            "ai_reason": f"Level {level} matching trial",
            "extra": {"level": level, "category": target_item["category"]},
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
            if response_time_ms < 2000:
                feedback = "⚡ Lightning fast! Amazing match!"
            elif response_time_ms < 4000:
                feedback = "🌟 Great job matching!"
            else:
                feedback = "✅ Correct match! Well done!"
        elif timed_out:
            feedback = "⏰ Time's up! Let's try again."
        else:
            feedback = "Almost! Let's try the next one."

        # AI recommendation
        if success:
            ai_recommendation = "Continue with current difficulty or increase."
            ai_reason = "Child matched correctly."
        elif timed_out:
            ai_recommendation = "Increase time limit or add visual prompt."
            ai_reason = "Child did not respond in time."
        else:
            ai_recommendation = "Reduce distractors or highlight correct answer."
            ai_reason = "Incorrect match — may need more support."

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
