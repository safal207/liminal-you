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

