# VFScore Validation Study - Complete Implementation Plan

**Document Version**: 1.0
**Date**: 2025-10-25
**Status**: Approved for Implementation
**Target**: PhD Research Publication

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Data Format Documentation](#data-format-documentation)
4. [Implementation Phases](#implementation-phases)
5. [Technical Specifications](#technical-specifications)
6. [Testing & Validation](#testing--validation)
7. [Timeline & Dependencies](#timeline--dependencies)
8. [References](#references)

---

## Executive Summary

### Purpose
Complete the VFScore validation study implementation to meet research publication standards. This includes implementing all three validation dimensions from the original plan: **stability**, **human agreement**, and **sensitivity analysis**.

### Scope
- **Phase 1**: Human Agreement Analysis (B) - HIGH PRIORITY
- **Phase 2**: ICC and Stability Metrics (A) - HIGH PRIORITY
- **Phase 3**: Confidence Intervals & Convergence (A) - MEDIUM PRIORITY
- **Phase 4**: Sensitivity & Signal Detection (C) - MANDATORY for publication

### Current Implementation Gap
The validation study currently runs parameter sweeps and computes basic statistics (median, MAD), but uses **placeholder values** for all critical research metrics:
- ICC (Intra-Class Correlation): Hardcoded 0.85-0.90
- Human correlation (Pearson/Spearman): Hardcoded 0.72-0.75
- Error metrics (MAE/RMSE): Hardcoded 0.08-0.10
- No sensitivity analysis exists

**Impact**: The current implementation cannot support research publication claims.

---

## Current State Analysis

### What Works ✅
1. **Parameter Sweep Infrastructure**
   - File: `validation_study/validation_study.py`
   - Successfully runs temperature × top_p grid (10 settings)
   - Batch mode with proper provenance tracking
   - Resume capability (skip already-scored items)

2. **Basic Statistical Aggregation**
   - File: `src/vfscore/aggregate.py`
   - Median computation: `compute_median()` (lines 112-116)
   - MAD computation: `compute_mad()` (lines 119-126)
   - Simple confidence metric: `compute_confidence()` (lines 129-133)

3. **Bilingual Report Generator**
   - File: `validation_study/validation_report_generator_enhanced.py`
   - HTML template with language toggle
   - Help menu with concept explanations
   - Interactive visualizations framework

### What's Missing ❌

#### Phase 1 (Point B): Human Agreement Analysis
- **File**: `validation_study/validation_study.py:413-418`
- **Status**: PLACEHOLDER VALUES ONLY
```python
spearman_r=0.75,  # Placeholder
pearson_r=0.72,   # Placeholder
mae=0.08,         # Placeholder
rmse=0.10,        # Placeholder
```
- **Missing**: All computation logic

#### Phase 2 (Point A): ICC Computation
- **File**: `validation_study/validation_study.py:413`
- **Status**: HARDCODED VALUES
```python
icc=0.90 if temp == 0.0 else 0.85,  # Placeholder
```
- **Missing**: Actual ICC(1,k) formula implementation

#### Phase 3 (Point A): Advanced Stability Metrics
- **Missing**: 95% CI computation
- **Missing**: Convergence curve generation
- **Missing**: Stop rule implementation

#### Phase 4 (Point C): Sensitivity Analysis
- **Missing**: Entire module
- **Missing**: Golden set generation
- **Missing**: Effect size computations

---

## Data Format Documentation

### Human Scores Dataset

**File**: `data/subjective.csv`

**Format Specification**:
```csv
3D Object filename,Visual Fidelity
{product_id}[_{variant}]__{algorithm}_{metadata}.glb,{score}
```

**Example Entries**:
```csv
188368__hunyuan3d_v2p1_single_N1_a_2025-08-17_v1_h00d888f7.glb,0.95
335888_curved-backrest_tripo3d_v2p5_multi_N3_A-B-C_2025-08-17_v1_h8a61ab22.glb,0.925
```

**Dataset Statistics**:
- **Total Evaluations**: 801 rows
- **Unique Products**: 94 distinct product IDs
- **Score Range**: 0.000 - 0.950
- **Mean Score**: 0.528
- **Encoding**: UTF-8 with BOM (utf-8-sig)

**Filename Pattern Parsing**:
```python
# Format: {product_id}[_{variant}]__{algorithm}_{job_metadata}.glb

# Example 1: No variant
"188368__hunyuan3d_v2p1_single_N1_a_2025-08-17_v1_h00d888f7.glb"
# product_id: "188368"
# variant: None
# item_id: "188368"

# Example 2: With variant
"335888_curved-backrest_tripo3d_v2p5_multi_N3_A-B-C_2025-08-17_v1_h8a61ab22.glb"
# product_id: "335888"
# variant: "curved-backrest"
# item_id: "335888_curved-backrest"
```

**Matching Logic**:
```python
from vfscore.data_sources.utils import make_item_id

def extract_item_id_from_filename(filename: str) -> str:
    """Extract item_id from subjective.csv filename."""
    # Split on double underscore
    parts = filename.split('__')
    if len(parts) < 2:
        raise ValueError(f"Invalid filename format: {filename}")

    product_part = parts[0]

    # Check if variant exists (underscore in product_part)
    if '_' in product_part:
        product_id, variant = product_part.split('_', 1)
        return make_item_id(product_id, variant)
    else:
        return make_item_id(product_part, None)
```

**VFScore Item ID Format**:
- Consistent with `src/vfscore/data_sources/utils.py:make_item_id()`
- Format: `{product_id}_{sanitized_variant}` or just `{product_id}`
- Variant sanitization: lowercase + replace spaces with hyphens

---

## Implementation Phases

### Phase 1: Human Agreement Analysis

**Priority**: HIGH
**Estimated Effort**: 6-8 hours
**Dependencies**: scipy, numpy (already installed)

#### 1.1 Create Human Scores Loader Module

**File**: `validation_study/human_scores.py`

```python
"""
Human scores loader and matching module.

This module loads human evaluations from subjective.csv and matches them
with LLM scores by item_id for correlation analysis.
"""

import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class HumanScore:
    """Human evaluation score."""
    filename: str
    item_id: str
    product_id: str
    variant: Optional[str]
    algorithm: str
    score: float

def load_human_scores(csv_path: Path) -> List[HumanScore]:
    """Load all human scores from subjective.csv."""
    pass

def match_llm_to_human(
    llm_results: Dict[str, float],
    human_scores: List[HumanScore]
) -> Tuple[List[float], List[float]]:
    """Match LLM and human scores by item_id.

    Returns:
        Tuple of (llm_scores, human_scores) as parallel lists
    """
    pass

def aggregate_human_scores_by_item(
    human_scores: List[HumanScore]
) -> Dict[str, float]:
    """Aggregate multiple human scores per item (mean)."""
    pass
```

#### 1.2 Create Correlation Analysis Module

**File**: `validation_study/correlation_analysis.py`

```python
"""
Human-LLM agreement analysis.

Computes correlation metrics, error metrics, and calibration curves
for validating automated scores against human judgment.
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class CorrelationResults:
    """Results of correlation analysis."""
    pearson_r: float
    pearson_p: float
    spearman_r: float
    spearman_p: float
    mae: float
    rmse: float
    n_pairs: int

    # Calibration results
    calibration_slope: Optional[float] = None
    calibration_intercept: Optional[float] = None
    calibrated_mae: Optional[float] = None
    calibrated_rmse: Optional[float] = None

def compute_correlations(
    llm_scores: List[float],
    human_scores: List[float]
) -> CorrelationResults:
    """Compute Pearson and Spearman correlations."""
    # scipy.stats.pearsonr()
    # scipy.stats.spearmanr()
    pass

def compute_error_metrics(
    llm_scores: np.ndarray,
    human_scores: np.ndarray
) -> Tuple[float, float]:
    """Compute MAE and RMSE.

    MAE = mean(|llm - human|)
    RMSE = sqrt(mean((llm - human)^2))
    """
    pass

def fit_calibration(
    llm_scores: np.ndarray,
    human_scores: np.ndarray,
    method: str = 'linear'
) -> Tuple[float, float]:
    """Fit calibration curve (linear regression).

    Returns:
        (slope, intercept) for calibration transform
    """
    # np.polyfit(llm_scores, human_scores, deg=1)
    pass

def apply_calibration(
    llm_scores: np.ndarray,
    slope: float,
    intercept: float
) -> np.ndarray:
    """Apply calibration transform."""
    pass
```

#### 1.3 Integrate into Validation Study

**File**: `validation_study/validation_study.py`

Update `_analyze_batch_results()` method (lines 377-424):

```python
def _analyze_batch_results(self) -> List[SettingResult]:
    """Analyze batch results with ACTUAL human agreement computation."""
    from validation_study.human_scores import load_human_scores, match_llm_to_human
    from validation_study.correlation_analysis import compute_correlations

    # Load human scores once
    human_scores_path = self.config.project_root / self.config.human_scores_csv
    human_scores = load_human_scores(human_scores_path)

    results = []
    llm_calls_dir = self.config.project_root / "outputs" / "llm_calls"

    # Load aggregated LLM scores
    aggregated_path = self.config.project_root / "outputs" / "results" / "per_item.jsonl"
    llm_scores_by_item = load_llm_aggregated_scores(aggregated_path)

    # Match scores
    llm_matched, human_matched = match_llm_to_human(llm_scores_by_item, human_scores)

    # Compute correlations
    corr_results = compute_correlations(llm_matched, human_matched)

    # For each parameter setting, compute statistics
    for temp, top_p in self.parameter_settings:
        # Load scores for this specific setting from batches
        setting_scores = load_scores_for_setting(llm_calls_dir, temp, top_p)

        # Compute ICC, MAD (will be implemented in Phase 2)
        icc = compute_icc(setting_scores)  # Phase 2
        mad = compute_setting_mad(setting_scores)

        setting = SettingResult(
            temperature=temp,
            top_p=top_p,
            icc=icc,
            mad=mad,
            spearman_r=corr_results.spearman_r,  # ACTUAL VALUE
            pearson_r=corr_results.pearson_r,    # ACTUAL VALUE
            mae=corr_results.mae,                # ACTUAL VALUE
            rmse=corr_results.rmse,              # ACTUAL VALUE
            json_validity_rate=compute_json_validity(setting_scores),
            n_evaluations=len(setting_scores)
        )
        results.append(setting)

    return results
```

#### 1.4 Update Report Generator

**File**: `validation_study/validation_report_generator_enhanced.py`

Add scatter plot generation for LLM vs. Human scores:

```python
def generate_scatter_plot_data(
    llm_scores: List[float],
    human_scores: List[float],
    item_ids: List[str]
) -> Dict:
    """Generate scatter plot data for Chart.js."""
    return {
        'datasets': [{
            'label': 'LLM vs Human',
            'data': [
                {'x': h, 'y': l, 'item_id': iid}
                for h, l, iid in zip(human_scores, llm_scores, item_ids)
            ],
            'backgroundColor': 'rgba(102, 126, 234, 0.6)'
        }],
        'identity_line': [
            {'x': 0, 'y': 0},
            {'x': 1, 'y': 1}
        ]
    }
```

---

### Phase 2: ICC and Reliability Metrics

**Priority**: HIGH
**Estimated Effort**: 6-8 hours
**Dependencies**: **pingouin** (NEW - must install)

#### 2.1 Add Dependencies

**File**: `requirements.txt`

```diff
 rich>=13.0.0
 jinja2>=3.1.0
 onnxruntime<=1.23.0
+scipy>=1.11.0
+pingouin>=0.5.3
```

**Installation Command**:
```bash
pip install scipy>=1.11.0 pingouin>=0.5.3
```

**Why Pingouin?**
- Specialized for psychometric and reliability analysis
- Implements ICC(1,k), ICC(2,k), ICC(3,k) variants
- Better than manual scipy implementation
- Well-documented for research use

#### 2.2 Create ICC Computation Module

**File**: `validation_study/icc_analysis.py`

```python
"""
Intra-Class Correlation (ICC) analysis module.

Implements ICC computation for measuring repeatability and reliability
of LLM visual fidelity scores across repeated evaluations.

ICC Formula (1,k - single fixed raters, k measurements averaged):
ICC(1,k) = (BMS - WMS) / (BMS + (k-1)*WMS + k*(JMS - WMS)/n)

Where:
- BMS: Between-subjects mean square
- WMS: Within-subjects mean square
- JMS: Judge (rater) mean square
- k: number of raters/repeats
- n: number of subjects/items

For our use case:
- Subjects = items being scored
- Raters = repeated LLM calls (with different run_ids)
- k = number of repeats (typically 5)
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass

# Use pingouin for ICC computation
import pingouin as pg

@dataclass
class ICCResult:
    """Results of ICC analysis."""
    icc_value: float
    icc_ci_lower: float
    icc_ci_upper: float
    icc_type: str  # e.g., "ICC1k", "ICC2k"
    f_statistic: float
    p_value: float
    n_items: int
    n_raters: int

def compute_icc_from_repeats(
    scores_matrix: np.ndarray,
    icc_type: str = 'ICC1k'
) -> ICCResult:
    """Compute ICC from matrix of repeated scores.

    Args:
        scores_matrix: 2D array of shape (n_items, n_repeats)
                      Each row is an item, each column is a repeat
        icc_type: Type of ICC to compute
                  - 'ICC1': One-way random effects
                  - 'ICC1k': Average of k random raters
                  - 'ICC2': Two-way random effects
                  - 'ICC2k': Average of k fixed raters (recommended)

    Returns:
        ICCResult with computed metrics
    """
    # Convert to long format for pingouin
    df = scores_to_dataframe(scores_matrix)

    # Compute ICC using pingouin
    icc_results = pg.intraclass_corr(
        data=df,
        targets='item',
        raters='repeat',
        ratings='score',
        nan_policy='omit'
    )

    # Extract specific ICC type
    icc_row = icc_results[icc_results['Type'] == icc_type].iloc[0]

    return ICCResult(
        icc_value=icc_row['ICC'],
        icc_ci_lower=icc_row['CI95%'][0],
        icc_ci_upper=icc_row['CI95%'][1],
        icc_type=icc_type,
        f_statistic=icc_row['F'],
        p_value=icc_row['pval'],
        n_items=scores_matrix.shape[0],
        n_raters=scores_matrix.shape[1]
    )

def scores_to_dataframe(scores_matrix: np.ndarray) -> pd.DataFrame:
    """Convert scores matrix to long-format DataFrame for pingouin."""
    n_items, n_repeats = scores_matrix.shape

    data = []
    for item_idx in range(n_items):
        for repeat_idx in range(n_repeats):
            data.append({
                'item': item_idx,
                'repeat': repeat_idx,
                'score': scores_matrix[item_idx, repeat_idx]
            })

    return pd.DataFrame(data)

def load_scores_matrix_from_batches(
    llm_calls_dir: Path,
    model: str,
    temperature: float,
    top_p: float,
    n_repeats: int
) -> np.ndarray:
    """Load scores from batch directories into matrix format.

    Returns:
        Matrix of shape (n_items, n_repeats) where each row is an item
        and each column is a repeat evaluation
    """
    # Implementation: scan batch directories matching (temp, top_p)
    # Extract scores from rep_1.json, rep_2.json, ..., rep_N.json
    # Organize into matrix format
    pass

def interpret_icc(icc_value: float) -> str:
    """Interpret ICC value according to standard thresholds.

    Returns:
        Interpretation string: "Excellent", "Good", "Moderate", "Poor"
    """
    if icc_value >= 0.85:
        return "Excellent"
    elif icc_value >= 0.70:
        return "Good"
    elif icc_value >= 0.50:
        return "Moderate"
    else:
        return "Poor"
```

#### 2.3 Update Aggregate Module

**File**: `src/vfscore/aggregate.py`

Add ICC computation alongside existing median/MAD:

```python
def compute_icc_for_item(scores: List[float]) -> Optional[float]:
    """Compute ICC for a single item's repeated scores.

    Note: Requires at least 3 repeats for meaningful ICC.
    """
    if len(scores) < 3:
        return None

    # For single-item ICC, use variance-based formula
    # Or return None and compute ICC across all items instead
    # (recommended: compute ICC at the dataset level, not per-item)
    return None  # TODO: Decide on per-item vs. dataset-level ICC
```

**Note**: ICC is typically computed **across all items** rather than per-item, since it measures between-item vs. within-item variance. The `icc_analysis.py` module handles this correctly.

---

### Phase 3: Confidence Intervals & Convergence Analysis

**Priority**: MEDIUM
**Estimated Effort**: 4-6 hours
**Dependencies**: scipy, numpy (already available after Phase 2)

#### 3.1 Add CI Computation to Aggregate Module

**File**: `src/vfscore/aggregate.py`

```python
import numpy as np
from scipy import stats

def compute_ci_95(values: List[float]) -> Tuple[float, float]:
    """Compute 95% confidence interval of the mean.

    Formula: mean ± 1.96 * (sd / sqrt(n))

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if len(values) < 2:
        return (values[0], values[0]) if values else (0.0, 0.0)

    mean = np.mean(values)
    std = np.std(values, ddof=1)  # Sample standard deviation
    n = len(values)

    # Standard error of the mean
    sem = std / np.sqrt(n)

    # 95% CI: ±1.96 * SEM (for normal distribution)
    # Or use t-distribution for small samples
    if n < 30:
        t_critical = stats.t.ppf(0.975, df=n-1)  # Two-tailed 95%
        margin = t_critical * sem
    else:
        margin = 1.96 * sem

    return (mean - margin, mean + margin)

def compute_ci_half_width(values: List[float]) -> float:
    """Compute half-width of 95% CI (margin of error)."""
    lower, upper = compute_ci_95(values)
    return (upper - lower) / 2.0
```

#### 3.2 Create Convergence Analysis Module

**File**: `validation_study/convergence_analysis.py`

```python
"""
Convergence analysis for determining optimal number of repeats.

Generates convergence curves showing how mean score and confidence
interval half-width stabilize as more repeats are added.

This helps determine the practical stopping rule: e.g., stop when
CI half-width ≤ ±0.02 (2 points on 0-100 scale).
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class ConvergencePoint:
    """Single point on convergence curve."""
    n_repeats: int
    running_mean: float
    running_median: float
    running_mad: float
    ci_half_width: float
    ci_lower: float
    ci_upper: float

def compute_convergence_curve(
    scores: List[float]
) -> List[ConvergencePoint]:
    """Compute convergence statistics for n=1, 2, 3, ..., N repeats.

    Args:
        scores: List of repeat scores for a single item (in order evaluated)

    Returns:
        List of ConvergencePoint objects showing statistics at each n
    """
    curve = []

    for n in range(1, len(scores) + 1):
        subset = scores[:n]

        # Compute statistics on first n repeats
        mean_n = np.mean(subset)
        median_n = np.median(subset)
        mad_n = np.median(np.abs(np.array(subset) - median_n))

        # Compute CI
        if n >= 2:
            ci_lower, ci_upper = compute_ci_95(subset)
            ci_half = (ci_upper - ci_lower) / 2.0
        else:
            ci_lower, ci_upper = mean_n, mean_n
            ci_half = 0.0

        curve.append(ConvergencePoint(
            n_repeats=n,
            running_mean=mean_n,
            running_median=median_n,
            running_mad=mad_n,
            ci_half_width=ci_half,
            ci_lower=ci_lower,
            ci_upper=ci_upper
        ))

    return curve

def find_convergence_point(
    curve: List[ConvergencePoint],
    threshold: float = 0.02
) -> int:
    """Find n where CI half-width first drops below threshold.

    Args:
        curve: Convergence curve from compute_convergence_curve()
        threshold: CI half-width threshold (default: 0.02 = ±2 points)

    Returns:
        Minimum number of repeats needed for convergence
    """
    for point in curve:
        if point.ci_half_width <= threshold:
            return point.n_repeats

    # Never converged
    return len(curve)

def aggregate_convergence_across_items(
    all_curves: List[List[ConvergencePoint]]
) -> Dict[int, Dict[str, float]]:
    """Aggregate convergence statistics across all items.

    Returns:
        Dict mapping n_repeats -> {mean_ci_width, median_ci_width, ...}
    """
    max_n = max(len(curve) for curve in all_curves)

    aggregated = {}
    for n in range(1, max_n + 1):
        ci_widths = []
        for curve in all_curves:
            if len(curve) >= n:
                ci_widths.append(curve[n-1].ci_half_width)

        aggregated[n] = {
            'mean_ci_width': np.mean(ci_widths),
            'median_ci_width': np.median(ci_widths),
            'max_ci_width': np.max(ci_widths),
            'n_items': len(ci_widths)
        }

    return aggregated
```

#### 3.3 Add to Validation Report

Update report generator to include convergence plots:

```javascript
// Convergence curve chart (Chart.js)
const convergenceCtx = document.getElementById('convergenceChart').getContext('2d');
new Chart(convergenceCtx, {
    type: 'line',
    data: {
        labels: [1, 2, 3, 4, 5],  // n_repeats
        datasets: [
            {
                label: 'Mean CI Half-Width',
                data: convergenceData.mean_ci_widths,
                borderColor: 'rgb(75, 192, 192)',
                fill: false
            },
            {
                label: 'Threshold (±0.02)',
                data: [0.02, 0.02, 0.02, 0.02, 0.02],
                borderColor: 'rgb(255, 99, 132)',
                borderDash: [5, 5],
                fill: false
            }
        ]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: { display: true, text: 'CI Half-Width' }
            },
            x: {
                title: { display: true, text: 'Number of Repeats' }
            }
        }
    }
});
```

---

### Phase 4: Sensitivity & Signal Detection Analysis (PILOT VERSION)

**Priority**: MANDATORY (PhD Research - Preliminary Pilot)
**Estimated Effort**: 8-10 hours (simplified for pilot study)
**Dependencies**: PIL/OpenCV (already installed), numpy (already installed)

**Pilot Rationale**: Full sensitivity analysis requires extensive API calls. For the pilot study, we implement a **single, highly effective sensitivity test** that validates VFScore's ability to detect significant appearance changes affecting both color and material properties.

#### 4.1 Create Golden Set Generation Tool (Simplified)

**File**: `validation_study/golden_set_generator.py`

```python
"""
Golden set generation for sensitivity analysis - PILOT VERSION.

Creates a SINGLE controlled appearance variation for testing VFScore's
sensitivity to known appearance changes.

PILOT VARIATION:
- Diagonal striped magenta-yellow texture overlay
- Applied to both albedo (color) and normal map simulation
- Calibrated to 6-7 bands across object surface
- Creates remarkable alteration to visual appearance on both aspects

This single test validates:
1. Color perception (magenta-yellow alternation)
2. Material/texture perception (stripe pattern affects surface appearance)
3. Large-magnitude detectability (expected Cohen's d ≥ 1.5)

For full study: expand to multiple variation types (hue, saturation, etc.)
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum

class VariationType(Enum):
    """Types of controlled appearance variations."""
    DIAGONAL_STRIPES = "diagonal_stripes"

@dataclass
class GoldenPair:
    """A pair of images with known appearance delta."""
    original_path: Path
    modified_path: Path
    variation_type: VariationType
    delta_magnitude: float  # e.g., +10 for +10° hue shift
    expected_direction: str  # "worse" or "better" (for scoring)
    item_id: str
    category_l3: str

def apply_diagonal_stripe_texture(
    image: Image.Image,
    n_bands: int = 7,
    color1: Tuple[int, int, int] = (255, 0, 255),  # Magenta
    color2: Tuple[int, int, int] = (255, 255, 0),  # Yellow
    blend_mode: str = "multiply",
    opacity: float = 0.7
) -> Image.Image:
    """Apply diagonal striped magenta-yellow texture overlay.

    This creates a dramatic visual alteration affecting both color
    and perceived material properties (surface pattern).

    Args:
        image: Input PIL Image (RGB)
        n_bands: Number of diagonal stripes (default: 7 for 6-7 bands)
        color1: First stripe color (default: magenta #FF00FF)
        color2: Second stripe color (default: yellow #FFFF00)
        blend_mode: How to blend texture ("multiply", "overlay", "normal")
        opacity: Texture opacity 0.0-1.0 (default: 0.7 for strong effect)

    Returns:
        Modified image with diagonal stripe texture overlay

    Technical approach:
    1. Create diagonal stripe pattern matching image dimensions
    2. Alternate between magenta and yellow bands
    3. Apply with multiply blend for color+material effect
    4. Use 70% opacity to preserve some original appearance
    """
    w, h = image.size

    # Create stripe pattern
    stripe_texture = Image.new('RGB', (w, h), color1)
    draw = ImageDraw.Draw(stripe_texture)

    # Calculate stripe width (diagonal distance / n_bands)
    diagonal_len = np.sqrt(w**2 + h**2)
    stripe_width = diagonal_len / n_bands

    # Draw diagonal stripes (alternating colors)
    # Stripe orientation: top-left to bottom-right (45° angle)
    for i in range(n_bands * 2):  # Double to cover entire image
        if i % 2 == 1:  # Odd stripes get color2
            # Calculate stripe polygon points
            offset = i * stripe_width / np.sqrt(2)

            # Top-left to bottom-right stripe
            points = [
                (offset - stripe_width / np.sqrt(2), 0),
                (offset, 0),
                (w, h - offset + stripe_width / np.sqrt(2)),
                (w, h - offset),
            ]

            # Handle edge cases
            if offset < w and offset < h:
                draw.polygon(points, fill=color2)

    # Blend texture with original image
    if blend_mode == "multiply":
        # Multiply blend (darkens, affects both color and perceived material)
        img_array = np.array(image, dtype=np.float32) / 255.0
        texture_array = np.array(stripe_texture, dtype=np.float32) / 255.0

        # Multiply and apply opacity
        blended = img_array * texture_array
        result = img_array * (1 - opacity) + blended * opacity

        result = (result * 255).clip(0, 255).astype(np.uint8)
        return Image.fromarray(result, mode='RGB')

    elif blend_mode == "overlay":
        # Overlay blend (high contrast)
        img_array = np.array(image, dtype=np.float32) / 255.0
        texture_array = np.array(stripe_texture, dtype=np.float32) / 255.0

        # Overlay formula
        mask = img_array < 0.5
        result = np.where(
            mask,
            2 * img_array * texture_array,
            1 - 2 * (1 - img_array) * (1 - texture_array)
        )

        result = img_array * (1 - opacity) + result * opacity
        result = (result * 255).clip(0, 255).astype(np.uint8)
        return Image.fromarray(result, mode='RGB')

    else:  # "normal" - simple alpha blend
        return Image.blend(image, stripe_texture, opacity)

def generate_golden_pair_for_item(
    item_id: str,
    original_render_path: Path,
    output_dir: Path,
    n_bands: int = 7
) -> GoldenPair:
    """Generate golden pair with diagonal stripe texture for a single item.

    PILOT VERSION: Single variation only.

    Args:
        item_id: Item identifier
        original_render_path: Path to original rendered candidate image
        output_dir: Directory to save modified image
        n_bands: Number of diagonal stripes (default: 7)

    Returns:
        GoldenPair object (original vs. striped version)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    original_image = Image.open(original_render_path).convert('RGB')

    # Apply diagonal stripe texture
    modified = apply_diagonal_stripe_texture(
        original_image,
        n_bands=n_bands,
        color1=(255, 0, 255),  # Magenta
        color2=(255, 255, 0),  # Yellow
        blend_mode="multiply",
        opacity=0.7
    )

    # Save modified image
    suffix = f"stripes{n_bands}"
    modified_path = output_dir / f"{item_id}_{suffix}.png"
    modified.save(modified_path)

    return GoldenPair(
        original_path=original_render_path,
        modified_path=modified_path,
        variation_type=VariationType.DIAGONAL_STRIPES,
        delta_magnitude=n_bands,  # Band count as magnitude metric
        expected_direction="worse",  # Striped texture degrades fidelity
        item_id=item_id,
        category_l3="unknown"  # TODO: load from manifest
    )

def generate_pilot_golden_set(
    items: List[str],
    render_dir: Path,
    output_dir: Path,
    n_bands: int = 7
) -> List[GoldenPair]:
    """Generate pilot golden set for sensitivity analysis.

    PILOT VERSION: Single variation type only.
    - Diagonal striped magenta-yellow texture
    - 6-7 bands (calibrated parameter)
    - Applied to all selected items

    Total: 1 variation per item × N items

    For full study: See IMPLEMENTATION_PLAN.md (9 variations per item)

    Args:
        items: List of item IDs to process
        render_dir: Directory containing original renders
        output_dir: Output directory for golden set
        n_bands: Number of diagonal stripes (default: 7)

    Returns:
        List of GoldenPair objects (one per item)
    """
    all_pairs = []

    for item_id in items:
        original_path = render_dir / item_id / "candidate.png"
        if not original_path.exists():
            print(f"[WARNING] Skipping {item_id}: original render not found")
            continue

        pair = generate_golden_pair_for_item(
            item_id=item_id,
            original_render_path=original_path,
            output_dir=output_dir / item_id,
            n_bands=n_bands
        )
        all_pairs.append(pair)

    return all_pairs
```

#### 4.2 Create Sensitivity Analysis Module

**File**: `validation_study/sensitivity_analysis.py`

```python
"""
Sensitivity and signal detection analysis.

Computes metrics for assessing VFScore's ability to detect
known appearance differences in the golden set.

Metrics:
1. Effect size (Cohen's d) between original and modified
2. Hit rate: fraction where score_modified < score_original
3. Dose-response: correlation between delta magnitude and score difference
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class SensitivityResult:
    """Results of sensitivity analysis."""
    variation_type: str
    n_pairs: int

    # Effect size
    cohens_d: float
    cohens_d_interpretation: str  # "small", "medium", "large"

    # Hit rate
    hit_rate: float
    n_hits: int
    n_misses: int

    # Dose-response (for graded variations like hue shift)
    correlation_magnitude_vs_delta: Optional[float] = None
    regression_slope: Optional[float] = None
    regression_r_squared: Optional[float] = None

    # Score statistics
    mean_score_original: float = 0.0
    mean_score_modified: float = 0.0
    mean_score_difference: float = 0.0

def compute_cohens_d(
    scores_original: np.ndarray,
    scores_modified: np.ndarray
) -> float:
    """Compute Cohen's d effect size.

    Cohen's d = (mean1 - mean2) / pooled_std

    Interpretation:
    - |d| < 0.2: negligible
    - 0.2 ≤ |d| < 0.5: small
    - 0.5 ≤ |d| < 0.8: medium
    - |d| ≥ 0.8: large
    """
    mean1 = np.mean(scores_original)
    mean2 = np.mean(scores_modified)

    std1 = np.std(scores_original, ddof=1)
    std2 = np.std(scores_modified, ddof=1)

    n1, n2 = len(scores_original), len(scores_modified)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1 + n2 - 2))

    d = (mean1 - mean2) / pooled_std
    return d

def interpret_cohens_d(d: float) -> str:
    """Interpret Cohen's d value."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def compute_hit_rate(
    scores_original: np.ndarray,
    scores_modified: np.ndarray,
    expected_direction: str = "worse"
) -> Tuple[float, int, int]:
    """Compute hit rate (fraction of correct score comparisons).

    Args:
        scores_original: Scores for original images
        scores_modified: Scores for modified images
        expected_direction: "worse" (score should decrease) or "better"

    Returns:
        (hit_rate, n_hits, n_misses)
    """
    if expected_direction == "worse":
        # Modified should score lower than original
        hits = np.sum(scores_modified < scores_original)
    elif expected_direction == "better":
        hits = np.sum(scores_modified > scores_original)
    else:  # "same"
        # Within ±0.05 tolerance
        hits = np.sum(np.abs(scores_modified - scores_original) < 0.05)

    n_pairs = len(scores_original)
    misses = n_pairs - hits
    hit_rate = hits / n_pairs if n_pairs > 0 else 0.0

    return hit_rate, hits, misses

def compute_dose_response(
    delta_magnitudes: np.ndarray,
    score_differences: np.ndarray
) -> Dict[str, float]:
    """Compute dose-response relationship.

    Analyzes whether score changes scale with magnitude of appearance change.
    E.g., does a 20° hue shift produce larger score drop than 5° shift?

    Returns:
        Dict with correlation, slope, r_squared
    """
    # Pearson correlation between magnitude and score difference
    correlation, p_value = stats.pearsonr(delta_magnitudes, score_differences)

    # Linear regression
    slope, intercept = np.polyfit(delta_magnitudes, score_differences, deg=1)

    # R-squared
    predicted = slope * delta_magnitudes + intercept
    ss_res = np.sum((score_differences - predicted) ** 2)
    ss_tot = np.sum((score_differences - np.mean(score_differences)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        'correlation': correlation,
        'p_value': p_value,
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared
    }

def analyze_golden_set_results(
    golden_pairs: List[GoldenPair],
    scores: Dict[str, float]  # {image_path: score}
) -> List[SensitivityResult]:
    """Analyze golden set results by variation type.

    Args:
        golden_pairs: List of GoldenPair objects
        scores: Dict mapping image paths to VFScore scores

    Returns:
        List of SensitivityResult objects (one per variation type)
    """
    # Group pairs by variation type
    by_type = {}
    for pair in golden_pairs:
        vtype = pair.variation_type.value
        if vtype not in by_type:
            by_type[vtype] = []
        by_type[vtype].append(pair)

    results = []

    for vtype, pairs in by_type.items():
        scores_orig = []
        scores_mod = []
        magnitudes = []

        for pair in pairs:
            orig_score = scores.get(str(pair.original_path))
            mod_score = scores.get(str(pair.modified_path))

            if orig_score is not None and mod_score is not None:
                scores_orig.append(orig_score)
                scores_mod.append(mod_score)
                magnitudes.append(abs(pair.delta_magnitude))

        if not scores_orig:
            continue

        scores_orig = np.array(scores_orig)
        scores_mod = np.array(scores_mod)
        score_diffs = scores_orig - scores_mod

        # Compute metrics
        d = compute_cohens_d(scores_orig, scores_mod)
        hit_rate, n_hits, n_misses = compute_hit_rate(
            scores_orig, scores_mod,
            expected_direction=pairs[0].expected_direction
        )

        # Dose-response (if applicable)
        dose_response = None
        if len(set(magnitudes)) > 2:  # Multiple magnitude levels
            dose_response = compute_dose_response(
                np.array(magnitudes),
                score_diffs
            )

        result = SensitivityResult(
            variation_type=vtype,
            n_pairs=len(pairs),
            cohens_d=d,
            cohens_d_interpretation=interpret_cohens_d(d),
            hit_rate=hit_rate,
            n_hits=n_hits,
            n_misses=n_misses,
            correlation_magnitude_vs_delta=dose_response['correlation'] if dose_response else None,
            regression_slope=dose_response['slope'] if dose_response else None,
            regression_r_squared=dose_response['r_squared'] if dose_response else None,
            mean_score_original=np.mean(scores_orig),
            mean_score_modified=np.mean(scores_mod),
            mean_score_difference=np.mean(score_diffs)
        )

        results.append(result)

    return results
```

#### 4.3 Integration Workflow

**File**: `validation_study/run_sensitivity_study.py`

```python
"""
Sensitivity study runner.

Complete workflow:
1. Generate golden set from selected items
2. Score all golden set images with VFScore
3. Analyze results for sensitivity metrics
4. Generate sensitivity report
"""

import sys
from pathlib import Path

def main():
    # Load selected items for sensitivity study
    # (subset of validation study items, e.g., 5-10 items)
    selected_items = load_selected_items()

    # Step 1: Generate golden set
    print("Generating golden set...")
    golden_pairs = generate_full_golden_set(
        items=selected_items,
        render_dir=Path("outputs/preprocess/cand"),
        output_dir=Path("outputs/golden_set")
    )
    print(f"Generated {len(golden_pairs)} golden pairs")

    # Step 2: Create scoring packets for golden set
    print("Creating scoring packets...")
    # TODO: Implement golden set packetization

    # Step 3: Score all golden set images
    print("Scoring golden set...")
    # Run vfscore score on golden set packets
    # TODO: Implement scoring

    # Step 4: Analyze results
    print("Analyzing sensitivity...")
    sensitivity_results = analyze_golden_set_results(golden_pairs, scores)

    # Step 5: Generate report
    print("Generating sensitivity report...")
    generate_sensitivity_report(sensitivity_results)

    print("Sensitivity study complete!")

if __name__ == "__main__":
    main()
```

---

## Technical Specifications

### Dependencies Matrix

| Phase | Package | Version | Purpose |
|-------|---------|---------|---------|
| 1 | scipy | ≥1.11.0 | Pearson/Spearman correlation |
| 1 | numpy | ≥1.24.0 | Array operations (INSTALLED) |
| 2 | pingouin | ≥0.5.3 | ICC computation |
| 2 | pandas | ≥2.0.0 | Data formatting for pingouin |
| 4 | PIL | ≥10.0.0 | Image manipulation (INSTALLED) |
| 4 | opencv-python | ≥4.8.0 | Advanced image ops (INSTALLED) |

**Installation Command**:
```bash
pip install scipy>=1.11.0 pingouin>=0.5.3 pandas>=2.0.0
```

### File Structure After Implementation

```
validation_study/
├── docs/
│   ├── IMPLEMENTATION_PLAN.md (this file)
│   ├── Validation_study_plan.txt (original plan)
│   └── ... (existing docs)
├── validation_study.py (updated)
├── validation_report_generator_enhanced.py (updated)
├── human_scores.py (NEW - Phase 1)
├── correlation_analysis.py (NEW - Phase 1)
├── icc_analysis.py (NEW - Phase 2)
├── convergence_analysis.py (NEW - Phase 3)
├── golden_set_generator.py (NEW - Phase 4)
├── sensitivity_analysis.py (NEW - Phase 4)
└── run_sensitivity_study.py (NEW - Phase 4)
```

---

## Testing & Validation

### Unit Tests

**File**: `tests/test_validation_metrics.py`

```python
"""Unit tests for validation study metrics."""

import pytest
import numpy as np
from validation_study.correlation_analysis import compute_correlations
from validation_study.icc_analysis import compute_icc_from_repeats
from validation_study.sensitivity_analysis import compute_cohens_d

def test_pearson_correlation():
    """Test Pearson correlation computation."""
    llm = [0.8, 0.6, 0.9, 0.7]
    human = [0.75, 0.65, 0.85, 0.70]

    result = compute_correlations(llm, human)

    assert 0.8 < result.pearson_r < 1.0  # Strong positive correlation
    assert result.p_value < 0.05  # Significant

def test_icc_perfect_agreement():
    """Test ICC with perfect agreement (all repeats identical)."""
    # 3 items, 5 repeats each, perfect agreement
    scores = np.array([
        [0.8, 0.8, 0.8, 0.8, 0.8],
        [0.6, 0.6, 0.6, 0.6, 0.6],
        [0.9, 0.9, 0.9, 0.9, 0.9]
    ])

    result = compute_icc_from_repeats(scores)

    assert result.icc_value > 0.99  # Nearly perfect ICC

def test_cohens_d_large_effect():
    """Test Cohen's d with large effect."""
    original = np.array([0.9, 0.85, 0.95, 0.88])
    modified = np.array([0.5, 0.45, 0.55, 0.48])  # Large drop

    d = compute_cohens_d(original, modified)

    assert d > 2.0  # Large effect
    assert interpret_cohens_d(d) == "large"
```

### Integration Tests

Test complete workflow end-to-end:
1. Load human scores
2. Match with LLM scores
3. Compute all metrics
4. Generate report

---

## Timeline & Dependencies

### Phase 1: Human Agreement (Week 1)
- **Days 1-2**: Implement `human_scores.py` + `correlation_analysis.py`
- **Day 3**: Integrate into `validation_study.py`
- **Day 4**: Update report generator with scatter plots
- **Day 5**: Testing and validation

**Deliverables**:
- [ ] Human scores loader
- [ ] Correlation computation
- [ ] Error metrics (MAE/RMSE)
- [ ] Scatter plot visualization
- [ ] Unit tests

### Phase 2: ICC & Reliability (Week 2)
- **Days 1-2**: Install dependencies, implement `icc_analysis.py`
- **Day 3**: Integrate ICC into aggregation pipeline
- **Day 4**: Update report with ICC results
- **Day 5**: Testing

**Deliverables**:
- [ ] pingouin integration
- [ ] ICC computation across parameter settings
- [ ] ICC interpretation guidelines
- [ ] Report updates

### Phase 3: CI & Convergence (Week 3)
- **Days 1-2**: Implement `convergence_analysis.py`
- **Day 3**: Add CI computation to aggregate
- **Days 4-5**: Convergence plots in report

**Deliverables**:
- [ ] 95% CI computation
- [ ] Convergence curve generation
- [ ] Stopping rule analysis
- [ ] Visualization

### Phase 4: Sensitivity Analysis (Weeks 4-5)
- **Week 4, Days 1-3**: Implement `golden_set_generator.py`
- **Week 4, Days 4-5**: Generate golden set for pilot items
- **Week 5, Days 1-2**: Implement `sensitivity_analysis.py`
- **Week 5, Days 3-4**: Run sensitivity study
- **Week 5, Day 5**: Generate sensitivity report

**Deliverables**:
- [ ] Golden set generator
- [ ] Effect size computation
- [ ] Hit rate analysis
- [ ] Dose-response regression
- [ ] Sensitivity report

### Total Timeline: 5 weeks (25 working days)

---

## References

### Statistical Methods

1. **ICC (Intra-Class Correlation)**
   - Shrout, P. E., & Fleiss, J. L. (1979). Intraclass correlations: Uses in assessing rater reliability. *Psychological Bulletin*, 86(2), 420-428.
   - Koo, T. K., & Li, M. Y. (2016). A guideline of selecting and reporting intraclass correlation coefficients for reliability research. *Journal of Chiropractic Medicine*, 15(2), 155-163.

2. **Cohen's d (Effect Size)**
   - Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Hillsdale, NJ: Lawrence Erlbaum Associates.

3. **Correlation Analysis**
   - Spearman, C. (1904). The proof and measurement of association between two things. *The American Journal of Psychology*, 15(1), 72-101.

### Software Documentation

- **pingouin**: https://pingouin-stats.org/generated/pingouin.intraclass_corr.html
- **scipy.stats**: https://docs.scipy.org/doc/scipy/reference/stats.html
- **PIL/Pillow**: https://pillow.readthedocs.io/

---

## Appendix A: Subjective.csv Format Specification

**File**: `data/subjective.csv`

**Columns**:
1. `3D Object filename`: GLB filename with full metadata
2. `Visual Fidelity`: Human score [0.0, 1.0]

**Filename Pattern**:
```
{product_id}[_{variant}]__{algorithm}_{job_metadata}.glb
```

**Examples**:
```
188368__hunyuan3d_v2p1_single_N1_a_2025-08-17_v1_h00d888f7.glb
335888_curved-backrest_tripo3d_v2p5_multi_N3_A-B-C_2025-08-17_v1_h8a61ab22.glb
```

**Parsing Algorithm**:
```python
def parse_subjective_filename(filename: str) -> Dict:
    # Split on double underscore
    parts = filename.replace('.glb', '').split('__')

    # First part: product_id[_variant]
    product_part = parts[0]
    if '_' in product_part:
        product_id, variant = product_part.split('_', 1)
    else:
        product_id, variant = product_part, None

    # Second part: algorithm
    algorithm = parts[1] if len(parts) > 1 else "unknown"

    # Generate item_id (matches VFScore format)
    from vfscore.data_sources.utils import make_item_id
    item_id = make_item_id(product_id, variant)

    return {
        'product_id': product_id,
        'variant': variant,
        'item_id': item_id,
        'algorithm': algorithm
    }
```

**Dataset Statistics**:
- Total rows: 801
- Unique products: 94
- Score range: [0.000, 0.950]
- Mean score: 0.528
- Encoding: UTF-8-BOM

---

## Appendix B: Decision Rules for Research Publication

### Metric Thresholds (From Original Plan)

**A. Stability (Repeatability)**:
- ICC(1,k) ≥ 0.85: "Excellent" ✅ REQUIRED
- Median MAD ≤ 0.05: "Excellent stability" ✅ TARGET
- 95% CI half-width ≤ 0.02: "Converged" 📊 ANALYZE

**B. Human Agreement**:
- Spearman ρ ≥ 0.7: "Strong agreement" ✅ REQUIRED
- MAE ≤ 0.10: "Excellent" ✅ TARGET
- RMSE ≤ 0.15: "Good" 📊 ACCEPTABLE

**C. Sensitivity**:
- Cohen's d ≥ 0.8: "Large effect" ✅ EXPECTED
- Hit rate ≥ 0.80: "Good discrimination" ✅ TARGET
- Dose-response R² ≥ 0.6: "Moderate fit" 📊 ANALYZE

### Recommended Configuration Selection

Choose parameter setting where:
1. ICC ≥ 0.85 (repeatability)
2. JSON validity ≥ 98% (robustness)
3. Spearman ρ ≥ 0.7 (human agreement)
4. MAD ≤ 0.05 (stability)

**Multi-criteria scoring**:
```python
score = (
    weight_icc * (icc - 0.85) / 0.15 +           # Scale to [0, 1]
    weight_json * (validity - 0.98) / 0.02 +
    weight_human * (spearman - 0.7) / 0.3 +
    weight_mad * (0.05 - mad) / 0.05             # Inverted (lower is better)
)
```

---

**END OF IMPLEMENTATION PLAN**

---

**Approval Signature**:

User: ________________
Date: ________________

**Implementation Start Date**: TBD
**Target Completion**: 5 weeks from start
