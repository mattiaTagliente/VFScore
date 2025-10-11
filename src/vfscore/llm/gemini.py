"""Google Gemini LLM client."""

# IMPORTANT: Set gRPC logging environment variables BEFORE importing google libraries
import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import json
import time
import re
import random
import threading
from pathlib import Path
from typing import Any, Dict, List

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image

from vfscore.llm.base import BaseLLMClient


class GeminiClient(BaseLLMClient):
    """Google Gemini vision model client."""

    # ---- NEW: rate limiter (per-process, per-model) ----
    _rate_lock = threading.Lock()
    _last_call_ts: Dict[str, float] = {}

    def __init__(
        self,
        model_name: str = "gemini-2.5-pro",
        temperature: float = 0.0,
        top_p: float = 1.0,
        api_key: str | None = None,
        min_interval_sec: float | None = None,  # NEW: throttle override
    ):
        """
        Args:
            model_name: Gemini model name (default: gemini-2.5-pro for complex reasoning)
            temperature: Sampling temperature
            top_p: Top-p sampling
            api_key: API key (if None, reads from GEMINI_API_KEY env var)
            min_interval_sec: minimo intervallo tra chiamate consecutive (default 31s per free tier)
        """
        super().__init__(model_name, temperature, top_p)

        # Get API key
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")

        # Configure Gemini
        genai.configure(api_key=api_key)

        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": temperature,
                "top_p": top_p,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )

        # ---- NEW: throttle setup ----
        # Free tier: 2 req/min → ~30s. Mettiamo 31s per sicurezza.
        env_min = os.getenv("GEMINI_MIN_INTERVAL_SEC")
        self.min_interval_sec = (
            float(env_min) if env_min else (min_interval_sec if min_interval_sec is not None else 31.0)
        )

    # ---- NEW: helper per attesa proattiva ----
    def _respect_min_interval(self) -> None:
        with self._rate_lock:
            last = self._last_call_ts.get(self.model_name, 0.0)
            now = time.monotonic()
            elapsed = now - last
            remaining = self.min_interval_sec - elapsed
            if remaining > 0:
                # piccolo jitter per evitare stampede
                time.sleep(remaining + random.uniform(0.05, 0.25))
            # prenota lo slot: se fallisce ci penserà il backoff
            self._last_call_ts[self.model_name] = time.monotonic()

    # ---- NEW: estrazione retry_delay dai messaggi 429 ----
    _RE_RETRY_DELAY_1 = re.compile(r"retry_delay\s*\{\s*seconds:\s*(\d+)", re.IGNORECASE)
    _RE_RETRY_DELAY_2 = re.compile(r"Please retry in\s+([\d\.]+)s", re.IGNORECASE)

    @classmethod
    def _extract_retry_seconds(cls, msg: str, default: float = 30.0) -> float:
        m = cls._RE_RETRY_DELAY_1.search(msg)
        if m:
            return float(m.group(1))
        m = cls._RE_RETRY_DELAY_2.search(msg)
        if m:
            return float(m.group(1))
        return default

    def _call_api(
        self,
        system_message: str,
        user_message: str,
        image_paths: List[Path],
        max_retries: int = 3,
    ) -> str:
        """Call Gemini API with retries, throttle, and robust error handling."""

        images = [Image.open(p) for p in image_paths]
        prompt_parts = [system_message, user_message] + images

        # ---- NEW: throttle proattivo per evitare 429 ----
        self._respect_min_interval()

        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt_parts)

                if not response.candidates or not response.candidates[0].content.parts:
                    reason = "Unknown"
                    if response.candidates:
                        reason = response.candidates[0].finish_reason.name
                    raise ValueError(f"API returned an empty response. Finish Reason: {reason}")

                return response.text

            except Exception as e:
                err_msg = str(e)
                last_error = e

                # 429 handling con retry_delay
                if "429" in err_msg or "Quota exceeded" in err_msg or "Please retry in" in err_msg:
                    wait_time = self._extract_retry_seconds(err_msg, default=max(self.min_interval_sec, 30.0))
                    # jitter piccolo per evitare collisioni
                    wait_time += random.uniform(0.2, 0.6)
                    if attempt < max_retries - 1:
                        print(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        # dopo il sleep, aggiorno il timestamp per evitare che un altro thread spari subito
                        with self._rate_lock:
                            self._last_call_ts[self.model_name] = time.monotonic()
                        continue
                    else:
                        break

                # altri errori: exponential backoff classico
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0.1, 0.3)
                    print(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    break

        raise RuntimeError(f"Gemini API failed after {max_retries} attempts: {last_error}")

    def score_visual_fidelity(
        self,
        image_paths: List[Path],
        context: Dict[str, Any],
        rubric_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Score visual fidelity with robust JSON parsing."""

        system_message = self._build_system_message()
        user_message = self._build_user_message(context, rubric_weights)

        response_text = self._call_api(system_message, user_message, image_paths)

        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end != -1:
                clean_json_str = response_text[json_start:json_end]
                result = json.loads(clean_json_str)
            else:
                raise json.JSONDecodeError("No JSON object found in response.", response_text, 0)

            required_keys = ["item_id", "subscores", "score", "rationale"]
            if not all(key in result for key in required_keys):
                raise ValueError(f"Missing required keys in response: {required_keys}")

            return result

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to decode or validate JSON from response. Error: {e}\n\nFull Response:\n{response_text}")


if __name__ == "__main__":
    client = GeminiClient()
    print(f"Gemini client initialized: {client.model_name}")
