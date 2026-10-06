"""
AI Service Module for DriftBridge

Provides local language detection and sentence-level translation
using langdetect and Argos Translate.
"""

import logging
import threading
import time
import re
import ctranslate2
from typing import Optional, Dict, Any, Tuple

from langdetect import detect, DetectorFactory


# Make language detection deterministic.
DetectorFactory.seed = 0


logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Supported languages
# ----------------------------------------------------------------------

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu",
    "tr": "Turkish",
}


def get_language_name(language_code: str) -> str:
    """Convert an ISO language code to a full language name."""

    return SUPPORTED_LANGUAGES.get(
        language_code,
        language_code.upper()
    )


# ----------------------------------------------------------------------
# AI Service
# ----------------------------------------------------------------------

class AIService:
    """Service class for local language detection and translation."""

    def __init__(self):

        self.available = True

        # --------------------------------------------------------------
        # Translation result cache
        # --------------------------------------------------------------

        self.translation_cache: Dict[
            Tuple[str, str, str],
            Dict[str, Any]
        ] = {}

        self.translation_cache_lock = threading.Lock()

        # --------------------------------------------------------------
        # Argos translation object cache
        #
        # Key:
        #     (source_language, target_language)
        #
        # Example:
        #     ("en", "hi")
        # --------------------------------------------------------------

        self.translation_pairs: Dict[
            Tuple[str, str],
            Any
        ] = {}

        # --------------------------------------------------------------
        # Argos / Stanza lock
        #
        # Argos/Stanza can perform lazy initialization during the first
        # actual translation. This lock prevents multiple requests from
        # initializing the same local resources simultaneously.
        # --------------------------------------------------------------

        self.translation_lock = threading.Lock()

        # --------------------------------------------------------------
        # Argos initialization
        # --------------------------------------------------------------

        self.argos_available = False

        self._initialize_argos()
        self._warm_up_argos()

    # ------------------------------------------------------------------
    # Argos initialization
    # ------------------------------------------------------------------

    def _initialize_argos(self):
        """
        Load Argos Translate when the AI service is initialized.

        This only loads the Argos module and checks installed languages.
        It intentionally does NOT perform a translation during startup.

        This keeps Flask startup fast and avoids a hard-coded language
        pair being initialized before the application is actually used.
        """

        start_time = time.perf_counter()

        try:

            import argostranslate.translate as argos_translate

            self.argos_translate = argos_translate

            installed_languages = (
                argos_translate.get_installed_languages()
            )

            elapsed = (
                time.perf_counter() - start_time
            )

            self.argos_available = True

            logger.info(
                "[ARGOS INIT] Argos initialized in %.3f seconds.",
                elapsed
            )

            logger.info(
                "[ARGOS INIT] Installed languages: %s",
                ", ".join(
                    language.code
                    for language in installed_languages
                )
            )

        except Exception as exc:

            elapsed = (
                time.perf_counter() - start_time
            )

            self.argos_available = False

            logger.exception(
                "[ARGOS INIT] Failed after %.3f seconds: %s",
                elapsed,
                exc
            )

               

    # ------------------------------------------------------------------
    # Argos runtime warm-up
    # ------------------------------------------------------------------

    def _warm_up_argos(self):
        """
        Perform one small internal translation so the common
        Argos/Stanza runtime is initialized before real user requests.
        """

        if not self.argos_available:
            return

        warmup_start = time.perf_counter()

        try:

            warmup_translation = (
                self.argos_translate
                .get_translation_from_codes(
                    "en",
                    "fr"
                )
            )

            if warmup_translation is None:
                logger.warning(
                    "[ARGOS WARMUP] English -> French pair "
                    "is unavailable."
                )
                return

            warmup_translation.translate("hello")

            warmup_time = (
                time.perf_counter()
                - warmup_start
            )

            logger.info(
                "[ARGOS WARMUP] Completed in %.3f seconds.",
                warmup_time
            )

        except Exception as exc:

            warmup_time = (
                time.perf_counter()
                - warmup_start
            )

            logger.exception(
                "[ARGOS WARMUP] Failed after %.3f seconds: %s",
                warmup_time,
                exc
            )
    # ------------------------------------------------------------------
    # Translation pair loading
    # ------------------------------------------------------------------

    def _get_translation_pair(
        self,
        source_language: str,
        target_language: str
    ):
        """
        Get and cache an Argos translation object.

        The translation pair is loaded only once per language pair.

        Argos 1.11.0 wraps PackageTranslation inside
        CachedTranslation. The actual CTranslate2 model is created
        lazily by PackageTranslation on the first translation.

        We initialize that CTranslate2 model here so the first real
        user translation does not have to pay the model-construction
        cost.
        """

        pair_key = (
            source_language,
            target_language
        )

        # --------------------------------------------------------------
        # Use cached translation pair if available.
        # --------------------------------------------------------------

        cached_pair = self.translation_pairs.get(
            pair_key
        )

        if cached_pair is not None:

            logger.info(
                "[ARGOS PAIR] Using cached pair: %s -> %s",
                source_language,
                target_language
            )

            return cached_pair

        # --------------------------------------------------------------
        # Load translation pair from Argos.
        # --------------------------------------------------------------

        pair_start = time.perf_counter()

        try:

            translation = (
                self.argos_translate
                .get_translation_from_codes(
                    source_language,
                    target_language
                )
            )

        except Exception as exc:

            logger.exception(
                "[ARGOS PAIR] Failed to load pair "
                "%s -> %s: %s",
                source_language,
                target_language,
                exc
            )

            return None

        pair_time = (
            time.perf_counter() - pair_start
        )

        # --------------------------------------------------------------
        # Pair does not exist.
        # --------------------------------------------------------------

        if translation is None:

            logger.warning(
                "[ARGOS PAIR] Pair unavailable: %s -> %s "
                "(lookup %.3f seconds)",
                source_language,
                target_language,
                pair_time
            )

            return None

        # --------------------------------------------------------------
        # Initialize the underlying CTranslate2 model.
        #
        # Argos 1.11.0 returns CachedTranslation.
        # Its underlying object is PackageTranslation.
        # PackageTranslation normally creates its translator lazily
        # during the first actual translation.
        # --------------------------------------------------------------

        model_start = time.perf_counter()

        try:

            underlying_translation = getattr(
                translation,
                "underlying",
                None
            )

            if (
                underlying_translation is not None
                and hasattr(
                    underlying_translation,
                    "translator"
                )
                and underlying_translation.translator is None
            ):

                model_path = str(
                    underlying_translation.pkg.package_path
                    / "model"
                )

                underlying_translation.translator = (
                    ctranslate2.Translator(
                        model_path,
                        device="cpu",
                        inter_threads=1,
                        intra_threads=0,
                        compute_type="auto",
                    )
                )

                model_time = (
                    time.perf_counter()
                    - model_start
                )

                logger.info(
                    "[ARGOS MODEL] Initialized CTranslate2 model "
                    "%s -> %s in %.3f seconds.",
                    source_language,
                    target_language,
                    model_time
                )

            else:

                model_time = (
                    time.perf_counter()
                    - model_start
                )

                logger.info(
                    "[ARGOS MODEL] Model already initialized or "
                    "underlying model unavailable for %s -> %s "
                    "(%.3f seconds).",
                    source_language,
                    target_language,
                    model_time
                )

        except Exception as exc:

            model_time = (
                time.perf_counter()
                - model_start
            )

            logger.exception(
                "[ARGOS MODEL] Failed to initialize CTranslate2 "
                "model for %s -> %s after %.3f seconds: %s",
                source_language,
                target_language,
                model_time,
                exc
            )

            # Do not destroy the translation object.
            # Argos can still attempt its normal lazy initialization
            # during the actual translation request.

        # --------------------------------------------------------------
        # Cache the translation object.
        # --------------------------------------------------------------

        self.translation_pairs[pair_key] = translation

        logger.info(
            "[ARGOS PAIR] Loaded pair %s -> %s "
            "in %.3f seconds.",
            source_language,
            target_language,
            pair_time
        )

        return translation

    def detect_message_language(
        self,
        text: str,
        preferred_language: Optional[str] = None
    ) -> str:
        """
        Detect the language of a chat message locally.

        Short messages are difficult for langdetect, so common
        English chat phrases are handled explicitly before using
        automatic detection.

        If the message is genuinely too short or ambiguous and
        cannot be identified reliably, the user's preferred language
        is used as the fallback.
        """

        fallback_language = (
            preferred_language
            if preferred_language in SUPPORTED_LANGUAGES
            else "en"
        )

        if not text or not text.strip():
            return fallback_language

        clean_text = text.strip()
        normalized_text = clean_text.lower()

        common_english_phrases = {
            "hi",
            "hii",
            "hiii",
            "hey",
            "heyy",
            "heyyy",
            "hello",
            "helloo",
            "ok",
            "okay",
            "yes",
            "no",
            "yeah",
            "yep",
            "nope",
            "thanks",
            "thank you",
            "thank u",
            "please",
            "sorry",
            "welcome",
            "good",
            "great",
            "fine",
            "cool",
            "nice",
            "test",
            "test one",
            "how are you",
            "how are u",
            "i am good",
            "i'm good",
            "i am fine",
            "i'm fine",
            "what's up",
            "whats up",
            "see you",
            "good morning",
            "good night",
            "good evening",
        }

        if normalized_text in common_english_phrases:
            return "en"

        english_prefixes = (
            "hi ",
            "hii ",
            "hiii ",
            "hey ",
            "heyy ",
            "heyyy ",
            "hello ",
            "helloo ",
        )

        if normalized_text.startswith(english_prefixes):
            return "en"

        if len(clean_text) >= 15:
            try:
                detected_language = detect(clean_text)

                if detected_language == "zh-cn":
                    detected_language = "zh"

                if detected_language in SUPPORTED_LANGUAGES:
                    return detected_language

                logger.warning(
                    "Detected unsupported language '%s'. "
                    "Falling back to '%s'.",
                    detected_language,
                    fallback_language
                )

            except Exception as exc:
                logger.warning(
                    "Local language detection failed: %s. "
                    "Falling back to '%s'.",
                    exc,
                    fallback_language
                )

        return fallback_language
    # ------------------------------------------------------------------
    # Translation
    # ------------------------------------------------------------------

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate the complete sentence at once.
        """

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
                exc
            )

            return {
                "success": False,
                "error": "Local translation failed.",
            }

    # ------------------------------------------------------------------
    # Sentence-level translation
    # ------------------------------------------------------------------

    def translate_text_with_word_mapping(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate the complete text in one operation.

        The historical function name is retained for compatibility.

        No individual word translations are performed.
        """

        total_start = time.perf_counter()

        # --------------------------------------------------------------
        # Basic validation
        # --------------------------------------------------------------

        if not text or not text.strip():

            return {
                "success": False,
                "error": "Cannot translate empty text."
            }

        if not target_language:

            return {
                "success": False,
                "error": "Target language is required."
            }

        try:

            # ----------------------------------------------------------
            # Check Argos availability
            # ----------------------------------------------------------

            if not self.argos_available:

                return {
                    "success": False,
                    "error": "Argos Translate is unavailable."
                }

            # ----------------------------------------------------------
            # Normalize language codes
            # ----------------------------------------------------------

            source_code = (
                source_language.lower().strip()
                if source_language
                else "en"
            )

            target_code = (
                target_language.lower().strip()
            )

            clean_text = text.strip()

            # Normalize spaces before punctuation so Argos tokenizes
            # conversational sentences correctly.
            clean_text = re.sub(
               r"\s+([?.!,;:])",
               r"\1",
               clean_text
            )

            # ----------------------------------------------------------
            # Validate language codes
            # ----------------------------------------------------------

            if source_code not in SUPPORTED_LANGUAGES:

                return {
                    "success": False,
                    "error": (
                        f"Unsupported source language: "
                        f"{source_code}"
                    )
                }

            if target_code not in SUPPORTED_LANGUAGES:

                return {
                    "success": False,
                    "error": (
                        f"Unsupported target language: "
                        f"{target_code}"
                    )
                }

            # ----------------------------------------------------------
            # Cache key
            # ----------------------------------------------------------

            cache_key = (
                clean_text,
                source_code,
                target_code
            )

            # ----------------------------------------------------------
            # Check translation-result cache
            # ----------------------------------------------------------

            with self.translation_cache_lock:

                cached_result = (
                    self.translation_cache.get(
                        cache_key
                    )
                )

            if cached_result is not None:

                total_time = (
                    time.perf_counter()
                    - total_start
                )

                logger.info(
                    "[TRANSLATION] Cached result in %.3f seconds: "
                    "%s -> %s",
                    total_time,
                    source_code,
                    target_code
                )

                return cached_result.copy()

            # ----------------------------------------------------------
            # Protect Argos / Stanza
            #
            # IMPORTANT:
            #
            # The FIRST actual translation for a new Argos pair can
            # trigger Stanza lazy initialization.
            #
            # We intentionally perform the actual translation only once.
            # We do NOT perform a fake "Hello." translation first because
            # that would make the user's request wait for two translations.
            # ----------------------------------------------------------

            with self.translation_lock:

                # ------------------------------------------------------
                # Check result cache again after waiting for the lock.
                #
                # Another request may have completed this exact
                # translation while we were waiting.
                # ------------------------------------------------------

                with self.translation_cache_lock:

                    cached_result = (
                        self.translation_cache.get(
                            cache_key
                        )
                    )

                if cached_result is not None:

                    total_time = (
                        time.perf_counter()
                        - total_start
                    )

                    logger.info(
                        "[TRANSLATION] Cached result after lock "
                        "in %.3f seconds.",
                        total_time
                    )

                    return cached_result.copy()

                # ------------------------------------------------------
                # Same language
                # ------------------------------------------------------

                if source_code == target_code:

                    result = {
                        "success": True,
                        "translated_text": clean_text,
                        "words": []
                    }

                    with self.translation_cache_lock:

                        self.translation_cache[
                            cache_key
                        ] = result.copy()

                    total_time = (
                        time.perf_counter()
                        - total_start
                    )

                    logger.info(
                        "[TRANSLATION] Same language: "
                        "%.3f seconds.",
                        total_time
                    )

                    return result

                # ======================================================
                # DIRECT TRANSLATION
                # ======================================================

                pair_start = time.perf_counter()

                direct_translation = (
                    self._get_translation_pair(
                        source_code,
                        target_code
                    )
                )

                pair_time = (
                    time.perf_counter()
                    - pair_start
                )

                logger.info(
                    "[TRANSLATION] Direct pair lookup "
                    "%s -> %s: %.3f seconds.",
                    source_code,
                    target_code,
                    pair_time
                )

                if direct_translation is not None:

                    logger.info(
                        "[TRANSLATION] Direct route: "
                        "%s -> %s",
                        source_code,
                        target_code
                    )

                    translation_start = (
                        time.perf_counter()
                    )

                    try:
                        logger.warning(
                          "[TRANSLATION DEBUG] Sending to Argos: "
                          "text=%r | source=%s | target=%s",
                          clean_text,
                          source_code,
                          target_code,
                        )



                        translated_text = (
                            direct_translation.translate(
                                clean_text
                            )
                        )

                    except Exception as exc:

                        translation_time = (
                            time.perf_counter()
                            - translation_start
                        )

                        logger.exception(
                            "[TRANSLATION] Direct translation "
                            "failed after %.3f seconds: "
                            "%s -> %s: %s",
                            translation_time,
                            source_code,
                            target_code,
                            exc
                        )

                        return {
                            "success": False,
                            "error": (
                                f"Local translation failed for "
                                f"{source_code} -> {target_code}."
                            )
                        }

                    translation_time = (
                        time.perf_counter()
                        - translation_start
                    )

                    logger.info(
                        "[TRANSLATION] Actual translation "
                        "%s -> %s: %.3f seconds.",
                        source_code,
                        target_code,
                        translation_time
                    )

                # ======================================================
                # ENGLISH BRIDGE
                # ======================================================

                else:

                    # --------------------------------------------------
                    # If English itself is one side of the translation,
                    # there is no bridge route to use.
                    # --------------------------------------------------

                    if (
                        source_code == "en"
                        or target_code == "en"
                    ):

                        total_time = (
                            time.perf_counter()
                            - total_start
                        )

                        logger.warning(
                            "[TRANSLATION] No direct route: "
                            "%s -> %s. "
                            "Completed in %.3f seconds.",
                            source_code,
                            target_code,
                            total_time
                        )

                        return {
                            "success": False,
                            "error": (
                                f"No local translation route "
                                f"available for "
                                f"{source_code} -> {target_code}."
                            )
                        }

                    logger.info(
                        "[TRANSLATION] Using English bridge: "
                        "%s -> en -> %s",
                        source_code,
                        target_code
                    )

                    # --------------------------------------------------
                    # Load both bridge pairs while the same lock is held.
                    # --------------------------------------------------

                    bridge_start = (
                        time.perf_counter()
                    )

                    source_to_english = (
                        self._get_translation_pair(
                            source_code,
                            "en"
                        )
                    )

                    english_to_target = (
                        self._get_translation_pair(
                            "en",
                            target_code
                        )
                    )

                    bridge_lookup_time = (
                        time.perf_counter()
                        - bridge_start
                    )

                    logger.info(
                        "[TRANSLATION] English bridge "
                        "pair loading: %.3f seconds.",
                        bridge_lookup_time
                    )

                    if (
                        source_to_english is None
                        or english_to_target is None
                    ):

                        return {
                            "success": False,
                            "error": (
                                f"No local translation route "
                                f"available for "
                                f"{source_code} -> {target_code}."
                            )
                        }

                    # --------------------------------------------------
                    # First translation:
                    #
                    # source -> English
                    # --------------------------------------------------

                    first_start = (
                        time.perf_counter()
                    )

                    try:

                        english_text = (
                            source_to_english.translate(
                                clean_text
                            )
                        )

                    except Exception as exc:

                        first_time = (
                            time.perf_counter()
                            - first_start
                        )

                        logger.exception(
                            "[TRANSLATION] %s -> en failed "
                            "after %.3f seconds: %s",
                            source_code,
                            first_time,
                            exc
                        )

                        return {
                            "success": False,
                            "error": (
                                f"Intermediate translation failed "
                                f"for {source_code} -> en."
                            )
                        }

                    first_time = (
                        time.perf_counter()
                        - first_start
                    )

                    logger.info(
                        "[TRANSLATION] %s -> en: "
                        "%.3f seconds.",
                        source_code,
                        first_time
                    )

                    if (
                        not english_text
                        or not english_text.strip()
                    ):

                        return {
                            "success": False,
                            "error": (
                                f"Intermediate translation failed "
                                f"for {source_code} -> en."
                            )
                        }

                    # --------------------------------------------------
                    # Second translation:
                    #
                    # English -> target
                    # --------------------------------------------------

                    second_start = (
                        time.perf_counter()
                    )

                    try:

                        translated_text = (
                            english_to_target.translate(
                                english_text
                            )
                        )

                    except Exception as exc:

                        second_time = (
                            time.perf_counter()
                            - second_start
                        )

                        logger.exception(
                            "[TRANSLATION] en -> %s failed "
                            "after %.3f seconds: %s",
                            target_code,
                            second_time,
                            exc
                        )

                        return {
                            "success": False,
                            "error": (
                                f"Translation failed for "
                                f"en -> {target_code}."
                            )
                        }

                    second_time = (
                        time.perf_counter()
                        - second_start
                    )

                    logger.info(
                        "[TRANSLATION] en -> %s: "
                        "%.3f seconds.",
                        target_code,
                        second_time
                    )

                # ------------------------------------------------------
                # Validate translation result
                # ------------------------------------------------------

                if (
                    not translated_text
                    or not translated_text.strip()
                ):

                    return {
                        "success": False,
                        "error": (
                            "Argos Translate returned empty content."
                        )
                    }

                translated_text = (
                    translated_text.strip()
                )

                # ------------------------------------------------------
                # Build final result
                # ------------------------------------------------------

                translation_result = {
                    "success": True,
                    "translated_text": translated_text,
                    "words": []
                }

                # ------------------------------------------------------
                # Store result in cache
                # ------------------------------------------------------

                with self.translation_cache_lock:

                    self.translation_cache[
                        cache_key
                    ] = translation_result.copy()

                total_time = (
                    time.perf_counter()
                    - total_start
                )

                logger.info(
                    "[TRANSLATION] COMPLETE: "
                    "%s -> %s in %.3f seconds.",
                    source_code,
                    target_code,
                    total_time
                )

                return translation_result

        except Exception as exc:

            total_time = (
                time.perf_counter()
                - total_start
            )

            logger.exception(
                "[TRANSLATION] Failed after %.3f seconds: "
                "%s -> %s: %s",
                total_time,
                source_language or "auto",
                target_language,
                exc
            )

            return {
                "success": False,
                "error": (
                    "Local translation is unavailable for "
                    f"{source_language or 'auto'} -> "
                    f"{target_language}."
                )
            }


