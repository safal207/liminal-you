# 🎯 Sprint Plan — Witness Layer (Week 1-2)

> **Цель**: Реализовать систему отслеживания качества присутствия и внимания
> **Философия**: "Тот, кто наблюдает" — добавить метауровень осознанности

---

## 📋 План на СЕЙЧАС (следующие 3 часа)

### ✅ Phase 1: Backend Foundation (2 часа)

#### Task 1.1: Witness Metrics Engine (45 мин)
**Файл**: `backend/app/witness/metrics.py`

```python
class WitnessMetrics:
    """Calculates presence and attention quality scores."""

    def calculate_presence_score(
        self,
        action_intervals: List[float],  # Секунды между действиями
        emotional_variance: float,      # Стабильность эмоций (0-1)
        coherence_trend: float          # Тренд coherence (-1 to 1)
    ) -> Dict[str, float]:
        """
        Returns:
            {
                'presence_score': 0.0-1.0,  # Общий балл присутствия
                'attention_quality': 0.0-1.0,  # Качество внимания
                'state': 'scattered' | 'present' | 'witnessing'
            }
        """
```

**Логика расчета**:
- **action_intervals**:
  - < 5 сек → scattered (автопилот)
  - 5-30 сек → present (осознанность)
  - > 30 сек → witnessing (глубокое наблюдение)
- **emotional_variance**:
  - Высокая → низкое присутствие
  - Низкая → высокое присутствие
- **coherence_trend**:
  - Растет → улучшение присутствия
  - Падает → ухудшение

---

#### Task 1.2: Witness Storage (30 мин)
**Файл**: `backend/app/witness/storage.py`

```python
class WitnessStorage:
    """In-memory storage for witness metrics (v0.3 MVP)."""

    def __init__(self):
        self._snapshots: Dict[str, List[WitnessSnapshot]] = {}
        # user_id -> [snapshot1, snapshot2, ...]

    def add_snapshot(self, user_id: str, snapshot: WitnessSnapshot):
        """Add witness snapshot for user."""

    def get_recent(self, user_id: str, limit: int = 100) -> List[WitnessSnapshot]:
        """Get recent snapshots."""
```

**Note**: Для v0.3 используем in-memory, DB в v0.4

---

#### Task 1.3: Witness Models (15 мин)
**Файл**: `backend/app/witness/models.py`

```python
@dataclass
class WitnessSnapshot:
    timestamp: datetime
    user_id: str
    presence_score: float
    attention_quality: float
    state: str  # 'scattered' | 'present' | 'witnessing'
    action_interval: float
    emotional_variance: float
    coherence: float
    entropy: float
```

---

#### Task 1.4: Witness API Routes (30 мин)
**Файл**: `backend/app/routes/witness.py`

```python
@router.get("/api/witness/score")
async def get_current_score(user_id: str = "user-001"):
    """Get current presence score."""

@router.get("/api/witness/history")
async def get_history(user_id: str = "user-001", limit: int = 100):
    """Get presence history."""

@router.get("/api/witness/insights")
async def get_insights(user_id: str = "user-001"):
    """Get insights about attention patterns."""
```

---

### ✅ Phase 2: Integration (1 час)

#### Task 2.1: Tracker в Feedback Hub (30 мин)
**Файл**: `backend/app/feedback.py`

Добавить tracking:
```python
class NeuroFeedbackHub:
    def __init__(self):
        # ... existing ...
        self._witness_tracker = WitnessTracker()
        self._last_action_time: Dict[str, float] = {}

    async def integrate_field(self, pad_vec, user_id: str = None):
        # Track action interval
        now = time.time()
        interval = now - self._last_action_time.get(user_id, now)
        self._last_action_time[user_id] = now

        # Calculate witness metrics
        self._witness_tracker.track_action(user_id, interval, state)
```

#### Task 2.2: WebSocket Broadcast (30 мин)

Добавить witness события в WebSocket:
```python
{
    "event": "witness_update",
    "data": {
        "presence_score": 0.75,
        "state": "present",
        "message": "Присутствие растёт"
    }
}
```

---

## 🧪 Phase 3: Testing (опционально, если время)

```python
# backend/tests/test_witness.py
def test_presence_score_calculation():
    metrics = WitnessMetrics()
    score = metrics.calculate_presence_score(
        action_intervals=[10.0, 15.0, 20.0],
        emotional_variance=0.2,
        coherence_trend=0.5
    )
    assert 0.5 <= score['presence_score'] <= 0.8
```

---

## 📁 Структура файлов

```
backend/app/
├── witness/
│   ├── __init__.py          # ✅ Создать
│   ├── metrics.py           # ✅ Создать - расчет scores
│   ├── models.py            # ✅ Создать - dataclasses
│   ├── storage.py           # ✅ Создать - in-memory storage
│   └── tracker.py           # ✅ Создать - tracking logic
├── routes/
│   └── witness.py           # ✅ Создать - API endpoints
└── feedback.py              # 🔄 Модифицировать - добавить tracking
```

---

## 🎯 Definition of Done (3 часа)

- [x] Создан модуль `witness/` с 5 файлами
- [x] Реализован расчет presence_score
- [x] API endpoints работают
- [x] Integration с FeedbackHub
- [x] Можно получить `/api/witness/score`

---

## 🚀 Следующие шаги (после Phase 1-2)

### Tomorrow: Frontend Components
1. PresenceIndicator.tsx (визуализация)
2. WitnessDashboard.tsx (дашборд)
3. Integration в App.tsx

### Day 3-4: Practice Engine (Sprint 2)
1. Breath invitations
2. Practice modal
3. Session tracking

---

## 💡 Quick Start

```bash
# 1. Создать ветку
git checkout -b feature/witness-layer

# 2. Создать структуру
mkdir -p backend/app/witness
touch backend/app/witness/{__init__.py,metrics.py,models.py,storage.py,tracker.py}
touch backend/app/routes/witness.py

# 3. Начать с metrics.py
# ... код ...

# 4. Запустить для проверки
cd backend
uvicorn app.main:app --reload

# 5. Тестировать
curl http://localhost:8000/api/witness/score
```

---

## 🌗 Философия

**Падмасамбхава**:
> "Ригпа (осознанность) — это не объект наблюдения, а сам наблюдатель"

Мы создаем **Свидетеля** — систему, которая наблюдает за качеством наблюдения.

Каждый presence_score — это зеркало, отражающее степень присутствия.

---

**Готов начинать? Начинаем с Task 1.1! 🚀**
