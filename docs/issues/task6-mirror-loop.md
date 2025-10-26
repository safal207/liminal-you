Готово, бро 🌗 — вот готовый текст Issue для GitHub, вставляй как есть.

---

🪞 Task 6 — Mirror Loop / Self-Learning Resonance

Цель

Сделать систему саморефлексивной: фиксировать, как нейро-отклик влияет на поле (AstroLayer), извлекать паттерны и самообучаться мягко регулировать резонанс (tone/intensity) в будущем.


---

Ключевая идея

Каждый цикл «отклик → изменение поля» = опыт. Мы собираем такие пары, агрегируем по контексту (время, нагрузка, доминирующая эмоция) и строим простую управляемую политику:

> в похожих условиях — выбирай такой же отклик, который в прошлом повышал coherence и снижал entropy.



---

Архитектура

Reflections → AstroLayer (state_t)
                 ↓
        NeuroFeedbackHub (tone,intensity,message)
                 ↓
            AstroLayer (state_t+Δ)
                 ↓
          MirrorLoop Logger  ──►  mirror_events (DB)
                 ↓
      MirrorPolicy Learner  ──►  policy_table (DB)
                 ↓
      FeedbackHub uses policy (warm/cool/neutral, intensity)


---

Backend

1) Сбор данных (MirrorLoop Logger)

Хук в NeuroFeedbackHub: после отправки feedback берём:

pre_state = {coherence, entropy, pad}

action = {tone, intensity}

через 3–5с (или при новом снапшоте) фиксируем post_state

сохраняем episode: ts, user_count, pre, action, post, dt



Таблица mirror_events

(id, ts, user_count, tone, intensity,
 pre_coh, pre_ent, pre_pad,
 post_coh, post_ent, post_pad, dt_ms, bucket_key)

2) Обучение политики (Policy Learner)

Периодический job (каждые 60с):

группирует по bucket_key:
bucket_key = hour_of_day + "-" + load_bin + "-" + dominant_pad_bin

считает reward = (Δcoherence - Δentropy) с нормировкой.

обновляет policy_table(bucket_key, tone, intensity_bin, reward_avg, n).



Таблица policy_table

(bucket_key, tone, intensity_bin, reward_avg, n, updated_at)
-- composite PK: (bucket_key, tone, intensity_bin)

3) Использование политики (FeedbackHub)

При формировании нового отклика:

вычислить bucket_key текущего контекста;

выбрать (tone, intensity) с max reward_avg (ε-greedy: ε=0.1);

если нет данных — fallback к текущей логике (анализ AstroLayer).



---

Frontend

Страница /mirror (мини-дашборд):

график Δcoherence/Δentropy по эпизодам;

heatmap эффективности (tone × intensity_bin) по времени суток;

индикатор текущего bucket_key и выбранной политики.


Тумблер “Adaptive feedback (Mirror)” в настройках профиля (по умолчанию ON).



---

API

POST /api/mirror/replay (admin-only): запустить обучение прямо сейчас.

GET  /api/mirror/policy?bucket_key=... → текущая политика.

GET  /api/mirror/stats?from&to → агрегаты reward/coverage.



---

Алгоритм (псевдокод)

# reward: чем выше coh и ниже ent после отклика — тем лучше
def reward(pre, post):
    return (post.coh - pre.coh) - (post.ent - pre.ent)

def bucket_key(now, load, pad):
    h = now.hour
    load_bin = "L" if load<20 else "M" if load<60 else "H"
    dom = argmax(pad)  # P/A/D
    return f"{h}-{load_bin}-{dom}"

# ε-greedy policy
def choose_action(bkey, candidates):
    if random()<0.1 or bkey not in policy:
        return fallback_action()  # old analyze_state
    return argmax(policy[bkey], key="reward_avg")


---

Метрики успеха

↑ средний coherence и ↓ entropy в тех же интервалах времени (A/B: adaptive vs static).

Покрытие bucket’ов ≥ 60% активного времени.

Сходимость политики: снижение дисперсии reward через 24ч.



---

Безопасность / этика

Логируем только агрегаты поля (без личного контента).

Персональные настройки: mirror_enabled (opt-out).

Rate-limit на записи episode’ов (не чаще 1 раз / 2с на bucket).



---

Миграции (LiminalBD)

mirror_events и policy_table + индексы:

idx_mirror_ts, idx_mirror_bucket, idx_policy_bucket.



---

Definition of Done

[ ] Записываются mirror_events (pre/action/post) с dt и bucket_key.

[ ] Периодический learner обновляет policy_table (reward_avg, n).

[ ] FeedbackHub использует политику (ε-greedy) с fallback.

[ ] /mirror показывает историю и эффективность политики.

[ ] Opt-out mirror_enabled работает (сервер уважает настройку).

[ ] Базовые автотесты на расчёт reward и выбор действия.



---

Тест-план

E2E: 2 браузера, серия отражений → видим, что через 10–15 минут политика начинает выбирать более «эффективные» тона/интенсивности (рост среднего reward).

A/B: for 1h — половина с adaptive OFF, половина ON → сравнить средний (Δcoh − Δent).

Нагрузочно: 100 WS-клиентов, логгер и learner не блокируют FeedbackHub.



---

