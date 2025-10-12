"""Translation client for converting LLM outputs to Italian using Gemini."""

# Suppress gRPC warnings before any Google library imports
import os
os.environ["GRPC_VERBOSITY"] = "NONE"  # Must be NONE, not ERROR
os.environ["GRPC_TRACE"] = ""  # Disable all tracing
os.environ["GRPC_PYTHON_LOG_LEVEL"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GOOGLE_LOGGING_VERBOSITY"] = "3"

import json
import time
import random
from typing import List

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


class TranslatorClient:
    """Lightweight translation client using Google Gemini."""

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        api_key: str | None = None,
    ):
        """
        Args:
            model_name: Gemini model name (default: gemini-2.5-flash for speed)
            api_key: API key (if None, reads from GEMINI_API_KEY env var)
        """
        # Get API key
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")

        # Configure Gemini
        genai.configure(api_key=api_key)

        self.model_name = model_name

        # Initialize model with JSON output
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.3,  # Low temperature for consistent translation
                "top_p": 0.95,
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

    def translate_rationale(self, rationale_en: List[str], max_retries: int = 3) -> List[str]:
        """Translate English rationale to Italian.

        Args:
            rationale_en: List of rationale strings in English
            max_retries: Maximum number of retry attempts

        Returns:
            List of translated strings in Italian

        Raises:
            RuntimeError: If translation fails after all retries
        """
        # Build prompt
        system_message = """You are a professional translator specializing in technical content about visual design, materials, colors, and textures.

Your task is to translate English text to Italian while:
1. Maintaining technical accuracy and terminology
2. Preserving the structure and tone
3. Using natural Italian phrasing
4. Keeping proper nouns unchanged

Translate ONLY the content. Do not add explanations or comments."""

        # Format input as JSON
        input_json = json.dumps({"rationale": rationale_en}, ensure_ascii=False)

        user_message = f"""Translate the following JSON object from English to Italian.
Return a JSON object with the same structure, but with "rationale" field translated to Italian.

Input:
{input_json}

Output format:
{{"rationale_it": ["translated string 1", "translated string 2", ...]}}"""

        # Call API with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content([system_message, user_message])

                if not response.candidates or not response.candidates[0].content.parts:
                    reason = "Unknown"
                    if response.candidates:
                        reason = response.candidates[0].finish_reason.name
                    raise ValueError(f"API returned empty response. Finish Reason: {reason}")

                # Parse response
                response_text = response.text

                # Extract JSON
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1

                if json_start != -1 and json_end != -1:
                    clean_json = response_text[json_start:json_end]
                    result = json.loads(clean_json)
                else:
                    raise json.JSONDecodeError("No JSON object found", response_text, 0)

                # Validate structure
                if "rationale_it" not in result:
                    raise ValueError("Missing 'rationale_it' key in response")

                if not isinstance(result["rationale_it"], list):
                    raise ValueError("'rationale_it' must be a list")

                if len(result["rationale_it"]) != len(rationale_en):
                    raise ValueError(
                        f"Translation mismatch: expected {len(rationale_en)} items, "
                        f"got {len(result['rationale_it'])}"
                    )

                return result["rationale_it"]

            except Exception as e:
                last_error = e
                err_msg = str(e)

                # Handle rate limiting
                if "429" in err_msg or "Quota exceeded" in err_msg:
                    wait_time = 30 + random.uniform(0.5, 1.5)
                    if attempt < max_retries - 1:
                        print(f"Translation API rate limited (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        break

                # Handle other errors with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0.1, 0.3)
                    print(f"Translation failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    break

        raise RuntimeError(f"Translation failed after {max_retries} attempts: {last_error}")


if __name__ == "__main__":
    # Test translation
    client = TranslatorClient()
    test_rationale = [
        "The color palette is completely incorrect; the candidate is monochromatic.",
        "The material finishes are wrong, lacking the expected texture."
    ]
    translated = client.translate_rationale(test_rationale)
    print("Original:", test_rationale)
    print("Translated:", translated)
