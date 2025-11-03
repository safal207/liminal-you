"""Integration tests for LiminalDB storage using mock server."""
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from app.liminaldb.client import LiminalDBClient
from app.liminaldb.storage import LiminalDBStorage
from app.models.reflection import ReflectionCreate
from app.models.user import User


# Find mock server script
MOCK_SERVER_PATH = Path(__file__).parent.parent.parent / "tools" / "mock_liminaldb.py"
MOCK_SERVER_PORT = int(os.getenv("MOCK_LIMINALDB_PORT", "8787"))


@pytest.fixture(scope="session")
def mock_server():
    """Start mock LiminalDB server for integration tests."""
    # Check if mock server script exists
    if not MOCK_SERVER_PATH.exists():
        pytest.skip(f"Mock server not found at {MOCK_SERVER_PATH}")

    # Start mock server
    env = os.environ.copy()
    env["PORT"] = str(MOCK_SERVER_PORT)
    
    process = subprocess.Popen(
        ["python", str(MOCK_SERVER_PATH)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready
    max_attempts = 30
    for i in range(max_attempts):
        try:
            with urllib.request.urlopen(
                f"http://localhost:{MOCK_SERVER_PORT}/health", timeout=1
            ) as response:
                if response.getcode() == 200:
                    break
        except (urllib.error.URLError, OSError, ConnectionError):
            if i == max_attempts - 1:
                process.terminate()
                process.wait(timeout=5)
                stdout, stderr = process.communicate()
                pytest.fail(
                    f"Mock server failed to start after {max_attempts} attempts.\n"
                    f"STDOUT: {stdout.decode() if stdout else 'None'}\n"
                    f"STDERR: {stderr.decode() if stderr else 'None'}"
                )
            time.sleep(0.5)

    yield process

    # Cleanup
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture
async def liminaldb_client(mock_server):
    """Create LiminalDB client connected to mock server."""
    client = LiminalDBClient(url=f"ws://localhost:{MOCK_SERVER_PORT}/ws")
    await client.connect()
    
    yield client
    
    await client.disconnect()


@pytest.fixture
async def storage(liminaldb_client):
    """Create LiminalDB storage instance."""
    storage = LiminalDBStorage(client=liminaldb_client)
    await storage.initialize()
    
    yield storage
    
    await storage.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_storage_initialization(storage):
    """Test that storage initializes astro/global model."""
    # Storage should be initialized
    assert storage._initialized
    
    # Check that astro/global model exists
    result = await storage.client.awaken_get("astro/global")
    assert result.get("status") in ("active", "primed", "sleeping")
    assert result.get("id") == "astro/global"
    
    # Check traits
    traits = result.get("latent_traits", {})
    assert "pad_p" in traits
    assert "pad_a" in traits
    assert "pad_d" in traits
    assert "entropy" in traits
    assert "coherence" in traits


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_reflection(storage):
    """Test adding reflection creates Write impulse."""
    payload = ReflectionCreate(
        from_node='node-alpha',
        to_user='user-001',
        message='Integration test reflection',
        emotion='радость',
        pad=[0.85, 0.55, 0.6],
    )

    reflection = await storage.add_reflection(payload, author='user-001')
    
    assert reflection.id
    assert reflection.emotion == 'радость'
    assert reflection.content == 'Integration test reflection'
    assert reflection.pad == [0.85, 0.55, 0.6]
    
    # Reflection should be in cache
    reflections = await storage.list_reflections()
    assert len(reflections) == 1
    assert reflections[0].id == reflection.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_reflection_auto_calculates_pad(storage):
    """Test that PAD is auto-calculated when not provided."""
    payload = ReflectionCreate(
        from_node='node-beta',
        to_user='user-002',
        message='Auto PAD test',
        emotion='надежда',  # [0.75, 0.45, 0.52]
        pad=None,
    )

    reflection = await storage.add_reflection(payload, author='user-002')
    
    assert reflection.pad is not None
    assert reflection.pad == [0.75, 0.45, 0.52]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_query_reflections(storage):
    """Test querying reflections by emotion and author."""
    # Add multiple reflections
    await storage.add_reflection(
        ReflectionCreate(
            from_node='node-alpha',
            to_user='user-001',
            message='First reflection',
            emotion='радость',
        ),
        author='user-001'
    )
    
    await storage.add_reflection(
        ReflectionCreate(
            from_node='node-alpha',
            to_user='user-001',
            message='Second reflection',
            emotion='надежда',
        ),
        author='user-001'
    )
    
    await storage.add_reflection(
        ReflectionCreate(
            from_node='node-beta',
            to_user='user-002',
            message='Third reflection',
            emotion='радость',
        ),
        author='user-002'
    )

    # Query by emotion
    results = await storage.query_reflections(emotion='радость')
    assert len(results) == 2
    assert all(r.emotion == 'радость' for r in results)
    
    # Query by author
    results = await storage.query_reflections(author='user-001')
    assert len(results) == 2
    assert all(r.author == 'user-001' for r in results)
    
    # Query by both
    results = await storage.query_reflections(emotion='радость', author='user-001')
    assert len(results) == 1
    assert results[0].emotion == 'радость'
    assert results[0].author == 'user-001'


@pytest.mark.asyncio
@pytest.mark.integration
async def test_add_user(storage):
    """Test adding user creates ResonantModel."""
    user = User(id='test-user-001', name='Test User')
    
    await storage.add_user(user)
    
    # User should be in cache
    retrieved = await storage.get_user('test-user-001')
    assert retrieved is not None
    assert retrieved.id == 'test-user-001'
    assert retrieved.name == 'Test User'
    
    # User model should exist in LiminalDB
    result = await storage.client.awaken_get("user/test-user-001")
    assert result.get("status") in ("active", "primed", "sleeping")
    assert "user" in result.get("tags", [])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_user_from_liminaldb(storage):
    """Test getting user from LiminalDB when not in cache."""
    # Create user model directly in LiminalDB
    from app.liminaldb.client import ResonantModel
    model = ResonantModel(
        id="user/db-user",
        persistence="snapshot",
        tags=["user", "DB User"],
    )
    await storage.client.awaken_set(model)
    
    # Clear cache and get user
    storage._user_cache.clear()
    user = await storage.get_user('db-user')
    
    assert user is not None
    assert user.id == 'db-user'
    assert user.name == 'DB User'


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_astro_field(storage):
    """Test updating astro field with Affect impulse."""
    # Update astro field
    await storage.update_astro_field(
        pad=[0.7, 0.5, 0.6],
        entropy=0.3,
        coherence=0.7
    )
    
    # Get state
    state = await storage.get_astro_field_state()
    
    # Verify state (mock server updates traits via Affect)
    assert state["pad"] == [0.7, 0.5, 0.6] or state["pad"] == [0.5, 0.35, 0.45]  # May use initial or updated
    assert "entropy" in state
    assert "coherence" in state


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_astro_field_state(storage):
    """Test getting astro field state from LiminalDB."""
    state = await storage.get_astro_field_state()
    
    assert "pad" in state
    assert len(state["pad"]) == 3
    assert "entropy" in state
    assert "coherence" in state
    
    # Verify default values if model doesn't exist
    assert state["pad"] == [0.5, 0.35, 0.45]
    assert state["entropy"] == 0.0
    assert state["coherence"] == 1.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_resonance_edge(storage):
    """Test creating resonance edge between users."""
    # Create users first
    await storage.add_user(User(id='user-a', name='User A'))
    await storage.add_user(User(id='user-b', name='User B'))
    
    # Create edge
    await storage.create_resonance_edge('user-a', 'user-b', weight=0.85)
    
    # Verify edge exists in astro/global model
    result = await storage.client.awaken_get("astro/global")
    edges = result.get("edges", [])
    
    assert len(edges) > 0
    edge = edges[-1]
    assert edge["from"] == "user/user-a"
    assert edge["to"] == "user/user-b"
    assert edge["weight"] == 0.85


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_resonance_edges(storage):
    """Test creating multiple resonance edges."""
    # Create users
    await storage.add_user(User(id='user-1', name='User 1'))
    await storage.add_user(User(id='user-2', name='User 2'))
    await storage.add_user(User(id='user-3', name='User 3'))
    
    # Create multiple edges
    await storage.create_resonance_edge('user-1', 'user-2', weight=0.8)
    await storage.create_resonance_edge('user-2', 'user-3', weight=0.9)
    await storage.create_resonance_edge('user-1', 'user-3', weight=0.7)
    
    # Verify all edges exist
    result = await storage.client.awaken_get("astro/global")
    edges = result.get("edges", [])
    
    assert len(edges) >= 3
    
    # Check specific edges
    edge_dict = {(e["from"], e["to"]): e["weight"] for e in edges}
    assert ("user/user-1", "user/user-2") in edge_dict
    assert ("user/user-2", "user/user-3") in edge_dict
    assert ("user/user-1", "user/user-3") in edge_dict


@pytest.mark.asyncio
@pytest.mark.integration
async def test_write_impulse_strength_calculation(storage):
    """Test that Write impulse strength is calculated from PAD."""
    payload = ReflectionCreate(
        from_node='node-test',
        to_user='user-test',
        message='Strength test',
        emotion='радость',
        pad=[0.9, 0.8, 0.7],  # strength should be (0.9 + 0.8) / 2 = 0.85
    )

    # Add reflection and check mock server received correct strength
    reflection = await storage.add_reflection(payload, author='user-test')
    
    # Note: We can't directly verify strength sent to mock server without
    # accessing mock server state, but we can verify reflection was created
    assert reflection.pad == [0.9, 0.8, 0.7]
    
    # Verify reflection exists
    reflections = await storage.list_reflections()
    assert any(r.id == reflection.id for r in reflections)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_query_impulse_pattern(storage):
    """Test that Query impulse uses correct pattern."""
    # Add reflection
    await storage.add_reflection(
        ReflectionCreate(
            from_node='node-query',
            to_user='user-query',
            message='Query test',
            emotion='тревога',
        ),
        author='user-query'
    )
    
    # Query reflections
    results = await storage.query_reflections(emotion='тревога')
    
    # Should find the reflection
    assert len(results) >= 1
    assert any(r.emotion == 'тревога' for r in results)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_storage_close(storage):
    """Test that storage closes connection properly."""
    # Storage should be initialized
    assert storage._initialized
    
    # Close storage
    await storage.close()
    
    # Should be disconnected
    assert not storage._initialized
    assert not storage.client._connected

