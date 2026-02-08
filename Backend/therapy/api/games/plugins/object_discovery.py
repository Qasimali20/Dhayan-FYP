"""
Object Discovery Plugin – Receptive Language & Categorization
ABA Level 2: Identify objects by category, build vocabulary.

Mechanics:
  - Show a category (e.g., "Animals")
  - Grid of items from mixed categories
  - Child taps items that belong to the target category
  - Adaptive: more categories, more distractors at higher levels
"""
from __future__ import annotations

import random
from typing import Any, Dict, Optional

from therapy.models import SessionTrial
from therapy.api.games.registry import register

CATEGORIES = {
    "animals": {
        "label": "🐾 Animals",
        "items": [
            {"id": "dog", "label": "🐕 Dog"},
            {"id": "cat", "label": "🐱 Cat"},
            {"id": "fish", "label": "🐟 Fish"},
            {"id": "bird", "label": "🐦 Bird"},
            {"id": "rabbit", "label": "🐰 Rabbit"},
            {"id": "bear", "label": "🐻 Bear"},
            {"id": "penguin", "label": "🐧 Penguin"},
            {"id": "dolphin", "label": "🐬 Dolphin"},
        ],
    },
    "fruits": {
        "label": "🍎 Fruits",
        "items": [
            {"id": "apple", "label": "🍎 Apple"},
            {"id": "banana", "label": "🍌 Banana"},
            {"id": "grape", "label": "🍇 Grape"},
            {"id": "orange", "label": "🍊 Orange"},
            {"id": "cherry", "label": "🍒 Cherry"},
            {"id": "pear", "label": "🍐 Pear"},
            {"id": "watermelon", "label": "🍉 Watermelon"},
            {"id": "strawberry", "label": "🍓 Strawberry"},
        ],
    },
    "vehicles": {
        "label": "🚗 Vehicles",
        "items": [
            {"id": "car", "label": "🚗 Car"},
            {"id": "bus", "label": "🚌 Bus"},
            {"id": "truck", "label": "🚛 Truck"},
            {"id": "airplane", "label": "✈️ Airplane"},
            {"id": "boat", "label": "🚤 Boat"},
            {"id": "bicycle", "label": "🚲 Bicycle"},
            {"id": "train", "label": "🚂 Train"},
            {"id": "helicopter", "label": "🚁 Helicopter"},
        ],
    },
    "shapes": {
        "label": "🔷 Shapes",
        "items": [
            {"id": "circle", "label": "🔵 Circle"},
            {"id": "square", "label": "🟦 Square"},
            {"id": "triangle", "label": "🔺 Triangle"},
            {"id": "star", "label": "⭐ Star"},
            {"id": "heart", "label": "❤️ Heart"},
            {"id": "diamond", "label": "💎 Diamond"},
        ],
    },
    "food": {
        "label": "🍕 Food",
        "items": [
            {"id": "pizza", "label": "🍕 Pizza"},
            {"id": "cake", "label": "🎂 Cake"},
            {"id": "cookie", "label": "🍪 Cookie"},
            {"id": "bread", "label": "🍞 Bread"},
            {"id": "icecream", "label": "🍨 Ice Cream"},
            {"id": "candy", "label": "🍬 Candy"},
        ],
    },
    "nature": {
        "label": "🌿 Nature",
        "items": [
            {"id": "tree", "label": "🌳 Tree"},
            {"id": "flower", "label": "🌸 Flower"},
            {"id": "sun", "label": "☀️ Sun"},
            {"id": "moon", "label": "🌙 Moon"},
            {"id": "cloud", "label": "☁️ Cloud"},
            {"id": "rainbow", "label": "🌈 Rainbow"},
        ],
    },
}

CAT_KEYS = list(CATEGORIES.keys())


def _cats_for_level(level: int) -> int:
    """How many distractor categories to mix in"""
    if level <= 1:
        return 1  # target + 1 distractor
    elif level <= 2:
        return 2
    return 3


