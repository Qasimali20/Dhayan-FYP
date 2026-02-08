"""
Speech feature extraction — prosody, energy, rate metrics.
"""
from __future__ import annotations

import math


def compute_features(
    samples: list[float],
    sample_rate: int,
    duration_ms: int,
    vad_result: dict,
    asr_result: dict,
) -> dict:
    """
    Compute prosody and voice features from audio samples.
    Returns feature dict for storage in features_json.
    """
    features = {
        "duration_ms": duration_ms,
        "speech_time_ms": vad_result.get("speech_time_ms", 0),
        "pause_count": vad_result.get("pause_count", 0),
        "pause_total_ms": vad_result.get("pause_total_ms", 0),
        "pause_ratio": vad_result.get("pause_ratio", 0),
    }

    # If VAD returned 0 speech_time but ASR found segments, estimate from ASR
    asr_segments = asr_result.get("segments", [])
    if features["speech_time_ms"] == 0 and asr_segments:
        # Reconstruct speech time from ASR segment timestamps
        asr_speech_ms = 0
        for seg in asr_segments:
            seg_dur = (seg.get("end", 0) - seg.get("start", 0)) * 1000
            asr_speech_ms += seg_dur
        if asr_speech_ms > 0:
            features["speech_time_ms"] = int(asr_speech_ms)
            features["pause_ratio"] = round(
                max(0, (duration_ms - asr_speech_ms) / max(duration_ms, 1)), 4
            ) if duration_ms > 0 else 0.0
            features["pause_total_ms"] = max(0, duration_ms - int(asr_speech_ms))

    # If duration is still 0 but ASR has segments, estimate duration from ASR
    if duration_ms == 0 and asr_segments:
        last_end = max(seg.get("end", 0) for seg in asr_segments)
        if last_end > 0:
            duration_ms = int(last_end * 1000)
            features["duration_ms"] = duration_ms

    # Speech rate (words per minute)
    transcript = asr_result.get("text", "")
    word_count = len(transcript.split()) if transcript else 0
    features["word_count"] = word_count

    speech_time_min = features["speech_time_ms"] / 60000 if features["speech_time_ms"] > 0 else 0
    features["estimated_speech_rate_wpm"] = round(word_count / speech_time_min, 1) if speech_time_min > 0 else 0

    # Energy statistics
    if samples:
        energies = [s ** 2 for s in samples]
        features["energy_mean"] = round(sum(energies) / len(energies), 6)
        if len(energies) > 1:
            mean = features["energy_mean"]
            variance = sum((e - mean) ** 2 for e in energies) / len(energies)
            features["energy_var"] = round(variance, 8)
        else:
            features["energy_var"] = 0.0

        # RMS energy
        features["energy_rms"] = round(math.sqrt(features["energy_mean"]), 4)
    else:
        features["energy_mean"] = 0.0
        features["energy_var"] = 0.0
        features["energy_rms"] = 0.0

    # Pitch estimation (simple zero-crossing rate as proxy)
    if samples and len(samples) > 1:
        zcr = _zero_crossing_rate(samples, sample_rate)
        features["pitch_proxy_zcr"] = round(zcr, 2)
        # Rough F0 estimate from ZCR (very approximate)
        features["pitch_estimate_hz"] = round(zcr / 2, 1) if zcr > 0 else 0
    else:
        features["pitch_proxy_zcr"] = 0
        features["pitch_estimate_hz"] = 0

    # Response latency: time from start to first speech segment
    vad_segments = vad_result.get("segments", [])
    if vad_segments:
        features["response_latency_ms"] = vad_segments[0].get("start_ms", 0)
    else:
        features["response_latency_ms"] = duration_ms  # no speech detected

    # Fluency indicators
    features["speech_continuity"] = 1.0 - features["pause_ratio"] if features["pause_ratio"] <= 1 else 0
    features["avg_pause_duration_ms"] = (
        round(features["pause_total_ms"] / features["pause_count"])
        if features["pause_count"] > 0 else 0
    )

    return features


def _zero_crossing_rate(samples: list[float], sample_rate: int) -> float:
    """Compute zero-crossing rate (crossings per second)."""
    crossings = 0
    for i in range(1, len(samples)):
        if (samples[i] >= 0) != (samples[i - 1] >= 0):
            crossings += 1

    duration_sec = len(samples) / sample_rate if sample_rate > 0 else 1
    return crossings / duration_sec if duration_sec > 0 else 0
