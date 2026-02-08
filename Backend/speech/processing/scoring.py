"""
Target alignment scoring — compare ASR transcript to expected text.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher


def compute_target_score(transcript: str, expected_text: str) -> dict:
    """
    Compare transcript to expected text. Returns scoring dict.
    """
    if not expected_text:
        return {}

    transcript_clean = _normalize(transcript)
    expected_clean = _normalize(expected_text)

    transcript_words = transcript_clean.split()
    expected_words = expected_clean.split()

    # Text similarity (SequenceMatcher ratio)
    text_similarity = SequenceMatcher(None, transcript_clean, expected_clean).ratio()

    # Keyword match
    expected_set = set(expected_words)
    found = set(w for w in transcript_words if w in expected_set)
    missing = expected_set - found
    extra = set(transcript_words) - expected_set

    keyword_match = len(found) / len(expected_set) if expected_set else 1.0

    # Simple WER proxy
    wer = _simple_wer(expected_words, transcript_words)

    # Exact match
    exact_match = transcript_clean == expected_clean

    return {
        "keyword_match": round(keyword_match, 3),
        "text_similarity": round(text_similarity, 3),
        "wer_proxy": round(wer, 3),
        "exact_match": exact_match,
        "expected_words": expected_words,
        "transcript_words": transcript_words,
        "found_keywords": list(found),
        "missing_keywords": list(missing),
        "extra_words": list(extra),
    }


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, normalize whitespace."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _simple_wer(reference: list[str], hypothesis: list[str]) -> float:
    """
    Simple word error rate (edit distance / reference length).
    """
    if not reference:
        return 0.0 if not hypothesis else 1.0

    n = len(reference)
    m = len(hypothesis)

    # DP table
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if reference[i - 1] == hypothesis[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,      # deletion
                d[i][j - 1] + 1,      # insertion
                d[i - 1][j - 1] + cost  # substitution
            )

    return d[n][m] / n
