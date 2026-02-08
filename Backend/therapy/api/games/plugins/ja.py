from __future__ import annotations

import random
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from django.conf import settings
from django.utils import timezone

from therapy.models import Observation
from therapy.api.games.registry import register

from gtts import gTTS

# =========================================================
# ✅ Backend TTS (Option B): create a file per prompt (cached)
# =========================================================

def _tts_cache_dir() -> Path:
    base = Path(getattr(settings, "MEDIA_ROOT", "media"))
    out = base / "tts" / "ja"
    out.mkdir(parents=True, exist_ok=True)
    return out

def tts_mp3_for_text(text: str, *, lang: str = "en") -> str:
    """
    Returns a MEDIA_URL path to an mp3 file for given text.
    Caches by hash so we don't regenerate.
    Uses gTTS by default (fast MVP). Replace with your own TTS later.
    """
    # hash stable key
    key = hashlib.md5(f"{lang}:{text}".encode("utf-8")).hexdigest()
    out_dir = _tts_cache_dir()
    file_path = out_dir / f"{key}.mp3"

    if not file_path.exists():
        try:
            # MVP: gTTS
            gTTS(text=text, lang=lang).save(str(file_path))
        except Exception:
            # If gTTS isn't available, fallback: no audio
            return ""

    media_url = getattr(settings, "MEDIA_URL", "/media/")
    if not media_url.endswith("/"):
        media_url += "/"
    # file is under MEDIA_ROOT/tts/ja/<hash>.mp3
    return f"{media_url}tts/ja/{file_path.name}"


# =========================================================
# ✅ Image catalog (use local static or media)
# You can put these images in:
#   therapy/static/therapy/ja/<id>.png
# and serve with STATIC_URL.
# =========================================================

def _img_url(stim_id: str) -> str:
    """
    Choose one:
      - STATIC: /static/therapy/ja/<id>.png
      - MEDIA:  /media/ja/<id>.png

    Keep STATIC for fast MVP.
    """
    static_url = getattr(settings, "STATIC_URL", "/static/")
    if not static_url.endswith("/"):
        static_url += "/"
    return f"{static_url}therapy/ja/{stim_id}.png"


# =========================================================
# ✅ State / AI policy
# =========================================================

@dataclass
class JAState:
    """Derived state from recent performance (no DB schema changes needed)."""
    level: int
    ema_acc: float
    ema_rt: float
    streak_correct: int
    streak_wrong: int
    time_limit_ms: int
    distractor_mode: str  # "easy" | "medium" | "hard"


