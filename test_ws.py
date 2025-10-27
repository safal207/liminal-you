"""Simple WebSocket connection test."""
import asyncio
import websockets

async def test_connection():
    url = "ws://127.0.0.1:8787"
    print(f"Attempting to connect to {url}...")

    try:
        async with websockets.connect(url, timeout=5) as ws:
            print("✓ Successfully connected!")
            print(f"WebSocket state: {ws.state}")
            return True
    except ConnectionRefusedError as e:
        print(f"✗ ConnectionRefusedError: {e}")
        return False
    except TimeoutError as e:
        print(f"✗ TimeoutError: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    exit(0 if result else 1)