# ----------------------------------------------------------------------
# Module-level service instance
# ----------------------------------------------------------------------

_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """
    Return the shared AIService instance.

    The service is initialized only once per Flask process.
    """

    global _ai_service

    if _ai_service is None:

        _ai_service = AIService()

    return _ai_service


# ----------------------------------------------------------------------
# Language detection convenience function
# ----------------------------------------------------------------------

def detect_message_language(
    text: str,
    preferred_language: Optional[str] = None
) -> str:

    service = get_ai_service()

    return service.detect_message_language(
        text,
        preferred_language
    )


# ----------------------------------------------------------------------
# Translation convenience function
# ----------------------------------------------------------------------

def translate_message(
    text: str,
    target_language: str,
    source_language: Optional[str] = None,
    message_id: Optional[int] = None,
) -> Tuple[bool, str]:
    """
    Translate a message and return:

        (True, translated_text)

    or:

        (False, error_message)
    """

    service = get_ai_service()

    result = service.translate_text(
        text,
        target_language,
        source_language
    )

    if not result.get("success"):

        logger.warning(
            "Translation failed - message_id=%s "
            "source=%s target=%s error=%s",
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


# ----------------------------------------------------------------------
# Compatibility translation function
# ----------------------------------------------------------------------

def translate_message_with_word_mapping(
    text: str,
    target_language: str,
    source_language: Optional[str] = None,
    message_id: Optional[int] = None,
) -> Tuple[bool, Any]:
    """
    Compatibility wrapper.

    The function name remains unchanged because existing
    Socket.IO code uses it.

    Translation is sentence-level only.
    """

    service = get_ai_service()

    result = service.translate_text_with_word_mapping(
        text,
        target_language,
        source_language
    )

    if not result.get("success"):

        logger.warning(
            "Sentence translation failed - "
            "message_id=%s source=%s target=%s error=%s",
            message_id,
            source_language,
            target_language,
            result.get("error")
        )

        return False, result.get(
            "error",
            "Translation failed."
        )

    return True, result


# ----------------------------------------------------------------------
# Content safety / toxicity detection
# ----------------------------------------------------------------------

_toxicity_classifier = None
_toxicity_lock = threading.Lock()

TOXICITY_MODEL_NAME = (
    "textdetox/bert-multilingual-toxicity-classifier"
)

# Messages at or above this probability are treated as toxic.
TOXICITY_THRESHOLD = 0.80


def _get_toxicity_classifier():
    """
    Load the local multilingual toxicity classifier once.

    The model is loaded lazily so importing this module does not
    immediately allocate the large Transformer model in memory.
    """

    global _toxicity_classifier

    if _toxicity_classifier is not None:
        return _toxicity_classifier

    with _toxicity_lock:

        # Another thread may have loaded the model while this
        # thread was waiting for the lock.
        if _toxicity_classifier is not None:
            return _toxicity_classifier

        try:

            from transformers import pipeline

            logger.info(
                "[TOXICITY AI] Loading local model: %s",
                TOXICITY_MODEL_NAME
            )

            _toxicity_classifier = pipeline(
                "text-classification",
                model=TOXICITY_MODEL_NAME,
                device=-1,
            )

            logger.info(
                "[TOXICITY AI] Local toxicity model loaded successfully."
            )

            return _toxicity_classifier

        except Exception as exc:

            logger.exception(
                "[TOXICITY AI] Failed to load local toxicity model: %s",
                exc
            )

            return None


def check_content_safety(
    text: str
) -> Tuple[bool, str]:
    """
    Check message content using the local multilingual toxicity model.

    Returns:

        (True, "")
            Content is considered safe.

        (False, reason)
            Content is considered toxic.

    The model uses:
        LABEL_0 = neutral
        LABEL_1 = toxic

    No external API or Gemini request is made.
    """

    if not text or not text.strip():
        return True, ""

    clean_text = text.strip()

    classifier = _get_toxicity_classifier()

    # Fail open if the local model cannot be loaded.
    #
    # This prevents an AI-model failure from taking the entire
    # chat system offline.
    if classifier is None:
        logger.warning(
            "[TOXICITY AI] Classifier unavailable. "
            "Allowing message."
        )

        return True, ""

    try:

        result = classifier(
            clean_text,
            truncation=True
        )

        if not result:
            return True, ""

        prediction = result[0]

        label = prediction.get("label", "")
        score = float(
            prediction.get("score", 0.0)
        )

        logger.info(
            "[TOXICITY AI] label=%s score=%.4f text=%r",
            label,
            score,
            clean_text[:100]
        )

        # LABEL_1 represents the toxic class for this model.
        if (
            label == "LABEL_1"
            and score >= TOXICITY_THRESHOLD
        ):

            reason = (
                "AI toxicity detection: "
                f"toxic content detected "
                f"(confidence={score:.2f})"
            )

            return False, reason

        return True, ""

    except Exception as exc:

        logger.exception(
            "[TOXICITY AI] Content analysis failed: %s",
            exc
        )

        # Keep the chat available if the local classifier
        # encounters an unexpected runtime error.
        return True, ""