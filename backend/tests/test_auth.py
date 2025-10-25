from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_and_device_info():
    resp = client.post('/api/auth/login', json={'user_id': 'user-001'})
    assert resp.status_code == 200
    data = resp.json()
    assert 'access_token' in data and data['token_type'] == 'Bearer'

    token = data['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    dev = client.get('/api/auth/device', headers=headers)
    assert dev.status_code == 200
    dev_data = dev.json()
    assert dev_data['user_id'] == 'user-001'
    assert 'trust_level' in dev_data

