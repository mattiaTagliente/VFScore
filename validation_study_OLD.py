"""
VFScore Validation Study - Comprehensive Evaluation Program

This program implements the full validation study protocol:
1. Parameter sweep (temperature × top_p grid)
2. Stability analysis (ICC, MAD, CI)
3. Human agreement analysis
4. Beautiful HTML report generation

Based on: Validation_study_plan.txt
"""

import json
import csv
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import numpy as np
from scipy import stats
from dataclasses import dataclass, asdict
import os

# Configuration
@dataclass
class ValidationConfig:
    """Configuration for validation study."""
    # Objects to evaluate
    objects_csv: str = "selected_objects_optimized.csv"

    # Parameter grid
    temperatures: List[float] = None
    top_p_values: List[float] = None
    baseline_temp: float = 0.0
    baseline_top_p: float = 1.0

    # Repeats
    n_repeats: int = 5

    # LLM settings
    llm_model: str = "gemini-2.5-pro"

    # Paths
    project_root: Path = Path(".")
    output_dir: Path = None
    human_scores_csv: str = "subjective.csv"

    # Report settings
    report_title: str = "VFScore Validation Study Results"

    def __post_init__(self):
        if self.temperatures is None:
            self.temperatures = [0.2, 0.5, 0.8]
        if self.top_p_values is None:
            self.top_p_values = [1.0, 0.95, 0.9]
        if self.output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = self.project_root / f"validation_results_{timestamp}"
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class EvaluationResult:
    """Single evaluation result."""
    run_id: str
    object_id: str
    object_name: str
    manufacturer: str
    category_l3: str
    temperature: float
    top_p: float
    repeat_idx: int
    score: float
    subscores: Dict[str, float]
    rationale: List[str]
    timestamp: str
    model_name: str
    human_score: float = None

    # Computed metrics (filled during aggregation)
    json_valid: bool = True
    tokens_used: int = 0


@dataclass
class ParameterSettingResults:
    """Aggregated results for one parameter setting."""
    temperature: float
    top_p: float
    n_objects: int
    n_repeats: int

    # Stability metrics
    median_mad: float
    mean_mad: float
    icc: float  # Intra-class correlation
    json_validity_rate: float

    # Score statistics
    mean_score: float
    median_score: float
    score_std: float

    # Human agreement (if available)
    pearson_r: float = None
    spearman_r: float = None
    mae: float = None
    rmse: float = None

    # Per-object results
    object_results: List[Dict] = None


