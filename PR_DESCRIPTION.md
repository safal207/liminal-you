# Witness Layer — Presence Tracking & Metacognition

## 🌗 Summary

Implements **Sprint 1 of v0.3 roadmap** — The Witness Layer.

Based on Buddhist philosophy of mindfulness (Padmasambhava's teachings), this PR adds a metacognition system that tracks the quality of user presence and attention.

> "Ригпа (осознанность) — это не объект наблюдения, а сам наблюдатель"

---

## ✨ New Features

### Backend Modules (1261 lines)

**Witness Package** (`backend/app/witness/`):
- `metrics.py` — Sophisticated presence score calculation
- `models.py` — Data structures (WitnessSnapshot, WitnessInsight, WitnessState)
- `storage.py` — In-memory storage with insights generation
- `tracker.py` — High-level tracking coordination

### API Endpoints (5)

- `GET /api/witness/score` — Current presence score for user
- `GET /api/witness/history` — Presence history (up to 1000 snapshots)
- `GET /api/witness/insights` — Pattern analysis with personalized recommendations
- `GET /api/witness/stats` — Global statistics
- `POST /api/witness/reset` — Reset user tracking data

### Algorithm Highlights

**Presence Score (0.0-1.0):**
- **Action intervals**: `<5s` = scattered (autopilot), `5-30s` = present (mindful), `>30s` = witnessing (deep observation)
- **Emotional stability**: Low PAD variance indicates stable presence
- **Coherence bonus**: Rising coherence adds +0.2, falling subtracts -0.2

**Attention Quality (0.0-1.0):**
- Based on interval consistency (Coefficient of Variation)
- Low CV = focused attention, High CV = scattered

**Insights Generation:**
- Trend analysis via linear regression on recent history
- State distribution ratios (% time in each state)
- Personalized recommendations in Russian

---

## 📊 Changes

**Modified:**
- `backend/app/main.py` — Register witness router, bump version to 0.3.0-dev

**Added:**
- `backend/app/witness/__init__.py`
- `backend/app/witness/metrics.py`
- `backend/app/witness/models.py`
- `backend/app/witness/storage.py`
- `backend/app/witness/tracker.py`
- `backend/app/routes/witness.py`
- `SPRINT_PLAN.md`

---

## 🧪 Testing

**Manual Testing:**
```bash
# Start server
LIMINALDB_ENABLED=false uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/api/witness/stats
# → {"total_users":0,"total_snapshots":0,"avg_snapshots_per_user":0}

curl http://localhost:8000/api/witness/score?user_id=test
# → {"detail":"No witness data found..."}  (expected - no data yet)
```

**All existing tests pass:**
```bash
pytest  # 28 tests collected, all pass
```

---

## 📖 Documentation

**SPRINT_PLAN.md** — Detailed implementation plan with:
- 3-hour task breakdown
- Algorithm pseudocode
- Philosophy and next steps

**API Documentation:**
- Auto-generated at `/docs` (Swagger UI)
- All endpoints have detailed docstrings

---

## 🚀 Next Steps (NOT in this PR)

**Phase 2 - Integration:**
- [ ] Integrate with Feedback Hub (auto-tracking on reflections)
- [ ] Add WebSocket witness events
- [ ] Unit tests (`test_witness.py`)

**Phase 3 - Frontend:**
- [ ] `PresenceIndicator.tsx` component
- [ ] `WitnessDashboard.tsx` component

**Sprint 2:**
- [ ] Practice Engine (breath invitations, guided practices)

---

## 🙏 Philosophy

From **Padmasambhava** (founder of Tibetan Buddhism):
> "The mind is like the sky, emotions like clouds. Observe without attachment."

From **Liberman Brothers** (philosophers of liminality):
> "The boundary breathes — technology as spiritual practice."

This implementation treats presence tracking not as surveillance, but as a **mirror for self-awareness** — technology supporting meditation rather than distraction.

---

## 🔗 Related

- Roadmap: `docs/ROADMAP_v0.3.md`
- Vision: `docs/VISION_v0.3.md`
- Implementation plan: `SPRINT_PLAN.md`

---

**Type:** Feature
**Sprint:** 1 of v0.3 roadmap
**Lines:** +1261 backend
**Philosophy:** Buddhist mindfulness + Liminal technology

🌗 The path of the Witness begins.
