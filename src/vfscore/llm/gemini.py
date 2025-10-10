"""Google Gemini LLM client."""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import google.generativeai as genai
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
                "max_output_tokens": 2048,  # Increased for detailed analysis
            }
        )
    
    def _call_api(
        self,
        system_message: str,
        user_message: str,
        image_paths: List[Path],
        max_retries: int = 3,
    ) -> str:
        """Call Gemini API with retries."""
        
        # Load images
        images = []
        for img_path in image_paths:
            img = Image.open(img_path)
            images.append(img)
        
        # Build prompt parts: system + images + user message
        prompt_parts = [
            system_message,
            "\n\n",
            user_message,
            "\n\nImages (in order):",
        ]
        
        # Add images
        for idx, img in enumerate(images):
            prompt_parts.append(img)
        
        # Retry logic
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt_parts)
                return response.text
            
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"Gemini API failed after {max_retries} attempts: {e}")
    
    def score_visual_fidelity(
        self,
        image_paths: List[Path],
        context: Dict[str, Any],
        rubric_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Score visual fidelity using Gemini 2.5 Pro."""
        
        # Build messages
        system_message = self._build_system_message()
        user_message = self._build_user_message(context, rubric_weights)
        
        # Call API
        response_text = self._call_api(system_message, user_message, image_paths)
        
        # Parse JSON response
        try:
            # Try to extract JSON from response (in case there's extra text)
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Validate structure
            required_keys = ["item_id", "subscores", "score", "rationale"]
            if not all(key in result for key in required_keys):
                raise ValueError(f"Missing required keys in response: {required_keys}")
            
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {response_text}")


if __name__ == "__main__":
    # Test client
    client = GeminiClient()
    print(f"Gemini client initialized: {client.model_name}")
