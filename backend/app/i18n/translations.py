"""Internationalization (i18n) support for liminal-you."""
from __future__ import annotations

from typing import Dict, Literal

Language = Literal["ru", "en", "zh"]

# Translations database
TRANSLATIONS: Dict[Language, Dict[str, str]] = {
    "ru": {
        # Feedback messages
        "feedback.warm": "Поле дрожит — пригласи дыхание.",
        "feedback.cool": "Поле гармонично, можно делиться.",
        "feedback.neutral": "Слушаем поле.",

        # UI labels
        "ui.feed": "Лента",
        "ui.profile": "Профиль",
        "ui.close_profile": "Закрыть профиль",
        "ui.send_reflection": "Отправить отражение",
        "ui.sending": "Отправка...",
        "ui.emotion": "Эмоция",
        "ui.message": "Сообщение",
        "ui.loading": "Загрузка резонансов...",
        "ui.empty_feed": "Пока тихо. Оставь первое отражение.",

        # Analytics
        "analytics.entropy": "Энтропия",
        "analytics.coherence": "Когерентность",
        "analytics.field_state": "Состояние поля",
        "analytics.trend": "Тренд",
        "analytics.stable": "стабильно",
        "analytics.increasing": "растёт",
        "analytics.decreasing": "падает",

        # Emotions (categories)
        "emotion.category.positive": "Положительные",
        "emotion.category.negative": "Отрицательные",
        "emotion.category.neutral": "Нейтральные",

        # Auth
        "auth.login": "Войти",
        "auth.logout": "Выйти",
        "auth.device_trust": "Доверие устройства",

        # Errors
        "error.network": "Ошибка сети",
        "error.auth_failed": "Ошибка аутентификации",
        "error.not_found": "Не найдено",
    },

    "en": {
        # Feedback messages
        "feedback.warm": "The field trembles — invite breath.",
        "feedback.cool": "The field is harmonious, ready to share.",
        "feedback.neutral": "Listening to the field.",

        # UI labels
        "ui.feed": "Feed",
        "ui.profile": "Profile",
        "ui.close_profile": "Close profile",
        "ui.send_reflection": "Send reflection",
        "ui.sending": "Sending...",
        "ui.emotion": "Emotion",
        "ui.message": "Message",
        "ui.loading": "Loading resonances...",
        "ui.empty_feed": "Quiet for now. Leave the first reflection.",

        # Analytics
        "analytics.entropy": "Entropy",
        "analytics.coherence": "Coherence",
        "analytics.field_state": "Field State",
        "analytics.trend": "Trend",
        "analytics.stable": "stable",
        "analytics.increasing": "increasing",
        "analytics.decreasing": "decreasing",

        # Emotions (categories)
        "emotion.category.positive": "Positive",
        "emotion.category.negative": "Negative",
        "emotion.category.neutral": "Neutral",

        # Auth
        "auth.login": "Login",
        "auth.logout": "Logout",
        "auth.device_trust": "Device Trust",

        # Errors
        "error.network": "Network error",
        "error.auth_failed": "Authentication failed",
        "error.not_found": "Not found",
    },

    "zh": {
        # Feedback messages
        "feedback.warm": "场域颤动——邀请呼吸。",
        "feedback.cool": "场域和谐，可以分享。",
        "feedback.neutral": "聆听场域。",

        # UI labels
        "ui.feed": "动态",
        "ui.profile": "档案",
        "ui.close_profile": "关闭档案",
        "ui.send_reflection": "发送反思",
        "ui.sending": "发送中...",
        "ui.emotion": "情绪",
        "ui.message": "消息",
        "ui.loading": "加载共振中...",
        "ui.empty_feed": "暂时安静。留下第一个反思。",

        # Analytics
        "analytics.entropy": "熵",
        "analytics.coherence": "连贯性",
        "analytics.field_state": "场域状态",
        "analytics.trend": "趋势",
        "analytics.stable": "稳定",
        "analytics.increasing": "上升",
        "analytics.decreasing": "下降",

        # Emotions (categories)
        "emotion.category.positive": "正面",
        "emotion.category.negative": "负面",
        "emotion.category.neutral": "中性",

        # Auth
        "auth.login": "登录",
        "auth.logout": "登出",
        "auth.device_trust": "设备信任",

        # Errors
        "error.network": "网络错误",
        "error.auth_failed": "认证失败",
        "error.not_found": "未找到",
    },
}


