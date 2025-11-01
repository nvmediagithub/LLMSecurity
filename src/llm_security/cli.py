from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Optional

from .features.models.infrastructure.dummy import DummyModelClient
from .features.reporting.infrastructure.csv_reporter import write_csv
from .features.reporting.infrastructure.html_reporter import write_html
from .features.reporting.infrastructure.json_reporter import write_json
from .features.testing.application.service import TestSuiteService

try:  # pragma: no cover - graceful degradation
    from rich.console import Console
    from rich.table import Table
except ImportError:  # pragma: no cover
    Console = None
    Table = None


console = Console() if Console else None


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="LLM Security Lab CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Запустить тесты для профиля защиты")
    run_parser.add_argument("--profile", default="strict_demo", help="ID профиля защиты")
    run_parser.add_argument("--categories", nargs="*", help="Список категорий тестов")
    run_parser.add_argument("--export-json", type=Path, help="Путь для JSON отчёта")
    run_parser.add_argument("--export-csv", type=Path, help="Путь для CSV отчёта")
    run_parser.add_argument("--export-html", type=Path, help="Путь для HTML отчёта")
    run_parser.add_argument("--ab", action="store_true", help="Выполнить A/B прогон (baseline и профиль)")

    args = parser.parse_args(list(argv) if argv is not None else None)

    service = TestSuiteService(model_client=DummyModelClient())

    if args.command == "run":
        if args.ab:
            result = service.run_ab(args.profile, categories=args.categories)
            _print_line(f"Baseline Pass%: {result.baseline.metrics.pass_rate}")
            _print_line(f"{args.profile} Pass%: {result.protected.metrics.pass_rate}")
            _print_line(f"Δ Pass%: {result.delta_pass_rate}")
            runs = result.protected.runs
        else:
            suite = service.run_suite(args.profile, categories=args.categories)
            runs = suite.runs
            _print_suite(suite.profile.id, suite.runs, suite.metrics.pass_rate)

        if args.export_json:
            write_json(args.export_json, runs)
            _print_line(f"JSON saved to {args.export_json}")
        if args.export_csv:
            write_csv(args.export_csv, runs)
            _print_line(f"CSV saved to {args.export_csv}")
        if args.export_html:
            write_html(args.export_html, runs)
            _print_line(f"HTML saved to {args.export_html}")


def _print_suite(profile_id: str, runs, pass_rate: float) -> None:
    if console and Table:
        table = Table(title=f"Results for profile: {profile_id} (Pass%={pass_rate})")
        table.add_column("ID")
        table.add_column("Категория")
        table.add_column("Статус")
        table.add_column("Защита")
        table.add_column("Причина")
        for run in runs:
            status = "[green]PASS[/green]" if run.passed else "[red]FAIL[/red]"
            table.add_row(run.test.id, run.test.category, status, run.defense_decision, run.evaluation.reason)
        console.print(table)
    else:
        _print_line(f"Results for profile: {profile_id} (Pass%={pass_rate})")
        for run in runs:
            status = "PASS" if run.passed else "FAIL"
            _print_line(f"- {run.test.id} [{run.test.category}] {status} ({run.defense_decision}) {run.evaluation.reason}")


def _print_line(message: str) -> None:
    if console:
        console.print(message)
    else:
        print(message)


if __name__ == "__main__":
    main()
