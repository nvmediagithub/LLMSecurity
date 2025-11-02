import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.llm_security.features.reporting.application.aggregator import MetricsAggregator, MetricsSummary
from src.llm_security.features.reporting.infrastructure.csv_reporter import write_csv
from src.llm_security.features.reporting.infrastructure.json_reporter import write_json
from src.llm_security.features.reporting.infrastructure.html_reporter import write_html
from src.llm_security.features.testing.domain.models import PassCriteria, PromptTest
from src.llm_security.features.testing.domain.results import TestRunResult, LayerLog
from datetime import datetime


class TestMetricsAggregator:
    def test_summarize_empty_runs(self):
        aggregator = MetricsAggregator()
        summary = aggregator.summarize([])
        assert summary.total == 0
        assert summary.passed == 0
        assert summary.failed == 0
        assert summary.pass_rate == 0.0
        assert summary.by_category == {}
        assert summary.by_layer == {}
        assert summary.false_positives == 0

    def test_summarize_all_passed(self):
        aggregator = MetricsAggregator()

        # Create mock runs
        run1 = Mock(spec=TestRunResult)
        run1.passed = True
        run1.test.category = "injection"
        run1.defense_logs_before = [Mock(layer_id="L1", decision="block")]
        run1.defense_logs_after = []

        run2 = Mock(spec=TestRunResult)
        run2.passed = True
        run2.test.category = "injection"
        run2.defense_logs_before = []
        run2.defense_logs_after = [Mock(layer_id="L2", decision="rewrite")]

        summary = aggregator.summarize([run1, run2])

        assert summary.total == 2
        assert summary.passed == 2
        assert summary.failed == 0
        assert summary.pass_rate == 100.0
        assert summary.by_category["injection"]["passed"] == 2
        assert summary.by_category["injection"]["failed"] == 0
        assert summary.by_layer["L1"] == 1
        assert summary.by_layer["L2"] == 1

    def test_summarize_mixed_results(self):
        aggregator = MetricsAggregator()

        # Create mock runs
        run1 = Mock(spec=TestRunResult)
        run1.passed = True
        run1.test.category = "injection"
        run1.defense_logs_before = []
        run1.defense_logs_after = []

        run2 = Mock(spec=TestRunResult)
        run2.passed = False
        run2.test.category = "other"
        run2.defense_logs_before = [Mock(layer_id="L1", decision="block")]
        run2.defense_logs_after = []

        run3 = Mock(spec=TestRunResult)
        run3.passed = True
        run3.test.category = "other"
        run3.defense_logs_before = []
        run3.defense_logs_after = []

        summary = aggregator.summarize([run1, run2, run3])

        assert summary.total == 3
        assert summary.passed == 2
        assert summary.failed == 1
        assert summary.pass_rate == 66.67  # (2/3) * 100 rounded to 2 decimals
        assert summary.by_category["injection"]["passed"] == 1
        assert summary.by_category["injection"]["failed"] == 0
        assert summary.by_category["other"]["passed"] == 1
        assert summary.by_category["other"]["failed"] == 1
        assert summary.by_layer["L1"] == 1

    def test_summarize_with_false_positives(self):
        aggregator = MetricsAggregator()

        # Create mock runs - control test that failed (false positive)
        run1 = Mock(spec=TestRunResult)
        run1.passed = False
        run1.test.category = "control"
        run1.test.metadata = {"control": "true"}
        run1.defense_logs_before = []
        run1.defense_logs_after = []

        summary = aggregator.summarize([run1])

        assert summary.total == 1
        assert summary.passed == 0
        assert summary.failed == 1
        assert summary.false_positives == 1

    def test_summarize_no_decisions_tracked(self):
        aggregator = MetricsAggregator()

        run1 = Mock(spec=TestRunResult)
        run1.passed = True
        run1.test.category = "test"
        run1.defense_logs_before = [Mock(layer_id="L1", decision="allow")]  # allow not tracked
        run1.defense_logs_after = [Mock(layer_id="L2", decision="allow")]   # allow not tracked

        summary = aggregator.summarize([run1])

        assert summary.by_layer == {}  # No block/rewrite/escalate decisions

    def test_summarize_multiple_decisions_per_layer(self):
        aggregator = MetricsAggregator()

        run1 = Mock(spec=TestRunResult)
        run1.passed = False
        run1.test.category = "test"
        run1.defense_logs_before = [
            Mock(layer_id="L1", decision="block"),
            Mock(layer_id="L1", decision="rewrite")  # Same layer triggered twice
        ]
        run1.defense_logs_after = []

        summary = aggregator.summarize([run1])

        assert summary.by_layer["L1"] == 2  # Count each decision


