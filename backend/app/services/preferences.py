"""In-memory storage for lightweight preference flags."""
from __future__ import annotations

from typing import Dict

_ASTRO_OPT_OUT: Dict[str, bool] = {}


def get_astro_opt_out(subject: str) -> bool:
    return _ASTRO_OPT_OUT.get(subject, False)


def set_astro_opt_out(subject: str, value: bool) -> None:
    _ASTRO_OPT_OUT[subject] = value
