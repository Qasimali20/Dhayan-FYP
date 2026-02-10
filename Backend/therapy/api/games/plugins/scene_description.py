"""
Scene Description Game – Describe an Image with Multimodal Gemini Evaluation
ABA Level 1-3: Receptive language, descriptive language, communication development.

Flow:
  - System shows a scenario image to the child
  - Child types what they see
  - Backend sends (image + child text + expected description + key elements) to Gemini (multimodal)
  - Gemini returns STRICT JSON evaluation:
      clarity_score (0-10), completeness_score (0-10), overall_score (0-100),
      key_elements_found, strengths, areas_for_improvement, feedback
  - Difficulty adapts based on avg overall_score across completed trials
  - Stores full evaluation in SceneDescriptionResponse

Each trial = one scenario image + child's description + LLM feedback.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple, List

from django.conf import settings
from django.core.files.storage import default_storage

from therapy.models import SessionTrial, ScenarioImage, SceneDescriptionResponse
from therapy.api.games.registry import register


# ─────────────────────────────────────────────────────────────
# Gemini (Multimodal) Utility
# ─────────────────────────────────────────────────────────────

def _get_gemini_client():
    """
    Uses Google GenAI Python SDK (google-genai).
    Requires:
      - pip install google-genai
      - GEMINI_API_KEY in settings (or as env var GEMINI_API_KEY)
    """
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        return None, None

    try:
        # Official SDK style (Gemini API) docs:
        # from google import genai
        # from google.genai import types
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        return client, types
    except Exception:
        return None, None


def _guess_mime_type(filename: str) -> str:
    """
    Best-effort MIME guess for image.
    """
    lower = (filename or "").lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    if lower.endswith(".avif"):
        return "image/avif"
    # default (most common)
    return "image/jpeg"


def _image_to_bytes(image_field) -> Tuple[bytes, str]:
    """
    Convert Django ImageField to raw bytes + mime_type.
    Returns (b"", "") if image not available.
    """
    if not image_field:
        return b"", ""
    try:
        with default_storage.open(image_field.name, "rb") as f:
            content = f.read()
        mime = _guess_mime_type(image_field.name)
        return content, mime
    except Exception:
        return b"", ""


def evaluate_scene_description(
    *,
    image_bytes: bytes,
    image_mime: str,
    child_response: str,
    expected_description: str,
    key_elements: List[str],
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluate child's description against the image + expected key points using multimodal Gemini.

    Returns:
    {
      "llm_score": 0-100,
      "feedback": str,
      "clarity_score": 0-10,
      "completeness_score": 0-10,
      "key_elements_found": [str],
      "strengths": str,
      "areas_for_improvement": str,
      "error": None | str
    }
    """
    client, types = _get_gemini_client()
    if not client:
        return {
            "llm_score": 50,
            "feedback": "LLM evaluation not available (Gemini API key not configured).",
            "clarity_score": 5,
            "completeness_score": 5,
            "key_elements_found": [],
            "strengths": "",
            "areas_for_improvement": "",
            "error": "Gemini API key not configured",
        }

    # Choose a multimodal-capable model.
    # You can change this in settings.GEMINI_MODEL, or pass model_name.
    model = model_name or getattr(settings, "GEMINI_MODEL", "gemini-3-flash-preview")

    elements_str = ", ".join(key_elements) if key_elements else "any relevant details"

    # Prompt: ask for STRICT JSON only.
    prompt = f"""
You are an autism therapy evaluation assistant.

Task:
A child described the image they saw. Evaluate their description in a supportive way.

Expected key elements to include (if present in the image):
{elements_str}

Expected reference description (teacher/therapist reference):
{expected_description}

Child's response:
"{child_response}"

Return STRICT JSON ONLY (no markdown, no extra text). Use this exact structure:
{{
  "clarity_score": <integer 0-10>,
  "completeness_score": <integer 0-10>,
  "overall_score": <integer 0-100>,
  "key_elements_found": [<strings from the expected key elements that the child mentioned>],
  "feedback": "<encouraging, constructive feedback addressed to the child>",
  "strengths": "<what the child did well>",
  "areas_for_improvement": "<gentle suggestions to improve next time>"
}}

Rules:
- Be encouraging and supportive for autistic children.
- If image details are unclear, focus on the child’s language quality and partial matches.
- Keep feedback short and child-friendly.
""".strip()

    import logging
    try:
        parts = []

        # Attach image as inline bytes if present
        if image_bytes and image_mime:
            img_part = types.Part.from_bytes(data=image_bytes, mime_type=image_mime)
            parts.append(img_part)

        parts.append(prompt)

        # Ask Gemini to output JSON
        config = None
        try:
            config = types.GenerateContentConfig(response_mime_type="application/json")
        except Exception:
            # Older versions may not expose GenerateContentConfig; fallback to prompt-only JSON enforcement.
            config = None

        resp = client.models.generate_content(
            model=model,
            contents=parts,
            config=config,
        )

        raw_text = (resp.text or "").strip()

        # Debug: log the raw Gemini response
        logging.getLogger("therapy.scene_description").info(f"Gemini raw response: {raw_text}")

        # Parse JSON (Gemini with response_mime_type should be JSON, but still defensive)
        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            # Attempt to extract JSON substring
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(raw_text[start:end])
            else:
                # Last resort: treat as feedback
                result = {
                    "clarity_score": 5,
                    "completeness_score": 5,
                    "overall_score": 50,
                    "key_elements_found": [],
                    "feedback": raw_text,
                    "strengths": "",
                    "areas_for_improvement": "",
                }

        # Debug: log the parsed result
        logging.getLogger("therapy.scene_description").info(f"Gemini parsed result: {result}")

        # Normalize fields + map overall_score -> llm_score
        clarity = int(result.get("clarity_score", 5))
        completeness = int(result.get("completeness_score", 5))
        overall = int(result.get("overall_score", 50))

        out = {
            "llm_score": overall,
            "feedback": result.get("feedback", "Feedback provided."),
            "clarity_score": max(0, min(10, clarity)),
            "completeness_score": max(0, min(10, completeness)),
            "key_elements_found": result.get("key_elements_found", []) or [],
            "strengths": result.get("strengths", "") or "",
            "areas_for_improvement": result.get("areas_for_improvement", "") or "",
            "error": None,
        }
        return out

    except Exception as e:
        logging.getLogger("therapy.scene_description").error(f"Gemini evaluation error: {str(e)}")
        return {
            "llm_score": 50,
            "feedback": f"Evaluation error: {str(e)}",
            "clarity_score": 5,
            "completeness_score": 5,
            "key_elements_found": [],
            "strengths": "",
            "areas_for_improvement": "",
            "error": str(e),
        }


