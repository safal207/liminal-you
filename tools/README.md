# Testing Tools for liminal-you

## Mock LiminalDB Server

Mock WebSocket server that emulates LiminalDB protocol for testing backend integration.

### Features

- ✅ CBOR protocol support
- ✅ JSON fallback support
- ✅ **Impulse processing** (Query/Write/Affect with pattern indexing)
- ✅ **ResonantModel storage** (awaken.set/get with edge and trait merging)
- ✅ **Introspect command** (model introspection with related impulses)
- ✅ **Harmony events** generation (entropy/coherence calculation)
- ✅ **Pattern indexing** for Query operations
- ✅ **Affect impulse** updates astro field models
- ✅ Metrics tracking
- ✅ Health check endpoint
- ✅ Stats endpoint with recent activity

### Quick Start

```bash
# Install dependencies
cd tools
pip install -r requirements.txt

# Run mock server
python mock_liminaldb.py
```

The server will start on:
- **WebSocket**: `ws://localhost:8787/ws` (default, configurable via PORT env)
- **Health**: `http://localhost:8787/health`
- **Stats**: `http://localhost:8787/stats`

**Note**: Default port changed to 8787 to match LiminalDB default port.

### Testing Integration

#### 1. Start Mock LiminalDB

```bash
# Terminal 1
cd tools
python mock_liminaldb.py
```

You should see:
```
============================================================
  Mock LiminalDB WebSocket Server
  Version: 0.2.0
  Protocol: CBOR + JSON
============================================================

Supported Commands:
  - awaken.set    : Store/update ResonantModel
  - awaken.get    : Retrieve ResonantModel
  - introspect    : Introspect model state
  - metrics       : Get cluster metrics

Supported Impulses:
  - Query         : Search for matching patterns
  - Write         : Store data as impulse
  - Affect        : Modify model state

Starting mock server...
WebSocket endpoint: ws://localhost:8787/ws
Health check: http://localhost:8787/health
Stats: http://localhost:8787/stats

Waiting for connections...
```

#### 2. Configure Backend

```bash
# backend/.env
LIMINALDB_ENABLED=true
LIMINALDB_URL=ws://localhost:8787/ws
STORAGE_BACKEND=liminaldb
```

#### 3. Start Backend

```bash
# Terminal 2
cd ../backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

You should see in backend logs:
```
✨ LiminalDB storage initialized at ws://localhost:8787/ws
```

And in mock server logs:
```
🔗 WebSocket connected: client_1234567890
💾 Model stored: astro/global | persistence=snapshot | edges=0
📨 Impulse received: Write | pattern='reflection/радость/...' | strength=0.73
```

#### 4. Test API

```bash
# Terminal 3

# 1. Login (creates device in LiminalDB)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user"}'

# 2. Create reflection (sends Write impulse)
curl -X POST http://localhost:8000/api/reflection \
  -H "Content-Type: application/json" \
  -d '{
    "from_node": "node-alpha",
    "to_user": "user-001",
    "message": "Тест интеграции с LiminalDB",
    "emotion": "радость"
  }'

# 3. Get analytics
curl http://localhost:8000/api/analytics/statistics

# 4. Check mock server stats
curl http://localhost:8787/stats

