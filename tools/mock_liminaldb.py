#!/usr/bin/env python3
"""Mock LiminalDB WebSocket server for testing liminal-you integration.

This mock server emulates LiminalDB WebSocket API with CBOR protocol.
It accepts impulses, stores them in memory, and responds with appropriate events.
"""
import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any

import cbor2
from aiohttp import web

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mock-liminaldb')


class MockLiminalDB:
    """Mock LiminalDB storage and logic."""

    def __init__(self):
        self.impulses: List[Dict[str, Any]] = []
        self.models: Dict[str, Dict[str, Any]] = {}
        self.pattern_index: Dict[str, List[Dict[str, Any]]] = {}  # Index impulses by pattern
        self.event_handlers: Dict[str, List[callable]] = {}  # Store event handlers per client
        self.metrics = {
            "cells": 0,
            "sleeping_pct": 0.0,
            "avg_metabolism": 0.5,
            "avg_latency_ms": 10.0,
        }

    def add_impulse(self, impulse: Dict[str, Any]) -> Dict[str, Any]:
        """Process impulse and return response."""
        impulse['timestamp'] = time.time()
        impulse['id'] = f"imp_{len(self.impulses)}"
        self.impulses.append(impulse)

        kind = impulse.get('kind', 'Query')
        pattern = impulse.get('pattern', '')
        strength = impulse.get('strength', 0.5)

        logger.info(f"📨 Impulse received: {kind} | pattern='{pattern}' | strength={strength:.2f}")

        # Index by pattern for Query operations
        if pattern:
            if pattern not in self.pattern_index:
                self.pattern_index[pattern] = []
            self.pattern_index[pattern].append(impulse)

        # Update metrics
        self.metrics['cells'] += 1
        self.metrics['avg_metabolism'] = (self.metrics['avg_metabolism'] * 0.9 + strength * 0.1)

        # Process impulse based on kind
        if kind == "Query":
            return self._handle_query_impulse(impulse)
        elif kind == "Write":
            return self._handle_write_impulse(impulse)
        elif kind == "Affect":
            return self._handle_affect_impulse(impulse)
        else:
            # Default handling
            harmony_event = self._generate_harmony_event(impulse)
            return {
                "status": "ok",
                "impulse_id": impulse['id'],
                "event": "harmony",
                "data": harmony_event
            }

    def _handle_query_impulse(self, impulse: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Query impulse - search for matching patterns."""
        pattern = impulse.get('pattern', '')
        strength = impulse.get('strength', 0.5)

        # Find matching impulses
        matches = []
        if pattern in self.pattern_index:
            matches = self.pattern_index[pattern][-10:]  # Last 10 matches
        
        # Also search for partial matches (prefix matching)
        for pat, impulses_list in self.pattern_index.items():
            if pat.startswith(pattern) and pat != pattern:
                matches.extend(impulses_list[-5:])

        logger.info(f"🔍 Query found {len(matches)} matches for pattern '{pattern}'")

        harmony_event = self._generate_harmony_event(impulse)
        
        return {
            "status": "ok",
            "impulse_id": impulse['id'],
            "kind": "Query",
            "matches": len(matches),
            "event": "harmony",
            "data": harmony_event
        }

    def _handle_write_impulse(self, impulse: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Write impulse - store data."""
        pattern = impulse.get('pattern', '')
        strength = impulse.get('strength', 0.5)
        tags = impulse.get('tags', [])

        logger.info(f"✍️  Write impulse stored: pattern='{pattern}', tags={tags}")

        harmony_event = self._generate_harmony_event(impulse)
        
        return {
            "status": "ok",
            "impulse_id": impulse['id'],
            "kind": "Write",
            "pattern": pattern,
            "event": "harmony",
            "data": harmony_event
        }

    def _handle_affect_impulse(self, impulse: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Affect impulse - modify model state."""
        pattern = impulse.get('pattern', '')
        strength = impulse.get('strength', 0.5)

        # Affect updates astro field or models
        if pattern.startswith("astro/"):
            # Update astro field model if exists
            if "astro/global" in self.models:
                model = self.models["astro/global"]
                traits = model.get("traits", {})
                traits["coherence"] = min(1.0, traits.get("coherence", 1.0) + strength * 0.1)
                traits["entropy"] = max(0.0, traits.get("entropy", 0.0) - strength * 0.05)
                model["traits"] = traits
                logger.info(f"⚡ Affect updated astro field: coherence={traits.get('coherence', 0):.2f}")

        harmony_event = self._generate_harmony_event(impulse)
        
        return {
            "status": "ok",
            "impulse_id": impulse['id'],
            "kind": "Affect",
            "pattern": pattern,
            "event": "harmony",
            "data": harmony_event
        }

    def _generate_harmony_event(self, impulse: Dict[str, Any]) -> Dict[str, Any]:
        """Generate harmony event from impulse."""
        strength = impulse.get('strength', 0.5)

        # Calculate entropy and coherence from strength
        entropy = max(0.0, 1.0 - strength)
        coherence = strength

        # Determine status
        if entropy > 0.7:
            status = "drift"
        elif coherence > 0.8:
            status = "OK"
        else:
            status = "balanced"

        return {
            "ev": "harmony",
            "meta": {
                "strength": round(strength, 2),
                "latency": round(self.metrics['avg_latency_ms'], 1),
                "entropy": round(entropy, 2),
                "coherence": round(coherence, 2),
                "status": status,
                "timestamp": int(time.time()),
            }
        }

    def set_model(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Store ResonantModel."""
        model_id = model.get('id', f'model_{len(self.models)}')
        model['last_updated'] = time.time()
        
        # Normalize traits field (can be "traits" or "latent_traits")
        if "latent_traits" in model:
            model["traits"] = model.pop("latent_traits")
        
        # Initialize edges if not present
        if "edges" not in model:
            model["edges"] = []
        
        # Merge with existing model if it exists (preserve edges and traits)
        if model_id in self.models:
            existing = self.models[model_id]
            # Merge edges
            if "edges" in model and model["edges"]:
                existing_edges = existing.get("edges", [])
                # Add new edges that don't already exist
                for edge in model["edges"]:
                    if edge not in existing_edges:
                        existing_edges.append(edge)
                model["edges"] = existing_edges
            # Merge traits
            if "traits" in model and model["traits"]:
                existing_traits = existing.get("traits", {})
                existing_traits.update(model["traits"])
                model["traits"] = existing_traits

        self.models[model_id] = model
        logger.info(f"💾 Model stored: {model_id} | persistence={model.get('persistence', 'memory')} | edges={len(model.get('edges', []))}")

        return {
            "status": "ok",
            "model_id": model_id,
            "message": f"Model {model_id} stored successfully"
        }

    def get_model(self, model_id: str) -> Dict[str, Any]:
        """Get ResonantModel by ID."""
        if model_id in self.models:
            logger.info(f"📖 Model retrieved: {model_id}")
            model = self.models[model_id].copy()
            model['status'] = 'active'
            
            # Convert "traits" back to "latent_traits" for compatibility
            if "traits" in model:
                model["latent_traits"] = model.pop("traits")
            
            return model
        else:
            logger.warning(f"⚠️  Model not found: {model_id}")
            return {
                "status": "not_found",
                "error": f"Model {model_id} not found"
            }

    def introspect_model(self, model_id: str) -> Dict[str, Any]:
        """Introspect model - return detailed state and connections."""
        if model_id not in self.models:
            return {
                "status": "not_found",
                "error": f"Model {model_id} not found"
            }

        model = self.models[model_id]
        
        # Count related impulses
        pattern_parts = model_id.split("/")
        related_impulses = []
        for pattern, impulses_list in self.pattern_index.items():
            if any(part in pattern for part in pattern_parts):
                related_impulses.extend(impulses_list)

        traits = model.get("traits", {})
        edges = model.get("edges", [])

        logger.info(f"🔬 Introspect: {model_id} | edges={len(edges)}, related_impulses={len(related_impulses)}")

        introspect_event = {
            "ev": "introspect",
            "id": model_id,
            "meta": {
                "status": model.get("status", "active"),
                "persistence": model.get("persistence", "memory"),
                "edges_count": len(edges),
                "related_impulses_count": len(related_impulses),
                "traits": traits,
                "timestamp": int(time.time()),
            }
        }

        return {
            "status": "ok",
            "model_id": model_id,
            "event": "introspect",
            "data": introspect_event
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            "cells": len(self.impulses),
            "sleeping_pct": self.metrics['sleeping_pct'],
            "avg_metabolism": round(self.metrics['avg_metabolism'], 3),
            "avg_latency_ms": self.metrics['avg_latency_ms'],
            "models_count": len(self.models),
        }


# Global instance
mock_db = MockLiminalDB()


async def websocket_handler(request):
    """WebSocket handler for CBOR protocol."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    client_id = f"client_{int(time.time() * 1000)}"
    logger.info(f"🔗 WebSocket connected: {client_id}")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.BINARY:
                try:
                    # Decode CBOR
                    data = cbor2.loads(msg.data)
                    logger.debug(f"📥 CBOR received from {client_id}: {data}")

                    # Handle different message types
                    response = await handle_message(data)

                    # Send CBOR response
                    cbor_response = cbor2.dumps(response)
                    await ws.send_bytes(cbor_response)
                    logger.debug(f"📤 CBOR sent to {client_id}: {response}")

                except Exception as e:
                    logger.error(f"❌ Error processing CBOR: {e}")
                    error_response = {"error": str(e), "status": "error"}
                    await ws.send_bytes(cbor2.dumps(error_response))

            elif msg.type == web.WSMsgType.TEXT:
                try:
                    # Handle JSON as well (fallback)
                    data = json.loads(msg.data)
                    logger.debug(f"📥 JSON received from {client_id}: {data}")

                    response = await handle_message(data)
                    await ws.send_str(json.dumps(response))

                except Exception as e:
                    logger.error(f"❌ Error processing JSON: {e}")

            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"❌ WebSocket error: {ws.exception()}")

    finally:
        logger.info(f"🔌 WebSocket disconnected: {client_id}")

    return ws


async def handle_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming message and return response."""

    # Check if it's a command
    if "cmd" in data:
        cmd = data['cmd']
        args = data.get('args', {})

        if cmd == "awaken.set":
            return mock_db.set_model(args)
        elif cmd == "awaken.get":
            model_id = args.get('id', '')
            return mock_db.get_model(model_id)
        elif cmd == "introspect":
            model_id = args.get('id', '')
            return mock_db.introspect_model(model_id)
        elif cmd == "metrics":
            return mock_db.get_metrics()
        else:
            logger.warning(f"⚠️  Unknown command: {cmd}")
            return {"error": f"Unknown command: {cmd}", "status": "error"}

    # Check if it's an impulse (has "kind" or "pattern" field)
    elif "kind" in data or ("pattern" in data and "cmd" not in data):
        return mock_db.add_impulse(data)

    else:
        logger.warning(f"⚠️  Unknown message format: {data}")
        return {"error": "Unknown message format", "status": "error"}


async def health_handler(request):
    """Health check endpoint."""
    return web.json_response({
        "status": "ok",
        "service": "mock-liminaldb",
        "version": "0.2.0",
        "uptime_seconds": int(time.time() - start_time),
        "stats": mock_db.get_metrics(),
        "supported_commands": ["awaken.set", "awaken.get", "introspect", "metrics"],
        "supported_impulses": ["Query", "Write", "Affect"],
    })


async def stats_handler(request):
    """Stats endpoint."""
    return web.json_response({
        "impulses": len(mock_db.impulses),
        "models": len(mock_db.models),
        "recent_impulses": mock_db.impulses[-10:] if mock_db.impulses else [],
        "metrics": mock_db.get_metrics(),
    })


# Start time
start_time = time.time()


def create_app():
    """Create aiohttp application."""
    app = web.Application()
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/health', health_handler)
    app.router.add_get('/stats', stats_handler)
    return app


if __name__ == '__main__':
    # Allow port override via environment variable
    port = int(os.getenv('PORT', '8787'))
    
    print(f"""
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
WebSocket endpoint: ws://localhost:{port}/ws
Health check: http://localhost:{port}/health
Stats: http://localhost:{port}/stats

Waiting for connections...
""")

    app = create_app()
    web.run_app(app, host='localhost', port=port)
