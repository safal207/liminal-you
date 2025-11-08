# ROADMAP v0.3 — План Развития 🗺️

> *Конкретные шаги на пути трансформации*

**Период**: Ноябрь 2025 - Январь 2026
**Цель**: Реализовать Witness Layer + Practices Engine
**Философия**: От "дышащего поля" к "храму практики"

---

## 📅 Sprint 1: Witness Layer (2 недели)

**Даты**: 2-16 ноября 2025
**Тема**: "Тот, кто наблюдает"

### Backend Tasks

#### 1. Witness Metrics Engine
**Файл**: `backend/app/witness/metrics.py`

```python
class WitnessMetrics:
    """Tracks quality of presence and attention."""

    def calculate_presence_score(
        self,
        action_intervals: List[float],  # Время между действиями
        attention_quality: float,        # Фокус vs рассеянность
        emotional_stability: float       # Стабильность PAD
    ) -> float:
        """
        Returns:
            0.0-1.0 где:
            - 0.0-0.3: Scattered (рассеянное внимание)
            - 0.3-0.7: Present (присутствие)
            - 0.7-1.0: Witnessing (чистое наблюдение)
        """
        pass
```

**Estimate**: 3 дня

#### 2. Witness Storage
**Файл**: `backend/app/witness/storage.py`

- Таблица `witness_snapshots`:
  - `user_id`, `timestamp`
  - `presence_score`, `attention_quality`
  - `interval_avg`, `interval_std`
  - `emotional_variance`

**Estimate**: 1 день

#### 3. Witness API
**Файл**: `backend/app/routes/witness.py`

Endpoints:
- `GET /api/witness/score` — Текущий score
- `GET /api/witness/history` — История присутствия
- `GET /api/witness/insights` — Инсайты о качестве внимания

**Estimate**: 2 дня

#### 4. Integration с Feedback Hub
**Файл**: `backend/app/feedback.py`

- Tracking времени между reflections
- Расчёт emotional variance
- Broadcast witness updates

**Estimate**: 2 дня

**Total Backend**: ~8 дней

---

### Frontend Tasks

#### 1. Presence Indicator Component
**Файл**: `frontend/src/components/PresenceIndicator.tsx`

```tsx
interface PresenceIndicatorProps {
  score: number;  // 0.0-1.0
  state: 'scattered' | 'present' | 'witnessing';
}

// Визуализация:
// - Scattered: Пульсирующий красный круг
// - Present: Спокойный синий круг
// - Witnessing: Ясный золотой круг
```

**Estimate**: 2 дня

#### 2. Witness Dashboard
**Файл**: `frontend/src/components/WitnessDashboard.tsx`

- История presence score
- График attention quality
- Insights карточки

**Estimate**: 3 дня

#### 3. Integration в App.tsx
**Estimate**: 1 день

**Total Frontend**: ~6 дней

---

### Testing & Documentation

#### Tests
- `backend/tests/test_witness.py`
- `frontend/src/__tests__/PresenceIndicator.test.tsx`

**Estimate**: 2 дня

#### Documentation
- API documentation в `docs/API_WITNESS.md`
- User guide в `docs/WITNESS_GUIDE.md`

**Estimate**: 1 день

**Total Sprint 1**: ~17 дней (с запасом)

---

## 📅 Sprint 2: Practice Engine (2 недели)

**Даты**: 16-30 ноября 2025
**Тема**: "Практики возвращения к ясности"

### Backend Tasks

#### 1. Practice Suggestion Engine
**Файл**: `backend/app/practice/engine.py`

```python
class PracticeEngine:
    """Suggests practices based on field state."""

    def suggest_practice(
        self,
        entropy: float,
        coherence: float,
        presence_score: float,
        recent_emotions: List[str]
    ) -> Practice:
        """
        Rules:
        - entropy > 0.7 → Breath practice
        - coherence < 0.3 → Grounding practice
        - presence_score < 0.3 → Awareness practice
        - "тревога" recurring → Lovingkindness practice
        """
        pass
```

**Practices Database**:
```json
{
  "breath_4_7_8": {
    "name": "Дыхание 4-7-8",
    "type": "breath",
    "duration": 180,
    "instructions": [
      "Вдох на 4 счёта",
      "Задержка на 7",
      "Выдох на 8"
    ],
    "effects": {
      "entropy": -0.3,
      "coherence": +0.2
    }
  },
  "body_scan": {
    "name": "Сканирование тела",
    "type": "grounding",
    "duration": 300,
    ...
  }
}
```

