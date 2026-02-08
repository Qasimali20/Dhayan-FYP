from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List


@dataclass
class TrialPayload:
    """What engine returns to the client for a new running trial."""
    trial_id: int
    game: str
    trial_type: str
    level: int
    prompt: str
    options: List[str]
    time_limit_ms: int = 10000
    highlight: Optional[str] = None

    # If you want to hide target from client later, keep it None in production
    target: Optional[str] = None

    # AI assistant signals
    ai_hint: Optional[str] = None
    ai_reason: Optional[str] = None

    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubmitInput:
    clicked: str
    response_time_ms: int
    timed_out: bool = False


@dataclass
class SubmitResult:
    success: bool
    score: int
    feedback: str = ""
    telemetry: Dict[str, Any] = field(default_factory=dict)

    # AI assistant (what to do next)
    ai_recommendation: Optional[str] = None
    ai_reason: Optional[str] = None

    # If the submit finishes the whole session
    session_completed: bool = False
    summary: Optional[Dict[str, Any]] = None
