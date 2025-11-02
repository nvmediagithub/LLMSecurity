from __future__ import annotations

from typing import Iterable, List, Optional, Set

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...testing.application.service import TestSuiteResult
from ...testing.domain.models import PromptTest
from ..application.controller import UISuiteController
from .connection_management_dialog import ConnectionManagementDialog


class MainWindow(QMainWindow):
    """Главное окно PyQt-приложения."""

    def __init__(self, controller: UISuiteController | None = None):
        super().__init__()
        self.controller = controller or UISuiteController()
        self.data = self.controller.load_initial_data()

        self.setWindowTitle("LLM Security Lab")
        self.resize(1150, 760)

        self.profile_combo = self._build_profile_combo()
        self.connection_combo = self._build_connection_combo()
        self.tests_table = self._build_tests_table(self.data.tests)
        self.categories_list = self._build_categories_list(self.data.tests)
        self.results_table = self._build_results_table()
        self.metrics_label = QLabel("-")
        self.delta_label = QLabel("")

        self.run_button = QPushButton("Запустить профиль")
        self.run_button.clicked.connect(self._on_run_clicked)  # type: ignore[arg-type]

        self.ab_button = QPushButton("A/B прогон")
        self.ab_button.clicked.connect(self._on_ab_clicked)  # type: ignore[arg-type]

        self.manage_connections_button = QPushButton("Управление подключениями")
        self.manage_connections_button.clicked.connect(self._on_manage_connections_clicked)  # type: ignore[arg-type]

        self._compose_layout()

    # region UI builders
    def _compose_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout()
        central.setLayout(root_layout)

        controls_box = QGroupBox("Настройки")
        controls_layout = QHBoxLayout()
        controls_box.setLayout(controls_layout)
        controls_layout.addWidget(QLabel("Профиль:"))
        controls_layout.addWidget(self.profile_combo)
        controls_layout.addWidget(QLabel("Подключение:"))
        controls_layout.addWidget(self.connection_combo)
        controls_layout.addWidget(self.run_button)
        controls_layout.addWidget(self.ab_button)
        controls_layout.addWidget(self.manage_connections_button)
        controls_layout.addStretch()
        controls_layout.addWidget(self.metrics_label)
        controls_layout.addWidget(self.delta_label)

        split_layout = QGridLayout()

        categories_box = QGroupBox("Категории")
        categories_layout = QVBoxLayout()
        categories_box.setLayout(categories_layout)
        categories_layout.addWidget(self.categories_list)

        tests_box = QGroupBox("Тесты")
        tests_layout = QVBoxLayout()
        tests_box.setLayout(tests_layout)
        tests_layout.addWidget(self.tests_table)

        results_box = QGroupBox("Результаты")
        results_layout = QVBoxLayout()
        results_box.setLayout(results_layout)
        results_layout.addWidget(self.results_table)

        split_layout.addWidget(categories_box, 0, 0)
        split_layout.addWidget(tests_box, 0, 1)
        split_layout.addWidget(results_box, 1, 0, 1, 2)

        root_layout.addWidget(controls_box)
        root_layout.addLayout(split_layout)

    def _build_profile_combo(self) -> QComboBox:
        combo = QComboBox()
        for profile in self.data.profiles:
            combo.addItem(profile)
        return combo

    def _build_connection_combo(self) -> QComboBox:
        combo = QComboBox()
        if not self.data.connections:
            combo.addItem("dummy (fallback)", userData="dummy")
            return combo
        for connection in self.data.connections:
            label = f"{connection.id} ({connection.provider})"
            combo.addItem(label, userData=connection.id)
        return combo

    def _build_tests_table(self, tests: List[PromptTest]) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Категория", "Severity", "Название"])
        table.setRowCount(len(tests))
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        table.verticalHeader().setVisible(False)
        for row, test in enumerate(tests):
            table.setItem(row, 0, QTableWidgetItem(test.id))
            table.setItem(row, 1, QTableWidgetItem(test.category))
            table.setItem(row, 2, QTableWidgetItem(test.severity.value))
            table.setItem(row, 3, QTableWidgetItem(test.name))
        table.resizeColumnsToContents()
        return table

    def _build_categories_list(self, tests: Iterable[PromptTest]) -> QListWidget:
        categories: Set[str] = {test.category for test in tests if test.category != "control"}
        widget = QListWidget()
        widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for category in sorted(categories):
            item = QListWidgetItem(category)
            item.setCheckState(Qt.CheckState.Unchecked)
            widget.addItem(item)
        return widget

    def _build_results_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID", "Категория", "Статус", "Решение защиты", "Причина"])
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return table

    # endregion

    # region handlers
    def _on_run_clicked(self) -> None:
        profile_id = self.profile_combo.currentText()
        tests = self._selected_test_ids()
        categories = self._selected_categories()
        connection_id = self._selected_connection_id()
        try:
            result = self.controller.run_suite(
                profile_id,
                categories=categories,
                test_ids=tests,
                connection_id=connection_id,
            )
            self._display_suite(result)
            self.delta_label.setText("")
        except Exception as exc:  # pragma: no cover - UI handler
            QMessageBox.critical(self, "Ошибка", str(exc))

    def _on_ab_clicked(self) -> None:
        profile_id = self.profile_combo.currentText()
        tests = self._selected_test_ids()
        categories = self._selected_categories()
        connection_id = self._selected_connection_id()
        try:
            result = self.controller.run_ab(
                profile_id,
                categories=categories,
                test_ids=tests,
                connection_id=connection_id,
            )
            self._display_suite(result.protected)
            self.delta_label.setText(f"Delta Pass%: {result.delta_pass_rate}")
        except Exception as exc:  # pragma: no cover
            QMessageBox.critical(self, "Ошибка", str(exc))

    def _on_manage_connections_clicked(self) -> None:
        dialog = ConnectionManagementDialog(parent=self)
        dialog.exec()
        # Обновляем список подключений в комбо-боксе после изменений
        self._refresh_connections_combo()

    # endregion

    # region helpers
    def _display_suite(self, suite: TestSuiteResult) -> None:
        runs = suite.runs
        self.results_table.setRowCount(len(runs))
        for row, run in enumerate(runs):
            self.results_table.setItem(row, 0, QTableWidgetItem(run.test.id))
            self.results_table.setItem(row, 1, QTableWidgetItem(run.test.category))
            status = "PASS" if run.passed else "FAIL"
            self.results_table.setItem(row, 2, QTableWidgetItem(status))
            self.results_table.setItem(row, 3, QTableWidgetItem(run.defense_decision))
            self.results_table.setItem(row, 4, QTableWidgetItem(run.evaluation.reason))
        self.results_table.resizeColumnsToContents()
        self.metrics_label.setText(f"Pass%: {suite.metrics.pass_rate} ({suite.metrics.passed}/{suite.metrics.total})")

    def _selected_categories(self) -> List[str]:
        categories: List[str] = []
        for idx in range(self.categories_list.count()):
            item = self.categories_list.item(idx)
            if item.checkState() == Qt.CheckState.Checked:
                categories.append(item.text())
        return categories

    def _selected_test_ids(self) -> List[str]:
        selection = self.tests_table.selectionModel()
        if not selection:
            return []
        rows = {idx.row() for idx in selection.selectedRows()}
        ids: List[str] = []
        for row in rows:
            item = self.tests_table.item(row, 0)
            if item:
                ids.append(item.text())
        return ids

    def _selected_connection_id(self) -> Optional[str]:
        idx = self.connection_combo.currentIndex()
        if idx < 0:
            return None
        value = self.connection_combo.itemData(idx)
        return value if isinstance(value, str) else None

    def _refresh_connections_combo(self) -> None:
        """Обновляет список подключений в комбо-боксе."""
        self.data = self.controller.load_initial_data()  # Перезагружаем данные
        self.connection_combo.clear()
        if not self.data.connections:
            self.connection_combo.addItem("dummy (fallback)", userData="dummy")
            return
        for connection in self.data.connections:
            label = f"{connection.id} ({connection.provider})"
            self.connection_combo.addItem(label, userData=connection.id)

    # endregion


def launch_app() -> None:  # pragma: no cover - GUI entrypoint
    import sys

    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication(sys.argv)
        owns_app = True
    window = MainWindow()
    window.show()
    if owns_app:
        sys.exit(app.exec())
    else:
        app.exec()

