"""
ProofWork AI - Groq API Service
=================================
Handles all interactions with the Groq API (llama-3.3-70b-versatile).

Responsibilities:
  - Client initialization with API key validation.
  - Structured JSON chat completion with retry logic.
  - Rate limit and network error handling.
  - Response parsing and validation.
  - Token usage tracking.

Author: Swetha
Module: services/groq_service.py
"""

import json
import os
import time
from typing import Any, Dict, Optional, Tuple

from groq import Groq, APIError, APIConnectionError, RateLimitError, APIStatusError
from dotenv import load_dotenv

from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
DEFAULT_TEMPERATURE = 0.2         # Low temp for consistent, structured output
DEFAULT_MAX_TOKENS = 2048
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0          # Exponential backoff: 2s, 4s, 8s


# ---------------------------------------------------------------------------
# GroqService Class
# ---------------------------------------------------------------------------

class GroqService:
    """
    Production-grade Groq API client with retry logic and structured JSON support.

    Usage:
        service = GroqService()
        data, raw = service.chat_json(system_prompt, user_prompt)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        """
        Initializes the Groq client.

        Args:
            api_key: Groq API key. Falls back to GROQ_API_KEY env var.
            model: LLM model name.
            temperature: Sampling temperature (0.0–1.0).
            max_tokens: Maximum tokens in the response.

        Raises:
            EnvironmentError: If no API key is found.
        """
        resolved_key = api_key or os.getenv("GROQ_API_KEY", "").strip()
        if not resolved_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file or set it as an environment variable."
            )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = Groq(api_key=resolved_key)

        logger.info(f"GroqService initialized | model={self.model} | max_tokens={self.max_tokens}")

    # -----------------------------------------------------------------------
    # Public Methods
    # -----------------------------------------------------------------------

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Performs a chat completion and parses the response as JSON.

        Implements exponential backoff retry on transient errors.

        Args:
            system_prompt: System role instruction.
            user_prompt: User turn message.

        Returns:
            Tuple of (parsed_dict, raw_response_text).

        Raises:
            ValueError: If the response cannot be parsed as valid JSON after retries.
            RuntimeError: On persistent API or network failures.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_exception: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(f"Groq API call attempt {attempt}/{MAX_RETRIES}")

                start_time = time.monotonic()
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                elapsed = time.monotonic() - start_time

                raw_text = response.choices[0].message.content.strip()
                usage = response.usage

                # Guard: usage can be None on certain Groq response variants
                if usage is not None:
                    logger.info(
                        f"Groq response received | attempt={attempt} | "
                        f"elapsed={elapsed:.2f}s | "
                        f"tokens_in={usage.prompt_tokens} | "
                        f"tokens_out={usage.completion_tokens}"
                    )
                else:
                    logger.info(
                        f"Groq response received | attempt={attempt} | "
                        f"elapsed={elapsed:.2f}s | usage=unavailable"
                    )

                parsed = self._parse_json_response(raw_text)
                return parsed, raw_text

            except RateLimitError as exc:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    f"Rate limit hit (attempt {attempt}). Retrying in {wait:.0f}s... | {exc}"
                )
                last_exception = exc
                time.sleep(wait)

            except APIConnectionError as exc:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    f"Connection error (attempt {attempt}). Retrying in {wait:.0f}s... | {exc}"
                )
                last_exception = exc
                time.sleep(wait)

            except APIStatusError as exc:
                # 4xx errors (except rate limit) are not retryable
                logger.error(f"API status error {exc.status_code}: {exc.message}")
                raise RuntimeError(
                    f"Groq API error {exc.status_code}: {exc.message}"
                ) from exc

            except APIError as exc:
                logger.error(f"Unexpected Groq API error: {exc}")
                raise RuntimeError(f"Unexpected Groq API error: {exc}") from exc

        raise RuntimeError(
            f"Groq API failed after {MAX_RETRIES} attempts. "
            f"Last error: {last_exception}"
        )

    def chat_raw(self, system_prompt: str, user_prompt: str) -> str:
        """
        Performs a chat completion and returns raw text without JSON parsing.

        Unlike chat_json, this method does NOT attempt to parse the response as
        JSON, so it will not raise ValueError for non-JSON model output.

        Args:
            system_prompt: System role instruction.
            user_prompt: User turn message.

        Returns:
            Raw response text from the model.

        Raises:
            RuntimeError: On persistent API or network failures.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_exception: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(f"Groq chat_raw call attempt {attempt}/{MAX_RETRIES}")
                start_time = time.monotonic()
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                elapsed = time.monotonic() - start_time
                raw_text = response.choices[0].message.content.strip()
                logger.info(
                    f"Groq chat_raw received | attempt={attempt} | elapsed={elapsed:.2f}s"
                )
                return raw_text

            except RateLimitError as exc:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(f"Rate limit hit in chat_raw (attempt {attempt}). Retrying in {wait:.0f}s...")
                last_exception = exc
                time.sleep(wait)

            except APIConnectionError as exc:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(f"Connection error in chat_raw (attempt {attempt}). Retrying in {wait:.0f}s...")
                last_exception = exc
                time.sleep(wait)

            except APIStatusError as exc:
                logger.error(f"API status error {exc.status_code} in chat_raw: {exc.message}")
                raise RuntimeError(f"Groq API error {exc.status_code}: {exc.message}") from exc

            except APIError as exc:
                logger.error(f"Unexpected Groq API error in chat_raw: {exc}")
                raise RuntimeError(f"Unexpected Groq API error: {exc}") from exc

        raise RuntimeError(
            f"Groq chat_raw failed after {MAX_RETRIES} attempts. Last error: {last_exception}"
        )

    # -----------------------------------------------------------------------
    # Private Helpers
    # -----------------------------------------------------------------------

    def _parse_json_response(self, raw_text: str) -> Dict[str, Any]:
        """
        Extracts and parses JSON from model response.

        Handles cases where the model wraps JSON in markdown code fences.

        Args:
            raw_text: Raw string from the model.

        Returns:
            Parsed Python dict.

        Raises:
            ValueError: If JSON cannot be parsed.
        """
        # Strip markdown code fences if present
        text = raw_text
        if "```json" in text:
            text = text.split("```json", 1)[1]
            text = text.rsplit("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1]
            text = text.rsplit("```", 1)[0]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error(
                f"Failed to parse JSON from model response. "
                f"Error: {exc}. Raw text (first 500 chars): {raw_text[:500]}"
            )
            raise ValueError(
                f"Model returned invalid JSON. Details: {exc}"
            ) from exc