# 5. Introspect a model
# (via WebSocket - see examples below)
```

### Expected Mock Server Logs

```
📨 Impulse received: Write | pattern='reflection/радость/node-alpha/...' | strength=0.73
💾 Model stored: user/test-user | persistence=snapshot
🔗 WebSocket connected: client_1699123456789
📖 Model retrieved: astro/global
```

### Mock Server Endpoints

#### WebSocket `/ws`

Accepts CBOR or JSON messages:

**Impulse:**
```json
{
  "kind": "Write",
  "pattern": "reflection/радость/user-001",
  "strength": 0.8,
  "ttl_ms": 5000,
  "tags": ["reflection", "emotion"]
}
```

**Response:**
```json
{
  "status": "ok",
  "impulse_id": "imp_1",
  "event": "harmony",
  "data": {
    "ev": "harmony",
    "meta": {
      "strength": 0.8,
      "latency": 10.0,
      "entropy": 0.2,
      "coherence": 0.8,
      "status": "OK"
    }
  }
}
```

**awaken.set (Store Model):**
```json
{
  "cmd": "awaken.set",
  "args": {
    "id": "user/test-user",
    "persistence": "snapshot",
    "latent_traits": {"created_at": 1699123456.789},
    "tags": ["user", "test"]
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "model_id": "user/test-user",
  "message": "Model user/test-user stored successfully"
}
```

**awaken.get (Retrieve Model):**
```json
{
  "cmd": "awaken.get",
  "args": {
    "id": "user/test-user"
  }
}
```

**Response:**
```json
{
  "id": "user/test-user",
  "persistence": "snapshot",
  "latent_traits": {"created_at": 1699123456.789},
  "tags": ["user", "test"],
  "edges": [],
  "status": "active",
  "last_updated": 1699123456.789
}
```

**introspect (Introspect Model):**
```json
{
  "cmd": "introspect",
  "args": {
    "id": "astro/global"
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "model_id": "astro/global",
  "event": "introspect",
  "data": {
    "ev": "introspect",
    "id": "astro/global",
    "meta": {
      "status": "active",
      "persistence": "snapshot",
      "edges_count": 0,
      "related_impulses_count": 5,
      "traits": {
        "pad_p": 0.5,
        "pad_a": 0.35,
        "pad_d": 0.45,
        "entropy": 0.0,
        "coherence": 1.0
      },
      "timestamp": 1699123456
    }
  }
}
```

**Query Impulse:**
```json
{
  "kind": "Query",
  "pattern": "reflection/радость",
  "strength": 0.7,
  "tags": ["reflection"]
}
```

**Response:**
```json
{
  "status": "ok",
  "impulse_id": "imp_5",
  "kind": "Query",
  "matches": 3,
  "event": "harmony",
  "data": {
    "ev": "harmony",
    "meta": {
      "strength": 0.7,
      "entropy": 0.3,
      "coherence": 0.7,
      "status": "balanced"
    }
  }
}
```

**Affect Impulse:**
```json
{
  "kind": "Affect",
  "pattern": "astro/global/update",
  "strength": 0.8,
  "tags": ["astro", "field", "update"]
}
```

**Response:**
```json
{
  "status": "ok",
  "impulse_id": "imp_6",
  "kind": "Affect",
  "pattern": "astro/global/update",
  "event": "harmony",
  "data": {
    "ev": "harmony",
    "meta": {
      "strength": 0.8,
      "entropy": 0.2,
      "coherence": 0.8,
      "status": "OK"
    }
  }
}
```

#### HTTP `/health`

Health check endpoint:

```bash
curl http://localhost:8787/health
```

Response:
```json
{
  "status": "ok",
  "service": "mock-liminaldb",
  "version": "0.2.0",
  "uptime_seconds": 123,
  "supported_commands": ["awaken.set", "awaken.get", "introspect", "metrics"],
  "supported_impulses": ["Query", "Write", "Affect"],
  "stats": {
    "cells": 5,
    "sleeping_pct": 0.0,
    "avg_metabolism": 0.523,
    "avg_latency_ms": 10.0,
    "models_count": 3
  }
}
```

#### HTTP `/stats`

Statistics and recent activity:

```bash
curl http://localhost:8001/stats
```

Response:
```json
{
  "impulses": 12,
  "models": 3,
  "recent_impulses": [
    {
      "kind": "Write",
      "pattern": "reflection/радость/user-001",
      "strength": 0.8,
      "timestamp": 1699123456.789
    }
  ],
  "metrics": {
    "cells": 12,
    "avg_metabolism": 0.623,
    "models_count": 3
  }
}
```

### Troubleshooting

**Backend не подключается:**
```bash
# Check if mock server is running
curl http://localhost:8787/health

# Check backend .env
cat backend/.env | grep LIMINALDB
```

**CBOR errors:**
```bash
# Mock server logs will show errors
# Check that cbor2 is installed:
pip list | grep cbor2
```

**Port already in use:**
```bash
# Kill process on port 8787
# Windows:
netstat -ano | findstr :8787
taskkill /PID <PID> /F

# Or change port via environment variable:
PORT=8001 python mock_liminaldb.py
```

### Development

The mock server is intentionally simple and stores everything in memory. It's designed for:
- ✅ Testing backend integration code
- ✅ Verifying CBOR protocol implementation
- ✅ Debugging WebSocket communication
- ✅ CI/CD pipelines (no external dependencies)

It does NOT:
- ❌ Persist data to disk
- ❌ Implement full LiminalDB logic (cells, evolution, resonance loop, etc.)
- ❌ Support all LiminalDB commands (missing: cluster commands, advanced queries)
- ❌ Emit real-time events to clients (only responds to requests)

For production testing, use real LiminalDB.

### Next Steps

**Using Real LiminalDB** (now working!):
1. Stop mock server
2. Start real LiminalDB:
   ```bash
   cd LiminalBD/liminal-db
   cargo +stable-x86_64-pc-windows-gnu run -p liminal-cli -- --ws-port 8787 --ws-format cbor
   ```
3. Update backend/.env: `LIMINALDB_URL=ws://localhost:8787`
4. Backend will work with real LiminalDB without code changes

**Compilation issues fixed by Qoder:**
- Removed duplicate definitions (ResonantModel, ModelFrame)
- Fixed awakening_config, sync_log field duplicates
- Added cached_resonant_model for Awakening state
- Snapshot limits for resonant models and sync logs

---

Generated with Claude Code
