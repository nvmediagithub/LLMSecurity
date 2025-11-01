from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ...testing.domain.results import TestRunResult
from ..application.aggregator import MetricsAggregator


def write_html(path: Path, runs: Iterable[TestRunResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    runs = list(runs)
    summary = MetricsAggregator().summarize(runs)
    rows = "\n".join(
        f"<tr><td>{run.test.id}</td><td>{run.test.name}</td><td>{run.test.category}</td><td>{'PASS' if run.passed else 'FAIL'}</td><td>{run.defense_decision}</td><td>{run.evaluation.reason}</td></tr>"
        for run in runs
    )
    layer_rows = "\n".join(f"<li>{layer}: {count}</li>" for layer, count in summary.by_layer.items())
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>LLM Security Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 1.5rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; }}
    th {{ background-color: #f4f4f4; }}
    .pass {{ color: green; }}
    .fail {{ color: red; }}
  </style>
</head>
<body>
  <h1>Отчёт по тестам prompt-инъекций</h1>
  <p>Всего тестов: {summary.total}, пройдено: {summary.passed}, провалено: {summary.failed}, Pass%: {summary.pass_rate}</p>
  <h2>Сработавшие слои</h2>
  <ul>{layer_rows}</ul>
  <h2>Результаты</h2>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>Название</th>
        <th>Категория</th>
        <th>Статус</th>
        <th>Защита</th>
        <th>Причина</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>"""
    path.write_text(html, encoding="utf-8")

