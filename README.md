# Liminal-You v0.2

[![Backend Tests](https://github.com/safal207/liminal-you/actions/workflows/backend.yml/badge.svg)](https://github.com/safal207/liminal-you/actions/workflows/backend.yml)
[![Frontend Tests](https://github.com/safal207/liminal-you/actions/workflows/frontend.yml/badge.svg)](https://github.com/safal207/liminal-you/actions/workflows/frontend.yml)
[![E2E Backend + LiminalDB](https://github.com/safal207/liminal-you/actions/workflows/e2e.yml/badge.svg)](https://github.com/safal207/liminal-you/actions/workflows/e2e.yml)

> Социальный слой LIMINAL OS — "Ты".
> Пространство, где внутренние миры встречаются через резонанс.

## 🌟 Что нового в v0.2

- 🧬 **LiminalBD Integration** — живая база данных с клетками и импульсами
- 🎭 **JWT + Device Memory** — аутентификация с эмоциональными отпечатками устройств
- 🎨 **48 эмоций** — расширенная PAD-модель (русский словарь)
- 📊 **Analytics Dashboard** — история entropy/coherence, тренды, пики
- 🌍 **Мультиязычность** — русский, английский, китайский

[Полный CHANGELOG →](./CHANGELOG_v0.2.md)

## Stack
- FastAPI 0.111 + Python 3.11+
- React + TypeScript + TailwindCSS
- LiminalBD (Rust) — опционально
- PostgreSQL — опционально
- Docker Compose

## Quick Start

### Вариант 1: Минимальный (in-memory)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Вариант 2: С LiminalBD

```bash
# 1. Запустить LiminalBD
cd ../LiminalBD/liminal-db
cargo run -p liminal-cli

# 2. Настроить .env
cd ../../liminal-you/backend
echo "LIMINALDB_ENABLED=true" > .env
echo "LIMINALDB_URL=ws://localhost:8001" >> .env
echo "STORAGE_BACKEND=liminaldb" >> .env

# 3. Запустить backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 4. Запустить frontend
cd ../frontend
npm install
npm run dev
```

### Вариант 3: Docker Compose

```bash
docker-compose up --build
```

## URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **LiminalBD**: ws://localhost:8001 (если запущен)

## API Examples

### Authentication
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-001"}'

# Get device info
curl http://localhost:8000/api/auth/device \
  -H "Authorization: Bearer {token}"
```

### Emotions
```bash
# Get all emotions (48)
curl http://localhost:8000/api/emotions

# Get specific emotion
curl http://localhost:8000/api/emotions/радость

# Suggest emotions
curl http://localhost:8000/api/emotions/suggest/рад?limit=5
```

### Analytics
```bash
# Get recent snapshots
curl http://localhost:8000/api/analytics/snapshots?count=100

# Get statistics (last hour)
curl http://localhost:8000/api/analytics/statistics?window_seconds=3600

# Get trends
curl http://localhost:8000/api/analytics/trends?window_seconds=3600

# Get peaks and valleys
curl http://localhost:8000/api/analytics/peaks?count=10
```

### i18n
```bash
# Get all translations (English)
curl http://localhost:8000/api/i18n/translations?language=en

# Get all emotion translations
curl http://localhost:8000/api/i18n/emotions

# Translate specific emotion to Chinese
curl http://localhost:8000/api/i18n/emotion/радость?language=zh
```

## Architecture

```
liminal-you/
├── backend/
│   ├── app/
│   │   ├── analytics/       # Analytics history tracking
│   │   ├── auth/            # JWT + Device Memory
│   │   ├── i18n/            # Internationalization
│   │   ├── liminaldb/       # LiminalDB client & storage
│   │   ├── models/          # Pydantic models
│   │   ├── routes/          # API routes (8 modules)
│   │   ├── services/        # Business logic
│   │   ├── astro.py         # AstroField (PAD model)
│   │   ├── feedback.py      # NeuroFeedback hub
│   │   ├── config.py        # Configuration
│   │   └── main.py          # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── api/             # API client
│   │   └── App.tsx
│   └── package.json
├── docs/
│   └── YOU_TZ_v0.1.md      # Technical specification
├── CHANGELOG_v0.2.md       # Full changelog
└── README.md
```

## Key Features

### 1. LiminalDB Integration
- Reflections stored as **Write impulses**
- Users stored as **ResonantModels**
- AstroField stored with **latent_traits**
- Real-time **harmony events** tracking

### 2. Device Memory
- **Fingerprinting**: Stable device_id from user-agent + IP
- **Emotional Seed**: PAD vector with EMA updates (α=0.15)
- **Trust Level**: Grows with interactions (0.1 → 1.0)
- **Resonance**: Cosine similarity between devices

### 3. Analytics
- **History**: Up to 1000 snapshots (24h max)
- **Statistics**: Average entropy/coherence/PAD
- **Trends**: Increasing/decreasing/stable analysis
- **Peaks & Valleys**: Extremes in metrics

### 4. Emotions (48 total)
- **18 positive**: радость, восторг, гармония, etc.
- **17 negative**: тревога, страх, отчаяние, etc.
- **8 neutral**: ностальгия, созерцание, покой, etc.

### 5. Multilingual (3 languages)
- 🇷🇺 Russian (primary)
- 🇬🇧 English
- 🇨🇳 Chinese

## Configuration

```bash
# backend/.env

# LiminalDB
LIMINALDB_ENABLED=true
LIMINALDB_URL=ws://localhost:8001
STORAGE_BACKEND=liminaldb  # memory | postgres | liminaldb

# PostgreSQL (if using)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=liminal
POSTGRES_PASSWORD=youpass
POSTGRES_DB=liminal_you

# JWT
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Feedback
FEEDBACK_ENABLED=true

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Development

### Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Format code
black app/
isort app/
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## API Documentation

FastAPI автоматически генерирует интерактивную документацию:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Modules
1. **Analytics** (`/api/analytics/*`) — 5 endpoints
2. **Auth** (`/api/auth/*`) — 4 endpoints
3. **Emotions** (`/api/emotions/*`) — 3 endpoints
4. **Feed** (`/api/feed`) — 1 endpoint
5. **i18n** (`/api/i18n/*`) — 5 endpoints
6. **Reflections** (`/api/reflection`) — 2 endpoints
7. **Profiles** (`/api/profile/*`) — 3 endpoints
8. **Feedback** (`/ws/feedback`) — WebSocket

**Total: 31 API endpoints**

## WebSocket

### Neuro-Feedback
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/feedback?profile_id=user-001');

ws.onmessage = (event) => {
  const payload = JSON.parse(event.data);

  if (payload.event === 'neuro_feedback') {
    const { tone, message, intensity, pad, entropy, coherence } = payload.data;
    console.log(`Tone: ${tone}, Message: ${message}`);
    console.log(`PAD: ${pad}, Entropy: ${entropy}, Coherence: ${coherence}`);
  }

  if (payload.event === 'new_reflection') {
    const reflection = payload.data;
    console.log(`New reflection: ${reflection.content}`);
  }
};
```

## Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## License

См. [LICENSE](./LICENSE)

## Links

- **GitHub**: https://github.com/safal207/liminal-you
- **LiminalBD**: https://github.com/safal207/LiminalBD
- **liminal-voice-core**: https://github.com/safal207/liminal-voice-core
- **LIMINAL OS**: Философия границ и переходов

---

🌌 **liminal-you v0.2** — Социальный слой, который дышит.

Generated with [Claude Code](https://claude.com/claude-code)
