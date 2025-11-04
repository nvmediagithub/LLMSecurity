from __future__ import annotations

from datetime import datetime
from typing import List

from ..domain.entities import AnalysisResult, UnifiedReport


class ReportGenerator:
    """Generates unified reports from analysis results."""

    def generate_report(self, analysis_result: AnalysisResult) -> UnifiedReport:
        """Generate a unified report from analysis results."""

        # Generate executive summary
        executive_summary = self._generate_executive_summary(analysis_result)

        # Generate security assessment
        security_assessment = self._generate_security_assessment(analysis_result)

        # Generate performance analysis
        performance_analysis = self._generate_performance_analysis(analysis_result)

        # Compile recommendations
        recommendations = analysis_result.recommendations.copy()

        return UnifiedReport(
            analysis_result=analysis_result,
            generated_at=datetime.now(),
            executive_summary=executive_summary,
            security_assessment=security_assessment,
            performance_analysis=performance_analysis,
            recommendations=recommendations,
        )

    def _generate_executive_summary(self, result: AnalysisResult) -> str:
        """Generate executive summary of the analysis."""

        lines = [
            "# Executive Summary",
            "",
            f"Analysis conducted on {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Key Metrics",
            f"- **Test Results**: {result.passed_tests}/{result.total_tests} passed ({result.test_pass_rate:.1f}%)",
            f"- **Attack Defense**: {result.blocked_attacks}/{result.total_attacks} attacks blocked ({result.attack_block_rate:.1f}%)",
            "",
            f"- **Defense Layers Analyzed**: {len(result.layer_metrics)}",
            f"- **Attack Categories Analyzed**: {len(result.attack_metrics)}",
            "",
        ]

        if result.vulnerabilities:
            lines.extend([
                "## Critical Findings",
                f"- **{len(result.vulnerabilities)}** vulnerabilities identified",
                "",
            ])
        else:
            lines.extend([
                "## Security Status",
                "- No critical vulnerabilities detected",
                "",
            ])

        # Add top recommendations
        if result.recommendations:
            lines.extend([
                "## Top Recommendations",
                *[f"- {rec}" for rec in result.recommendations[:3]],  # Top 3 recommendations
                "",
            ])

        return "\n".join(lines)

    def _generate_security_assessment(self, result: AnalysisResult) -> str:
        """Generate detailed security assessment."""

        lines = [
            "# Security Assessment",
            "",
        ]

        # Overall security posture
        overall_score = self._calculate_overall_security_score(result)
        lines.extend([
            f"## Overall Security Posture: {overall_score}/100",
            "",
        ])

        # Layer effectiveness
        if result.layer_metrics:
            lines.extend([
                "## Defense Layer Effectiveness",
                "",
                "| Layer | Effectiveness | False Positives | Block Rate |",
                "|-------|---------------|-----------------|------------|",
            ])

            for metric in sorted(result.layer_metrics, key=lambda x: x.effectiveness_score, reverse=True):
                lines.append(
                    f"| {metric.layer_id} | {metric.effectiveness_score:.1f}% | {metric.false_positives} | {metric.block_rate:.1f}% |"
                )

            lines.append("")

        # Attack analysis
        if result.attack_metrics:
            lines.extend([
                "## Attack Pattern Analysis",
                "",
                "| Category | Success Rate | Total Attempts | Successful |",
                "|----------|--------------|----------------|------------|",
            ])

            for metric in sorted(result.attack_metrics, key=lambda x: x.success_rate, reverse=True):
                lines.append(
                    f"| {metric.category} | {metric.success_rate:.1f}% | {metric.total_attempts} | {metric.successful_attempts} |"
                )

            lines.append("")

        # Vulnerabilities
        if result.vulnerabilities:
            lines.extend([
                "## Identified Vulnerabilities",
                "",
            ])
            for vuln in result.vulnerabilities:
                lines.append(f"- **{vuln}**")
            lines.append("")

        return "\n".join(lines)

    def _generate_performance_analysis(self, result: AnalysisResult) -> str:
        """Generate performance analysis section."""

        lines = [
            "# Performance Analysis",
            "",
        ]

        # Test performance
        if result.test_results:
            total_duration = sum((r.finished_at - r.started_at).total_seconds() * 1000 for r in result.test_results)
            avg_duration = total_duration / len(result.test_results)

            lines.extend([
                "## Test Suite Performance",
                f"- **Total Tests**: {len(result.test_results)}",
                f"- **Average Test Duration**: {avg_duration:.2f}ms",
                f"- **Total Duration**: {total_duration:.2f}ms",
                "",
            ])

        # Layer performance
        if result.layer_metrics:
            lines.extend([
                "## Defense Layer Performance",
                "",
                "| Layer | Avg Latency | Total Decisions |",
                "|-------|-------------|-----------------|",
            ])

            for metric in sorted(result.layer_metrics, key=lambda x: x.average_latency_ms, reverse=True):
                lines.append(
                    f"| {metric.layer_id} | {metric.average_latency_ms:.2f}ms | {metric.total_decisions} |"
                )

            lines.append("")

            # Performance insights
            slow_layers = [m for m in result.layer_metrics if m.average_latency_ms > 50]
            if slow_layers:
                lines.extend([
                    "### Performance Optimization Opportunities",
                    "",
                ])
                for layer in slow_layers[:5]:  # Top 5 slowest
                    lines.append(f"- **{layer.layer_id}**: {layer.average_latency_ms:.2f}ms average latency")
                lines.append("")

        return "\n".join(lines)

    def _calculate_overall_security_score(self, result: AnalysisResult) -> int:
        """Calculate overall security score (0-100)."""

        if not result.total_tests and not result.total_attacks:
            return 0

        score_components = []

        # Test pass rate (40% weight)
        if result.total_tests > 0:
            test_score = result.test_pass_rate
            score_components.append(test_score * 0.4)

        # Attack block rate (40% weight)
        if result.total_attacks > 0:
            attack_score = result.attack_block_rate
            score_components.append(attack_score * 0.4)

        # Layer effectiveness (20% weight)
        if result.layer_metrics:
            avg_effectiveness = sum(m.effectiveness_score for m in result.layer_metrics) / len(result.layer_metrics)
            layer_score = min(100, avg_effectiveness)  # Cap at 100%
            score_components.append(layer_score * 0.2)

        # False positive penalty
        fp_penalty = 0
        if result.layer_metrics:
            total_fp = sum(m.false_positives for m in result.layer_metrics)
            total_decisions = sum(m.total_decisions for m in result.layer_metrics)
            if total_decisions > 0:
                fp_rate = total_fp / total_decisions * 100
                fp_penalty = min(20, fp_rate * 0.5)  # Max 20 point penalty

        overall_score = sum(score_components) - fp_penalty
        return max(0, min(100, int(overall_score)))