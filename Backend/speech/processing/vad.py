"""
Voice Activity Detection (VAD) — energy-based for MVP.
Falls back to silero-vad if installed.
"""
from __future__ import annotations

import math
from typing import Optional


def run_vad(samples: list[float], sample_rate: int, duration_ms: int) -> dict:
    """
    Run VAD on audio samples. Returns:
      {
        "segments": [{"start_ms": ..., "end_ms": ..., "is_speech": true}],
        "speech_time_ms": ...,
        "pause_count": ...,
        "pause_total_ms": ...,
        "pause_ratio": ...,
        "model": "..."
      }
    """
    # Try silero-vad first
    try:
        return _silero_vad(samples, sample_rate, duration_ms)
    except (ImportError, Exception):
        pass

    # Fallback: energy-based VAD
    return _energy_vad(samples, sample_rate, duration_ms)


def _silero_vad(samples: list[float], sample_rate: int, duration_ms: int) -> dict:
    """Use silero-vad model for speech detection."""
    import torch

    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        force_reload=False,
        onnx=True,
    )
    get_speech_timestamps = utils[0]

    tensor = torch.FloatTensor(samples)
    if sample_rate != 16000:
        # silero expects 16kHz
        import torchaudio
        tensor = torchaudio.functional.resample(tensor, sample_rate, 16000)
        sample_rate = 16000

    timestamps = get_speech_timestamps(tensor, model, sampling_rate=sample_rate)

    segments = []
    speech_ms = 0
    for ts in timestamps:
        start_ms = int(ts["start"] / sample_rate * 1000)
        end_ms = int(ts["end"] / sample_rate * 1000)
        segments.append({"start_ms": start_ms, "end_ms": end_ms, "is_speech": True})
        speech_ms += (end_ms - start_ms)

    # Calculate pauses
    pauses = _calculate_pauses(segments, duration_ms)

    return {
        "segments": segments,
        "speech_time_ms": speech_ms,
        "pause_count": pauses["count"],
        "pause_total_ms": pauses["total_ms"],
        "pause_ratio": round(pauses["total_ms"] / max(duration_ms, 1), 4),
        "model": "silero-vad-v4",
    }


def _energy_vad(samples: list[float], sample_rate: int, duration_ms: int) -> dict:
    """
    Simple energy-based VAD as fallback.
    Divides audio into 30ms frames, marks frames above energy threshold as speech.
    """
    if not samples:
        return {
            "segments": [],
            "speech_time_ms": 0,
            "pause_count": 0,
            "pause_total_ms": duration_ms,
            "pause_ratio": 1.0,
            "model": "energy-based",
        }

    frame_ms = 30
    frame_size = int(sample_rate * frame_ms / 1000)
    if frame_size == 0:
        frame_size = 1

    # Compute frame energies
    frame_energies = []
    for i in range(0, len(samples), frame_size):
        frame = samples[i:i + frame_size]
        if frame:
            energy = sum(s ** 2 for s in frame) / len(frame)
            frame_energies.append(energy)

    if not frame_energies:
        return {
            "segments": [],
            "speech_time_ms": 0,
            "pause_count": 0,
            "pause_total_ms": duration_ms,
            "pause_ratio": 1.0,
            "model": "energy-based",
        }

    # Threshold: mean + 0.3 * std (adaptive)
    mean_energy = sum(frame_energies) / len(frame_energies)
    variance = sum((e - mean_energy) ** 2 for e in frame_energies) / len(frame_energies)
    std_energy = math.sqrt(variance) if variance > 0 else 0
    threshold = mean_energy * 0.5 + std_energy * 0.1
    threshold = max(threshold, 0.001)  # minimum threshold

    # Mark speech frames
    speech_flags = [e > threshold for e in frame_energies]

    # Smooth: fill short gaps (< 100ms = ~3 frames)
    min_gap = max(1, int(100 / frame_ms))
    for i in range(len(speech_flags)):
        if not speech_flags[i]:
            # Check if surrounded by speech within min_gap
            left = any(speech_flags[max(0, i - min_gap):i])
            right = any(speech_flags[i + 1:min(len(speech_flags), i + min_gap + 1)])
            if left and right:
                speech_flags[i] = True

    # Build segments
    segments = []
    in_speech = False
    seg_start = 0
    speech_ms = 0

    for i, is_speech in enumerate(speech_flags):
        t_ms = i * frame_ms
        if is_speech and not in_speech:
            in_speech = True
            seg_start = t_ms
        elif not is_speech and in_speech:
            in_speech = False
            seg_end = t_ms
            segments.append({"start_ms": seg_start, "end_ms": seg_end, "is_speech": True})
            speech_ms += (seg_end - seg_start)

    # Close last segment
    if in_speech:
        seg_end = len(speech_flags) * frame_ms
        segments.append({"start_ms": seg_start, "end_ms": seg_end, "is_speech": True})
        speech_ms += (seg_end - seg_start)

    pauses = _calculate_pauses(segments, duration_ms)

    return {
        "segments": segments,
        "speech_time_ms": speech_ms,
        "pause_count": pauses["count"],
        "pause_total_ms": pauses["total_ms"],
        "pause_ratio": round(pauses["total_ms"] / max(duration_ms, 1), 4),
        "model": "energy-based",
    }


def _calculate_pauses(speech_segments: list[dict], duration_ms: int) -> dict:
    """Calculate pause metrics from speech segments."""
    if not speech_segments:
        return {"count": 0, "total_ms": duration_ms, "pauses": []}

    pauses = []
    # Pause before first speech
    if speech_segments[0]["start_ms"] > 200:  # ignore tiny leading silence
        pauses.append({"start_ms": 0, "end_ms": speech_segments[0]["start_ms"]})

    # Pauses between segments
    for i in range(1, len(speech_segments)):
        gap_start = speech_segments[i - 1]["end_ms"]
        gap_end = speech_segments[i]["start_ms"]
        if gap_end - gap_start > 100:  # pause > 100ms
            pauses.append({"start_ms": gap_start, "end_ms": gap_end})

    total_pause_ms = sum(p["end_ms"] - p["start_ms"] for p in pauses)

    return {
        "count": len(pauses),
        "total_ms": total_pause_ms,
        "pauses": pauses,
    }
