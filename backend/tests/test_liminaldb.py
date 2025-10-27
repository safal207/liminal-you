import asyncio

import pytest

from app.liminaldb.storage import LiminalDBStorage
from app.models.reflection import ReflectionCreate


class DummyClient:
    def __init__(self):
        self.connected = False
        self.sent = []
        self._handlers = {}

    async def connect(self):
        self.connected = True

    async def disconnect(self):
        self.connected = False

    def on_event(self, ev, handler):
        self._handlers.setdefault(ev, []).append(handler)

    async def awaken_set(self, model):
        return {"status": "active", "id": model.id}

    async def awaken_get(self, model_id: str):
        return {"status": "active", "id": model_id, "edges": [], "latent_traits": {}}

    async def write(self, pattern: str, strength: float, tags=None):
        self.sent.append((pattern, strength, tags))
        return {"status": "ok"}

    async def affect(self, pattern: str, strength: float, tags=None):
        self.sent.append((pattern, strength, tags))
        return {"status": "ok"}


@pytest.mark.asyncio
async def test_storage_add_reflection_with_dummy_client():
    storage = LiminalDBStorage(client=DummyClient())
    await storage.initialize()

    payload = ReflectionCreate(
        from_node='node-alpha',
        to_user='user-001',
        message='hello',
        emotion='радость',
        pad=[0.8, 0.6, 0.6],
    )

    reflection = await storage.add_reflection(payload, author='user-001')
    assert reflection.id
    assert reflection.emotion == 'радость'
    assert any('reflection' in p[0] for p in storage.client.sent)


@pytest.mark.asyncio
async def test_pad_auto_calculation_with_known_emotion():
    """Test that PAD is auto-calculated for known emotions when not provided."""
    storage = LiminalDBStorage(client=DummyClient())
    await storage.initialize()

    # Create reflection without PAD - should auto-calculate from emotion
    payload = ReflectionCreate(
        from_node='node-alpha',
        to_user='user-001',
        message='Testing auto-calculation',
        emotion='надежда',  # hope: [0.75, 0.45, 0.52]
        pad=None,
    )

    reflection = await storage.add_reflection(payload, author='user-001')

    # Verify PAD was auto-calculated
    assert reflection.id
    assert reflection.emotion == 'надежда'
    assert reflection.pad is not None
    assert reflection.pad == [0.75, 0.45, 0.52]

    # Verify impulse was sent with calculated strength
    assert len(storage.client.sent) > 0
    pattern, strength, tags = storage.client.sent[-1]
    assert 'reflection' in pattern
    assert 'надежда' in pattern
    # Strength should be (0.75 + 0.45) / 2 = 0.6
    assert abs(strength - 0.6) < 0.01


@pytest.mark.asyncio
async def test_pad_auto_calculation_with_unknown_emotion():
    """Test that PAD falls back to default for unknown emotions."""
    storage = LiminalDBStorage(client=DummyClient())
    await storage.initialize()

    # Create reflection with unknown emotion - should use default PAD
    payload = ReflectionCreate(
        from_node='node-beta',
        to_user='user-002',
        message='Unknown emotion test',
        emotion='hope',  # English name not in Russian dict -> default [0.5, 0.35, 0.45]
        pad=None,
    )

    reflection = await storage.add_reflection(payload, author='user-002')

    # Verify default PAD was used
    assert reflection.id
    assert reflection.emotion == 'hope'
    assert reflection.pad is not None
    assert reflection.pad == [0.5, 0.35, 0.45]

    # Verify strength calculation
    pattern, strength, tags = storage.client.sent[-1]
    # Strength should be (0.5 + 0.35) / 2 = 0.425
    assert abs(strength - 0.425) < 0.01


@pytest.mark.asyncio
async def test_pad_explicit_value_overrides_auto_calculation():
    """Test that explicitly provided PAD is not overridden."""
    storage = LiminalDBStorage(client=DummyClient())
    await storage.initialize()

    # Explicitly provide PAD - should use it instead of auto-calculation
    custom_pad = [0.9, 0.8, 0.7]
    payload = ReflectionCreate(
        from_node='node-gamma',
        to_user='user-003',
        message='Custom PAD test',
        emotion='радость',  # Would auto-calculate to [0.85, 0.55, 0.6]
        pad=custom_pad,
    )

    reflection = await storage.add_reflection(payload, author='user-003')

    # Verify custom PAD was used
    assert reflection.pad == custom_pad

    # Verify strength uses custom PAD
    pattern, strength, tags = storage.client.sent[-1]
    # Strength should be (0.9 + 0.8) / 2 = 0.85
    assert abs(strength - 0.85) < 0.01