# ─────────────────────────────────────────────────────────────
# Game Plugin
# ─────────────────────────────────────────────────────────────

@register
class SceneDescriptionGame:
    code = "scene_description"
    trial_type = "scene_description"
    game_name = "Scene Description"

    def compute_level(self, session_id: int) -> int:
        """
        Adapt difficulty based on previous completed trials.
        Uses average LLM score.
        """
        completed = SessionTrial.objects.filter(
            session_id=session_id,
            trial_type=self.trial_type,
            status="completed",
        )

        total = completed.count()
        if total == 0:
            return 1

        scores = []
        for trial in completed:
            resp = SceneDescriptionResponse.objects.filter(trial=trial).first()
            if resp and resp.llm_score is not None:
                scores.append(resp.llm_score)

        if not scores:
            return 1

        avg_score = sum(scores) / len(scores)

        if avg_score >= 80 and total >= 2:
            return 3
        elif avg_score >= 60:
            return 2
        return 1

    def build_trial(self, level: int, *, session_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Select a random scenario image from all available images (ignores level and scenario).
        Returns scenario data for the frontend.
        """
        scenarios = ScenarioImage.objects.filter(is_active=True).order_by("?")[:1]

        if not scenarios:
            return {
                "target": "placeholder",
                "scenario_id": None,
                "image_url": None,
                "prompt": "Please describe what you see in the image.",
                "ai_hint": "Take your time and describe as much as you can see.",
            }

        scenario = scenarios[0]
        image_url = scenario.image.url if scenario.image else None

        # Use generic prompt/hint since scenario is random
        prompt = "Look at this picture. Can you tell me what you see?"
        ai_hint = "Describe the main things — colors, objects, people, actions."

        return {
            "target": f"scenario_{scenario.id}",
            "scenario_id": scenario.id,
            "image_url": image_url,
            "title": getattr(scenario, "title", ""),
            "prompt": prompt,
            "ai_hint": ai_hint,
        }

    def evaluate(
        self,
        *,
        target: str,
        submit: Dict[str, Any],
        level: int,
        session_id: Optional[int] = None,
        trial=None,
    ) -> Dict[str, Any]:
        """
        Evaluate the child's description against the scenario image using multimodal Gemini.

        submit = {
          "scenario_id": <id>,
          "child_response": "child's description text"
        }

        If `trial` is passed (recommended), the full evaluation will be saved
        to SceneDescriptionResponse linked to that trial.
        """
        scenario_id = submit.get("scenario_id")
        child_response = (submit.get("child_response") or "").strip()

        if not scenario_id or not child_response:
            return {
                "success": False,
                "score": 0,
                "feedback": "Please provide a description.",
                "llm_score": 0,
                "clarity_score": 0,
                "completeness_score": 0,
                "key_elements_found": [],
                "strengths": "",
                "areas_for_improvement": "",
            }

        try:
            scenario = ScenarioImage.objects.get(id=scenario_id)
        except ScenarioImage.DoesNotExist:
            return {
                "success": False,
                "score": 0,
                "feedback": "Scenario not found.",
                "llm_score": 0,
                "clarity_score": 0,
                "completeness_score": 0,
                "key_elements_found": [],
                "strengths": "",
                "areas_for_improvement": "",
            }

        image_bytes, image_mime = _image_to_bytes(scenario.image) if scenario.image else (b"", "")

        eval_result = evaluate_scene_description(
            image_bytes=image_bytes,
            image_mime=image_mime,
            child_response=child_response,
            expected_description=getattr(scenario, "expected_description", "") or "",
            key_elements=getattr(scenario, "key_elements", None) or [],
        )

        llm_score = int(eval_result.get("llm_score", 50))
        success = llm_score >= 60

        feedback = eval_result.get("feedback", "")
        if eval_result.get("error"):
            feedback = f"{feedback} [Note: {eval_result['error']}]"

        # Save response
        if trial is not None:
            SceneDescriptionResponse.objects.create(
                trial=trial,
                scenario=scenario,
                child_response=child_response,
                llm_feedback=eval_result.get("feedback", ""),
                llm_score=llm_score,
                key_elements_found=eval_result.get("key_elements_found", []),
                clarity_score=eval_result.get("clarity_score", 0),
                completeness_score=eval_result.get("completeness_score", 0),
            )

        return {
            "success": success,
            "score": llm_score // 10,  # 0-100 -> 0-10
            "feedback": feedback,
            "llm_score": llm_score,
            "clarity_score": eval_result.get("clarity_score", 5),
            "completeness_score": eval_result.get("completeness_score", 5),
            "key_elements_found": eval_result.get("key_elements_found", []),
            "strengths": eval_result.get("strengths", ""),
            "areas_for_improvement": eval_result.get("areas_for_improvement", ""),
        }
