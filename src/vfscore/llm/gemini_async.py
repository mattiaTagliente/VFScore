"""Async Google Gemini LLM client with multi-key pool support."""

# Suppress gRPC warnings before any Google library imports
import os
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_TRACE"] = ""
os.environ["GRPC_PYTHON_LOG_LEVEL"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GOOGLE_LOGGING_VERBOSITY"] = "3"

import asyncio
import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
from rich.console import Console

from vfscore.llm.base import BaseLLMClient
from vfscore.llm.key_pool import GeminiKeyPool, QuotaExhaustedError

console = Console(legacy_windows=True)


class AsyncGeminiClient(BaseLLMClient):
    """Async Google Gemini vision model client with multi-key pool support."""

    # Thread pool for blocking I/O operations
    _executor = ThreadPoolExecutor(max_workers=10)

    # Regex for extracting retry delay from error messages
    _RE_RETRY_DELAY_1 = re.compile(r"retry_delay\s*\{\s*seconds:\s*(\d+)", re.IGNORECASE)
    _RE_RETRY_DELAY_2 = re.compile(r"Please retry in\s+([\d\.]+)s", re.IGNORECASE)

    def __init__(
        self,
        model_name: str = "gemini-2.5-pro",
        temperature: float = 0.0,
        top_p: float = 1.0,
        run_id: str = None,
        key_pool: Optional[GeminiKeyPool] = None,
        api_key: Optional[str] = None,
    ):
        """
        Args:
            model_name: Gemini model name
            temperature: Sampling temperature
            top_p: Top-p sampling
            run_id: Unique identifier for this run
            key_pool: GeminiKeyPool instance (multi-key mode)
            api_key: Single API key (backward compatibility mode)
        """
        super().__init__(model_name, temperature, top_p, run_id)

        self.key_pool = key_pool
        self.single_api_key = api_key

        if not key_pool and not api_key:
            # Fall back to environment variable
            self.single_api_key = os.getenv("GEMINI_API_KEY")
            if not self.single_api_key:
                raise ValueError(
                    "Either key_pool, api_key, or GEMINI_API_KEY environment variable must be provided"
                )

        # Generation config
        self.generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    @classmethod
    def _extract_retry_seconds(cls, msg: str, default: float = 30.0) -> float:
        """Extract retry delay from API error message."""
        m = cls._RE_RETRY_DELAY_1.search(msg)
        if m:
            return float(m.group(1))
        m = cls._RE_RETRY_DELAY_2.search(msg)
        if m:
            return float(m.group(1))
        return default

    def _create_model(self, api_key: str) -> genai.GenerativeModel:
        """Create Gemini model instance with specific API key."""
        genai.configure(api_key=api_key)

        return genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )

    async def _call_api_with_key(
        self,
        api_key: str,
        key_label: str,
        system_message: str,
        user_message: str,
        image_paths: List[Path],
        max_retries: int = 3,
    ) -> str:
        """Call Gemini API with specific key (async wrapper around sync API)."""

        # Load images
        loop = asyncio.get_event_loop()
        images = await loop.run_in_executor(
            self._executor,
            lambda: [Image.open(p) for p in image_paths]
        )

        prompt_parts = [system_message, user_message] + images

        last_error = None
        for attempt in range(max_retries):
            try:
                # Create model (sync operation)
                model = await loop.run_in_executor(
                    self._executor,
                    self._create_model,
                    api_key
                )

                # Call API (sync operation wrapped in async)
                response = await loop.run_in_executor(
                    self._executor,
                    model.generate_content,
                    prompt_parts
                )

                if not response.candidates or not response.candidates[0].content.parts:
                    reason = "Unknown"
                    if response.candidates:
                        reason = response.candidates[0].finish_reason.name
                    raise ValueError(f"API returned empty response. Finish Reason: {reason}")

                # Success - record in key pool
                if self.key_pool:
                    self.key_pool.record_request(key_label, token_count=5000)

                return response.text

            except Exception as e:
                err_msg = str(e)
                last_error = e

                # 429 handling
                if "429" in err_msg or "Quota exceeded" in err_msg or "Please retry in" in err_msg:
                    wait_time = self._extract_retry_seconds(err_msg, default=30.0)
                    wait_time += random.uniform(0.2, 0.6)

                    # Determine which rate limit was hit
                    limit_type = "UNKNOWN"
                    if "requests per day" in err_msg.lower() or "rpd" in err_msg.lower() or "50" in err_msg:
                        limit_type = "RPD (50 requests/day)"
                    elif "requests per minute" in err_msg.lower() or "rpm" in err_msg.lower() or "limit: 2" in err_msg:
                        limit_type = "RPM (2 requests/minute)"
                    elif "tokens per minute" in err_msg.lower() or "tpm" in err_msg.lower():
                        limit_type = "TPM (125K tokens/minute)"
                    elif "quota" in err_msg.lower():
                        limit_type = "QUOTA (likely RPM or RPD)"

                    if attempt < max_retries - 1:
                        # Use console.log() to avoid interfering with progress bar
                        console.log(
                            f"[yellow][{key_label or 'unknown'}] Google rate limit triggered ({limit_type})[/yellow]"
                        )
                        console.log(
                            f"[dim]  Note: Local quota tracking uses 75% safety margin, but Google's rate limiter may still "
                            f"trigger due to async timing, clock skew, or billing status.[/dim]"
                        )
                        console.log(f"[dim]  Retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})[/dim]")
                        console.log(f"[dim]  Error: {err_msg}[/dim]")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        break

                # Other errors: exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0.1, 0.3)
                    console.log(
                        f"[yellow][{key_label or 'unknown'}] API error: {e}, retrying in {wait_time:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries})[/yellow]"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break

        raise RuntimeError(f"API failed after {max_retries} attempts: {last_error}")

    async def _call_api(
        self,
        system_message: str,
        user_message: str,
        image_paths: List[Path],
        max_retries: int = 3,
    ) -> str:
        """Call Gemini API with intelligent key selection."""

        if self.key_pool:
            # Multi-key mode: get available key from pool
            try:
                api_key, key_label = await self.key_pool.get_available_key(estimated_tokens=5000)
                # Log which key is being used (verbose mode - can be disabled)
                # console.print(f"[dim]    Using key: {key_label}[/dim]")
                return await self._call_api_with_key(
                    api_key, key_label, system_message, user_message, image_paths, max_retries
                )
            except QuotaExhaustedError as e:
                console.print(f"[red]All API keys exhausted: {e}[/red]")
                raise
        else:
            # Single key mode (backward compatibility)
            return await self._call_api_with_key(
                self.single_api_key, "single_key", system_message, user_message, image_paths, max_retries
            )

    async def score_visual_fidelity_async(
        self,
        image_paths: List[Path],
        context: Dict[str, Any],
        rubric_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Score visual fidelity asynchronously."""

        system_message = self._build_system_message()
        user_message = self._build_user_message(context, rubric_weights)

        response_text = await self._call_api(system_message, user_message, image_paths)

        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end != -1:
                clean_json_str = response_text[json_start:json_end]
                result = json.loads(clean_json_str)
            else:
                raise json.JSONDecodeError("No JSON object found in response.", response_text, 0)

            # Validate required keys
            required_keys = ["item_id", "subscores", "score", "rationale"]
            if not all(key in result for key in required_keys):
                raise ValueError(f"Missing required keys in response: {required_keys}")

            # Convert scores from 0-100 to 0.0-1.0 range
            result["score"] = result["score"] / 100.0
            for key in result["subscores"]:
                result["subscores"][key] = result["subscores"][key] / 100.0

            # Add metadata
            result["metadata"] = {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "run_id": self.run_id,
                "timestamp": datetime.now().isoformat(),
                "model_name": self.model_name
            }

            return result

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to decode or validate JSON from response. Error: {e}\n\n"
                f"Full Response:\n{response_text}"
            )

    def score_visual_fidelity(
        self,
        image_paths: List[Path],
        context: Dict[str, Any],
        rubric_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Synchronous wrapper for backward compatibility."""
        # Run async method in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context - this shouldn't happen in normal usage
                raise RuntimeError("Cannot call synchronous wrapper from async context")
            return loop.run_until_complete(
                self.score_visual_fidelity_async(image_paths, context, rubric_weights)
            )
        except RuntimeError:
            # No event loop - create one
            return asyncio.run(
                self.score_visual_fidelity_async(image_paths, context, rubric_weights)
            )
