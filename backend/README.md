# Liminal-You Backend

FastAPI bootstrap service powering the Liminal-You social layer.

## Endpoints

- `GET /api/feed` — получить ленту отражений.
- `POST /api/reflection` — создать новое отражение.
- `GET /api/profile/{id}` — профиль пользователя с узлами и эмоциями.

## Local run

```bash
uvicorn app.main:app --reload
```
