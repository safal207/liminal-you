from fastapi.testclient import TestClient

from app.main import app
from app.analytics import get_analytics_history


client = TestClient(app)


def test_analytics_endpoints():
    history = get_analytics_history()
    # seed some snapshots
    history.add_snapshot([0.6, 0.4, 0.5], entropy=0.3, coherence=0.7, samples=10, tone='warm')
    history.add_snapshot([0.62, 0.41, 0.5], entropy=0.32, coherence=0.68, samples=20, tone='warm')

    s = client.get('/api/analytics/snapshots?count=2')
    assert s.status_code == 200
    assert len(s.json()) >= 2

    stats = client.get('/api/analytics/statistics')
    assert stats.status_code == 200
    body = stats.json()
    assert 'avg_entropy' in body and 'avg_coherence' in body

    trends = client.get('/api/analytics/trends?window_seconds=3600')
    assert trends.status_code == 200

    peaks = client.get('/api/analytics/peaks?count=2')
    assert peaks.status_code == 200


def test_statistics_empty_history_returns_zero_span():
    history = get_analytics_history()
    history._snapshots.clear()  # ensure empty state for test isolation

    stats = client.get('/api/analytics/statistics')

    assert stats.status_code == 200
    body = stats.json()
    assert body['count'] == 0
    assert body['time_span_seconds'] == 0.0
