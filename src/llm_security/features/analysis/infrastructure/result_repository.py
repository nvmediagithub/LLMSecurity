from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ...attacks.domain.entities import AttackResult
from ...testing.domain.results import TestRunResult
from ..domain.entities import AnalysisResult


class IResultRepository(ABC):
    """Interface for storing and retrieving analysis results."""

    @abstractmethod
    def save_analysis_result(self, result: AnalysisResult) -> str:
        """Save analysis result and return ID."""
        pass

    @abstractmethod
    def get_analysis_result(self, result_id: str) -> Optional[AnalysisResult]:
        """Retrieve analysis result by ID."""
        pass

    @abstractmethod
    def list_analysis_results(self, limit: int = 50) -> List[AnalysisResult]:
        """List recent analysis results."""
        pass


class SQLiteResultRepository(IResultRepository):
    """SQLite-based repository for analysis results."""

    def __init__(self, db_path: str = "analysis_results.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_analysis_result(self, result: AnalysisResult) -> str:
        """Save analysis result to database."""
        import uuid
        result_id = str(uuid.uuid4())

        # Serialize the result
        data = {
            "id": result_id,
            "timestamp": result.timestamp.isoformat(),
            "total_tests": result.total_tests,
            "passed_tests": result.passed_tests,
            "failed_tests": result.failed_tests,
            "total_attacks": result.total_attacks,
            "blocked_attacks": result.blocked_attacks,
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
                }
                for m in result.layer_metrics
            ],
            "attack_metrics": [
                {
                    "category": m.category,
                    "total_attempts": m.total_attempts,
                    "successful_attempts": m.successful_attempts,
                    "blocked_attempts": m.blocked_attempts,
                    "pattern_distribution": m.pattern_distribution,
                    "average_complexity": m.average_complexity,
                }
                for m in result.attack_metrics
            ],
            "vulnerabilities": result.vulnerabilities,
            "recommendations": result.recommendations,
        }

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO analysis_results (id, timestamp, data) VALUES (?, ?, ?)",
                (result_id, result.timestamp.isoformat(), json.dumps(data))
            )

        return result_id

    def get_analysis_result(self, result_id: str) -> Optional[AnalysisResult]:
        """Retrieve analysis result by ID."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT data FROM analysis_results WHERE id = ?",
                (result_id,)
            ).fetchone()

            if not row:
                return None

            data = json.loads(row[0])

            # Reconstruct AnalysisResult
            from datetime import datetime
            from ..domain.entities import LayerMetrics, AttackMetrics

            layer_metrics = [
                LayerMetrics(**m) for m in data["layer_metrics"]
            ]
            attack_metrics = [
                AttackMetrics(**m) for m in data["attack_metrics"]
            ]

            return AnalysisResult(
                timestamp=datetime.fromisoformat(data["timestamp"]),
                test_results=[],  # Raw results not stored for simplicity
                attack_results=[],  # Raw results not stored for simplicity
                total_tests=data["total_tests"],
                passed_tests=data["passed_tests"],
                failed_tests=data["failed_tests"],
                total_attacks=data["total_attacks"],
                blocked_attacks=data["blocked_attacks"],
                layer_metrics=layer_metrics,
                attack_metrics=attack_metrics,
                vulnerabilities=data["vulnerabilities"],
                recommendations=data["recommendations"],
            )

    def list_analysis_results(self, limit: int = 50) -> List[AnalysisResult]:
        """List recent analysis results."""
        results = []
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id FROM analysis_results ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()

            for row in rows:
                result = self.get_analysis_result(row[0])
                if result:
                    results.append(result)

        return results


class ResultRepository(SQLiteResultRepository):
    """Default result repository implementation."""
    pass