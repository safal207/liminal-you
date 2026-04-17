from fastapi.testclient import TestClient

from app.main import app
from app.product import get_product_metrics_tracker


client = TestClient(app)


def _reset_tracker_state() -> None:
    tracker = get_product_metrics_tracker()
    tracker._sessions.clear()  # noqa: SLF001
    tracker._weekly_completed.clear()  # noqa: SLF001
    tracker._funnel["reflection_users"].clear()  # noqa: SLF001
    tracker._funnel["practice_users"].clear()  # noqa: SLF001
    tracker._funnel["improved_users"].clear()  # noqa: SLF001


def test_wws_requires_practice_completion():
    _reset_tracker_state()
    tracker = get_product_metrics_tracker()

    tracker.track_reflection("user-001")
    tracker.track_state_change("user-001", coherence=0.8, entropy=0.2)

    before = client.get('/api/product/wws')
    assert before.status_code == 200
    assert before.json()['weekly_witnessed_sessions'] == 0

    mark = client.post('/api/product/practice-completed', json={'user_id': 'user-001'})
    assert mark.status_code == 200
    assert mark.json()['wws_completed'] is True

    after = client.get('/api/product/wws')
    assert after.status_code == 200
    assert after.json()['weekly_witnessed_sessions'] == 1


def test_funnel_includes_practice_stage():
    _reset_tracker_state()
    tracker = get_product_metrics_tracker()

    tracker.track_reflection("user-001")

    mark = client.post('/api/product/practice-completed', json={'user_id': 'user-001'})
    assert mark.status_code == 200

    tracker.track_state_change("user-001", coherence=0.8, entropy=0.2)

    funnel = client.get('/api/product/funnel')
    assert funnel.status_code == 200
    body = funnel.json()
    assert body['reflection_users'] == 1
    assert body['practice_users'] == 1
    assert body['improved_users'] == 1
    assert body['reflection_to_practice'] == 1.0
    assert body['practice_to_improved'] == 1.0
    assert body['reflection_to_improved'] == 1.0
