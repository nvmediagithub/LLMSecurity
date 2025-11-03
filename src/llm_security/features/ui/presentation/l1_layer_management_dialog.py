from __future__ import annotations

import asyncio

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from ...l1.application.config_service import L1ConfigService
from ...l1.domain.entities import L1AttackCategory, L1LayerConfig


class L1LayerManagementDialog(QDialog):
    """Диалог настройки параметров слоя L1."""

    def __init__(self, config_service: L1ConfigService | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        if config_service is None:
            from ...l1.infrastructure.config_repository import YamlL1ConfigRepository
            from pathlib import Path
            config_repo = YamlL1ConfigRepository(Path("config/l1/l1_config.yaml"))
            self.config_service = L1ConfigService(config_repo)
        else:
            self.config_service = config_service
        self.setModal(True)
        self.setWindowTitle("Настройки слоя L1")
        self.resize(500, 400)

        self._original_config: L1LayerConfig | None = None

        # Создание виджетов
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setRange(1, 100000)
        self.max_length_spin.setToolTip("Максимальная длина текста в символах (1-100000)")

        self.normalize_unicode_check = QCheckBox("Нормализация Unicode")
        self.normalize_unicode_check.setToolTip("Включить нормализацию Unicode символов")

        self.strip_zero_width_check = QCheckBox("Удаление zero-width символов")
        self.strip_zero_width_check.setToolTip("Включить удаление невидимых символов")

        self.enabled_check = QCheckBox("Слой L1 включен")
        self.enabled_check.setToolTip("Общее включение слоя L1")

        # Категории атак - чекбоксы для каждого типа
        self.category_checks: dict[L1AttackCategory, QCheckBox] = {}
        for category in L1AttackCategory:
            checkbox = QCheckBox(category.value.replace('_', ' ').title())
            checkbox.setToolTip(f"Включить категорию атак: {category.value}")
            self.category_checks[category] = checkbox

        # Кнопки
        buttons = QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        self.button_box = QDialogButtonBox(buttons)
        self.button_box.accepted.connect(self._on_save)
        self.button_box.rejected.connect(self.reject)

        self._setup_layout()
        # Загружаем конфигурацию в синхронном контексте
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._load_config())
        finally:
            loop.close()

    def _setup_layout(self) -> None:
        """Настройка layout диалога."""
        layout = QVBoxLayout()

        # Группа основных настроек
        basic_group = QGroupBox("Основные настройки")
        basic_layout = QFormLayout()

        basic_layout.addRow("Максимальная длина:", self.max_length_spin)
        basic_layout.addRow(self.enabled_check)
        basic_layout.addRow(self.normalize_unicode_check)
        basic_layout.addRow(self.strip_zero_width_check)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Группа категорий атак
        categories_group = QGroupBox("Включенные категории атак")
        categories_layout = QVBoxLayout()

        for checkbox in self.category_checks.values():
            categories_layout.addWidget(checkbox)

        categories_group.setLayout(categories_layout)
        layout.addWidget(categories_group)

        layout.addStretch()
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    async def _load_config(self) -> None:
        """Загрузить текущую конфигурацию."""
        try:
            self._original_config = await self.config_service.get_config()
            self._populate_form(self._original_config)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить конфигурацию: {exc}")
            self.reject()

    def _populate_form(self, config: L1LayerConfig) -> None:
        """Заполнить форму данными конфигурации."""
        self.max_length_spin.setValue(config.max_length)
        self.normalize_unicode_check.setChecked(config.normalize_unicode)
        self.strip_zero_width_check.setChecked(config.sanitize_zero_width)
        self.enabled_check.setChecked(len(config.enabled_categories) > 0)  # Простая логика включения

        for category in L1AttackCategory:
            self.category_checks[category].setChecked(category in config.enabled_categories)

    def _collect_config(self) -> L1LayerConfig:
        """Собрать конфигурацию из формы."""
        enabled_categories: set[L1AttackCategory] = set()
        if self.enabled_check.isChecked():
            for category, checkbox in self.category_checks.items():
                if checkbox.isChecked():
                    enabled_categories.add(category)

        return L1LayerConfig(
            max_length=self.max_length_spin.value(),
            enabled_categories=enabled_categories,
            sanitize_zero_width=self.strip_zero_width_check.isChecked(),
            normalize_unicode=self.normalize_unicode_check.isChecked(),
        )

    def _on_save(self) -> None:
        """Обработчик сохранения конфигурации."""
        try:
            new_config = self._collect_config()

            # Валидация
            from ...l1.domain.policy import L1Policy
            errors = L1Policy.validate_config(new_config)
            if errors:
                QMessageBox.warning(
                    self,
                    "Ошибка валидации",
                    "Обнаружены ошибки в конфигурации:\n" + "\n".join(errors)
                )
                return

            # Подтверждение изменений
            if not self._confirm_changes(self._original_config, new_config):
                return

            # Сохранение
            import asyncio
            asyncio.run(self.config_service.update_config(new_config))

            QMessageBox.information(self, "Успешно", "Конфигурация L1 слоя сохранена")
            self.accept()

        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить конфигурацию: {exc}")

    def _confirm_changes(self, old_config: L1LayerConfig | None, new_config: L1LayerConfig) -> bool:
        """Подтверждение изменений конфигурации."""
        if old_config is None:
            return True

        changes: list[str] = []
        if old_config.max_length != new_config.max_length:
            changes.append(f"Максимальная длина: {old_config.max_length} -> {new_config.max_length}")
        if old_config.normalize_unicode != new_config.normalize_unicode:
            changes.append(f"Нормализация Unicode: {old_config.normalize_unicode} -> {new_config.normalize_unicode}")
        if old_config.sanitize_zero_width != new_config.sanitize_zero_width:
            changes.append(f"Удаление zero-width: {old_config.sanitize_zero_width} -> {new_config.sanitize_zero_width}")

        old_categories = set(old_config.enabled_categories)
        new_categories = set(new_config.enabled_categories)
        if old_categories != new_categories:
            added = new_categories - old_categories
            removed = old_categories - new_categories
            if added:
                changes.append(f"Добавлены категории: {', '.join(c.value for c in added)}")
            if removed:
                changes.append(f"Удалены категории: {', '.join(c.value for c in removed)}")

        if not changes:
            return True

        message = "Следующие параметры будут изменены:\n\n" + "\n".join(changes)
        reply = QMessageBox.question(
            self,
            "Подтверждение изменений",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes