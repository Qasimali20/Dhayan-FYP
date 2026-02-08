"""
Rule-based feedback generation for speech therapy.
Therapist-approved suggestions based on analysis metrics.
"""
from __future__ import annotations


def generate_feedback(
    features: dict,
    vad: dict,
    transcript: str,
    expected_text: str,
    target_score: dict,
    activity_category: str = "",
) -> dict:
    """
    Generate therapist-friendly feedback and suggestions.
    Returns: {"suggestions": [...], "severity": "info|warning|concern", "summary": "..."}
    """
    suggestions = []
    severity = "info"

    word_count = features.get("word_count", 0)
    pause_ratio = features.get("pause_ratio", 0)
    speech_rate = features.get("estimated_speech_rate_wpm", 0)
    response_latency = features.get("response_latency_ms", 0)
    speech_continuity = features.get("speech_continuity", 0)
    keyword_match = target_score.get("keyword_match", None)
    text_similarity = target_score.get("text_similarity", None)
    missing_keywords = target_score.get("missing_keywords", [])

    # ─── No speech detected ────────────────────────────────────────────
    if not transcript or word_count == 0:
        suggestions.append({
            "type": "no_speech",
            "message": "No speech detected. Consider modeling the response for the child "
                       "and using a full verbal prompt (Level 0).",
            "action": "Increase support to Level 0 (full model). "
                      "Say the target word/phrase, then ask the child to repeat.",
        })
        severity = "concern"
        return {"suggestions": suggestions, "severity": severity, "summary": "No speech detected"}

    # ─── Short response in question tasks ──────────────────────────────
    if activity_category in ("wh_questions", "yes_no_questions"):
        if word_count < 3:
            suggestions.append({
                "type": "short_response",
                "message": f"Response was only {word_count} word(s). Encourage longer answers.",
                "action": "Model a sentence starter. For example: 'It is a ___' or 'The ___ is ___'.",
            })
            if severity == "info":
                severity = "warning"

    # ─── High pause ratio ──────────────────────────────────────────────
    if pause_ratio > 0.6 and word_count > 0:
        suggestions.append({
            "type": "high_pause_ratio",
            "message": f"Speech had {int(pause_ratio * 100)}% silence between words. "
                       "Child may need extra processing time.",
            "action": "Try shorter prompts, allow extra wait time, "
                      "or provide a visual cue alongside the verbal prompt.",
        })
        if severity == "info":
            severity = "warning"

    # ─── Slow speech rate ──────────────────────────────────────────────
    if 0 < speech_rate < 60:
        suggestions.append({
            "type": "slow_speech_rate",
            "message": f"Speech rate is approximately {int(speech_rate)} words/minute (typical: 100-150 wpm).",
            "action": "This is normal for practice. If persistent, consider speech pacing exercises.",
        })

    # ─── Long response latency ─────────────────────────────────────────
    if response_latency > 5000:
        suggestions.append({
            "type": "long_latency",
            "message": f"Response latency was {response_latency / 1000:.1f}s. "
                       "Child needed extra time to begin speaking.",
            "action": "Ensure prompt is understood. Try adding a gesture or visual cue "
                      "before the verbal prompt.",
        })

    # ─── Target word scoring ──────────────────────────────────────────
    if keyword_match is not None:
        if keyword_match == 1.0:
            suggestions.append({
                "type": "target_match",
                "message": "All target words were produced correctly! ✅",
                "action": "Consider increasing difficulty or reducing prompt level.",
            })
        elif keyword_match >= 0.5:
            suggestions.append({
                "type": "partial_match",
                "message": f"Keyword match: {int(keyword_match * 100)}%. "
                           f"Missing: {', '.join(missing_keywords[:5])}",
                "action": "Repeat the activity with partial support (Level 1-2). "
                          "Emphasize the missing words.",
            })
            if severity == "info":
                severity = "warning"
        else:
            suggestions.append({
                "type": "low_match",
                "message": f"Only {int(keyword_match * 100)}% of target words produced. "
                           f"Missing: {', '.join(missing_keywords[:5])}",
                "action": "Increase support (Level 0-1). Model the full response, "
                          "then have the child repeat with you.",
            })
            severity = "concern"

    # ─── Repetition tasks: similarity check ────────────────────────────
    if activity_category in ("word_repetition", "phrase_repetition", "sentence_repetition"):
        if text_similarity is not None:
            if text_similarity >= 0.85:
                suggestions.append({
                    "type": "good_repetition",
                    "message": f"Good repetition! Similarity: {int(text_similarity * 100)}%.",
                    "action": "Ready to try the next difficulty level or reduce prompt support.",
                })
            elif text_similarity >= 0.5:
                suggestions.append({
                    "type": "partial_repetition",
                    "message": f"Partial repetition ({int(text_similarity * 100)}% match).",
                    "action": "Try breaking the phrase into smaller chunks. "
                              "Repeat each word separately, then combine.",
                })
            else:
                suggestions.append({
                    "type": "poor_repetition",
                    "message": f"Low repetition accuracy ({int(text_similarity * 100)}%).",
                    "action": "Simplify the target. Use a shorter word or add visual support.",
                })

    # ─── Repeated attempts without improvement ─────────────────────────
    # (This would need historical data — flag for future)

    # ─── Summary ───────────────────────────────────────────────────────
    summary_parts = []
    if word_count > 0:
        summary_parts.append(f"{word_count} words detected")
    if speech_rate > 0:
        summary_parts.append(f"{int(speech_rate)} wpm")
    if keyword_match is not None:
        summary_parts.append(f"{int(keyword_match * 100)}% target match")

    summary = ". ".join(summary_parts) if summary_parts else "Analysis complete"

    return {
        "suggestions": suggestions,
        "severity": severity,
        "summary": summary,
    }
