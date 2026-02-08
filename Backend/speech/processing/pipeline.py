"""
Speech audio processing pipeline.

Steps:
  1. Normalize audio (mono, 16kHz WAV)
  2. Run VAD  (silero-vad)
  3. Run ASR  (faster-whisper / Whisper)
  4. Compute prosody & voice features
  5. Target alignment scoring
  6. Generate rule-based feedback
"""
from __future__ import annotations

import io
import logging
import math
import struct
import tempfile
import wave
from pathlib import Path
from typing import Optional

from django.utils import timezone

from speech.processing.features import compute_features
from speech.processing.feedback import generate_feedback
from speech.processing.scoring import compute_target_score
from speech.processing.vad import run_vad

logger = logging.getLogger(__name__)


# ─── Audio Normalization ────────────────────────────────────────────────────

def _normalize_to_wav16k(file_path: str) -> str:
    """
    Convert any audio file to mono 16kHz WAV.
    Returns path to temp WAV file.

    For MVP we use a simple approach:
    - If it's already wav/16k/mono, just return
    - Otherwise, try pydub (if installed) or fallback to raw copy
    """
    out_path = tempfile.mktemp(suffix=".wav")

    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        audio.export(out_path, format="wav")
        return out_path
    except ImportError:
        logger.warning("pydub not installed — cannot normalize non-WAV audio")
    except Exception as e:
        logger.error(f"pydub normalization failed: {e}")

    # Fallback: try reading as wav directly
    try:
        with wave.open(file_path, "rb") as wf:
            if wf.getnchannels() == 1 and wf.getframerate() == 16000:
                return file_path  # already good
    except Exception:
        pass

    # Last resort: copy as-is (ASR will try its best)
    import shutil
    shutil.copy2(file_path, out_path)
    return out_path


def _get_wav_duration_ms(file_path: str) -> int:
    """Get duration of WAV in milliseconds."""
    try:
        with wave.open(file_path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return int((frames / rate) * 1000)
    except Exception as e:
        logger.warning(f"wave.open failed for duration: {e}")
        # Fallback: try pydub
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            return len(audio)
        except Exception:
            pass
        return 0


def _read_wav_samples(file_path: str) -> tuple[list[float], int]:
    """Read WAV file and return (samples_as_floats, sample_rate)."""
    try:
        with wave.open(file_path, "rb") as wf:
            n_frames = wf.getnframes()
            sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            raw = wf.readframes(n_frames)

        if sample_width == 2:
            fmt = f"<{n_frames * n_channels}h"
            int_samples = struct.unpack(fmt, raw)
        elif sample_width == 1:
            int_samples = [b - 128 for b in raw]
        else:
            return [], sample_rate

        # Mix to mono if needed
        if n_channels > 1:
            mono = []
            for i in range(0, len(int_samples), n_channels):
                mono.append(sum(int_samples[i:i + n_channels]) / n_channels)
            int_samples = mono

        max_val = 2 ** (sample_width * 8 - 1)
        samples = [s / max_val for s in int_samples]
        return samples, sample_rate
    except Exception as e:
        logger.warning(f"wave.open failed for samples: {e}")
        # Fallback: try pydub to extract raw samples
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
            raw = audio.raw_data
            n_frames = len(raw) // 2
            int_samples = struct.unpack(f"<{n_frames}h", raw)
            samples = [s / 32768.0 for s in int_samples]
            logger.info(f"pydub fallback read {len(samples)} samples")
            return samples, 16000
        except Exception as e2:
            logger.error(f"pydub fallback also failed: {e2}")
        return [], 16000


# ─── ASR ────────────────────────────────────────────────────────────────────

def _run_asr(wav_path: str, language: str = "en") -> dict:
    """
    Run ASR on normalized WAV. Returns:
      {"text": "...", "segments": [...], "language": "en", "model": "..."}
    """
    # Try faster-whisper first
    try:
        from faster_whisper import WhisperModel
        model_size = "base"
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(wav_path, language=language if language != "auto" else None)
        seg_list = []
        full_text = ""
        for seg in segments:
            seg_list.append({
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
            })
            full_text += seg.text

        return {
            "text": full_text.strip(),
            "segments": seg_list,
            "language": info.language if hasattr(info, "language") else language,
            "model": f"faster-whisper-{model_size}",
        }
    except ImportError:
        pass

    # Try openai-whisper
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(wav_path, language=language if language != "auto" else None)
        seg_list = []
        for seg in result.get("segments", []):
            seg_list.append({
                "start": round(seg["start"], 3),
                "end": round(seg["end"], 3),
                "text": seg["text"].strip(),
            })
        return {
            "text": result.get("text", "").strip(),
            "segments": seg_list,
            "language": result.get("language", language),
            "model": "whisper-base",
        }
    except ImportError:
        pass

    # Fallback: no ASR available
    logger.warning("No ASR engine available (install faster-whisper or openai-whisper)")
    return {
        "text": "",
        "segments": [],
        "language": language,
        "model": "none",
        "error": "No ASR engine installed. Install faster-whisper for best results.",
    }


# ─── Main Pipeline ──────────────────────────────────────────────────────────

def process_speech_audio(
    audio_file_path: str,
    expected_text: str = "",
    language: str = "en",
    activity_category: str = "",
) -> dict:
    """
    Full speech processing pipeline. Returns a dict with all analysis results.
    """
    result = {
        "transcript_text": "",
        "transcript_json": {},
        "vad_json": {},
        "features_json": {},
        "target_score_json": {},
        "feedback_json": {},
        "model_versions": {},
    }

    # 1. Normalize audio
    try:
        wav_path = _normalize_to_wav16k(audio_file_path)
    except Exception as e:
        logger.error(f"Audio normalization failed: {e}")
        wav_path = audio_file_path  # try with original

    # 2. Read samples for feature extraction
    samples, sample_rate = _read_wav_samples(wav_path)
    duration_ms = _get_wav_duration_ms(wav_path)
    logger.info(f"Pipeline: {len(samples)} samples, {sample_rate}Hz, {duration_ms}ms duration")

    # 3. Run VAD
    vad_result = run_vad(samples, sample_rate, duration_ms)
    result["vad_json"] = vad_result

    # 4. Run ASR
    asr_result = _run_asr(wav_path, language)
    result["transcript_text"] = asr_result.get("text", "")
    result["transcript_json"] = {
        "segments": asr_result.get("segments", []),
        "language": asr_result.get("language", language),
    }
    result["model_versions"]["asr"] = asr_result.get("model", "unknown")
    result["model_versions"]["vad"] = vad_result.get("model", "energy-based")

    # 5. Compute prosody / voice features
    features = compute_features(samples, sample_rate, duration_ms, vad_result, asr_result)
    result["features_json"] = features

    # 6. Target alignment scoring
    if expected_text:
        target_score = compute_target_score(result["transcript_text"], expected_text)
        result["target_score_json"] = target_score

    # 7. Generate feedback
    feedback = generate_feedback(
        features=features,
        vad=vad_result,
        transcript=result["transcript_text"],
        expected_text=expected_text,
        target_score=result.get("target_score_json", {}),
        activity_category=activity_category,
    )
    result["feedback_json"] = feedback

    # Cleanup temp file
    import os
    if wav_path != audio_file_path and os.path.exists(wav_path):
        try:
            os.unlink(wav_path)
        except Exception:
            pass

    return result
