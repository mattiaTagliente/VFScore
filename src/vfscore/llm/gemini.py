"""Google Gemini LLM client."""

# IMPORTANT: Set gRPC logging environment variables BEFORE importing google libraries
import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image

from vfscore.llm.base import BaseLLMClient


class GeminiClient(BaseLLMClient):
    """Google Gemini vision model client."""
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-pro",
        temperature: float = 0.0,
        top_p: float = 1.0,
        api_key: str | None = None,
    ):
        """Initialize Gemini client.
        
        Args:
            model_name: Gemini model name (default: gemini-2.5-pro for complex reasoning)
            temperature: Sampling temperature
            top_p: Top-p sampling
            api_key: API key (if None, reads from GEMINI_API_KEY env var)
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
                "max_output_tokens": 8192,  # Increased to prevent truncated JSON
                "response_mime_type": "application/json",
            },
            # Relax safety settings to avoid false positives
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )
    
    def _call_api(
        self,
        system_message: str,
        user_message: str,
        image_paths: List[Path],
        max_retries: int = 3,
    ) -> str:
        """Call Gemini API with retries and robust error handling."""
        
        images = [Image.open(p) for p in image_paths]
        prompt_parts = [system_message, user_message] + images
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt_parts)
                
                # Handle cases where the model returns no content (e.g., safety block)
                if not response.candidates or not response.candidates[0].content.parts:
                    reason = "Unknown"
                    if response.candidates:
                        reason = response.candidates[0].finish_reason.name
                    raise ValueError(f"API returned an empty response. Finish Reason: {reason}")
                
                return response.text
            
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"Gemini API failed after {max_retries} attempts: {e}")
    
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
            # Robustly find and parse the JSON block
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                clean_json_str = response_text[json_start:json_end]
                result = json.loads(clean_json_str)
            else:
                raise json.JSONDecodeError("No JSON object found in response.", response_text, 0)

            # Validate structure
            required_keys = ["item_id", "subscores", "score", "rationale"]
            if not all(key in result for key in required_keys):
                raise ValueError(f"Missing required keys in response: {required_keys}")
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            # Raise with a more informative message for debugging
            raise ValueError(f"Failed to decode or validate JSON from response. Error: {e}\n\nFull Response:\n{response_text}")


if __name__ == "__main__":
    # Test client
    client = GeminiClient()
    print(f"Gemini client initialized: {client.model_name}")