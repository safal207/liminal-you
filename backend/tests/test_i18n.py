from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_translations_and_emotions_i18n():
    t = client.get('/api/i18n/translations?language=en')
    assert t.status_code == 200
    data = t.json()
    assert data['language'] == 'en'
    assert 'translations' in data

    emotions = client.get('/api/i18n/emotions')
    assert emotions.status_code == 200
    assert 'emotions' in emotions.json()

    # translate a single emotion (use a common one from emotions list)
    name = list(emotions.json()['emotions'].keys())[0]
    translated = client.get(f'/api/i18n/emotion/{name}?language=en')
    assert translated.status_code == 200

