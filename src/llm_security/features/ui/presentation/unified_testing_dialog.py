from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Set

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...attacks.application.attack_manager import AttackManager
from ...attacks.domain.entities import AttackCategory, AttackDefinition, AttackResult
from ...attacks.infrastructure.integration import setup_attack_registry
from ...layers.application.layer_manager import LayerManager
from ...layers.domain.entities import LayerMetadata
from ...layers.infrastructure.layer_registry import LayerRegistry
from ...analysis.application.analysis_service import AnalysisService
from ...analysis.domain.entities import AnalysisResult, UnifiedReport


class TestingWorker(QThread):
    """Worker thread for running unified testing."""
    progress = pyqtSignal(int)
    result_ready = pyqtSignal(AttackResult)
    log_message = pyqtSignal(str)
    finished_all = pyqtSignal(list, AnalysisResult)

    def __init__(
        self,
        attack_manager: AttackManager,
        layer_manager: LayerManager,
        analysis_service: AnalysisService,
        selected_layers: List[str],
        selected_attacks: List[str]
    ):
        super().__init__()
        self.attack_manager = attack_manager
        self.layer_manager = layer_manager
        self.analysis_service = analysis_service
        self.selected_layers = selected_layers
        self.selected_attacks = selected_attacks
        self.results: List[AttackResult] = []

    def run(self):
        """Run the unified testing in background thread."""
        try:
            # Load attacks and execute them on selected layers
            attack_results = []
            total_operations = len(self.selected_layers) * len(self.selected_attacks)
            current_operation = 0

            for layer_id in self.selected_layers:
                self.log_message.emit(f"Testing layer: {layer_id}")

                for attack_id in self.selected_attacks:
                    self.log_message.emit(f"Executing attack {attack_id} on layer {layer_id}")

                    # Execute attack on layer (simplified - would need proper integration)
                    # For now, create mock results
                    result = AttackResult(
                        attack=AttackDefinition(
                            id=attack_id,
                            name=f"Attack {attack_id}",
                            description=f"Description for {attack_id}",
                            category=AttackCategory.PROMPT_INJECTION,
                            payload="test payload",
                            target_layer=layer_id
                        ),
                        success=True,
                        layer_response={"decision": "BLOCK", "reason": "Test reason"},
                        metrics={"execution_time": 0.1}
                    )

                    attack_results.append(result)
                    self.result_ready.emit(result)
                    self.log_message.emit(f"Attack {attack_id} completed")

                    current_operation += 1
                    self.progress.emit(int((current_operation / total_operations) * 100))

            # Perform analysis
            self.log_message.emit("Performing analysis...")
            analysis_result = self.analysis_service.analyze_results([], attack_results)
            self.log_message.emit("Analysis completed")

            self.finished_all.emit(attack_results, analysis_result)

        except Exception as e:
            self.log_message.emit(f"Testing error: {str(e)}")


