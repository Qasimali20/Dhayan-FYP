from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

from django.conf import settings
from django.http import FileResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError


def _safe_text(s: str) -> str:
    s = (s or "").strip()
    s = " ".join(s.split())
    return s


def _tts_cache_dir() -> Path:
    base = Path(getattr(settings, "MEDIA_ROOT", "media"))
    out = base / "tts_cache" / "ja"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _hash_key(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p or "").encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()


def _piper_model_path() -> str:
    # env var preferred; fallback to settings
    return os.environ.get("PIPER_MODEL_PATH") or getattr(settings, "PIPER_MODEL_PATH", "")


def _generate_wav_with_piper(text: str, wav_path: Path) -> None:
    model = _piper_model_path()
    if not model:
        raise ValidationError("PIPER_MODEL_PATH is not configured on the server.")

    # piper CLI creates wav from stdin
    # command: piper --model <model.onnx> --output_file <out.wav>
    cmd = ["piper", "--model", model, "--output_file", str(wav_path)]
    try:
        subprocess.run(cmd, input=text.encode("utf-8"), check=True)
    except FileNotFoundError:
        raise ValidationError("piper binary not found. Did you install piper-tts?")
    except subprocess.CalledProcessError as e:
        raise ValidationError(f"Piper TTS failed: {e}")


class JATTSAPIView(APIView):
    """
    GET /api/v1/therapy/games/ja/tts/?text=Look%20at%20the%20cat
    Returns audio/wav, cached by hash.

    Auth required (so only therapists can generate/play).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        text = _safe_text(request.query_params.get("text", ""))
        if not text:
            raise ValidationError("Missing text")

        # You can optionally accept voice later. For now keep single voice.
        voice = request.query_params.get("voice", "en_amy_low")

        key = _hash_key("ja", voice, text)
        cache_dir = _tts_cache_dir()
        wav_path = cache_dir / f"{key}.wav"

        if not wav_path.exists() or wav_path.stat().st_size < 1024:
            _generate_wav_with_piper(text, wav_path)

        # FileResponse streams efficiently
        resp = FileResponse(open(wav_path, "rb"), content_type="audio/wav")
        resp["Cache-Control"] = "public, max-age=31536000, immutable"
        resp["Content-Disposition"] = 'inline; filename="prompt.wav"'
        return resp
