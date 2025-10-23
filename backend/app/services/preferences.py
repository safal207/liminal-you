"""In-memory storage for lightweight preference flags."""
from __future__ import annotations

from typing import Dict

_ASTRO_OPT_OUT: Dict[str, bool] = {}
_FEEDBACK_ENABLED: Dict[str, bool] = {}


def get_astro_opt_out(subject: str) -> bool:
    return _ASTRO_OPT_OUT.get(subject, False)


def set_astro_opt_out(subject: str, value: bool) -> None:
    _ASTRO_OPT_OUT[subject] = value


def get_feedback_enabled(subject: str) -> bool:
    return _FEEDBACK_ENABLED.get(subject, True)


def set_feedback_enabled(subject: str, value: bool) -> None:
    _FEEDBACK_ENABLED[subject] = value
