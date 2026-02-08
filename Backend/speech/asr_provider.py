from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class ASRResult:
    text: str
    confidence: Optional[float] = None


class ASRHTTPProvider:
    """
    Calls an external ASR service over HTTP.
    This keeps your backend scalable and avoids embedding heavy ML in Django.
    Expected endpoint:
      POST {ASR_HTTP_URL}
      body: {"audio_url": "..."} OR {"audio_path": "..."} depending on your infra.
    Expected response:
      {"text": "...", "confidence": 0.93}
    """

    def __init__(self, url: str, timeout_seconds: int = 60):
        self.url = url
        self.timeout_seconds = timeout_seconds

    def transcribe(self, payload: dict) -> ASRResult:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
            out = json.loads(raw)
        return ASRResult(text=out.get("text", ""), confidence=out.get("confidence"))