@register
class JointAttentionGame:
    """
    AI-assisted Joint Attention module (speech prompt + image options):

    - L1: spoken+text prompt + highlight target
    - L2: spoken+text prompt, NO highlight
    - L3: spoken minimal cue ("Look where I point"), NO highlight (maintenance)

    AI adapts:
      - level (prompt fading)
      - time limit
      - distractor difficulty
    """
    code = "ja"
    trial_type = "joint_attention"
    game_name = "Look Where I Point"

    # 👇 Stimuli IDs must match your image filenames
    STIMULI_EASY = ["car", "ball", "cat", "cup", "apple", "book", "fish", "hat"]
    STIMULI_MED  = ["dog", "pen", "chair", "shoe", "fork", "spoon", "door", "ring"]
    STIMULI_HARD = ["cap", "bat", "rat", "mat", "mug", "cook", "hook", "pack"]

    # Base time limits by level
    TIME_LIMIT_L1 = 12000
    TIME_LIMIT_L2 = 10000
    TIME_LIMIT_L3 = 8000

    EMA_ALPHA = 0.35
    WINDOW = 8

    # If you want Urdu prompts later, set lang="ur" and switch prompt text.
    TTS_LANG = "en"

    # -----------------------------
    # Telemetry + state
    # -----------------------------

    def _recent_telemetry(self, session_id: int, limit: int = WINDOW) -> List[Dict[str, Any]]:
        qs = Observation.objects.filter(
            session_id=session_id,
            note="trial_telemetry",
        ).order_by("-id")[:limit]
        out: List[Dict[str, Any]] = []
        for o in qs:
            if isinstance(o.tags, dict):
                out.append(o.tags)
        return out

    def _compute_state(self, session_id: int) -> JAState:
        history = list(reversed(self._recent_telemetry(session_id)))  # oldest->newest

        if not history:
            return JAState(
                level=1,
                ema_acc=0.0,
                ema_rt=0.0,
                streak_correct=0,
                streak_wrong=0,
                time_limit_ms=self.TIME_LIMIT_L1,
                distractor_mode="easy",
            )

        ema_acc = 0.0
        ema_rt = 0.0
        streak_correct = 0
        streak_wrong = 0

        for t in history:
            success = bool(t.get("success", False))
            rt = int(t.get("response_time_ms", 0) or 0)

            ema_acc = (self.EMA_ALPHA * (1.0 if success else 0.0)) + ((1 - self.EMA_ALPHA) * ema_acc)
            ema_rt = (self.EMA_ALPHA * float(rt)) + ((1 - self.EMA_ALPHA) * ema_rt)

            if success:
                streak_correct += 1
                streak_wrong = 0
            else:
                streak_wrong += 1
                streak_correct = 0

        # Level decision
        if ema_acc >= 0.78 and (ema_rt <= 3200 or ema_rt == 0.0) and streak_correct >= 2:
            level = 2
        else:
            level = 1

        if ema_acc >= 0.88 and (ema_rt <= 2500 or ema_rt == 0.0) and streak_correct >= 3:
            level = 3

        # distractor difficulty
        if level == 1:
            distractor_mode = "easy" if ema_acc < 0.65 else "medium"
        elif level == 2:
            distractor_mode = "medium" if ema_acc < 0.85 else "hard"
        else:
            distractor_mode = "hard"

        # base time limit by level
        base = self.TIME_LIMIT_L1 if level == 1 else self.TIME_LIMIT_L2 if level == 2 else self.TIME_LIMIT_L3

        # adapt time limit
        if ema_rt and ema_rt > 4500:
            time_limit_ms = min(base + 2000, 15000)
        elif ema_rt and ema_rt < 2000 and ema_acc > 0.8:
            time_limit_ms = max(base - 1000, 5000)
        else:
            time_limit_ms = base

        return JAState(
            level=level,
            ema_acc=float(round(ema_acc, 3)),
            ema_rt=float(round(ema_rt, 1)),
            streak_correct=streak_correct,
            streak_wrong=streak_wrong,
            time_limit_ms=int(time_limit_ms),
            distractor_mode=distractor_mode,
        )

    def compute_level(self, session_id: int) -> int:
        return self._compute_state(session_id).level

    # -----------------------------
    # Stimuli + options + target
    # -----------------------------

    def _stimuli_pool(self, mode: str) -> List[str]:
        if mode == "easy":
            return list(self.STIMULI_EASY)
        if mode == "hard":
            return list(set(self.STIMULI_HARD + self.STIMULI_MED))
        return list(set(self.STIMULI_MED + self.STIMULI_EASY))

    def _pick_options(self, mode: str) -> List[str]:
        pool = self._stimuli_pool(mode)
        if len(pool) < 4:
            pool = pool + self.STIMULI_EASY
        return random.sample(pool, 4)

    def _pick_target(self, options: List[str], session_id: int) -> str:
        last = Observation.objects.filter(session_id=session_id, note="trial_started").order_by("-id").first()
        last_target = None
        if last and isinstance(last.tags, dict):
            last_target = last.tags.get("target_id") or last.tags.get("target")

        candidates = [o for o in options if o != last_target] if last_target else options
        return random.choice(candidates) if candidates else random.choice(options)

    def _option_payload(self, stim_id: str) -> Dict[str, Any]:
        # Display label (capitalized) for UI, but keep id stable
        return {
            "id": stim_id,
            "label": stim_id.capitalize(),
            "image": _img_url(stim_id),
        }

    # -----------------------------
    # Build trial (speech prompt + image options)
    # -----------------------------

    def build_trial(self, level: int, *, session_id: Optional[int] = None) -> Dict[str, Any]:
        # If we have session context, enforce AI state
        if session_id is not None:
            state = self._compute_state(session_id)
            mode = state.distractor_mode
            time_limit_ms = state.time_limit_ms
            level = state.level
        else:
            mode = "easy"
            time_limit_ms = self.TIME_LIMIT_L1

        option_ids = self._pick_options(mode)
        target_id = self._pick_target(option_ids, session_id or 0)

        # Prompt hierarchy (text + audio)
        if level == 1:
            prompt_text = f"Look at the {target_id}"
            highlight_id = target_id
            ai_hint = "Use highlight + speech + text (errorless learning)."
        elif level == 2:
            prompt_text = f"Look at the {target_id}"
            highlight_id = None
            ai_hint = "Fade prompt: speech + text only."
        else:
            prompt_text = "Look where I point"
            highlight_id = None
            ai_hint = "Minimal cue (maintenance)."

        prompt_audio = tts_mp3_for_text(prompt_text, lang=self.TTS_LANG)

        return {
            "prompt_text": prompt_text,
            "prompt_audio": prompt_audio,         # ✅ MP3 URL (backend generated)
            "options": [self._option_payload(x) for x in option_ids],  # ✅ image cards
            "target_id": target_id,               # stable id
            "highlight_id": highlight_id,         # for level 1 only
            "time_limit_ms": int(time_limit_ms),
            "ai_hint": ai_hint,
            "ai_reason": f"mode={mode}",
            "extra": {
                "distractor_mode": mode,
                "level": level,
            },
        }

    # -----------------------------
    # Evaluate (clicked id vs target id)
    # -----------------------------

    def evaluate(self, *, target: str, submit: dict, level: int, session_id: Optional[int] = None) -> dict:
        clicked_id = (submit.get("clicked_id") or submit.get("clicked") or "").strip().lower()
        target_id = (target or "").strip().lower()

        timed_out = bool(submit.get("timed_out", False))
        response_time_ms = int(submit.get("response_time_ms", 0) or 0)

        success = (not timed_out) and (clicked_id == target_id)
        score = 10 if success else 0

        rec, reason = self._ai_recommend_after_trial(
            session_id=session_id,
            level=level,
            success=success,
            timed_out=timed_out,
            rt=response_time_ms,
        )

        telemetry = {
            "game": self.code,
            "trial_type": self.trial_type,
            "level": level,
            "target_id": target_id,
            "clicked_id": clicked_id,
            "response_time_ms": response_time_ms,
            "timed_out": timed_out,
            "success": success,
            "ai_recommendation": rec,
            "ai_reason": reason,
            # Optional: store mode to analyze later
            "distractor_mode": self._compute_state(session_id).distractor_mode if session_id else None,
        }

        feedback = "Correct!" if success else ("Timed out" if timed_out else "Try again")

        return {
            "success": success,
            "score": score,
            "feedback": feedback,
            "telemetry": telemetry,
            "ai_recommendation": rec,
            "ai_reason": reason,
        }

    def _ai_recommend_after_trial(
        self,
        *,
        session_id: Optional[int],
        level: int,
        success: bool,
        timed_out: bool,
        rt: int,
    ) -> Tuple[str, str]:
        if session_id is None:
            return ("Continue", "No session context")

        state = self._compute_state(session_id)

        if timed_out or state.streak_wrong >= 2 or state.ema_acc < 0.55:
            return (
                "Recommendation: Increase prompting (Level 1), reduce distractor difficulty, slow pacing.",
                f"ema_acc={state.ema_acc}, streak_wrong={state.streak_wrong}, ema_rt={state.ema_rt}",
            )

        if state.ema_acc >= 0.8 and state.ema_rt <= 3200 and state.streak_correct >= 2:
            if level < 3:
                return (
                    "Recommendation: Fade prompt (move toward Level 2/3) and use harder distractors.",
                    f"ema_acc={state.ema_acc}, streak_correct={state.streak_correct}, ema_rt={state.ema_rt}",
                )

        return (
            "Recommendation: Maintain current level and continue trials.",
            f"ema_acc={state.ema_acc}, ema_rt={state.ema_rt}, level={state.level}",
        )
