"""Base LLM client interface."""

import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class BaseLLMClient(ABC):
    """Abstract base class for LLM vision clients."""

    def __init__(self, model_name: str, temperature: float = 0.0, top_p: float = 1.0, run_id: str = None):
        """Initialize LLM client.

        Args:
            model_name: Name of the model to use
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            run_id: Unique identifier for this run (for statistical independence)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.run_id = run_id or str(uuid.uuid4())
    
    @abstractmethod
    def score_visual_fidelity(
        self,
        image_paths: List[Path],
        context: Dict[str, Any],
        rubric_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Score visual fidelity given images and context.
        
        Args:
            image_paths: List of image paths (GT images first, then candidate)
            context: Context dict with item_id, categories, gt_count, etc.
            rubric_weights: Dict of dimension -> weight
        
        Returns:
            Dict with:
                - item_id: str
                - subscores: dict of dimension -> score [0.0-1.0]
                - score: float (weighted sum in range 0.0-1.0)
                - rationale: list of explanation strings
        """
        pass
    
    def _build_system_message(self) -> str:
        """Build system message for the LLM."""
        return """You are a meticulous visual rater. Score only the **appearance fidelity** of a rendered 3D object labeled "CANDIDATE" against up to five real product photos labeled "GT #k". Focus on: color palette, material finish, texture identity, and texture scale/placement.

**Ignore geometry/silhouette** and **ignore backgrounds** (backgrounds are blacked out). Compare the candidate to the **set** of GT images jointly. Use the rubric and weights. Return strict JSON only."""
    
    def _build_user_message(
        self,
        context: Dict[str, Any],
        rubric_weights: Dict[str, float],
    ) -> str:
        """Build user message with instructions."""

        gt_labels_str = ", ".join([f'"{label}"' for label in context["gt_labels"]])

        message = f"""Context:
- item_id: {context["item_id"]}
- categories: {{ "l1": "{context["l1"]}", "l2": "{context["l2"]}", "l3": "{context["l3"]}" }}
- gt_count: {context["gt_count"]}
- candidate_label: "CANDIDATE"
- gt_labels: [{gt_labels_str}]
- run_id: {self.run_id}

Rubric (weights in percent):
- color_palette: {rubric_weights["color_palette"]}
- material_finish: {rubric_weights["material_finish"]}
- texture_identity: {rubric_weights["texture_identity"]}
- texture_scale_placement: {rubric_weights["texture_scale_placement"]}

Instructions:
1) Assign each sub-score an integer in [0,100].
2) Compute the weighted sum:
   score = round({rubric_weights["color_palette"]/100}*color_palette + {rubric_weights["material_finish"]/100}*material_finish + {rubric_weights["texture_identity"]/100}*texture_identity + {rubric_weights["texture_scale_placement"]/100}*texture_scale_placement)
3) Provide 2–4 short bullets explaining the main drivers. Do not mention geometry or silhouette.
4) Confirm you compared images labeled "GT #k" (ground truth) against "CANDIDATE".
5) Output exactly the following JSON, with no extra text:

{{
  "item_id": "{context["item_id"]}",
  "subscores": {{
    "color_palette": 0,
    "material_finish": 0,
    "texture_identity": 0,
    "texture_scale_placement": 0
  }},
  "score": 0,
  "rationale": ["...", "..."]
}}"""
        
        return message
    
    @abstractmethod
    def _call_api(
        self,
        system_message: str,
        user_message: str,
        image_paths: List[Path],
    ) -> str:
        """Call the LLM API and return raw response text.
        
        Args:
            system_message: System prompt
            user_message: User prompt with instructions
            image_paths: List of image file paths
        
        Returns:
            Raw response text from the API
        """
        pass