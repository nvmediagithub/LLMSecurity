from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Optional

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

    run_parser = subparsers.add_parser("run", help="Запустить тесты для выбранного профиля защиты")
    run_parser.add_argument("--profile", default="strict_demo", help="ID профиля защиты")
    run_parser.add_argument("--categories", nargs="*", help="Список категорий тестов")
    run_parser.add_argument("--connection", default="dummy", help="ID подключения к LLM из config/llm_connections.yaml")
    run_parser.add_argument("--export-json", type=Path, help="Путь для JSON-отчета")
    run_parser.add_argument("--export-csv", type=Path, help="Путь для CSV-отчета")
    run_parser.add_argument("--export-html", type=Path, help="Путь для HTML-отчета")
    run_parser.add_argument("--ab", action="store_true", help="Выполнить A/B прогон (baseline и профиль)")

    subparsers.add_parser("connections", help="Показать доступные подключения к LLM")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "connections":
        service = TestSuiteService()
        _print_connections(service)
        return

    if args.command == "run":
        service = TestSuiteService(default_connection=args.connection)
        if args.ab:
            result = service.run_ab(
                args.profile,
                categories=args.categories,
                connection_id=args.connection,
            )
            _print_line(f"Baseline Pass%: {result.baseline.metrics.pass_rate}")
            _print_line(f"{args.profile} Pass%: {result.protected.metrics.pass_rate}")
            _print_line(f"Delta Pass%: {result.delta_pass_rate}")
            runs = result.protected.runs
        else:
            suite = service.run_suite(
                args.profile,
                categories=args.categories,
                connection_id=args.connection,
            )
            runs = suite.runs
            _print_suite(suite.profile.id, suite.runs, suite.metrics.pass_rate, args.connection)

        if args.export_json:
            write_json(args.export_json, runs)
            _print_line(f"JSON saved to {args.export_json}")
        if args.export_csv:
            write_csv(args.export_csv, runs)
            _print_line(f"CSV saved to {args.export_csv}")
        if args.export_html:
            write_html(args.export_html, runs)
            _print_line(f"HTML saved to {args.export_html}")


def _print_suite(profile_id: str, runs, pass_rate: float, connection_id: Optional[str]) -> None:
    title = f"Results for profile: {profile_id} (Pass%={pass_rate}"
    if connection_id:
        title += f", connection={connection_id}"
    title += ")"

    if console and Table:
        table = Table(title=title)
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
        _print_line(title)
        for run in runs:
            status = "PASS" if run.passed else "FAIL"
            _print_line(f"- {run.test.id} [{run.test.category}] {status} ({run.defense_decision}) {run.evaluation.reason}")


def _print_connections(service: TestSuiteService) -> None:
    connections = service.list_connections()
    if not connections:
        _print_line("No connections configured (config/llm_connections.yaml).")
        return
    if console and Table:
        table = Table(title="Available LLM connections")
        table.add_column("ID")
        table.add_column("Provider")
        table.add_column("Description")
        for info in connections:
            table.add_row(info.id, info.provider, info.description)
        console.print(table)
    else:
        _print_line("Available LLM connections:")
        for info in connections:
            _print_line(f"- {info.id} ({info.provider}): {info.description}")


def _print_line(message: str) -> None:
    if console:
        console.print(message)
    else:
        print(message)


if __name__ == "__main__":
    main()

