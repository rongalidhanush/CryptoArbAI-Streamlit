"""Google Gemini integration wrapper."""

from __future__ import annotations

import logging

import requests

from config import get_settings


LOGGER = logging.getLogger(__name__)


class GeminiError(RuntimeError):
    """Raised when Gemini text generation fails."""


class GeminiClient:
    """Small Google Gemini REST client for text generation."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 12,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.base_url = (base_url or settings.gemini_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    @property
    def configured(self) -> bool:
        """Return whether the client has an API key."""
        return bool(self.api_key)

    def generate_text(self, prompt: str) -> str:
        """Generate natural-language text from Gemini."""
        if not self.configured:
            raise GeminiError("Gemini API key is not configured.")

        url = f"{self.base_url}/models/{self.model}:generateContent"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 500,
            },
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                headers={"x-goog-api-key": self.api_key},
                timeout=self.timeout_seconds,
            )
            if not response.ok:
                raise GeminiError(_response_error_message(response))
            data = response.json()
        except requests.RequestException:
            LOGGER.info("Gemini request failed.")
            raise GeminiError("Gemini request failed.") from None
        except ValueError:
            raise GeminiError("Gemini returned invalid JSON.") from None

        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "\n".join(part["text"] for part in parts if "text" in part).strip()
        except (KeyError, IndexError, TypeError):
            raise GeminiError("Gemini returned an unexpected response.") from None


def _response_error_message(response: requests.Response) -> str:
    """Return a sanitized Gemini HTTP error message."""
    try:
        data = response.json()
        message = data.get("error", {}).get("message", "")
    except ValueError:
        message = response.text[:160]

    if message:
        return f"Gemini request failed with HTTP {response.status_code}: {message}"
    return f"Gemini request failed with HTTP {response.status_code}."