**Estimate**: 4 дня

#### 2. Practice Session Tracking
**Файл**: `backend/app/practice/tracker.py`

- Таблица `practice_sessions`:
  - `user_id`, `practice_id`, `started_at`, `completed_at`
  - `pre_entropy`, `post_entropy`
  - `pre_coherence`, `post_coherence`
  - `completion_rate` (0.0-1.0)

**Estimate**: 2 дня

#### 3. Practice API
**Файл**: `backend/app/routes/practice.py`

Endpoints:
- `GET /api/practice/suggest` — Предложить практику
- `POST /api/practice/start` — Начать сессию
- `POST /api/practice/complete` — Завершить сессию
- `GET /api/practice/history` — История практик
- `GET /api/practice/effects` — Эффективность практик

**Estimate**: 2 дня

**Total Backend**: ~8 дней

---

### Frontend Tasks

#### 1. Practice Modal Component
**Файл**: `frontend/src/components/PracticeModal.tsx`

```tsx
interface PracticeModalProps {
  practice: Practice;
  onStart: () => void;
  onComplete: () => void;
  onSkip: () => void;
}

// Features:
// - Анимированные инструкции
// - Таймер обратного отсчёта
// - Breath visualization (круг расширяется/сжимается)
// - Ambient sounds (опционально)
```

**Estimate**: 4 дня

#### 2. Practice History View
**Файл**: `frontend/src/components/PracticeHistory.tsx`

- График эффективности практик
- Streak tracking (дни подряд)
- Favorite practices

**Estimate**: 2 дня

#### 3. Breath Invitation Toast
**Файл**: `frontend/src/components/BreathInvitation.tsx`

Появляется когда:
- entropy > 0.7
- Мягкая анимация
- "Поле дрожит. Приглашаем дыхание?"

**Estimate**: 1 день

**Total Frontend**: ~7 дней

---

### Testing & Documentation

#### Tests
- `backend/tests/test_practice.py`
- `frontend/src/__tests__/PracticeModal.test.tsx`

**Estimate**: 2 дня

#### Documentation
- Practice library в `docs/PRACTICES.md`
- API docs в `docs/API_PRACTICE.md`

**Estimate**: 1 день

**Total Sprint 2**: ~18 дней

---

## 📅 Sprint 3: Shadow Work (1 неделя)

**Даты**: 1-7 декабря 2025
**Тема**: "Интеграция тени"

### Backend Tasks

#### 1. Shadow Emotion Detection
**Файл**: `backend/app/shadow/detector.py`

```python
SHADOW_EMOTIONS = {
    "тревога", "страх", "отчаяние", "ярость",
    "зависть", "стыд", "вина", "одиночество"
}

def detect_shadow_pattern(
    recent_emotions: List[str],
    window_hours: int = 24
) -> Optional[ShadowPattern]:
    """Detects recurring difficult emotions."""
    pass
```

**Estimate**: 2 дня

#### 2. Transmutation Mapping
**Файл**: `backend/app/shadow/transmutation.py`

```python
TRANSMUTATION_MAP = {
    "страх": "смелость",
    "тревога": "присутствие",
    "ярость": "сила",
    "зависть": "восхищение",
    "стыд": "принятие",
    ...
}
```

**Estimate**: 1 день

#### 3. Shadow API
**Файл**: `backend/app/routes/shadow.py`

Endpoints:
- `GET /api/shadow/patterns` — Паттерны тени
- `POST /api/shadow/transmute` — Запрос на трансмутацию
- `GET /api/shadow/insights` — Инсайты

**Estimate**: 1 день

**Total Backend**: ~4 дня

---

### Frontend Tasks

#### 1. Shadow Space Component
**Файл**: `frontend/src/components/ShadowSpace.tsx`

```tsx
// Dark, safe UI for difficult emotions
// Features:
// - Безопасная визуализация
// - Transmutation animation (тьма → свет)
// - Journaling space
// - "Эту эмоцию видят" (не одинок)
```

**Estimate**: 3 дня

#### 2. Transmutation Visualization
**Файл**: `frontend/src/components/TransmutationViz.tsx`

- Анимация превращения эмоции
- Particle effects

**Estimate**: 2 дня

**Total Frontend**: ~5 дней

---

### Testing & Documentation
**Estimate**: 2 дня

**Total Sprint 3**: ~11 дней

---

## 📅 Sprint 4: Silence & Thresholds (1 неделя)

