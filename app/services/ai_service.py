"""
AI Service Module for DriftBridge

Provides local language detection and translation using
langdetect and Argos Translate.
"""

import json
import logging
import re
from typing import Optional, Dict, Any, Tuple

from langdetect import detect, DetectorFactory

from sqlalchemy import text

DetectorFactory.seed = 0

logger = logging.getLogger(__name__)


SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'mr': 'Marathi',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'ur': 'Urdu',
    'tr': 'Turkish',
}


def get_language_name(language_code: str) -> str:
    """Convert an ISO language code to a full language name."""
    return SUPPORTED_LANGUAGES.get(
        language_code,
        language_code.upper()
    )


class AIService:
    """Service class for local language detection and translation."""

    def __init__(self):
        # Local translation and language detection do not require
        # an external API key or internet connection.
        self.available = True

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------

    def detect_message_language(
        self,
        text: str,
        preferred_language: Optional[str] = None
    ) -> str:
        """Detect the actual language of a message locally."""

        if not text or not text.strip():
            return preferred_language or "en"

        try:
            detected_language = detect(text.strip())

            # Normalize langdetect's regional Chinese code.
            if detected_language == "zh-cn":
                detected_language = "zh"

            # Only use languages supported by DriftBridge.
            if detected_language in SUPPORTED_LANGUAGES:
                return detected_language

            logger.warning(
                "Detected unsupported language '%s'. "
                "Falling back to English.",
                detected_language
            )
            return "en"

        except Exception as exc:
            logger.warning(
                "Local language detection failed: %s. "
                "Falling back to '%s'.",
                exc,
                preferred_language or "en"
            )
            return preferred_language or "en"

    # ------------------------------------------------------------------
    # Translation
    # ------------------------------------------------------------------

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text locally using Argos Translate."""

        if not text or not text.strip():
            return {
                "success": False,
                "error": "Text cannot be empty.",
            }

        if not target_language:
            return {
                "success": False,
                "error": "Target language is required.",
            }

        try:
            result = self.translate_text_with_word_mapping(
                text=text,
                target_language=target_language,
                source_language=source_language,
            )

            if not result.get("success"):
                return result

            translated = (
                result.get("translated_text") or ""
            ).strip()

            if not translated:
                return {
                    "success": False,
                    "error": "Translation returned empty content.",
                }

            return {
                "success": True,
                "translated_text": translated,
            }

        except Exception as exc:
            logger.exception(
                "Local translation failed: %s",
                exc,
            )

            return {
                "success": False,
                "error": "Local translation failed.",
            }

    # ------------------------------------------------------------------
    # Translation mapping
    # ------------------------------------------------------------------

    def translate_text_with_word_mapping(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text locally using Argos Translate.

        Uses a direct language pair when available.
        If no direct pair exists, falls back through English.
        """

        if not text or not text.strip():
            return {
                "success": False,
                "error": "Cannot translate empty text."
            }

        try:
            import argostranslate.translate as argos_translate

            source_code = (
                source_language.lower().strip()
                if source_language
                else "en"
            )

            target_code = target_language.lower().strip()

            # Nothing to translate.
            if source_code == target_code:
                return {
                    "success": True,
                    "translated_text": text,
                    "words": [
                        {
                            "original": word.strip(),
                            "translated": word.strip()
                        }
                        for word in text.split()
                        if word.strip()
                    ]
                }

            def has_direct_translation(
                from_code: str,
                to_code: str
            ) -> bool:
                """Check whether Argos has the requested local pair."""
                try:
                    translation = (
                        argos_translate.get_translation_from_codes(
                            from_code,
                            to_code
                        )
                    )
                    return translation is not None
                except Exception:
                    return False

            # ----------------------------------------------------------
            # 1. Try direct translation first.
            # ----------------------------------------------------------
            if has_direct_translation(source_code, target_code):
                translated_text = argos_translate.translate(
                    text,
                    source_code,
                    target_code
                )

            # ----------------------------------------------------------
            # 2. Fall back through English.
            # ----------------------------------------------------------
            elif (
                source_code != "en"
                and target_code != "en"
                and has_direct_translation(source_code, "en")
                and has_direct_translation("en", target_code)
            ):
                english_text = argos_translate.translate(
                    text,
                    source_code,
                    "en"
                )

                if not english_text or not english_text.strip():
                    return {
                        "success": False,
                        "error": (
                            f"Intermediate translation failed for "
                            f"{source_code} -> en."
                        )
                    }

                translated_text = argos_translate.translate(
                    english_text,
                    "en",
                    target_code
                )

            # ----------------------------------------------------------
            # 3. No usable local route.
            # ----------------------------------------------------------
            else:
                return {
                    "success": False,
                    "error": (
                        f"No local translation route available for "
                        f"{source_code} -> {target_code}."
                    )
                }

            if not translated_text or not translated_text.strip():
                return {
                    "success": False,
                    "error": "Argos Translate returned empty content."
                }

            # ----------------------------------------------------------
            # Build word-level mappings.
            # ----------------------------------------------------------
            original_words = re.findall(r"\S+", text)
            words = []

            for original_word in original_words:
                clean_original = original_word.strip()

                if not clean_original:
                    continue

                token_match = re.match(
                    r"^([^\w\u0080-\uFFFF]*)(.*?)([^\w\u0080-\uFFFF]*)$",
                    clean_original,
                    re.UNICODE
                )

                if token_match:
                    prefix, core, suffix = token_match.groups()
                else:
                    prefix = ""
                    core = clean_original
                    suffix = ""

                if not core:
                    words.append({
                        "original": clean_original,
                        "translated": clean_original
                    })
                    continue

                try:
                    token_translation = argos_translate.translate(
                        core,
                        source_code,
                        target_code
                    )

                    token_translation = (
                        token_translation.strip()
                        if token_translation
                        else core
                    )

                except Exception:
                    token_translation = core

                words.append({
                    "original": clean_original,
                    "translated": (
                        f"{prefix}{token_translation}{suffix}"
                    )
                })

            return {
                "success": True,
                "translated_text": translated_text.strip(),
                "words": words
            }

        except Exception as exc:
            logger.exception(
                "Argos translation failed: source=%s target=%s error=%s",
                source_language,
                target_language,
                exc
            )

            return {
                "success": False,
                "error": (
                    "Local translation is unavailable for "
                    f"{source_language or 'auto'} -> {target_language}."
                )
            }