class TestCSVReporter:
    def test_write_csv_empty_runs(self, tmp_path):
        output_file = tmp_path / "test.csv"
        write_csv(output_file, [])

        content = output_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 1  # Just header
        assert "test_id" in lines[0]

    def test_write_csv_with_runs(self, tmp_path):
        output_file = tmp_path / "test.csv"

        # Create mock runs
        run1 = Mock(spec=TestRunResult)
        run1.test.id = "test1"
        run1.test.name = "Test 1"
        run1.test.category = "injection"
        run1.passed = True
        run1.evaluation.reason = "ok"
        run1.defense_decision = "allow"
        run1.response = "Response with\nnewline"

        run2 = Mock(spec=TestRunResult)
        run2.test.id = "test2"
        run2.test.name = "Test 2"
        run2.test.category = "other"
        run2.passed = False
        run2.evaluation.reason = "failed criteria"
        run2.defense_decision = "block"
        run2.response = "Another response"

        write_csv(output_file, [run1, run2])

        content = output_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 3  # Header + 2 data rows

        # Check header
        header = lines[0].split(";")
        assert header == ["test_id", "test_name", "category", "passed", "reason", "defense_decision", "response"]

        # Check first data row
        row1 = lines[1].split(";")
        assert row1[0] == "test1"
        assert row1[1] == "Test 1"
        assert row1[2] == "injection"
        assert row1[3] == "PASS"
        assert row1[4] == "ok"
        assert row1[5] == "allow"
        assert row1[6] == "Response with newline"  # Newlines replaced with spaces

        # Check second data row
        row2 = lines[2].split(";")
        assert row2[0] == "test2"
        assert row2[3] == "FAIL"

    def test_write_csv_creates_parent_dirs(self, tmp_path):
        output_dir = tmp_path / "subdir" / "nested"
        output_file = output_dir / "test.csv"

        run = Mock(spec=TestRunResult)
        run.test.id = "test1"
        run.test.name = "Test 1"
        run.test.category = "test"
        run.passed = True
        run.evaluation.reason = "ok"
        run.defense_decision = "allow"
        run.response = "response"

        write_csv(output_file, [run])

        assert output_file.exists()


class TestJSONReporter:
    def test_write_json_empty_runs(self, tmp_path):
        output_file = tmp_path / "test.json"
        write_json(output_file, [])

        content = output_file.read_text(encoding="utf-8")
        import json
        data = json.loads(content)
        assert data == []

    def test_write_json_with_runs(self, tmp_path):
        output_file = tmp_path / "test.json"

        # Create mock runs with realistic data
        run1 = Mock(spec=TestRunResult)
        run1.test.id = "test1"
        run1.test.name = "Test 1"
        run1.test.category = "injection"
        run1.test.severity.value = "HIGH"
        run1.passed = True
        run1.evaluation.reason = "ok"
        run1.defense_decision = "allow"
        run1.defense_logs_before = []
        run1.defense_logs_after = []
        run1.response = "Test response"
        run1.started_at = datetime(2023, 1, 1, 10, 0, 0)
        run1.finished_at = datetime(2023, 1, 1, 10, 0, 1)
        run1.duration_ms = 1000.0

        run2 = Mock(spec=TestRunResult)
        run2.test.id = "test2"
        run2.test.name = "Test 2"
        run2.test.category = "other"
        run2.test.severity.value = "LOW"
        run2.passed = False
        run2.evaluation.reason = "failed"
        run2.defense_decision = "block"
        mock_log = Mock()
        mock_log.layer_id = "L1"
        mock_log.decision = "block"
        mock_log.reason = "test"
        mock_log.metadata = {}
        run2.defense_logs_before = []
        run2.defense_logs_after = []
        run2.response = "Blocked response"
        run2.started_at = datetime(2023, 1, 1, 10, 0, 0)
        run2.finished_at = datetime(2023, 1, 1, 10, 0, 2)
        run2.duration_ms = 2000.0

        write_json(output_file, [run1, run2])

        import json
        content = output_file.read_text(encoding="utf-8")
        data = json.loads(content)

        assert len(data) == 2

        # Check first entry
        entry1 = data[0]
        assert entry1["test_id"] == "test1"
        assert entry1["name"] == "Test 1"
        assert entry1["category"] == "injection"
        assert entry1["severity"] == "HIGH"
        assert entry1["passed"] is True
        assert entry1["reason"] == "ok"
        assert entry1["defense_decision"] == "allow"
        assert entry1["response"] == "Test response"
        assert entry1["duration_ms"] == 1000.0

        # Check second entry logs
        entry2 = data[1]
        assert len(entry2["defense_logs_before"]) == 0

    def test_write_json_creates_parent_dirs(self, tmp_path):
        output_dir = tmp_path / "subdir" / "nested"
        output_file = output_dir / "test.json"

        run = Mock(spec=TestRunResult)
        run.test.id = "test1"
        run.test.name = "Test 1"
        run.test.category = "test"
        run.test.severity.value = "MEDIUM"
        run.passed = True
        run.evaluation.reason = "ok"
        run.defense_decision = "allow"
        run.defense_logs_before = []
        run.defense_logs_after = []
        run.response = "response"
        run.started_at = datetime.now()
        run.finished_at = datetime.now()
        run.duration_ms = 100.0

        write_json(output_file, [run])

        assert output_file.exists()


