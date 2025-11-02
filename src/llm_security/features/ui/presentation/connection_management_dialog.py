from __future__ import annotations

import re

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...models.application.connection_service import ModelConnectionService
from ...models.domain.connection import ConnectionConfig


class ConnectionManagementDialog(QDialog):
    """Диалог управления подключениями к LLM."""

    def __init__(self, connection_service: ModelConnectionService | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.connection_service = connection_service or ModelConnectionService()
        self.setModal(True)
        self.setWindowTitle("Управление подключениями")
        self.resize(800, 600)

        self.table = self._build_table()
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self._on_add_clicked)
        self.edit_button = QPushButton("Изменить")
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self._on_delete_clicked)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self._refresh_table()

    def _build_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["ID", "Провайдер", "Описание"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        return table

    def _on_add_clicked(self) -> None:
        dialog = ConnectionEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._create_connection(dialog.get_config())

    def _on_edit_clicked(self) -> None:
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите подключение для редактирования")
            return
        connection_id = self.table.item(selected, 0).text()
        try:
            config = self.connection_service.get_connection_config(connection_id)
            dialog = ConnectionEditDialog(config, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._update_connection(dialog.get_config())
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))

    def _on_delete_clicked(self) -> None:
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите подключение для удаления")
            return
        connection_id = self.table.item(selected, 0).text()
        if connection_id == "dummy":
            QMessageBox.warning(self, "Предупреждение", "Нельзя удалить встроенное подключение dummy")
            return
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить подключение '{connection_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._delete_connection(connection_id)

    def _create_connection(self, config: ConnectionConfig) -> None:
        try:
            self.connection_service.create_connection(config)
            self._refresh_table()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать подключение: {exc}")

    def _update_connection(self, config: ConnectionConfig) -> None:
        try:
            self.connection_service.update_connection(config)
            self._refresh_table()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить подключение: {exc}")

    def _delete_connection(self, connection_id: str) -> None:
        try:
            self.connection_service.delete_connection(connection_id)
            self._refresh_table()
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить подключение: {exc}")

    def _refresh_table(self) -> None:
        connections = self.connection_service.list_connections()
        self.table.setRowCount(len(connections))
        for row, conn in enumerate(connections):
            self.table.setItem(row, 0, QTableWidgetItem(conn.id))
            self.table.setItem(row, 1, QTableWidgetItem(conn.provider))
            self.table.setItem(row, 2, QTableWidgetItem(conn.description))


class ConnectionEditDialog(QDialog):
    """Диалог редактирования подключения."""

    def __init__(self, config: ConnectionConfig | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.config = config or ConnectionConfig(id="", provider="", description="")
        self.setModal(True)
        self.setWindowTitle("Редактирование подключения" if config else "Новое подключение")
        self.resize(500, 400)

        # Поля формы
        self.id_edit = QLineEdit(self.config.id)
        self.provider_edit = QLineEdit(self.config.provider)
        self.description_edit = QLineEdit(self.config.description)
        self.model_id_edit = QLineEdit(self.config.model_id or "")
        self.base_url_edit = QLineEdit(self.config.base_url or "")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 300)
        self.timeout_spin.setValue(self.config.timeout or 60)
        self.auth_type_edit = QLineEdit(self.config.auth.get("type", ""))
        self.auth_env_var_edit = QLineEdit(self.config.auth.get("env_var", ""))
        self.headers_text = QTextEdit()
        self.headers_text.setPlainText("\n".join(f"{k}: {v}" for k, v in self.config.headers.items()))

        # Кнопки
        buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.button_box = QDialogButtonBox(buttons)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)

        # Layout
        form = QFormLayout()
        form.addRow("ID:", self.id_edit)
        form.addRow("Провайдер:", self.provider_edit)
        form.addRow("Описание:", self.description_edit)
        form.addRow("Model ID:", self.model_id_edit)
        form.addRow("Base URL:", self.base_url_edit)
        form.addRow("Timeout:", self.timeout_spin)
        form.addRow("Auth Type:", self.auth_type_edit)
        form.addRow("Auth Env Var:", self.auth_env_var_edit)
        form.addRow("Headers (key: value):", self.headers_text)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def _on_accept(self) -> None:
        if not self._validate():
            return
        self.accept()

    def _validate(self) -> bool:
        connection_id = self.id_edit.text().strip()
        if not connection_id:
            QMessageBox.warning(self, "Ошибка валидации", "ID подключения обязателен")
            return False
        if not re.match(r"^[a-zA-Z0-9_-]+$", connection_id):
            QMessageBox.warning(self, "Ошибка валидации", "ID может содержать только буквы, цифры, _ и -")
            return False

        provider = self.provider_edit.text().strip()
        if not provider:
            QMessageBox.warning(self, "Ошибка валидации", "Провайдер обязателен")
            return False

        base_url = self.base_url_edit.text().strip()
        if base_url and not self._is_valid_url(base_url):
            QMessageBox.warning(self, "Ошибка валидации", "Неверный формат URL")
            return False

        return True

    def _is_valid_url(self, url: str) -> bool:
        pattern = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
        return pattern.match(url) is not None

    def get_config(self) -> ConnectionConfig:
        headers = {}
        for line in self.headers_text.toPlainText().strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        auth = {}
        auth_type = self.auth_type_edit.text().strip()
        if auth_type:
            auth["type"] = auth_type
        auth_env_var = self.auth_env_var_edit.text().strip()
        if auth_env_var:
            auth["env_var"] = auth_env_var

        timeout = self.timeout_spin.value()
        if timeout == 0:
            timeout = None

        return ConnectionConfig(
            id=self.id_edit.text().strip(),
            provider=self.provider_edit.text().strip(),
            description=self.description_edit.text().strip(),
            model_id=self.model_id_edit.text().strip() or None,
            base_url=self.base_url_edit.text().strip() or None,
            timeout=timeout,
            headers=headers,
            auth=auth,
        )