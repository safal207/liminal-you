from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_emotions():
    r = client.get('/api/emotions')
    assert r.status_code == 200
    data = r.json()
    assert data['total'] >= 40
    assert 'emotions' in data and isinstance(data['emotions'], list)


def test_get_emotion_and_suggest():
    # take first from list
    r = client.get('/api/emotions')
    name = r.json()['emotions'][0]['name']
    g = client.get(f'/api/emotions/{name}')
    assert g.status_code == 200
    s = client.get(f'/api/emotions/suggest/{name[:2]}?limit=3')
    assert s.status_code == 200
    assert len(s.json()) <= 3