class UnifiedTestingDialog(QDialog):
    """Unified testing dialog for layers and attacks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.attack_manager = AttackManager()
        self.layer_manager = LayerManager()
        self.analysis_service = AnalysisService()
        self.attack_registry = setup_attack_registry()

        self.worker: Optional[TestingWorker] = None
        self.results: List[AttackResult] = []
        self.analysis_result: Optional[AnalysisResult] = None

        self.setModal(True)
        self.setWindowTitle("Unified Testing Interface")
        self.resize(1200, 800)

        # Initialize UI components
        self._init_ui_components()
        self._setup_layout()

        # Load data asynchronously
        self._load_initial_data()

    def _init_ui_components(self):
        """Initialize UI components."""
        # Defense layers panel
        self.layers_group = QGroupBox("Defense Layers (L1-L9)")
        self.layer_checkboxes: Dict[str, QCheckBox] = {}

        # Attacks panel
        self.attacks_tab_widget = QTabWidget()
        self.attack_checkboxes: Dict[str, QCheckBox] = {}

        # Run button and progress
        self.run_button = QPushButton("Start Unified Testing")
        self.run_button.clicked.connect(self._on_run_testing)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # Logs area
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)

        # Results table
        self.results_table = self._build_results_table()

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.button_box.rejected.connect(self.reject)

    def _setup_layout(self):
        """Setup the main layout."""
        layout = QVBoxLayout()

        # Top controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.run_button)
        controls_layout.addWidget(self.progress_bar)
        controls_layout.addStretch()

        # Main content area
        content_layout = QHBoxLayout()

        # Left panel - Layers
        left_panel = QVBoxLayout()
        left_panel.addWidget(self.layers_group)

        # Right panel - Attacks
        right_panel = QVBoxLayout()
        right_panel.addWidget(self.attacks_tab_widget)

        content_layout.addLayout(left_panel, 1)
        content_layout.addLayout(right_panel, 2)

        # Bottom area - Results and logs
        results_group = QGroupBox("Testing Results")
        results_layout = QVBoxLayout()
        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)

        log_group = QGroupBox("Execution Logs")
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        # Add all to main layout
        layout.addLayout(controls_layout)
        layout.addLayout(content_layout)
        layout.addWidget(results_group)
        layout.addWidget(log_group)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def _load_initial_data(self):
        """Load initial data for layers and attacks."""
        try:
            # Load defense layers
            self._load_defense_layers()

            # Load attacks by category
            self._load_attacks_by_category()

        except Exception as e:
            self.log_text.append(f"Error loading data: {str(e)}")

    def _load_defense_layers(self):
        """Load and display defense layers."""
        layers_layout = QVBoxLayout()

        # Default L1-L9 layers
        layer_descriptions = {
            "L1": "Input Sanitization - Basic input cleaning and validation",
            "L2": "Prompt Classification - Detects malicious prompt patterns",
            "L3": "Context Firewall - Blocks unauthorized context access",
            "L4": "Policy Engine - Enforces security policies and rules",
            "L5": "Tool Gatekeeper - Controls access to external tools",
            "L6": "Suffix Detector - Removes adversarial suffixes",
            "L7": "Output Guard - Filters and moderates responses",
            "L8": "Memory Guard - Protects against memory-based attacks",
            "L9": "Rate/Scope Guard - Controls request frequency and scope"
        }

        for layer_id, description in layer_descriptions.items():
            checkbox = QCheckBox(f"{layer_id}: {description}")
            checkbox.setChecked(True)  # Default to enabled
            checkbox.setToolTip(description)
            self.layer_checkboxes[layer_id] = checkbox
            layers_layout.addWidget(checkbox)

        layers_layout.addStretch()
        self.layers_group.setLayout(layers_layout)

    def _load_attacks_by_category(self):
        """Load and organize attacks by category in tabs."""
        # Clear existing tabs
        while self.attacks_tab_widget.count() > 0:
            self.attacks_tab_widget.removeTab(0)

        # Get attacks by category
        attacks_by_category = self._get_attacks_by_category()

        for category, attacks in attacks_by_category.items():
            tab = QWidget()
            layout = QVBoxLayout()

            for attack in attacks:
                checkbox = QCheckBox(f"{attack.name}: {attack.description}")
                checkbox.setToolTip(attack.description)
                self.attack_checkboxes[attack.id] = checkbox
                layout.addWidget(checkbox)

            layout.addStretch()
            tab.setLayout(layout)

            # Format category name for display
            category_name = category.value.replace('_', ' ').title()
            self.attacks_tab_widget.addTab(tab, category_name)

    def _get_attacks_by_category(self) -> Dict[AttackCategory, List[AttackDefinition]]:
        """Get attacks organized by category."""
        attacks_by_category: Dict[AttackCategory, List[AttackDefinition]] = {}

        # For now, create mock attacks per category
        for category in AttackCategory:
            attacks = []

            # Mock attacks for each category
            for i in range(3):
                attack = AttackDefinition(
                    id=f"{category.value}_attack_{i+1}",
                    name=f"{category.value.title()} Attack {i+1}",
                    description=f"Mock attack for {category.value}",
                    category=category,
                    payload=f"Mock payload {i+1}",
                    target_layer="L1"
                )
                attacks.append(attack)

            attacks_by_category[category] = attacks

        return attacks_by_category

    def _build_results_table(self) -> QTableWidget:
        """Build the results table."""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Layer", "Attack ID", "Attack Name", "Success", "Decision", "Reason"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        return table

    def _get_selected_layers(self) -> List[str]:
        """Get selected layer IDs."""
        return [layer_id for layer_id, checkbox in self.layer_checkboxes.items()
                if checkbox.isChecked()]

    def _get_selected_attacks(self) -> List[str]:
        """Get selected attack IDs."""
        return [attack_id for attack_id, checkbox in self.attack_checkboxes.items()
                if checkbox.isChecked()]

    def _on_run_testing(self):
        """Handle unified testing execution."""
        selected_layers = self._get_selected_layers()
        selected_attacks = self._get_selected_attacks()

        if not selected_layers:
            self.log_text.append("Please select at least one defense layer")
            return

        if not selected_attacks:
            self.log_text.append("Please select at least one attack")
            return

        self._run_unified_testing(selected_layers, selected_attacks)

    def _run_unified_testing(self, selected_layers: List[str], selected_attacks: List[str]):
        """Run the unified testing."""
        if self.worker and self.worker.isRunning():
            return

        # Clear previous results
        self.results.clear()
        self.results_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        # Create and start worker
        self.worker = TestingWorker(
            self.attack_manager,
            self.layer_manager,
            self.analysis_service,
            selected_layers,
            selected_attacks
        )

        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.result_ready.connect(self._on_result_ready)
        self.worker.finished_all.connect(self._on_testing_finished)
        self.worker.log_message.connect(self.log_text.append)

        self.run_button.setEnabled(False)
        self.worker.start()

    def _on_result_ready(self, result: AttackResult):
        """Handle individual test result."""
        self.results.append(result)
        self._add_result_to_table(result)

    def _on_testing_finished(self, results: List[AttackResult], analysis: AnalysisResult):
        """Handle testing completion."""
        self.results = results
        self.analysis_result = analysis
        self.run_button.setEnabled(True)
        self.log_text.append("Unified testing completed successfully")

    def _add_result_to_table(self, result: AttackResult):
        """Add result to the table."""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)

        decision = result.layer_decision or "N/A"
        reason = result.layer_reason or "N/A"

        self.results_table.setItem(row, 0, QTableWidgetItem(result.attack.target_layer))
        self.results_table.setItem(row, 1, QTableWidgetItem(result.attack.id))
        self.results_table.setItem(row, 2, QTableWidgetItem(result.attack.name))
        self.results_table.setItem(row, 3, QTableWidgetItem("Yes" if result.success else "No"))
        self.results_table.setItem(row, 4, QTableWidgetItem(decision))
        self.results_table.setItem(row, 5, QTableWidgetItem(reason))

        self.results_table.resizeRowsToContents()

    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        super().closeEvent(event)