class TestHTMLReporter:
    def test_write_html_empty_runs(self, tmp_path):
        output_file = tmp_path / "test.html"
        write_html(output_file, [])

        content = output_file.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Отчёт по тестам prompt-инъекций" in content
        assert "Всего тестов: 0" in content

    def test_write_html_with_runs(self, tmp_path):
        output_file = tmp_path / "test.html"

        # Create mock runs and summary
        run1 = Mock(spec=TestRunResult)
        run1.test.id = "test1"
        run1.test.name = "Test 1"
        run1.test.category = "injection"
        run1.passed = True
        run1.defense_decision = "allow"
        run1.evaluation.reason = "ok"
        run1.defense_logs_before = []
        run1.defense_logs_after = []

        run2 = Mock(spec=TestRunResult)
        run2.test.id = "test2"
        run2.test.name = "Test 2"
        run2.test.category = "other"
        run2.passed = False
        run2.defense_decision = "block"
        run2.evaluation.reason = "failed"
        run2.defense_logs_before = []
        run2.defense_logs_after = []

        write_html(output_file, [run1, run2])

        content = output_file.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Отчёт по тестам prompt-инъекций" in content
        assert "Всего тестов: 2" in content
        assert "пройдено: 1" in content
        assert "провалено: 1" in content

        # Check table rows
        assert "test1" in content
        assert "test2" in content
        assert "PASS" in content
        assert "FAIL" in content

    def test_write_html_with_layer_summary(self, tmp_path):
        output_file = tmp_path / "test.html"

        # Create mock run with layer logs
        run = Mock(spec=TestRunResult)
        run.test.id = "test1"
        run.test.name = "Test 1"
        run.test.category = "test"
        run.passed = False
        run.defense_decision = "block"
        run.evaluation.reason = "blocked"

        # Mock aggregator to return summary with layer data
        with patch('src.llm_security.features.reporting.infrastructure.html_reporter.MetricsAggregator') as mock_agg:
            mock_summary = Mock()
            mock_summary.total = 1
            mock_summary.passed = 0
            mock_summary.failed = 1
            mock_summary.pass_rate = 0.0
            mock_summary.by_layer = {"L1": 2, "L2": 1}
            mock_agg.return_value.summarize.return_value = mock_summary

            write_html(output_file, [run])

        content = output_file.read_text(encoding="utf-8")
        assert "L1: 2" in content
        assert "L2: 1" in content

    def test_write_html_creates_parent_dirs(self, tmp_path):
        output_dir = tmp_path / "subdir" / "nested"
        output_file = output_dir / "test.html"

        run = Mock(spec=TestRunResult)
        run.test.id = "test1"
        run.test.name = "Test 1"
        run.test.category = "test"
        run.passed = True
        run.defense_decision = "allow"
        run.evaluation.reason = "ok"
        run.defense_logs_before = []
        run.defense_logs_after = []

        write_html(output_file, [run])

        assert output_file.exists()

    def test_write_html_russian_text_and_styling(self, tmp_path):
        output_file = tmp_path / "test.html"
        write_html(output_file, [])

        content = output_file.read_text(encoding="utf-8")
        assert 'lang="ru"' in content
        assert 'font-family: Arial, sans-serif' in content
        assert 'border-collapse: collapse' in content