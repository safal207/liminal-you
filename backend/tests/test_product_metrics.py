from fastapi.testclient import TestClient

from app.main import app
from app.product import get_product_metrics_tracker


client = TestClient(app)


def test_product_metrics_funnel_and_wws():
    tracker = get_product_metrics_tracker()

    # Reset in-memory state for deterministic test
    tracker._sessions.clear()  # noqa: SLF001
    tracker._weekly_completed.clear()  # noqa: SLF001
    tracker._funnel["reflection_users"].clear()  # noqa: SLF001
    tracker._funnel["improved_users"].clear()  # noqa: SLF001

    # Simulate one user action + improved state
    tracker.track_reflection("user-001")
    tracker.track_state_change("user-001", coherence=0.8, entropy=0.2)

    wws = client.get('/api/product/wws')
    assert wws.status_code == 200
    wws_body = wws.json()
    assert wws_body['weekly_witnessed_sessions'] == 1

    funnel = client.get('/api/product/funnel')
    assert funnel.status_code == 200
    funnel_body = funnel.json()
    assert funnel_body['reflection_users'] == 1
    assert funnel_body['improved_users'] == 1
    assert funnel_body['improvement_conversion'] == 1.0
