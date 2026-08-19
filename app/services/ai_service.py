"""
AI Service Module for DriftBridge
Handles Google Gemini API integration for translation and content moderation
"""

import os
import requests
from typing import Optional, Dict, Any


class AIService:
    """Service class for AI-powered features using Google Gemini API"""

    def __init__(self):
        """Initialize Gemini AI with API key from environment"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key or self.api_key == "your-gemini-api-key-here":
            raise ValueError(
                "GEMINI_API_KEY not configured. "
                "Please add your Google Gemini API key to .env file"
            )
        
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

    def _make_request(self, prompt: str) -> str:
        """Make API request to Gemini"""
        headers = {
            "Content-Type": "application/json",
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        # Add API key as query parameter
        url = f"{self.api_url}?key={self.api_key}"
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract text from response
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                parts = candidate["content"]["parts"]
                if len(parts) > 0 and "text" in parts[0]:
                    return parts[0]["text"]
        
        raise ValueError("Invalid response from Gemini API")

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate text to target language using Gemini AI
        
        Args:
            text: The text to translate
            target_language: Target language code (e.g., 'hi', 'es', 'fr')
            source_language: Optional source language code
            
        Returns:
            Dictionary with translated text and metadata
        """
        try:
            if source_language:
                prompt = f"""Translate the following text from {source_language} to {target_language}.
Only provide the translated text, no explanations or additional commentary.

Text: {text}"""
            else:
                prompt = f"""Translate the following text to {target_language}.
Only provide the translated text, no explanations or additional commentary.

Text: {text}"""

            translated = self._make_request(prompt)
            
            return {
                "success": True,
                "translated_text": translated.strip(),
                "original_text": text,
                "target_language": target_language,
                "source_language": source_language
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_text": text
            }

    def detect_hate_speech(self, text: str) -> Dict[str, Any]:
        """
        Detect hate speech, offensive content, or inappropriate language
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with detection results and severity
        """
        try:
            prompt = f"""Analyze the following text for hate speech, harassment, discrimination, 
offensive language, threats, or any inappropriate content.

Respond in JSON format with:
- "is_inappropriate": true/false
- "severity": "none", "low", "medium", or "high"
- "categories": list of issue types found (e.g., ["hate_speech", "harassment"])
- "reason": brief explanation if inappropriate

Text to analyze: {text}"""

            result_text = self._make_request(prompt)
            
            # Parse the response (basic parsing, can be improved)
            if "true" in result_text.lower() and "is_inappropriate" in result_text.lower():
                is_inappropriate = True
            else:
                is_inappropriate = False
            
            # Extract severity
            severity = "none"
            if "high" in result_text.lower():
                severity = "high"
            elif "medium" in result_text.lower():
                severity = "medium"
            elif "low" in result_text.lower():
                severity = "low"
            
            return {
                "success": True,
                "is_inappropriate": is_inappropriate,
                "severity": severity,
                "raw_analysis": result_text,
                "original_text": text
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "is_inappropriate": False,
                "severity": "none"
            }

    def get_language_name(self, language_code: str) -> str:
        """
        Convert language code to full language name
        
        Args:
            language_code: ISO language code (e.g., 'hi', 'es')
            
        Returns:
            Full language name
        """
        language_map = {
            'en': 'English',
            'hi': 'Hindi',
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
            'mr': 'Marathi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'pa': 'Punjabi',
            'ur': 'Urdu'
        }
        
        return language_map.get(language_code, language_code.upper())


# Global AI service instance
ai_service = None


def get_ai_service() -> AIService:
    """
    Get or create the global AI service instance
    
    Returns:
        AIService instance
    """
    global ai_service
    
    if ai_service is None:
        ai_service = AIService()
    
    return ai_service


def translate_message(
    text: str,
    target_language: str,
    source_language: Optional[str] = None
) -> str:
    """
    Convenience function to translate text
    
    Args:
        text: Text to translate
        target_language: Target language code
        source_language: Optional source language code
        
    Returns:
        Translated text or original if translation fails
    """
    try:
        service = get_ai_service()
        result = service.translate_text(text, target_language, source_language)
        
        if result["success"]:
            return result["translated_text"]
        else:
            return text
            
    except Exception:
        return text


def check_content_safety(text: str) -> tuple[bool, str]:
    """
    Check if content is safe and appropriate
    
    Args:
        text: Text to check
        
    Returns:
        Tuple of (is_safe, reason)
    """
    try:
        service = get_ai_service()
        result = service.detect_hate_speech(text)
        
        if result["success"]:
            is_safe = not result["is_inappropriate"]
            reason = result.get("raw_analysis", "Content flagged as inappropriate")
            return is_safe, reason
        else:
            # If check fails, allow content (fail open)
            return True, ""
            
    except Exception:
        # If check fails, allow content (fail open)
        return True, ""