**Даты**: 8-14 декабря 2025
**Тема**: "Священные паузы и пороги"

### Backend Tasks

#### 1. Silence Zone Manager
**Файл**: `backend/app/silence/manager.py`

```python
class SilenceZone:
    """Manages periods of intentional silence."""

    def create_zone(
        self,
        duration_minutes: int,
        participants: List[str]
    ) -> SilenceZone:
        """
        During silence:
        - No reflections allowed
        - Only breathing/presence tracking
        - Special UI state
        """
        pass
```

**Estimate**: 2 дня

#### 2. Threshold Detection
**Файл**: `backend/app/threshold/detector.py`

```python
def detect_threshold_moment(
    field_state: Dict,
    history: List[Dict]
) -> Optional[ThresholdType]:
    """
    Detects:
    - Entropy spikes (chaos → calm)
    - Coherence shifts
    - Emotional transitions
    - First reflection after silence
    """
    pass
```

**Estimate**: 2 дня

**Total Backend**: ~4 дня

---

### Frontend Tasks

#### 1. Silence UI
**Файл**: `frontend/src/components/SilenceZone.tsx`

- Минималистичный интерфейс
- Таймер молчания
- Breath visualization only

**Estimate**: 2 дня

#### 2. Threshold Markers
**Файл**: `frontend/src/components/ThresholdMarker.tsx`

- Визуальные "врата"
- Transition animations
- Sacred geometry

**Estimate**: 2 дня

**Total Frontend**: ~4 дня

---

**Total Sprint 4**: ~10 дней

---

## 🎯 Summary: v0.3 Timeline

| Sprint | Тема | Длительность | Завершение |
|--------|------|--------------|------------|
| 1 | Witness Layer | 2 недели | 16 ноября |
| 2 | Practice Engine | 2 недели | 30 ноября |
| 3 | Shadow Work | 1 неделя | 7 декабря |
| 4 | Silence & Thresholds | 1 неделя | 14 декабря |
| — | Testing & Polish | 1 неделя | 21 декабря |
| — | Documentation | 3 дня | 24 декабря |
| ✨ | **v0.3 Release** | — | **25 декабря 2025** 🎄 |

---

## 🏗️ Архитектура v0.3

```
┌─────────────────────────────────────────────┐
│             Frontend (React)                │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Components                         │   │
│  │  - PresenceIndicator                │   │
│  │  - PracticeModal                    │   │
│  │  - ShadowSpace                      │   │
│  │  - SilenceZone                      │   │
│  │  - ThresholdMarker                  │   │
│  └─────────────────────────────────────┘   │
└──────────────────┬──────────────────────────┘
                   │ HTTP/WS
                   ↓
┌─────────────────────────────────────────────┐
│          Backend (FastAPI)                  │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  New Modules (v0.3)                 │   │
│  │  - witness/     (Метрики внимания)  │   │
│  │  - practice/    (Практики)          │   │
│  │  - shadow/      (Работа с тенью)    │   │
│  │  - silence/     (Молчание)          │   │
│  │  - threshold/   (Пороги)            │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Existing (v0.2)                    │   │
│  │  - astro/       (AstroField)        │   │
│  │  - feedback/    (NeuroFeedback)     │   │
│  │  - mirror/      (MirrorLoop)        │   │
│  │  - analytics/   (Analytics)         │   │
│  │  - auth/        (Device Memory)     │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 📊 Метрики Успеха v0.3

### Quantitative
- [ ] Presence score tracking для 100% пользователей
- [ ] ≥ 60% пользователей завершают хотя бы 1 практику
- [ ] Shadow patterns обнаружены у ≥ 30% активных
- [ ] Silence zones используются ≥ 10% времени
- [ ] Threshold moments детектятся с точностью ≥ 70%

### Qualitative
- [ ] Пользователи чувствуют "наблюдателя"
- [ ] Практики реально снижают entropy
- [ ] Shadow space ощущается безопасным
- [ ] Silence ценится как "священное"

---

## 🌟 Философский Результат

**v0.2**: "Поле, которое дышит"
**v0.3**: "Храм, где дышат вместе"

После v0.3 пользователь:
1. **Видит** своё присутствие (Witness)
2. **Практикует** возвращение к ясности (Practices)
3. **Интегрирует** тень (Shadow)
4. **Ценит** молчание (Silence)
5. **Узнаёт** пороги трансформации (Thresholds)

---

🌗 **Путь начинается. Пойдём вместе.**

*С присутствием,
Claude Code
2 ноября 2025*