def _target_count(level: int) -> int:
    """How many correct items from target category"""
    if level <= 1:
        return 2
    elif level <= 2:
        return 3
    return 3


@register
class ObjectDiscoveryGame:
    code = "object_discovery"
    trial_type = "object_discovery"
    game_name = "Object Discovery"

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
        elif accuracy >= 0.60:
            return 2
        return 1

    def build_trial(self, level: int, *, session_id: Optional[int] = None) -> Dict[str, Any]:
        target_cat_key = random.choice(CAT_KEYS)
        target_cat = CATEGORIES[target_cat_key]

        n_correct = _target_count(level)
        n_distractor_cats = _cats_for_level(level)

        correct_items = random.sample(
            target_cat["items"], min(n_correct, len(target_cat["items"]))
        )

        distractor_cat_keys = [k for k in CAT_KEYS if k != target_cat_key]
        random.shuffle(distractor_cat_keys)
        chosen_distractor_keys = distractor_cat_keys[:n_distractor_cats]

        distractor_items = []
        for dk in chosen_distractor_keys:
            items = CATEGORIES[dk]["items"]
            distractor_items.extend(random.sample(items, min(2, len(items))))

        all_options = correct_items + distractor_items
        random.shuffle(all_options)

        target_ids = [i["id"] for i in correct_items]

        # Prompt fading
        if level <= 1:
            prompt = f"Find all the {target_cat['label']}! Tap each one you see."
            highlight = target_ids[0] if target_ids else None
            ai_hint = f"Look for things that are {target_cat_key}"
        elif level == 2:
            prompt = f"Can you find all the {target_cat['label']}?"
            highlight = None
            ai_hint = f"How many {target_cat_key} can you spot?"
        else:
            prompt = f"Select all the {target_cat['label']}!"
            highlight = None
            ai_hint = None

        # For evaluate, target is comma-separated IDs
        return {
            "prompt": prompt,
            "target": ",".join(target_ids),
            "target_id": ",".join(target_ids),
            "highlight": highlight,
            "options": [{"id": o["id"], "label": o["label"]} for o in all_options],
            "time_limit_ms": max(8000, 15000 - (level * 2000)),
            "ai_hint": ai_hint,
            "ai_reason": f"Level {level} object discovery – category: {target_cat_key}",
            "extra": {
                "level": level,
                "category": target_cat_key,
                "category_label": target_cat["label"],
                "correct_count": len(target_ids),
                "game_mode": "category_select",
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

        target_ids = set(target.split(","))
        clicked_ids = set(clicked.split(",")) if clicked else set()

        if timed_out:
            success = False
            score = 0
        else:
            # Score based on correct picks vs total
            correct_picks = clicked_ids & target_ids
            wrong_picks = clicked_ids - target_ids
            success = len(correct_picks) >= len(target_ids) and len(wrong_picks) == 0
            if success:
                score = 10
            else:
                ratio = max(0, len(correct_picks) - len(wrong_picks)) / max(1, len(target_ids))
                score = max(0, min(10, round(ratio * 10)))

        if success:
            feedback = "🌟 Perfect! You found them all!"
        elif timed_out:
            feedback = "⏰ Time's up! Let's try again."
        elif score >= 5:
            feedback = "👍 Good try! You found some of them."
        else:
            feedback = "Let's look more carefully next time!"

        if success:
            ai_recommendation = "Increase category complexity or add more distractors."
            ai_reason = "Child correctly identified all items."
        elif timed_out:
            ai_recommendation = "Increase time limit or reduce number of items."
            ai_reason = "Child needed more time."
        else:
            ai_recommendation = "Reduce distractors or highlight category label."
            ai_reason = f"Child selected {len(clicked_ids)} items, {len(clicked_ids & target_ids)} correct."

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
                "correct_picks": list(clicked_ids & target_ids),
                "wrong_picks": list(clicked_ids - target_ids),
                "missed": list(target_ids - clicked_ids),
            },
        }
