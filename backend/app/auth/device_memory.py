"""Device Memory integration with liminal-voice-core."""
from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DeviceProfile:
    """Device profile from liminal-voice-core Device Memory."""

    device_id: str
    user_id: str
    first_seen: float
    last_seen: float
    interaction_count: int
    emotional_seed: List[float]  # PAD vector
    trust_level: float  # 0.0-1.0
    tags: List[str]

    def to_dict(self) -> Dict:
        return {
            "device_id": self.device_id,
            "user_id": self.user_id,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "interaction_count": self.interaction_count,
            "emotional_seed": self.emotional_seed,
            "trust_level": self.trust_level,
            "tags": self.tags,
        }


class DeviceMemoryStore:
    """In-memory device memory store (mimics liminal-voice-core)."""

    def __init__(self):
        self._devices: Dict[str, DeviceProfile] = {}
        self._user_devices: Dict[str, List[str]] = {}  # user_id -> [device_ids]

    def generate_device_id(self, user_agent: str, ip: str, user_id: str) -> str:
        """Generate stable device ID from fingerprint.

        Args:
            user_agent: User-Agent header
            ip: IP address
            user_id: User identifier

        Returns:
            Device ID (SHA256 hash)
        """
        fingerprint = f"{user_agent}:{ip}:{user_id}"
        device_id = hashlib.sha256(fingerprint.encode()).hexdigest()[:16]
        return device_id

    def register_device(
        self,
        device_id: str,
        user_id: str,
        emotional_seed: List[float] | None = None,
        tags: List[str] | None = None,
    ) -> DeviceProfile:
        """Register or update device profile.

        Args:
            device_id: Device identifier
            user_id: User identifier
            emotional_seed: Initial PAD vector
            tags: Device tags

        Returns:
            Device profile
        """
        now = time.time()

        if device_id in self._devices:
            # Update existing device
            profile = self._devices[device_id]
            profile.last_seen = now
            profile.interaction_count += 1

            # Update emotional seed with EMA
            if emotional_seed:
                alpha = 0.15  # Same as liminal-voice-core
                profile.emotional_seed = [
                    old * (1 - alpha) + new * alpha
                    for old, new in zip(profile.emotional_seed, emotional_seed)
                ]

            # Increase trust with more interactions
            profile.trust_level = min(1.0, profile.trust_level + 0.05)

            logger.info("Updated device %s for user %s (interactions: %d)", device_id, user_id, profile.interaction_count)
        else:
            # Create new device profile
            profile = DeviceProfile(
                device_id=device_id,
                user_id=user_id,
                first_seen=now,
                last_seen=now,
                interaction_count=1,
                emotional_seed=emotional_seed or [0.5, 0.35, 0.45],
                trust_level=0.1,  # Start with low trust
                tags=tags or [],
            )

            self._devices[device_id] = profile

            # Track user's devices
            if user_id not in self._user_devices:
                self._user_devices[user_id] = []
            self._user_devices[user_id].append(device_id)

            logger.info("Registered new device %s for user %s", device_id, user_id)

        return profile

    def get_device(self, device_id: str) -> Optional[DeviceProfile]:
        """Get device profile by ID.

        Args:
            device_id: Device identifier

        Returns:
            Device profile or None
        """
        return self._devices.get(device_id)

    def get_user_devices(self, user_id: str) -> List[DeviceProfile]:
        """Get all devices for a user.

        Args:
            user_id: User identifier

        Returns:
            List of device profiles
        """
        device_ids = self._user_devices.get(user_id, [])
        return [self._devices[did] for did in device_ids if did in self._devices]

    def update_emotional_seed(self, device_id: str, pad: List[float]) -> None:
        """Update device's emotional seed.

        Args:
            device_id: Device identifier
            pad: PAD vector [Pleasure, Arousal, Dominance]
        """
        if device_id in self._devices:
            profile = self._devices[device_id]
            alpha = 0.15

            profile.emotional_seed = [
                old * (1 - alpha) + new * alpha
                for old, new in zip(profile.emotional_seed, pad)
            ]

            logger.debug("Updated emotional seed for device %s: %s", device_id, profile.emotional_seed)

    def calculate_resonance(self, device1_id: str, device2_id: str) -> float:
        """Calculate resonance between two devices based on emotional seeds.

        Args:
            device1_id: First device ID
            device2_id: Second device ID

        Returns:
            Resonance score (0.0-1.0)
        """
        profile1 = self._devices.get(device1_id)
        profile2 = self._devices.get(device2_id)

        if not profile1 or not profile2:
            return 0.0

        # Calculate cosine similarity between emotional seeds
        seed1 = profile1.emotional_seed
        seed2 = profile2.emotional_seed

        dot_product = sum(a * b for a, b in zip(seed1, seed2))
        magnitude1 = sum(a * a for a in seed1) ** 0.5
        magnitude2 = sum(b * b for b in seed2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        similarity = dot_product / (magnitude1 * magnitude2)

        # Normalize to 0-1 range (cosine is -1 to 1)
        resonance = (similarity + 1) / 2

        return resonance

    def get_stats(self) -> Dict:
        """Get device memory statistics.

        Returns:
            Statistics dict
        """
        total_interactions = sum(p.interaction_count for p in self._devices.values())
        avg_trust = (
            sum(p.trust_level for p in self._devices.values()) / len(self._devices)
            if self._devices
            else 0.0
        )

        return {
            "total_devices": len(self._devices),
            "total_users": len(self._user_devices),
            "total_interactions": total_interactions,
            "avg_trust_level": round(avg_trust, 3),
        }


# Global device memory instance
_device_memory: DeviceMemoryStore | None = None


def get_device_memory() -> DeviceMemoryStore:
    """Get global device memory instance."""
    global _device_memory
    if _device_memory is None:
        _device_memory = DeviceMemoryStore()
    return _device_memory
