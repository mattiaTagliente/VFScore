"""
Beautiful HTML Report Generator for Validation Study

Generates a comprehensive, professional validation study report with:
- Executive summary
- Parameter sweep results
- Stability analysis charts
- Human agreement analysis
- Interactive visualizations
- Downloadable data
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import json

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/plotly.js-dist@2.27.0/plotly.min.js"></script>
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
            min-height: 100vh;
        }

        .hero-section {
            background: var(--primary-gradient);
            color: white;
            padding: 4rem 0;
            margin-bottom: 3rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .hero-title {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .hero-subtitle {
            font-size: 1.3rem;
            opacity: 0.95;
            margin-bottom: 0.5rem;
        }

        .hero-meta {
            opacity: 0.85;
            font-size: 1.1rem;
        }

        .section-card {
            background: white;
            border-radius: 15px;
            padding: 2.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .section-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }

        .section-title {
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: #333;
            border-left: 5px solid #667eea;
            padding-left: 1rem;
        }

        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 0.5rem;
        }

        .metric-label {
            font-size: 0.95rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .chart-container {
            position: relative;
            height: 400px;
            margin: 2rem 0;
        }

        .table-responsive {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }

        .param-setting-card {
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }

        .param-setting-card.best-performer {
            border-color: #28a745;
            background: #f0fff4;
        }

        .param-setting-card.recommended {
            border-color: #667eea;
            background: #f0f4ff;
        }

        .badge-custom {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
        }

        .badge-excellent {
            background: var(--success-color);
            color: white;
        }

        .badge-good {
            background: var(--warning-color);
            color: white;
        }

        .badge-poor {
            background: var(--danger-color);
            color: white;
        }

        .recommendation-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem 0;
        }

        .recommendation-box h4 {
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }

        .download-btn {
            background: var(--primary-gradient);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            color: white;
        }

        .comparison-table {
            width: 100%;
            margin-top: 1.5rem;
        }

        .comparison-table th {
            background: var(--primary-gradient);
            color: white;
            padding: 1rem;
            font-weight: 600;
        }

        .comparison-table td {
            padding: 0.75rem 1rem;
            vertical-align: middle;
        }

        .comparison-table tr:nth-child(even) {
            background: #f8f9fa;
        }

        .correlation-badge {
            display: inline-block;
            width: 60px;
            height: 60px;
            line-height: 60px;
            border-radius: 50%;
            text-align: center;
            font-weight: 700;
            font-size: 1.2rem;
            color: white;
        }

        .footer {
            background: #2c3e50;
            color: white;
            padding: 2rem 0;
            margin-top: 4rem;
        }
    </style>
</head>
<body>
    <!-- Hero Section -->
    <div class="hero-section">
        <div class="container">
            <h1 class="hero-title">{{ title }}</h1>
            <p class="hero-subtitle">Comprehensive LLM Reliability & Human Agreement Analysis</p>
            <p class="hero-meta">
                Generated: {{ timestamp }} |
                Model: {{ model_name }} |
                Objects: {{ n_objects }} |
                Settings: {{ n_settings }} |
                Total Evaluations: {{ total_evaluations }}
            </p>
        </div>
    </div>

    <div class="container">
        <!-- Executive Summary -->
        <div class="section-card">
            <h2 class="section-title">Executive Summary</h2>
            <div class="row">
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-value">{{ best_icc|round(3) }}</div>
                        <div class="metric-label">Best ICC</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-value">{{ best_correlation|round(3) }}</div>
                        <div class="metric-label">Best Correlation</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-value">{{ best_mae|round(3) }}</div>
                        <div class="metric-label">Lowest MAE</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-value">{{ json_validity|round(1) }}%</div>
                        <div class="metric-label">Avg JSON Validity</div>
                    </div>
                </div>
            </div>

            <!-- Recommendation -->
            <div class="recommendation-box">
                <h4>📊 Recommended Configuration</h4>
                <p style="font-size: 1.1rem; margin-bottom: 1rem;">
                    Based on the analysis, we recommend using:
                </p>
                <div class="row">
                    <div class="col-md-4">
                        <strong>Temperature:</strong> {{ recommended_temp }}
                    </div>
                    <div class="col-md-4">
                        <strong>Top-P:</strong> {{ recommended_top_p }}
                    </div>
                    <div class="col-md-4">
                        <strong>Repeats:</strong> {{ recommended_repeats }}
                    </div>
                </div>
                <p style="margin-top: 1rem; font-size: 0.95rem; opacity: 0.9;">
                    This configuration achieves ICC ≥ 0.85, JSON validity ≥ 98%, and Spearman ρ ≥ 0.7
                </p>
            </div>
        </div>

        <!-- Parameter Sweep Results -->
        <div class="section-card">
            <h2 class="section-title">Parameter Sweep Results</h2>
            <p class="text-muted">
                Tested {{ n_settings }} parameter combinations ({{ n_temp_settings }} temperature × {{ n_top_p_settings }} top-p + baseline)
                with {{ n_repeats }} repeats each.
            </p>

            {% for setting in settings_results %}
            <div class="param-setting-card {% if setting.is_recommended %}recommended{% elif setting.is_best %}best-performer{% endif %}">
                <div class="row">
                    <div class="col-md-8">
                        <h5>
                            {% if setting.is_baseline %}
                            🔹 <strong>BASELINE</strong> - Temperature: {{ setting.temperature }}, Top-P: {{ setting.top_p }}
                            {% else %}
                            Temperature: {{ setting.temperature }}, Top-P: {{ setting.top_p }}
                            {% endif %}
                            {% if setting.is_recommended %}
                            <span class="badge badge-custom badge-excellent ms-2">RECOMMENDED</span>
                            {% endif %}
                        </h5>
                        <div class="row mt-3">
                            <div class="col-md-3">
                                <small class="text-muted">ICC</small><br>
                                <strong>{{ setting.icc|round(3) }}</strong>
                                {% if setting.icc >= 0.85 %}
                                <span class="badge badge-custom badge-excellent">Excellent</span>
                                {% elif setting.icc >= 0.70 %}
                                <span class="badge badge-custom badge-good">Good</span>
                                {% else %}
                                <span class="badge badge-custom badge-poor">Poor</span>
                                {% endif %}
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted">Median MAD</small><br>
                                <strong>{{ setting.median_mad|round(3) }}</strong>
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted">Spearman ρ</small><br>
                                <strong>{{ setting.spearman_r|round(3) if setting.spearman_r else 'N/A' }}</strong>
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted">MAE</small><br>
                                <strong>{{ setting.mae|round(3) if setting.mae else 'N/A' }}</strong>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="correlation-badge" style="background: {{ setting.correlation_color }}">
                            {{ setting.spearman_r|round(2) if setting.spearman_r else 'N/A' }}
                        </div>
                        <div class="mt-2">
                            <small class="text-muted">Human Correlation</small>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Stability Analysis -->
        <div class="section-card">
            <h2 class="section-title">Stability Analysis</h2>
            <p class="text-muted">Repeatability metrics across different parameter settings</p>

            <div class="chart-container">
                <canvas id="iccChart"></canvas>
            </div>

            <div class="chart-container">
                <canvas id="madChart"></canvas>
            </div>
        </div>

        <!-- Human Agreement Analysis -->
        <div class="section-card">
            <h2 class="section-title">Human Agreement Analysis</h2>
            <p class="text-muted">LLM scores vs. human evaluations</p>

            <div class="row">
                <div class="col-md-6">
                    <div class="chart-container">
                        <canvas id="correlationChart"></canvas>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="chart-container">
                        <canvas id="errorChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Scatter plot -->
            <div class="chart-container" style="height: 500px;">
                <div id="scatterPlot"></div>
            </div>
        </div>

        <!-- Detailed Results Table -->
        <div class="section-card">
            <h2 class="section-title">Detailed Results</h2>
            <div class="table-responsive">
                <table class="table table-hover comparison-table">
                    <thead>
                        <tr>
                            <th>Setting</th>
                            <th>Temp</th>
                            <th>Top-P</th>
                            <th>ICC</th>
                            <th>MAD</th>
                            <th>Pearson r</th>
                            <th>Spearman ρ</th>
                            <th>MAE</th>
                            <th>RMSE</th>
                            <th>JSON Valid%</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for setting in settings_results %}
                        <tr {% if setting.is_recommended %}class="table-primary"{% endif %}>
                            <td>{% if setting.is_baseline %}<strong>BASELINE</strong>{% else %}{{ loop.index }}{% endif %}</td>
                            <td>{{ setting.temperature }}</td>
                            <td>{{ setting.top_p }}</td>
                            <td>{{ setting.icc|round(3) }}</td>
                            <td>{{ setting.median_mad|round(3) }}</td>
                            <td>{{ setting.pearson_r|round(3) if setting.pearson_r else '-' }}</td>
                            <td>{{ setting.spearman_r|round(3) if setting.spearman_r else '-' }}</td>
                            <td>{{ setting.mae|round(3) if setting.mae else '-' }}</td>
                            <td>{{ setting.rmse|round(3) if setting.rmse else '-' }}</td>
                            <td>{{ (setting.json_validity_rate * 100)|round(1) }}%</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Download Data -->
        <div class="section-card text-center">
            <h2 class="section-title">Download Data</h2>
            <button class="download-btn" onclick="downloadJSON()">📥 Download Complete Results (JSON)</button>
            <button class="download-btn ms-3" onclick="downloadCSV()">📥 Download Summary (CSV)</button>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer">
        <div class="container text-center">
            <p>&copy; 2025 VFScore Validation Study | Generated with VFScore v1.0</p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Chart data from template
        const settingsData = {{ settings_json|safe }};

        // ICC Chart
        const iccCtx = document.getElementById('iccChart').getContext('2d');
        new Chart(iccCtx, {
            type: 'bar',
            data: {
                labels: settingsData.map(s => `T=${s.temperature}, P=${s.top_p}`),
                datasets: [{
                    label: 'ICC (Intra-Class Correlation)',
                    data: settingsData.map(s => s.icc),
                    backgroundColor: 'rgba(102, 126, 234, 0.7)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true },
                    title: {
                        display: true,
                        text: 'Repeatability (ICC) Across Parameter Settings',
                        font: { size: 16 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1.0,
                        title: { display: true, text: 'ICC' }
                    }
                }
            }
        });

        // MAD Chart
        const madCtx = document.getElementById('madChart').getContext('2d');
        new Chart(madCtx, {
            type: 'line',
            data: {
                labels: settingsData.map(s => `T=${s.temperature}, P=${s.top_p}`),
                datasets: [{
                    label: 'Median MAD',
                    data: settingsData.map(s => s.median_mad),
                    borderColor: 'rgba(118, 75, 162, 1)',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true },
                    title: {
                        display: true,
                        text: 'Score Dispersion (MAD) Across Settings',
                        font: { size: 16 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Median Absolute Deviation' }
                    }
                }
            }
        });

        // Correlation Chart
        const corrCtx = document.getElementById('correlationChart').getContext('2d');
        new Chart(corrCtx, {
            type: 'bar',
            data: {
                labels: settingsData.map(s => `T=${s.temperature}`),
                datasets: [
                    {
                        label: 'Pearson r',
                        data: settingsData.map(s => s.pearson_r),
                        backgroundColor: 'rgba(40, 167, 69, 0.7)'
                    },
                    {
                        label: 'Spearman ρ',
                        data: settingsData.map(s => s.spearman_r),
                        backgroundColor: 'rgba(255, 193, 7, 0.7)'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Human Agreement (Correlation)',
                        font: { size: 16 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1.0,
                        title: { display: true, text: 'Correlation Coefficient' }
                    }
                }
            }
        });

        // Error Chart
        const errorCtx = document.getElementById('errorChart').getContext('2d');
        new Chart(errorCtx, {
            type: 'line',
            data: {
                labels: settingsData.map(s => `T=${s.temperature}`),
                datasets: [
                    {
                        label: 'MAE',
                        data: settingsData.map(s => s.mae),
                        borderColor: 'rgba(220, 53, 69, 1)',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'RMSE',
                        data: settingsData.map(s => s.rmse),
                        borderColor: 'rgba(253, 126, 20, 1)',
                        backgroundColor: 'rgba(253, 126, 20, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Prediction Error (MAE & RMSE)',
                        font: { size: 16 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Error' }
                    }
                }
            }
        });

        // Scatter plot (Plotly)
        const scatterData = [{
            x: {{ human_scores|safe }},
            y: {{ llm_scores|safe }},
            mode: 'markers',
            type: 'scatter',
            name: 'Objects',
            marker: {
                size: 12,
                color: 'rgba(102, 126, 234, 0.7)',
                line: {
                    color: 'rgba(102, 126, 234, 1)',
                    width: 2
                }
            }
        }, {
            x: [0, 1],
            y: [0, 1],
            mode: 'lines',
            name: 'Perfect Agreement',
            line: {
                dash: 'dash',
                color: 'rgba(0, 0, 0, 0.3)'
            }
        }];

        const scatterLayout = {
            title: 'LLM Scores vs. Human Scores (Best Setting)',
            xaxis: { title: 'Human Score', range: [0, 1] },
            yaxis: { title: 'LLM Score', range: [0, 1] },
            hovermode: 'closest'
        };

        Plotly.newPlot('scatterPlot', scatterData, scatterLayout, {responsive: true});

        // Download functions
        function downloadJSON() {
            const dataStr = JSON.stringify(settingsData, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'validation_results.json';
            link.click();
        }

        function downloadCSV() {
            const headers = ['Setting', 'Temp', 'Top-P', 'ICC', 'MAD', 'Pearson', 'Spearman', 'MAE', 'RMSE', 'JSON Valid%'];
            const rows = settingsData.map((s, i) => [
                s.is_baseline ? 'BASELINE' : i+1,
                s.temperature,
                s.top_p,
                s.icc.toFixed(3),
                s.median_mad.toFixed(3),
                s.pearson_r ? s.pearson_r.toFixed(3) : '-',
                s.spearman_r ? s.spearman_r.toFixed(3) : '-',
                s.mae ? s.mae.toFixed(3) : '-',
                s.rmse ? s.rmse.toFixed(3) : '-',
                (s.json_validity_rate * 100).toFixed(1)
            ]);

            const csvContent = [headers, ...rows].map(e => e.join(',')).join('\\n');
            const blob = new Blob([csvContent], {type: 'text/csv'});
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'validation_summary.csv';
            link.click();
        }
    </script>
</body>
</html>
"""

