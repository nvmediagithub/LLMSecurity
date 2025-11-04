from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from ..domain.entities import UnifiedReport


class IReportExporter(ABC):
    """Interface for exporting unified reports."""

    @abstractmethod
    def export(self, report: UnifiedReport, output_path: str) -> None:
        """Export report to specified path."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for this exporter."""
        pass


class CSVReportExporter(IReportExporter):
    """Exports reports in CSV format."""

    @property
    def file_extension(self) -> str:
        return ".csv"

    def export(self, report: UnifiedReport, output_path: str) -> None:
        """Export report as CSV."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(['Section', 'Metric', 'Value'])

            # Executive summary
            writer.writerow(['Executive Summary', 'Generated At', report.generated_at.isoformat()])
            writer.writerow(['Executive Summary', 'Analysis Timestamp', report.analysis_result.timestamp.isoformat()])
            writer.writerow(['Executive Summary', 'Test Pass Rate', f"{report.analysis_result.test_pass_rate:.2f}%"])
            writer.writerow(['Executive Summary', 'Attack Block Rate', f"{report.analysis_result.attack_block_rate:.2f}%"])

            # Layer metrics
            for metric in report.analysis_result.layer_metrics:
                writer.writerow(['Layer Metrics', f"{metric.layer_id} - Effectiveness", f"{metric.effectiveness_score:.2f}%"])
                writer.writerow(['Layer Metrics', f"{metric.layer_id} - False Positives", str(metric.false_positives)])
                writer.writerow(['Layer Metrics', f"{metric.layer_id} - Block Rate", f"{metric.block_rate:.2f}%"])
                writer.writerow(['Layer Metrics', f"{metric.layer_id} - Avg Latency", f"{metric.average_latency_ms:.2f}ms"])

            # Attack metrics
            for metric in report.analysis_result.attack_metrics:
                writer.writerow(['Attack Metrics', f"{metric.category} - Success Rate", f"{metric.success_rate:.2f}%"])
                writer.writerow(['Attack Metrics', f"{metric.category} - Total Attempts", str(metric.total_attempts)])
                writer.writerow(['Attack Metrics', f"{metric.category} - Blocked", str(metric.blocked_attempts)])

            # Vulnerabilities
            for i, vuln in enumerate(report.analysis_result.vulnerabilities):
                writer.writerow(['Vulnerabilities', f'Vulnerability {i+1}', vuln])

            # Recommendations
            for i, rec in enumerate(report.recommendations):
                writer.writerow(['Recommendations', f'Recommendation {i+1}', rec])


class JSONReportExporter(IReportExporter):
    """Exports reports in JSON format."""

    @property
    def file_extension(self) -> str:
        return ".json"

    def export(self, report: UnifiedReport, output_path: str) -> None:
        """Export report as JSON."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert report to dictionary
        report_data = {
            "generated_at": report.generated_at.isoformat(),
            "analysis_result": {
                "timestamp": report.analysis_result.timestamp.isoformat(),
                "total_tests": report.analysis_result.total_tests,
                "passed_tests": report.analysis_result.passed_tests,
                "failed_tests": report.analysis_result.failed_tests,
                "total_attacks": report.analysis_result.total_attacks,
                "blocked_attacks": report.analysis_result.blocked_attacks,
                "test_pass_rate": report.analysis_result.test_pass_rate,
                "attack_block_rate": report.analysis_result.attack_block_rate,
                "layer_metrics": [
                    {
                        "layer_id": m.layer_id,
                        "blocks_count": m.blocks_count,
                        "rewrites_count": m.rewrites_count,
                        "escalates_count": m.escalates_count,
                        "allows_count": m.allows_count,
                        "false_positives": m.false_positives,
                        "average_latency_ms": m.average_latency_ms,
                        "effectiveness_score": m.effectiveness_score,
                        "total_decisions": m.total_decisions,
                        "block_rate": m.block_rate,
                    }
                    for m in report.analysis_result.layer_metrics
                ],
                "attack_metrics": [
                    {
                        "category": m.category,
                        "total_attempts": m.total_attempts,
                        "successful_attempts": m.successful_attempts,
                        "blocked_attempts": m.blocked_attempts,
                        "success_rate": m.success_rate,
                        "block_rate": m.block_rate,
                        "pattern_distribution": m.pattern_distribution,
                        "average_complexity": m.average_complexity,
                    }
                    for m in report.analysis_result.attack_metrics
                ],
                "vulnerabilities": report.analysis_result.vulnerabilities,
                "recommendations": report.analysis_result.recommendations,
            },
            "executive_summary": report.executive_summary,
            "security_assessment": report.security_assessment,
            "performance_analysis": report.performance_analysis,
            "recommendations": report.recommendations,
            "export_formats": {
                "csv": report.supports_csv,
                "json": report.supports_json,
                "html": report.supports_html,
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)


class HTMLReportExporter(IReportExporter):
    """Exports reports in HTML format."""

    @property
    def file_extension(self) -> str:
        return ".html"

    def export(self, report: UnifiedReport, output_path: str) -> None:
        """Export report as HTML."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        html_content = self._generate_html(report)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_html(self, report: UnifiedReport) -> str:
        """Generate HTML content for the report."""

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLMSecurity Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .vulnerability {{
            background: #fee;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .recommendation {{
            background: #efe;
            border-left: 4px solid #27ae60;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .status-good {{ color: #27ae60; }}
        .status-warning {{ color: #f39c12; }}
        .status-bad {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 LLMSecurity Analysis Report</h1>
        <p>Generated on {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>

    <div class="metric-grid">
        <div class="metric-card">
            <h3>Test Pass Rate</h3>
            <div class="metric-value {'status-good' if report.analysis_result.test_pass_rate >= 80 else 'status-warning' if report.analysis_result.test_pass_rate >= 60 else 'status-bad'}">
                {report.analysis_result.test_pass_rate:.1f}%
            </div>
        </div>
        <div class="metric-card">
            <h3>Attack Block Rate</h3>
            <div class="metric-value {'status-good' if report.analysis_result.attack_block_rate >= 80 else 'status-warning' if report.analysis_result.attack_block_rate >= 60 else 'status-bad'}">
                {report.analysis_result.attack_block_rate:.1f}%
            </div>
        </div>
        <div class="metric-card">
            <h3>Total Tests</h3>
            <div class="metric-value">{report.analysis_result.total_tests}</div>
        </div>
        <div class="metric-card">
            <h3>Total Attacks</h3>
            <div class="metric-value">{report.analysis_result.total_attacks}</div>
        </div>
    </div>

    <div class="section">
        <h2>📊 Executive Summary</h2>
        <pre style="white-space: pre-wrap; font-family: inherit;">{report.executive_summary}</pre>
    </div>

    {self._generate_layer_metrics_html(report)}

    {self._generate_attack_metrics_html(report)}

    {self._generate_vulnerabilities_html(report)}

    {self._generate_recommendations_html(report)}

    <div class="section">
        <h2>📈 Performance Analysis</h2>
        <pre style="white-space: pre-wrap; font-family: inherit;">{report.performance_analysis}</pre>
    </div>

    <div class="section">
        <h2>🔍 Security Assessment</h2>
        <pre style="white-space: pre-wrap; font-family: inherit;">{report.security_assessment}</pre>
    </div>
</body>
</html>
"""

    def _generate_layer_metrics_html(self, report: UnifiedReport) -> str:
        """Generate HTML for layer metrics."""
        if not report.analysis_result.layer_metrics:
            return ""

        rows = ""
        for metric in report.analysis_result.layer_metrics:
            rows += f"""
            <tr>
                <td>{metric.layer_id}</td>
                <td>{metric.effectiveness_score:.1f}%</td>
                <td>{metric.false_positives}</td>
                <td>{metric.block_rate:.1f}%</td>
                <td>{metric.average_latency_ms:.2f}ms</td>
            </tr>
            """

        return f"""
        <div class="section">
            <h2>🛡️ Defense Layer Performance</h2>
            <table>
                <thead>
                    <tr>
                        <th>Layer</th>
                        <th>Effectiveness</th>
                        <th>False Positives</th>
                        <th>Block Rate</th>
                        <th>Avg Latency</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    def _generate_attack_metrics_html(self, report: UnifiedReport) -> str:
        """Generate HTML for attack metrics."""
        if not report.analysis_result.attack_metrics:
            return ""

        rows = ""
        for metric in report.analysis_result.attack_metrics:
            rows += f"""
            <tr>
                <td>{metric.category}</td>
                <td>{metric.success_rate:.1f}%</td>
                <td>{metric.total_attempts}</td>
                <td>{metric.successful_attempts}</td>
                <td>{metric.blocked_attempts}</td>
            </tr>
            """

        return f"""
        <div class="section">
            <h2>⚔️ Attack Pattern Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Success Rate</th>
                        <th>Total Attempts</th>
                        <th>Successful</th>
                        <th>Blocked</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    def _generate_vulnerabilities_html(self, report: UnifiedReport) -> str:
        """Generate HTML for vulnerabilities."""
        if not report.analysis_result.vulnerabilities:
            return '<div class="section"><h2>✅ Vulnerabilities</h2><p>No critical vulnerabilities identified.</p></div>'

        items = "".join(f'<div class="vulnerability">{vuln}</div>' for vuln in report.analysis_result.vulnerabilities)

        return f"""
        <div class="section">
            <h2>🚨 Identified Vulnerabilities</h2>
            {items}
        </div>
        """

    def _generate_recommendations_html(self, report: UnifiedReport) -> str:
        """Generate HTML for recommendations."""
        if not report.recommendations:
            return ""

        items = "".join(f'<div class="recommendation">{rec}</div>' for rec in report.recommendations)

        return f"""
        <div class="section">
            <h2>💡 Recommendations</h2>
            {items}
        </div>
        """