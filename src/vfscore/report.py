"""HTML report generation with thumbnails and scores."""

import base64
import json
from pathlib import Path
from typing import Dict, List

from jinja2 import Template
from rich.console import Console

from vfscore.config import Config

console = Console()


def encode_image_base64(image_path: Path) -> str:
    """Encode image as base64 for embedding in HTML."""
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


def load_results(results_path: Path) -> List[Dict]:
    """Load aggregated results from JSONL."""
    results = []
    with open(results_path, "r", encoding="utf-8") as f:
        for line in f:
            results.append(json.loads(line))
    return results


def get_confidence_color(confidence: float) -> str:
    """Get color for confidence badge."""
    if confidence >= 0.8:
        return "success"
    elif confidence >= 0.6:
        return "warning"
    else:
        return "danger"


def get_score_color(score: float) -> str:
    """Get color for score badge."""
    if score >= 80:
        return "success"
    elif score >= 60:
        return "primary"
    elif score >= 40:
        return "warning"
    else:
        return "danger"


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VFScore Report - Visual Fidelity Scoring</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }
        .item-card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        .image-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        .image-grid img {
            width: 100%;
            height: auto;
            border-radius: 4px;
            border: 2px solid #dee2e6;
        }
        .candidate-image {
            border: 3px solid #667eea !important;
        }
        .subscore-bar {
            height: 24px;
            background-color: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }
        .subscore-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }
        .score-circle {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            font-weight: bold;
            color: white;
            margin: 0 auto;
        }
        .rationale {
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 1rem;
            margin-top: 1rem;
            border-radius: 4px;
        }
        .stats-card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1 class="display-4">VFScore Report</h1>
            <p class="lead">Visual Fidelity Scoring for 3D Generated Objects</p>
        </div>
    </div>

    <div class="container">
        <!-- Summary Statistics -->
        <div class="stats-card">
            <h2 class="mb-3">Summary Statistics</h2>
            <div class="row text-center">
                <div class="col-md-3">
                    <h3 class="text-primary">{{ summary.total_items }}</h3>
                    <p class="text-muted">Total Items</p>
                </div>
                <div class="col-md-3">
                    <h3 class="text-success">{{ "%.1f"|format(summary.mean_score) }}</h3>
                    <p class="text-muted">Mean Score</p>
                </div>
                <div class="col-md-3">
                    <h3 class="text-info">{{ "%.1f"|format(summary.median_score) }}</h3>
                    <p class="text-muted">Median Score</p>
                </div>
                <div class="col-md-3">
                    <h3 class="text-warning">{{ "%.2f"|format(summary.mean_confidence) }}</h3>
                    <p class="text-muted">Mean Confidence</p>
                </div>
            </div>
        </div>

        <!-- Individual Items -->
        {% for item in items %}
        <div class="item-card">
            <div class="row">
                <div class="col-md-8">
                    <h3>Item: {{ item.item_id }}</h3>
                    <p class="text-muted">
                        {{ item.l1 }} → {{ item.l2 }} → {{ item.l3 }} 
                        <span class="badge bg-secondary">{{ item.n_gt }} GT images</span>
                    </p>

                    <!-- Images -->
                    <h5 class="mt-3">Ground Truth Images</h5>
                    <div class="image-grid">
                        {% for gt_img in item.gt_images %}
                        <img src="data:image/png;base64,{{ gt_img }}" alt="GT">
                        {% endfor %}
                    </div>

                    <h5 class="mt-3">Candidate</h5>
                    <div class="image-grid">
                        <img src="data:image/png;base64,{{ item.cand_image }}" alt="Candidate" class="candidate-image">
                    </div>
                </div>

                <div class="col-md-4">
                    <!-- Score -->
                    <div class="score-circle bg-{{ item.score_color }}">
                        {{ item.final_score }}
                    </div>
                    <p class="text-center mt-2">
                        <span class="badge bg-{{ item.conf_color }}">
                            Confidence: {{ "%.2f"|format(item.confidence) }}
                        </span>
                    </p>

                    <!-- Model Scores -->
                    {% if item.model_scores %}
                    <h6 class="mt-3">Model Scores</h6>
                    <ul class="list-unstyled">
                        {% for model, score in item.model_scores.items() %}
                        <li><strong>{{ model }}:</strong> {{ score }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}

                    <!-- Subscores -->
                    <h6 class="mt-3">Subscores</h6>
                    {% for dim, score in item.subscores.items() %}
                    <div>
                        <small>{{ dim.replace('_', ' ').title() }}: {{ score }}</small>
                        <div class="subscore-bar">
                            <div class="subscore-fill" style="width: {{ score }}%"></div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Rationale -->
            {% if item.rationale %}
            <div class="rationale">
                <h6>Assessment Rationale</h6>
                <ul>
                    {% for point in item.rationale %}
                    <li>{{ point }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        {% endfor %}

        <footer class="text-center text-muted py-4">
            <p>Generated by VFScore v0.1.0</p>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


def run_report(config: Config) -> Path:
    """Generate HTML report."""
    
    # Load results
    results_path = config.paths.out_dir / "results" / "per_item.jsonl"
    
    if not results_path.exists():
        raise FileNotFoundError(f"Results not found: {results_path}. Run 'vfscore aggregate' first.")
    
    results = load_results(results_path)
    
    console.print(f"\n[bold]Generating report for {len(results)} items...[/bold]")
    
    # Prepare data for template
    items_data = []
    
    labels_dir = config.paths.out_dir / "labels"
    
    for result in results:
        item_id = result["item_id"]
        
        # Load images
        item_labels_dir = labels_dir / item_id
        
        gt_images = []
        for gt_file in sorted(item_labels_dir.glob("gt_*_labeled.png")):
            gt_images.append(encode_image_base64(gt_file))
        
        cand_file = item_labels_dir / "candidate_labeled.png"
        cand_image = encode_image_base64(cand_file) if cand_file.exists() else ""
        
        # Get first model's rationale
        rationale = []
        if result.get("scores"):
            first_model = list(result["scores"].keys())[0]
            llm_result_dir = config.paths.out_dir / "llm_calls" / first_model / item_id
            rep_file = llm_result_dir / "rep_2.json"  # Use middle repeat
            
            if rep_file.exists():
                with open(rep_file, "r", encoding="utf-8") as f:
                    rep_data = json.load(f)
                    rationale = rep_data.get("rationale", [])
        
        # Get subscores (from first model's median)
        subscores = {}
        if result.get("scores"):
            first_model = list(result["scores"].keys())[0]
            subscores = result["scores"][first_model].get("subscores_median", {})
        
        # Model scores
        model_scores = {
            model: data["median"]
            for model, data in result.get("scores", {}).items()
        }
        
        items_data.append({
            "item_id": item_id,
            "l1": result.get("l1", ""),
            "l2": result.get("l2", ""),
            "l3": result.get("l3", ""),
            "n_gt": result.get("n_gt", 0),
            "final_score": result["final_score"],
            "confidence": result["confidence"],
            "score_color": get_score_color(result["final_score"]),
            "conf_color": get_confidence_color(result["confidence"]),
            "gt_images": gt_images,
            "cand_image": cand_image,
            "subscores": subscores,
            "model_scores": model_scores,
            "rationale": rationale,
        })
    
    # Sort by score descending
    items_data.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Calculate summary statistics
    import numpy as np
    scores = [r["final_score"] for r in results]
    confidences = [r["confidence"] for r in results]
    
    summary = {
        "total_items": len(results),
        "mean_score": np.mean(scores),
        "median_score": np.median(scores),
        "mean_confidence": np.mean(confidences),
    }
    
    # Render template
    template = Template(HTML_TEMPLATE)
    html = template.render(items=items_data, summary=summary)
    
    # Save report
    report_dir = config.paths.out_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = report_dir / "index.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    console.print(f"[green]Report saved: {report_path}[/green]")
    
    return report_path


if __name__ == "__main__":
    from vfscore.config import get_config
    
    config = get_config()
    run_report(config)