# Emotion translations
EMOTION_TRANSLATIONS: Dict[str, Dict[Language, str]] = {
    # Positive emotions
    "свет": {"ru": "свет", "en": "light", "zh": "光"},
    "радость": {"ru": "радость", "en": "joy", "zh": "喜悦"},
    "восторг": {"ru": "восторг", "en": "delight", "zh": "欢欣"},
    "спокойствие": {"ru": "спокойствие", "en": "calmness", "zh": "平静"},
    "вдохновение": {"ru": "вдохновение", "en": "inspiration", "zh": "灵感"},
    "любовь": {"ru": "любовь", "en": "love", "zh": "爱"},
    "интерес": {"ru": "интерес", "en": "interest", "zh": "兴趣"},
    "надежда": {"ru": "надежда", "en": "hope", "zh": "希望"},
    "благодарность": {"ru": "благодарность", "en": "gratitude", "zh": "感恩"},
    "умиротворение": {"ru": "умиротворение", "en": "peace", "zh": "安详"},
    "нежность": {"ru": "нежность", "en": "tenderness", "zh": "温柔"},
    "восхищение": {"ru": "восхищение", "en": "admiration", "zh": "钦佩"},
    "предвкушение": {"ru": "предвкушение", "en": "anticipation", "zh": "期待"},
    "облегчение": {"ru": "облегчение", "en": "relief", "zh": "宽慰"},
    "удовлетворение": {"ru": "удовлетворение", "en": "satisfaction", "zh": "满足"},
    "любопытство": {"ru": "любопытство", "en": "curiosity", "zh": "好奇"},
    "азарт": {"ru": "азарт", "en": "excitement", "zh": "兴奋"},
    "гармония": {"ru": "гармония", "en": "harmony", "zh": "和谐"},

    # Negative emotions
    "грусть": {"ru": "грусть", "en": "sadness", "zh": "悲伤"},
    "злость": {"ru": "злость", "en": "anger", "zh": "愤怒"},
    "тревога": {"ru": "тревога", "en": "anxiety", "zh": "焦虑"},
    "страх": {"ru": "страх", "en": "fear", "zh": "恐惧"},
    "печаль": {"ru": "печаль", "en": "sorrow", "zh": "忧伤"},
    "разочарование": {"ru": "разочарование", "en": "disappointment", "zh": "失望"},
    "отчаяние": {"ru": "отчаяние", "en": "despair", "zh": "绝望"},
    "вина": {"ru": "вина", "en": "guilt", "zh": "内疚"},
    "стыд": {"ru": "стыд", "en": "shame", "zh": "羞耻"},
    "зависть": {"ru": "зависть", "en": "envy", "zh": "嫉妒"},
    "обида": {"ru": "обида", "en": "resentment", "zh": "怨恨"},
    "ярость": {"ru": "ярость", "en": "rage", "zh": "暴怒"},
    "беспокойство": {"ru": "беспокойство", "en": "worry", "zh": "担忧"},
    "тоска": {"ru": "тоска", "en": "melancholy", "zh": "惆怅"},
    "одиночество": {"ru": "одиночество", "en": "loneliness", "zh": "孤独"},
    "растерянность": {"ru": "растерянность", "en": "confusion", "zh": "困惑"},
    "скука": {"ru": "скука", "en": "boredom", "zh": "无聊"},

    # Neutral emotions
    "удивление": {"ru": "удивление", "en": "surprise", "zh": "惊讶"},
    "замешательство": {"ru": "замешательство", "en": "embarrassment", "zh": "尴尬"},
    "ностальгия": {"ru": "ностальгия", "en": "nostalgia", "zh": "怀旧"},
    "меланхолия": {"ru": "меланхолия", "en": "melancholy", "zh": "忧郁"},
    "задумчивость": {"ru": "задумчивость", "en": "thoughtfulness", "zh": "沉思"},
    "созерцание": {"ru": "созерцание", "en": "contemplation", "zh": "凝思"},
    "покой": {"ru": "покой", "en": "tranquility", "zh": "宁静"},
    "безмятежность": {"ru": "безмятежность", "en": "serenity", "zh": "恬静"},
}


def translate(key: str, language: Language = "ru") -> str:
    """Translate a key to the specified language.

    Args:
        key: Translation key
        language: Target language (ru, en, zh)

    Returns:
        Translated string or key if not found
    """
    return TRANSLATIONS.get(language, {}).get(key, key)


def translate_emotion(emotion: str, language: Language = "ru") -> str:
    """Translate emotion name to specified language.

    Args:
        emotion: Russian emotion name
        language: Target language

    Returns:
        Translated emotion name
    """
    emotion_lower = emotion.strip().lower()
    return EMOTION_TRANSLATIONS.get(emotion_lower, {}).get(language, emotion)


def get_all_translations(language: Language = "ru") -> Dict[str, str]:
    """Get all translations for a language.

    Args:
        language: Target language

    Returns:
        Dictionary of all translations
    """
    return TRANSLATIONS.get(language, {})


def get_supported_languages() -> list[Language]:
    """Get list of supported languages.

    Returns:
        List of language codes
    """
    return ["ru", "en", "zh"]
