"""LiminalDB storage adapter for liminal-you."""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import List

from ..models.reflection import Reflection, ReflectionCreate
from ..models.user import User
from ..models.profile import Profile
from .client import LiminalDBClient, get_liminaldb_client, Impulse, ResonantModel

logger = logging.getLogger(__name__)


class LiminalDBStorage:
    """Storage adapter using LiminalDB as backend."""

    def __init__(self, client: LiminalDBClient | None = None):
        self.client = client or get_liminaldb_client()
        self._reflection_cache: List[Reflection] = []
        self._user_cache: dict[str, User] = {}
        self._profile_cache: dict[str, Profile] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize connection and create base models."""
        if self._initialized:
            return

        await self.client.connect()

        # Create global astro field model
        astro_model = ResonantModel(
            id="astro/global",
            persistence="snapshot",
            latent_traits={
                "pad_p": 0.5,
                "pad_a": 0.35,
                "pad_d": 0.45,
                "entropy": 0.0,
                "coherence": 1.0,
            },
            tags=["astro", "field", "global"],
        )

        try:
            await self.client.awaken_set(astro_model)
            logger.info("Initialized astro/global model in LiminalDB")
        except Exception as e:
            logger.warning("Could not initialize astro/global model: %s", e)

        # Subscribe to harmony events for astro field updates
        self.client.on_event("harmony", self._handle_harmony_event)
        self.client.on_event("introspect", self._handle_introspect_event)

        self._initialized = True
        logger.info("LiminalDB storage initialized")

    async def _handle_harmony_event(self, event: dict) -> None:
        """Handle harmony events from LiminalDB."""
        logger.debug("Harmony event: %s", event.get("meta", {}).get("status"))

    async def _handle_introspect_event(self, event: dict) -> None:
        """Handle introspect events from LiminalDB."""
        logger.debug("Introspect event for model: %s", event.get("id"))

    async def add_reflection(self, payload: ReflectionCreate, author: str | None = None) -> Reflection:
        """Store reflection as Write impulse in LiminalDB."""
        reflection_id = f"refl_{uuid.uuid4().hex[:12]}"
        reflection = Reflection(
            id=reflection_id,
            author=author or payload.from_node,
            content=payload.message,
            emotion=payload.emotion,
            pad=payload.pad,
        )

        # Store as impulse in LiminalDB
        pattern = f"reflection/{payload.emotion}/{author or payload.from_node}"
        tags = [
            "reflection",
            payload.emotion,
            author or payload.from_node,
            payload.to_user,
        ]

        # Encode reflection data in pattern for later retrieval
        # Pattern format: "reflection/<emotion>/<author>/<content_hash>"
        content_hash = str(abs(hash(payload.message)))[:8]
        pattern = f"reflection/{payload.emotion}/{author or payload.from_node}/{content_hash}"

        try:
            # Calculate strength from PAD if available
            strength = 0.7
            if payload.pad and len(payload.pad) >= 2:
                # Use pleasure and arousal to calculate strength
                strength = (payload.pad[0] + payload.pad[1]) / 2

            await self.client.write(
                pattern=pattern,
                strength=strength,
                tags=tags,
            )

            logger.info("Stored reflection %s in LiminalDB: %s", reflection_id, pattern)
        except Exception as e:
            logger.error("Failed to store reflection in LiminalDB: %s", e)
            # Continue anyway, keep in cache

        # Cache locally for fast retrieval
        self._reflection_cache.append(reflection)

        return reflection

    async def list_reflections(self) -> List[Reflection]:
        """List all reflections from cache."""
        # In a full implementation, query LiminalDB with Query impulse
        # For now, return cached reflections
        return list(self._reflection_cache)

    async def query_reflections(self, emotion: str | None = None, author: str | None = None) -> List[Reflection]:
        """Query reflections by emotion or author."""
        # Build pattern for query
        pattern_parts = ["reflection"]
        if emotion:
            pattern_parts.append(emotion)
        if author:
            pattern_parts.append(author)

        pattern = "/".join(pattern_parts)

        try:
            await self.client.query(pattern=pattern, strength=0.6)
            logger.info("Queried reflections with pattern: %s", pattern)
        except Exception as e:
            logger.error("Failed to query reflections: %s", e)

        # Filter from cache
        results = self._reflection_cache
        if emotion:
            results = [r for r in results if r.emotion == emotion]
        if author:
            results = [r for r in results if r.author == author]

        return results

    async def add_user(self, user: User) -> None:
        """Store user as ResonantModel in LiminalDB."""
        model = ResonantModel(
            id=f"user/{user.id}",
            persistence="snapshot",
            latent_traits={
                "created_at": time.time(),
            },
            tags=["user", user.name],
        )

        try:
            await self.client.awaken_set(model)
            logger.info("Created user model: user/%s", user.id)
        except Exception as e:
            logger.error("Failed to create user model: %s", e)

        self._user_cache[user.id] = user

    async def get_user(self, user_id: str) -> User | None:
        """Get user from cache or LiminalDB."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            result = await self.client.awaken_get(f"user/{user_id}")
            if result.get("status") in ("active", "primed", "sleeping"):
                # Reconstruct user from model
                tags = result.get("tags", [])
                name = tags[1] if len(tags) > 1 else user_id

                user = User(id=user_id, name=name)
                self._user_cache[user_id] = user
                return user
        except Exception as e:
            logger.error("Failed to get user from LiminalDB: %s", e)

        return None

    async def update_astro_field(self, pad: List[float], entropy: float, coherence: float) -> None:
        """Update global astro field in LiminalDB."""
        try:
            # Send affect impulse to update field
            pattern = f"astro/global/update"
            strength = coherence  # Use coherence as strength

            await self.client.affect(
                pattern=pattern,
                strength=strength,
                tags=["astro", "field", "update"],
            )

            logger.debug("Updated astro field: entropy=%.2f, coherence=%.2f", entropy, coherence)
        except Exception as e:
            logger.error("Failed to update astro field: %s", e)

    async def get_astro_field_state(self) -> dict:
        """Get current astro field state from LiminalDB."""
        try:
            result = await self.client.awaken_get("astro/global")
            if result.get("status"):
                traits = result.get("latent_traits", {})
                return {
                    "pad": [
                        traits.get("pad_p", 0.5),
                        traits.get("pad_a", 0.35),
                        traits.get("pad_d", 0.45),
                    ],
                    "entropy": traits.get("entropy", 0.0),
                    "coherence": traits.get("coherence", 1.0),
                }
        except Exception as e:
            logger.error("Failed to get astro field state: %s", e)

        return {
            "pad": [0.5, 0.35, 0.45],
            "entropy": 0.0,
            "coherence": 1.0,
        }

    async def create_resonance_edge(self, from_user: str, to_user: str, weight: float) -> None:
        """Create resonance edge between users in astro field."""
        try:
            # Get current astro model
            result = await self.client.awaken_get("astro/global")
            edges = result.get("edges", [])

            # Add new edge
            edge = {"from": f"user/{from_user}", "to": f"user/{to_user}", "weight": weight}
            edges.append(edge)

            # Update model
            model = ResonantModel(
                id="astro/global",
                edges=edges,
                persistence="snapshot",
                tags=["astro", "field", "global"],
            )

            await self.client.awaken_set(model)
            logger.info("Created resonance edge: %s -> %s (weight=%.2f)", from_user, to_user, weight)
        except Exception as e:
            logger.error("Failed to create resonance edge: %s", e)

    async def close(self) -> None:
        """Close LiminalDB connection."""
        if self._initialized:
            await self.client.disconnect()
            self._initialized = False
            logger.info("LiminalDB storage closed")


# Global storage instance
_storage: LiminalDBStorage | None = None


async def get_storage() -> LiminalDBStorage:
    """Get global LiminalDB storage instance."""
    global _storage
    if _storage is None:
        _storage = LiminalDBStorage()
        await _storage.initialize()
    return _storage