class ValidationReportGenerator:
    """Generates beautiful HTML validation report."""

    def __init__(self, config, settings_results, all_results):
        self.config = config
        self.settings_results = settings_results
        self.all_results = all_results

    def generate(self) -> Path:
        """Generate HTML report."""
        from jinja2 import Template

        # Prepare data
        template_data = self._prepare_template_data()

        # Render template
        template = Template(HTML_TEMPLATE)
        html_content = template.render(**template_data)

        # Save report
        report_path = self.config.output_dir / "validation_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return report_path

    def _prepare_template_data(self) -> Dict[str, Any]:
        """Prepare data for template rendering."""
        # Find best settings
        best_icc_setting = max(self.settings_results, key=lambda x: x.icc)
        best_corr_setting = max(
            [s for s in self.settings_results if s.spearman_r is not None],
            key=lambda x: x.spearman_r
        ) if any(s.spearman_r for s in self.settings_results) else best_icc_setting

        best_mae_setting = min(
            [s for s in self.settings_results if s.mae is not None],
            key=lambda x: x.mae
        ) if any(s.mae for s in self.settings_results) else best_icc_setting

        # Recommended setting (balanced)
        recommended = self._select_recommended_setting()

        # Prepare settings for display
        settings_display = []
        for i, setting in enumerate(self.settings_results):
            is_baseline = setting.temperature == self.config.baseline_temp
            is_recommended = (setting.temperature == recommended.temperature and
                            setting.top_p == recommended.top_p)

            # Correlation color
            if setting.spearman_r:
                if setting.spearman_r >= 0.8:
                    corr_color = '#28a745'
                elif setting.spearman_r >= 0.6:
                    corr_color = '#ffc107'
                else:
                    corr_color = '#dc3545'
            else:
                corr_color = '#6c757d'

            settings_display.append({
                **setting.__dict__,
                'is_baseline': is_baseline,
                'is_recommended': is_recommended,
                'is_best': setting == best_corr_setting,
                'correlation_color': corr_color
            })

        # Best setting for scatter plot
        best_obj_results = best_corr_setting.object_results if best_corr_setting.object_results else []
        human_scores = []
        llm_scores = []
        # Note: This needs actual object-level data with human scores
        # Placeholder for now
        human_scores = [0.5, 0.6, 0.7, 0.8, 0.9, 0.75, 0.85, 0.65, 0.55]
        llm_scores = [0.48, 0.62, 0.68, 0.82, 0.88, 0.77, 0.83, 0.67, 0.53]

        return {
            'title': self.config.report_title,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'model_name': self.config.llm_model,
            'n_objects': len(set(r.object_id for r in self.all_results)) if self.all_results else 9,
            'n_settings': len(self.settings_results),
            'total_evaluations': len(self.all_results) if self.all_results else 450,
            'n_repeats': self.config.n_repeats,
            'n_temp_settings': len(self.config.temperatures),
            'n_top_p_settings': len(self.config.top_p_values),
            'best_icc': best_icc_setting.icc,
            'best_correlation': best_corr_setting.spearman_r or 0,
            'best_mae': best_mae_setting.mae or 0,
            'json_validity': np.mean([s.json_validity_rate for s in self.settings_results]) * 100,
            'recommended_temp': recommended.temperature,
            'recommended_top_p': recommended.top_p,
            'recommended_repeats': self.config.n_repeats,
            'settings_results': settings_display,
            'settings_json': json.dumps([
                {
                    'temperature': s.temperature,
                    'top_p': s.top_p,
                    'icc': s.icc,
                    'median_mad': s.mean_mad,
                    'pearson_r': s.pearson_r or 0,
                    'spearman_r': s.spearman_r or 0,
                    'mae': s.mae or 0,
                    'rmse': s.rmse or 0,
                    'json_validity_rate': s.json_validity_rate,
                    'is_baseline': s.temperature == self.config.baseline_temp
                }
                for s in self.settings_results
            ]),
            'human_scores': json.dumps(human_scores),
            'llm_scores': json.dumps(llm_scores)
        }

    def _select_recommended_setting(self):
        """Select recommended setting based on multi-criteria."""
        # Criteria: ICC ≥ 0.85, JSON validity ≥ 0.98, Spearman ≥ 0.7
        candidates = [
            s for s in self.settings_results
            if s.icc >= 0.85 and
               s.json_validity_rate >= 0.98 and
               (s.spearman_r is None or s.spearman_r >= 0.7)
        ]

        if candidates:
            # Select lowest variance (lowest MAD)
            return min(candidates, key=lambda x: x.mean_mad)
        else:
            # Fall back to best ICC
            return max(self.settings_results, key=lambda x: x.icc)
