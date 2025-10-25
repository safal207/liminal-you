"""i18n API routes."""
from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..i18n import Language, translate, translate_emotion, get_all_translations, get_supported_languages

router = APIRouter()


class TranslationsResponse(BaseModel):
    """Translations response."""

    language: str
    translations: Dict[str, str]


class EmotionTranslation(BaseModel):
    """Emotion translation in all languages."""

    ru: str
    en: str
    zh: str


class EmotionsTranslationsResponse(BaseModel):
    """All emotion translations."""

    emotions: Dict[str, EmotionTranslation]


@router.get("/i18n/languages")
def list_languages() -> Dict[str, list[str]]:
    """Get list of supported languages.

    Returns:
        List of language codes
    """
    return {"languages": get_supported_languages()}


@router.get("/i18n/translations", response_model=TranslationsResponse)
def get_translations(
    language: Language = Query("ru", description="Language code (ru, en, zh)")
) -> TranslationsResponse:
    """Get all translations for a language.

    Args:
        language: Target language

    Returns:
        All translations for the language
    """
    translations = get_all_translations(language)
    return TranslationsResponse(language=language, translations=translations)


@router.get("/i18n/translate/{key}")
def translate_key(
    key: str,
    language: Language = Query("ru", description="Language code (ru, en, zh)"),
) -> Dict[str, str]:
    """Translate a specific key.

    Args:
        key: Translation key
        language: Target language

    Returns:
        Translated string
    """
    translation = translate(key, language)
    return {"key": key, "translation": translation, "language": language}


@router.get("/i18n/emotions", response_model=EmotionsTranslationsResponse)
def get_emotion_translations() -> EmotionsTranslationsResponse:
    """Get all emotion translations.

    Returns:
        All emotions in all supported languages
    """
    from ..i18n.translations import EMOTION_TRANSLATIONS

    emotions = {}
    for emotion_ru, translations in EMOTION_TRANSLATIONS.items():
        emotions[emotion_ru] = EmotionTranslation(
            ru=translations.get("ru", emotion_ru),
            en=translations.get("en", emotion_ru),
            zh=translations.get("zh", emotion_ru),
        )

    return EmotionsTranslationsResponse(emotions=emotions)


@router.get("/i18n/emotion/{emotion}")
def translate_emotion_name(
    emotion: str,
    language: Language = Query("ru", description="Language code (ru, en, zh)"),
) -> Dict[str, str]:
    """Translate a specific emotion name.

    Args:
        emotion: Russian emotion name
        language: Target language

    Returns:
        Translated emotion name
    """
    translation = translate_emotion(emotion, language)
    return {
        "original": emotion,
        "translation": translation,
        "language": language,
    }
