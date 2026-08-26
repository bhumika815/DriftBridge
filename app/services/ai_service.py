"""
AI Service Module for DriftBridge
Handles Google Gemini API integration for translation and content moderation.

Uses the current google-genai SDK (NOT the deprecated google.generativeai).
The service degrades gracefully when GEMINI_API_KEY is not configured:
non-AI features keep working and callers receive a clear "unavailable"
result instead of a silent fallback.
"""

import json
import logging
import os
import re
from typing import Optional, Dict, Any, Tuple

from google import genai
from google.genai import errors as genai_errors


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
}


def get_language_name(language_code: str) -> str:
    """Convert an ISO language code to a full language name."""
    return SUPPORTED_LANGUAGES.get(language_code, language_code.upper())


class AIService:
    """Service class for AI-powered features using Google Gemini API."""

    # A fast, inexpensive text model suitable for translation + moderation.
    MODEL_ID = "gemini-2.0-flash"

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key.strip() == "":
            logger.warning(
                "GEMINI_API_KEY is not configured. AI features "
                "(translation and moderation) will be unavailable."
            )
            self.client = None
            self.available = False
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.available = True
            except Exception as exc:
                logger.error("Failed to initialize Gemini client: %s", exc)
                self.client = None
                self.available = False

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _generate(self, prompt: str) -> Optional[str]:
        """Send a prompt to Gemini and return the raw text response."""
        if not self.available:
            return None
        try:
            response = self.client.models.generate_content(
                model=self.MODEL_ID,
                contents=prompt,
            )
            text = response.text
            return text.strip() if text else None
        except genai_errors.APIError as exc:
            logger.error("Gemini API error: %s", exc)
            return None
        except Exception as exc:
            logger.error("Unexpected Gemini error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Translation
    # ------------------------------------------------------------------

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text to target_language using Gemini.

        Returns a dict with:
          success: bool
          translated_text: str (only if success)
          error: str (only if not success)
        """
        if not self.available:
            return {
                "success": False,
                "error": "AI translation is currently unavailable. "
                         "Please configure the Gemini API key.",
            }

        target_name = get_language_name(target_language)

        if source_language:
            source_name = get_language_name(source_language)
            prompt = (
                f"Translate the following text from {source_name} to "
                f"{target_name}. Reply with ONLY the translated text, "
                f"no explanations, no quotes, no extra commentary.\n\n"
                f"Text: {text}"
            )
        else:
            prompt = (
                f"Translate the following text to {target_name}. "
                f"Reply with ONLY the translated text, no explanations, "
                f"no quotes, no extra commentary.\n\n"
                f"Text: {text}"
            )

        translated = self._generate(prompt)

        if not translated:
            return {
                "success": False,
                "error": "Translation request failed. "
                         "The AI service may be unavailable.",
            }

        # Strip wrapping quotes Gemini sometimes adds.
        translated = translated.strip().strip('"').strip("'").strip()

        if not translated:
            return {
                "success": False,
                "error": "Translation returned empty content.",
            }

        return {
            "success": True,
            "translated_text": translated,
        }

    # ------------------------------------------------------------------
    # Content moderation / hate-speech detection
    # ------------------------------------------------------------------

    def detect_hate_speech(self, text: str) -> Dict[str, Any]:
        """Analyze text for inappropriate content.

        Returns a dict with:
          success: bool
          is_inappropriate: bool
          severity: str  ("none"|"low"|"medium"|"high")
          categories: list[str]
          reason: str
        """
        if not self.available:
            return {
                "success": False,
                "error": "Content moderation service is unavailable.",
                "is_inappropriate": False,
                "severity": "none",
                "categories": [],
                "reason": "",
            }

        prompt = (
            "You are a content moderation system. Analyze the following text "
            "for hate speech, harassment, threats, discrimination, or abusive "
            "content.\n\n"
            "Respond with ONLY a JSON object (no markdown, no code fences) in "
            "exactly this format:\n"
            '{\n'
            '  "is_inappropriate": false,\n'
            '  "severity": "none",\n'
            '  "categories": [],\n'
            '  "reason": ""\n'
            '}\n\n'
            "Rules:\n"
            '- "is_inappropriate": boolean\n'
            '- "severity": one of "none", "low", "medium", "high"\n'
            '- "categories": list of strings, e.g. ["hate_speech", '
            '"harassment", "threat", "discrimination"]\n'
            '- "reason": brief explanation if inappropriate, otherwise empty\n\n'
            f"Text to analyze: {text}"
        )

        raw = self._generate(prompt)

        if not raw:
            return {
                "success": False,
                "error": "Moderation request failed.",
                "is_inappropriate": False,
                "severity": "none",
                "categories": [],
                "reason": "",
            }

        parsed = self._parse_moderation_json(raw)
        if parsed is None:
            logger.warning("Could not parse moderation response: %s", raw[:200])
            return {
                "success": False,
                "error": "Moderation returned an unparseable response.",
                "is_inappropriate": False,
                "severity": "none",
                "categories": [],
                "reason": "",
            }

        return {
            "success": True,
            "is_inappropriate": parsed.get("is_inappropriate", False),
            "severity": parsed.get("severity", "none"),
            "categories": parsed.get("categories", []),
            "reason": parsed.get("reason", ""),
        }

    @staticmethod
    def _parse_moderation_json(raw: str) -> Optional[Dict[str, Any]]:
        """Safely extract a JSON object from the model's text response."""
        if not raw:
            return None

        # Strip markdown code fences if present.
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            # Remove first line (```json or ```) and trailing fence.
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        # Try direct JSON parse first.
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Fallback: extract the first {...} block.
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

        return None


# ----------------------------------------------------------------------
# Module-level convenience functions
# ----------------------------------------------------------------------

_ai_service: Optional[AIService] = None


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

    Returns (success, translated_text_or_error_message).
    Logs failures with context. Never silently returns the original text.
    """
    service = get_ai_service()
    result = service.translate_text(text, target_language, source_language)

    if not result.get("success"):
        logger.warning(
            "Translation failed — message_id=%s source=%s target=%s error=%s",
            message_id,
            source_language,
            target_language,
            result.get("error"),
        )
        return False, result.get("error", "Translation failed.")

    return True, result["translated_text"]


def check_content_safety(text: str) -> Tuple[bool, str]:
    """Check if content is safe.

    Returns (is_safe, reason).
    Policy when the AI service is unavailable: fail open (allow content)
    to avoid blocking all user content during an AI outage, but log loudly
    so it is not silent.
    """
    service = get_ai_service()
    result = service.detect_hate_speech(text)

    if not result.get("success"):
        logger.warning(
            "Content moderation unavailable — allowing content. reason=%s",
            result.get("error"),
        )
        return True, ""

    is_safe = not result["is_inappropriate"]
    reason = result.get("reason", "")
    return is_safe, reason
