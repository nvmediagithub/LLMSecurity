"""Пример запуска A/B прогона без GUI."""

from pathlib import Path

from llm_security.features.testing.application.service import TestSuiteService
from llm_security.features.reporting.infrastructure.html_reporter import write_html


def main() -> None:
    service = TestSuiteService(default_connection="dummy")
    result = service.run_ab("strict_demo", connection_id="dummy")
    print(f"Baseline pass%: {result.baseline.metrics.pass_rate}")
    print(f"Protected pass%: {result.protected.metrics.pass_rate}")
    print(f"Delta pass%: {result.delta_pass_rate}")

    report_path = Path("reports") / "demo_ab.html"
    write_html(report_path, result.protected.runs)
    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()