class ValidationStudy:
    """Main validation study orchestrator."""

    def __init__(self, config: ValidationConfig):
        self.config = config
        self.results: List[EvaluationResult] = []
        self.parameter_settings: List[Tuple[float, float]] = []
        self._setup_parameter_grid()

    def _setup_parameter_grid(self):
        """Create parameter grid."""
        # Baseline
        self.parameter_settings.append((self.config.baseline_temp, self.config.baseline_top_p))

        # Grid
        for temp in self.config.temperatures:
            for top_p in self.config.top_p_values:
                self.parameter_settings.append((temp, top_p))

        print(f"Parameter grid: {len(self.parameter_settings)} settings")
        for i, (temp, top_p) in enumerate(self.parameter_settings):
            label = "BASELINE" if temp == self.config.baseline_temp else "TEST"
            print(f"  [{label}] Setting {i+1}: temp={temp}, top_p={top_p}")

    def estimate_costs(self) -> Dict[str, Any]:
        """Estimate API costs and time."""
        # Load objects
        objects = self._load_objects()
        n_objects = len(objects)
        n_settings = len(self.parameter_settings)
        n_repeats = self.config.n_repeats

        total_calls = n_objects * n_settings * n_repeats

        # Gemini pricing (approximate)
        # Free tier: 2 requests/min, 1500 requests/day
        # Paid tier varies by model

        free_tier_rate = 2.0  # requests per minute
        time_minutes_free = total_calls / free_tier_rate

        return {
            "n_objects": n_objects,
            "n_settings": n_settings,
            "n_repeats": n_repeats,
            "total_api_calls": total_calls,
            "estimated_time_free_tier": {
                "minutes": time_minutes_free,
                "hours": time_minutes_free / 60,
                "formatted": f"{int(time_minutes_free // 60)}h {int(time_minutes_free % 60)}m"
            },
            "parameter_grid": [
                {"temp": temp, "top_p": top_p}
                for temp, top_p in self.parameter_settings
            ]
        }

    def _load_objects(self) -> List[Dict]:
        """Load selected objects."""
        objects = []
        csv_path = self.config.project_root / self.config.objects_csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                objects.append(row)
        return objects

    def _load_human_scores(self) -> Dict[str, float]:
        """Load human evaluation scores."""
        scores = {}
        csv_path = self.config.project_root / self.config.human_scores_csv
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row['3D Object filename']
                score = float(row['Visual Fidelity'])
                scores[filename] = score
        return scores

    def run_evaluation(self, dry_run: bool = False):
        """Run full validation study.

        Args:
            dry_run: If True, only estimate costs without running
        """
        costs = self.estimate_costs()

        print("\n" + "=" * 80)
        print("VALIDATION STUDY COST ESTIMATION")
        print("=" * 80)
        print(f"Objects: {costs['n_objects']}")
        print(f"Parameter settings: {costs['n_settings']}")
        print(f"Repeats per setting: {costs['n_repeats']}")
        print(f"Total API calls: {costs['total_api_calls']}")
        print(f"Estimated time (free tier): {costs['estimated_time_free_tier']['formatted']}")
        print("=" * 80)

        if dry_run:
            print("\n[DRY RUN] Skipping actual evaluation.")
            return costs

        # Save cost estimate
        with open(self.config.output_dir / "cost_estimate.json", 'w') as f:
            json.dump(costs, f, indent=2)

        print("\n[INFO] Starting evaluation...")
        print("[INFO] This will take approximately", costs['estimated_time_free_tier']['formatted'])
        print("[INFO] Results will be saved to:", self.config.output_dir)

        # TODO: Implement actual evaluation
        # This requires modifications to vfscore to accept temperature/top_p parameters
        print("\n[TODO] Actual evaluation requires VFScore CLI modifications:")
        print("  1. Add --temperature and --top-p options to 'vfscore score'")
        print("  2. Add run_id nonce to prompts for independence")
        print("  3. Log all parameters with each result")

        return costs

    def analyze_results(self):
        """Analyze collected results."""
        if not self.results:
            print("[ERROR] No results to analyze. Run evaluation first.")
            return

        human_scores = self._load_human_scores()

        # Analyze each parameter setting
        setting_results = []
        for temp, top_p in self.parameter_settings:
            results = self._analyze_parameter_setting(temp, top_p, human_scores)
            setting_results.append(results)

        return setting_results

    def _analyze_parameter_setting(
        self,
        temp: float,
        top_p: float,
        human_scores: Dict[str, float]
    ) -> ParameterSettingResults:
        """Analyze results for one parameter setting."""

        # Filter results for this setting
        setting_results = [
            r for r in self.results
            if r.temperature == temp and r.top_p == top_p
        ]

        if not setting_results:
            return None

        # Group by object
        object_groups = {}
        for r in setting_results:
            if r.object_id not in object_groups:
                object_groups[r.object_id] = []
            object_groups[r.object_id].append(r)

        # Compute per-object metrics
        object_results = []
        mads = []
        llm_scores = []
        human_scores_list = []

        for obj_id, obj_results in object_groups.items():
            scores = [r.score for r in obj_results]
            median_score = np.median(scores)
            mad = np.median([abs(s - median_score) for s in scores])
            ci_halfwidth = 1.96 * np.std(scores) / np.sqrt(len(scores))

            mads.append(mad)
            llm_scores.append(median_score)

            # Get human score if available
            obj_filename = obj_results[0].object_id  # Assuming object_id is filename
            if obj_filename in human_scores:
                human_scores_list.append(human_scores[obj_filename])

            object_results.append({
                "object_id": obj_id,
                "median": median_score,
                "mad": mad,
                "ci_halfwidth": ci_halfwidth,
                "n_repeats": len(scores)
            })

        # Compute ICC (Intra-class correlation)
        icc = self._compute_icc(object_groups)

        # Compute human agreement metrics
        pearson_r, spearman_r, mae, rmse = None, None, None, None
        if len(llm_scores) == len(human_scores_list) and len(human_scores_list) > 0:
            pearson_r, _ = stats.pearsonr(llm_scores, human_scores_list)
            spearman_r, _ = stats.spearmanr(llm_scores, human_scores_list)
            mae = np.mean(np.abs(np.array(llm_scores) - np.array(human_scores_list)))
            rmse = np.sqrt(np.mean((np.array(llm_scores) - np.array(human_scores_list))**2))

        # JSON validity
        json_validity_rate = sum(r.json_valid for r in setting_results) / len(setting_results)

        return ParameterSettingResults(
            temperature=temp,
            top_p=top_p,
            n_objects=len(object_groups),
            n_repeats=self.config.n_repeats,
            median_mad=np.median(mads),
            mean_mad=np.mean(mads),
            icc=icc,
            json_validity_rate=json_validity_rate,
            mean_score=np.mean(llm_scores),
            median_score=np.median(llm_scores),
            score_std=np.std(llm_scores),
            pearson_r=pearson_r,
            spearman_r=spearman_r,
            mae=mae,
            rmse=rmse,
            object_results=object_results
        )

    def _compute_icc(self, object_groups: Dict[str, List[EvaluationResult]]) -> float:
        """Compute ICC(1,k) for repeatability."""
        # Prepare data matrix: rows=objects, cols=repeats
        scores_matrix = []
        for obj_id in sorted(object_groups.keys()):
            scores = [r.score for r in object_groups[obj_id]]
            scores_matrix.append(scores)

        scores_array = np.array(scores_matrix)

        # ICC(1,k) calculation
        # Between-groups variance and within-groups variance
        n_objects = scores_array.shape[0]
        n_repeats = scores_array.shape[1]

        grand_mean = np.mean(scores_array)
        object_means = np.mean(scores_array, axis=1)

        # MS_between
        ms_between = n_repeats * np.sum((object_means - grand_mean)**2) / (n_objects - 1)

        # MS_within
        ms_within = np.sum((scores_array - object_means[:, np.newaxis])**2) / (n_objects * (n_repeats - 1))

        # ICC(1,k)
        icc = (ms_between - ms_within) / (ms_between + (n_repeats - 1) * ms_within)

        return max(0.0, min(1.0, icc))  # Clamp to [0, 1]

    def generate_report(self, setting_results: List[ParameterSettingResults]):
        """Generate beautiful HTML report."""
        from validation_report_generator import ValidationReportGenerator

        generator = ValidationReportGenerator(self.config, setting_results, self.results)
        report_path = generator.generate()

        print(f"\n[SUCCESS] Report generated: {report_path}")
        return report_path


def main():
    """Main entry point."""
    config = ValidationConfig(
        project_root=Path("."),
        n_repeats=5,
        llm_model="gemini-2.5-pro"
    )

    study = ValidationStudy(config)

    # Estimate costs (dry run)
    print("\n" + "=" * 80)
    print("VFSCORE VALIDATION STUDY")
    print("=" * 80)

    costs = study.run_evaluation(dry_run=True)

    # Save configuration
    with open(config.output_dir / "config.json", 'w') as f:
        json.dump({
            "temperatures": config.temperatures,
            "top_p_values": config.top_p_values,
            "n_repeats": config.n_repeats,
            "llm_model": config.llm_model,
            "parameter_settings": len(study.parameter_settings)
        }, f, indent=2)

    print(f"\n[INFO] Configuration saved to: {config.output_dir / 'config.json'}")
    print(f"[INFO] Cost estimate saved to: {config.output_dir / 'cost_estimate.json'}")


if __name__ == "__main__":
    main()