# ----------------------------------------------------------------------
# Module-level convenience functions
# ----------------------------------------------------------------------

_ai_service: Optional[AIService] = None


def detect_message_language(
    text: str,
    preferred_language: Optional[str] = None
) -> str:
    """Detect a message's actual language using the local detector."""
    service = get_ai_service()

    return service.detect_message_language(
        text,
        preferred_language
    )


def get_ai_service() -> AIService:
    """Return a lazily-initialized singleton AIService."""

    global _ai_service

    if _ai_service is None:
        _ai_service = AIService()

    return _ai_service


def translate_message(
    text: str,
    target_language: str,
    source_language: Optional[str] = None,
    message_id: Optional[int] = None,
) -> Tuple[bool, str]:
    """Translate text.

    Returns:
        (success, translated_text_or_error_message)
    """

    service = get_ai_service()

    result = service.translate_text(
        text,
        target_language,
        source_language
    )

    if not result.get("success"):
        logger.warning(
            "Translation failed - message_id=%s source=%s "
            "target=%s error=%s",
            message_id,
            source_language,
            target_language,
            result.get("error"),
        )

        return False, result.get(
            "error",
            "Translation failed."
        )

    return True, result["translated_text"]


def translate_message_with_word_mapping(
    text: str,
    target_language: str,
    source_language: Optional[str] = None,
    message_id: Optional[int] = None,
) -> Tuple[bool, Any]:
    """Translate text and return word-level translation mapping."""

    service = get_ai_service()

    result = service.translate_text_with_word_mapping(
        text,
        target_language,
        source_language
    )

    if not result.get("success"):
        logger.warning(
            "Word-level translation failed - "
            "message_id=%s source=%s target=%s error=%s",
            message_id,
            source_language,
            target_language,
            result.get("error"),
        )

        return False, result.get(
            "error",
            "Word-level translation failed."
        )

    return True, result


def check_content_safety(
    text: str
) -> Tuple[bool, str]:
    """Check content safety without using an external AI service.

    External content moderation has been removed from DriftBridge.
    Content is currently allowed by default.
    """

    if not text or not text.strip():
        return True, ""

    return True, ""