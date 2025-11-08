"""Witness layer — metacognition and presence tracking.

This module implements the "Witness" concept from Buddhist philosophy:
the observer who watches the mind without attachment.

Components:
- metrics: Calculate presence and attention quality scores
- models: Data structures for witness snapshots
- storage: In-memory storage for witness data
- tracker: High-level tracking logic
"""

from .metrics import WitnessMetrics
from .models import WitnessSnapshot, WitnessState
from .storage import WitnessStorage, get_witness_storage
from .tracker import WitnessTracker

__all__ = [
    "WitnessMetrics",
    "WitnessSnapshot",
    "WitnessState",
    "WitnessStorage",
    "get_witness_storage",
    "WitnessTracker",
]
