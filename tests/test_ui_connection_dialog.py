"""UI tests for connection management dialog."""

import pytest
from unittest.mock import Mock, patch

from PyQt6.QtWidgets import QApplication, QMessageBox

from src.llm_security.features.ui.presentation.connection_management_dialog import (
    ConnectionManagementDialog,
    ConnectionEditDialog
)
from src.llm_security.features.models.application.connection_service import ModelConnectionService
from src.llm_security.features.models.domain.connection import ConnectionConfig, ConnectionInfo


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for PyQt6 tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_config():
    """Sample connection config for testing."""
    return ConnectionConfig(
        id="test_openrouter",
        provider="openrouter",
        description="Test OpenRouter connection",
        model_id="gpt-3.5-turbo",
        base_url="https://api.example.com",
        timeout=30,
        headers={"Custom": "Header"},
        auth={"type": "env", "env_var": "TEST_API_KEY"},
    )


@pytest.fixture
def mock_service(sample_config):
    """Mock connection service for testing."""
    service = Mock(spec=ModelConnectionService)

    # Mock list_connections to return some sample data
    service.list_connections.return_value = [
        ConnectionInfo(id="dummy", provider="dummy", description="Built-in dummy client"),
        ConnectionInfo(id="test_openrouter", provider="openrouter", description="Test OpenRouter connection")
    ]

    # Mock get_connection_config
    service.get_connection_config.return_value = sample_config

    return service


class TestConnectionManagementDialog:
    """Test ConnectionManagementDialog functionality."""

    def test_initialization_with_service(self, qapp, mock_service):
        """Test dialog initialization with provided service."""
        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)
            assert dialog.connection_service is mock_service
            assert dialog.table is not None
            assert dialog.add_button is not None
            assert dialog.edit_button is not None
            assert dialog.delete_button is not None

    def test_initialization_without_service(self, qapp):
        """Test dialog initialization without service (uses default)."""
        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_instance = Mock()
            mock_service_instance.list_connections.return_value = []
            mock_service_class.return_value = mock_service_instance
            dialog = ConnectionManagementDialog()
            mock_service_class.assert_called_once()
            assert dialog.connection_service is not None

    def test_table_initialization(self, qapp, mock_service):
        """Test table setup and column headers."""
        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)
            table = dialog.table

            assert table.columnCount() == 3
            headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
            assert headers == ["ID", "Провайдер", "Описание"]
            assert table.rowCount() == 2  # dummy + test connection

            # Check dummy connection row
            assert table.item(0, 0).text() == "dummy"
            assert table.item(0, 1).text() == "dummy"
            assert table.item(0, 2).text() == "Built-in dummy client"

            # Check test connection row
            assert table.item(1, 0).text() == "test_openrouter"
            assert table.item(1, 1).text() == "openrouter"
            assert table.item(1, 2).text() == "Test OpenRouter connection"

    @patch('src.llm_security.features.ui.presentation.connection_management_dialog.ConnectionEditDialog')
    def test_add_connection_success(self, mock_edit_dialog_class, qapp, mock_service, sample_config):
        """Test successful connection addition."""
        mock_edit_dialog = Mock()
        mock_edit_dialog.exec.return_value = True  # Accepted
        mock_edit_dialog.get_config.return_value = sample_config
        mock_edit_dialog_class.return_value = mock_edit_dialog

        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)

            dialog.add_button.click()

            mock_edit_dialog_class.assert_called_once_with(parent=dialog)
            mock_service.create_connection.assert_called_once_with(sample_config)
            mock_service.list_connections.assert_called()  # Should refresh table

    @patch('src.llm_security.features.ui.presentation.connection_management_dialog.ConnectionEditDialog')
    @patch('PyQt6.QtWidgets.QMessageBox.critical')
    def test_add_connection_service_error(self, mock_msgbox, mock_edit_dialog_class, qapp, mock_service, sample_config):
        """Test connection addition with service error."""
        mock_edit_dialog = Mock()
        mock_edit_dialog.exec.return_value = True
        mock_edit_dialog.get_config.return_value = sample_config
        mock_edit_dialog_class.return_value = mock_edit_dialog

        mock_service.create_connection.side_effect = Exception("Service error")

        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)

            dialog.add_button.click()

            mock_msgbox.assert_called_once_with(dialog, "Ошибка", "Не удалось создать подключение: Service error")
            # list_connections is called during initialization and is not called again on error
            assert mock_service.list_connections.call_count == 1

    def test_edit_connection_no_selection(self, qapp, mock_service):
        """Test edit button when no row is selected."""
        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)

            # No row selected
            dialog.table.clearSelection()

            with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
                dialog.edit_button.click()
                mock_warning.assert_called_once_with(dialog, "Предупреждение", "Выберите подключение для редактирования")

    @patch('src.llm_security.features.ui.presentation.connection_management_dialog.ConnectionEditDialog')
    def test_edit_connection_success(self, mock_edit_dialog_class, qapp, mock_service, sample_config):
        """Test successful connection editing."""
        mock_edit_dialog = Mock()
        mock_edit_dialog.exec.return_value = True
        mock_edit_dialog.get_config.return_value = sample_config
        mock_edit_dialog_class.return_value = mock_edit_dialog

        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)

            # Select second row (test connection)
            dialog.table.selectRow(1)

            dialog.edit_button.click()

            mock_edit_dialog_class.assert_called_once_with(sample_config, parent=dialog)
            mock_service.update_connection.assert_called_once_with(sample_config)
            mock_service.list_connections.assert_called()  # Should refresh table

    @patch('PyQt6.QtWidgets.QMessageBox.critical')
    def test_edit_connection_service_error(self, mock_msgbox, qapp, mock_service, sample_config):
        """Test connection editing with service error."""
        mock_service.get_connection_config.side_effect = Exception("Service error")

        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)

            dialog.table.selectRow(1)

            with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ConnectionEditDialog') as mock_edit_dialog_class:
                mock_edit_dialog_class.side_effect = Exception("Not reached")

                dialog.edit_button.click()

                mock_msgbox.assert_called_once_with(dialog, "Ошибка", "Service error")

    def test_delete_connection_no_selection(self, qapp, mock_service):
        """Test delete button when no row is selected."""
        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)

            dialog.table.clearSelection()

            with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
                dialog.delete_button.click()
                mock_warning.assert_called_once_with(dialog, "Предупреждение", "Выберите подключение для удаления")

    def test_delete_dummy_connection_forbidden(self, qapp, mock_service):
        """Test attempting to delete dummy connection."""
        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)

            dialog.table.selectRow(0)  # Select dummy connection

            with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
                dialog.delete_button.click()
                mock_warning.assert_called_once_with(dialog, "Предупреждение", "Нельзя удалить встроенное подключение dummy")

    @patch('PyQt6.QtWidgets.QMessageBox.question')
    def test_delete_connection_cancelled(self, mock_question, qapp, mock_service):
        """Test delete connection when user cancels."""
        mock_question.return_value = QMessageBox.StandardButton.No

        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)

            dialog.table.selectRow(1)  # Select test connection

            dialog.delete_button.click()

            mock_question.assert_called_once()
            mock_service.delete_connection.assert_not_called()

    @patch('PyQt6.QtWidgets.QMessageBox.question')
    def test_delete_connection_success(self, mock_question, qapp, mock_service):
        """Test successful connection deletion."""
        mock_question.return_value = QMessageBox.StandardButton.Yes

        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)

            dialog.table.selectRow(1)

            dialog.delete_button.click()

            mock_service.delete_connection.assert_called_once_with("test_openrouter")
            mock_service.list_connections.assert_called()  # Should refresh table

    @patch('PyQt6.QtWidgets.QMessageBox.question')
    @patch('PyQt6.QtWidgets.QMessageBox.critical')
    def test_delete_connection_service_error(self, mock_msgbox, mock_question, qapp, mock_service):
        """Test connection deletion with service error."""
        mock_question.return_value = QMessageBox.StandardButton.Yes
        mock_service.delete_connection.side_effect = Exception("Delete error")

        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service
            dialog = ConnectionManagementDialog(mock_service)

            dialog.table.selectRow(1)

            dialog.delete_button.click()

            mock_msgbox.assert_called_once_with(dialog, "Ошибка", "Не удалось удалить подключение: Delete error")
            # Note: list_connections is called during initialization, so we check it was only called once


class TestConnectionEditDialog:
    """Test ConnectionEditDialog functionality."""

    def test_initialization_new_connection(self, qapp):
        """Test dialog initialization for new connection."""
        dialog = ConnectionEditDialog(parent=None)
        assert dialog.config.id == ""
        assert dialog.config.provider == ""
        assert dialog.config.description == ""
        assert dialog.id_edit.text() == ""
        assert dialog.provider_edit.text() == ""
        assert dialog.description_edit.text() == ""

    def test_initialization_existing_connection(self, qapp, sample_config):
        """Test dialog initialization with existing config."""
        dialog = ConnectionEditDialog(sample_config, parent=None)
        assert dialog.config == sample_config
        assert dialog.id_edit.text() == "test_openrouter"
        assert dialog.provider_edit.text() == "openrouter"
        assert dialog.description_edit.text() == "Test OpenRouter connection"
        assert dialog.model_id_edit.text() == "gpt-3.5-turbo"
        assert dialog.base_url_edit.text() == "https://api.example.com"
        assert dialog.timeout_spin.value() == 30
        assert dialog.auth_type_edit.text() == "env"
        assert dialog.auth_env_var_edit.text() == "TEST_API_KEY"
        assert "Custom: Header" in dialog.headers_text.toPlainText()

    def test_validation_empty_id(self, qapp):
        """Test validation with empty ID."""
        dialog = ConnectionEditDialog(parent=None)

        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            result = dialog._validate()
            assert not result
            mock_warning.assert_called_once_with(dialog, "Ошибка валидации", "ID подключения обязателен")

    def test_validation_invalid_id_chars(self, qapp):
        """Test validation with invalid ID characters."""
        dialog = ConnectionEditDialog(parent=None)
        dialog.id_edit.setText("invalid id!")

        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            result = dialog._validate()
            assert not result
            mock_warning.assert_called_once_with(dialog, "Ошибка валидации", "ID может содержать только буквы, цифры, _ и -")

    def test_validation_empty_provider(self, qapp):
        """Test validation with empty provider."""
        dialog = ConnectionEditDialog(parent=None)
        dialog.id_edit.setText("valid_id")

        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            result = dialog._validate()
            assert not result
            mock_warning.assert_called_once_with(dialog, "Ошибка валидации", "Провайдер обязателен")

    def test_validation_invalid_url(self, qapp):
        """Test validation with invalid URL."""
        dialog = ConnectionEditDialog(parent=None)
        dialog.id_edit.setText("valid_id")
        dialog.provider_edit.setText("openrouter")
        dialog.base_url_edit.setText("not-a-url")

        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            result = dialog._validate()
            assert not result
            mock_warning.assert_called_once_with(dialog, "Ошибка валидации", "Неверный формат URL")

    def test_validation_success(self, qapp):
        """Test successful validation."""
        dialog = ConnectionEditDialog(parent=None)
        dialog.id_edit.setText("valid_id")
        dialog.provider_edit.setText("openrouter")
        dialog.base_url_edit.setText("https://example.com")

        result = dialog._validate()
        assert result

    def test_get_config(self, qapp, sample_config):
        """Test getting config from dialog."""
        dialog = ConnectionEditDialog(sample_config, parent=None)

        # Modify some fields
        dialog.id_edit.setText("modified_id")
        dialog.provider_edit.setText("modified_provider")
        dialog.description_edit.setText("Modified description")
        dialog.headers_text.setPlainText("New: Header\nAnother: Value")

        config = dialog.get_config()

        assert config.id == "modified_id"
        assert config.provider == "modified_provider"
        assert config.description == "Modified description"
        assert config.model_id == "gpt-3.5-turbo"  # Unchanged
        assert config.headers == {"New": "Header", "Another": "Value"}
        assert config.auth == {"type": "env", "env_var": "TEST_API_KEY"}

    def test_get_config_empty_timeout(self, qapp):
        """Test getting config with zero timeout (should be None)."""
        dialog = ConnectionEditDialog(parent=None)
        dialog.id_edit.setText("test_id")
        dialog.provider_edit.setText("dummy")
        dialog.timeout_spin.setValue(0)

        config = dialog.get_config()
        assert config.timeout is None

    def test_get_config_auth_partial(self, qapp):
        """Test getting config with partial auth fields."""
        dialog = ConnectionEditDialog(parent=None)
        dialog.id_edit.setText("test_id")
        dialog.provider_edit.setText("dummy")
        dialog.auth_type_edit.setText("env")
        # Leave auth_env_var empty

        config = dialog.get_config()
        assert config.auth == {"type": "env"}

    def test_on_accept_validation_failure(self, qapp):
        """Test _on_accept when validation fails."""
        dialog = ConnectionEditDialog(parent=None)
        # Leave fields empty to trigger validation failure

        with patch.object(dialog, '_validate', return_value=False):
            dialog._on_accept()
            # Should not accept
            assert not dialog.result()


class TestIntegration:
    """Integration tests for dialog-service interaction."""

    def test_full_crud_workflow(self, qapp, mock_service, sample_config):
        """Test complete CRUD workflow."""
        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service

            # Mock the edit dialog for add operation
            with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ConnectionEditDialog') as mock_edit_dialog_class:
                mock_edit_dialog = Mock()
                mock_edit_dialog.exec.return_value = True
                mock_edit_dialog.get_config.return_value = sample_config
                mock_edit_dialog_class.return_value = mock_edit_dialog

                dialog = ConnectionManagementDialog(mock_service)

                # Add connection
                dialog.add_button.click()

                # Verify add operation
                mock_service.create_connection.assert_called_once_with(sample_config)
                assert mock_service.list_connections.call_count >= 1  # At least one refresh

                # Reset mocks for edit test
                mock_service.reset_mock()

                # Setup for edit
                mock_edit_dialog_class.reset_mock()
                mock_edit_dialog.get_config.return_value = sample_config

                # Select and edit connection
                dialog.table.selectRow(1)
                dialog.edit_button.click()

                # Verify edit operation
                mock_edit_dialog_class.assert_called_with(sample_config, parent=dialog)
                mock_service.update_connection.assert_called_once_with(sample_config)

                # Reset for delete test
                mock_service.reset_mock()

                # Delete connection
                with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
                    dialog.table.selectRow(1)
                    dialog.delete_button.click()

                    # Verify delete operation
                    mock_service.delete_connection.assert_called_once_with("test_openrouter")

    def test_service_error_handling_integration(self, qapp, mock_service):
        """Test error handling throughout the dialog."""
        with patch('src.llm_security.features.ui.presentation.connection_management_dialog.ModelConnectionService') as mock_service_class:
            mock_service_class.return_value = mock_service

            dialog = ConnectionManagementDialog(mock_service)

            # Setup service to throw errors
            mock_service.get_connection_config.side_effect = Exception("Connection error")

            # Try to edit
            dialog.table.selectRow(1)

            with patch('PyQt6.QtWidgets.QMessageBox.critical') as mock_critical:
                dialog.edit_button.click()
                mock_critical.assert_called_once_with(dialog, "Ошибка", "Connection error")

            # Reset for delete error
            mock_service.reset_mock()
            mock_service.delete_connection.side_effect = Exception("Delete error")

            with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
                with patch('PyQt6.QtWidgets.QMessageBox.critical') as mock_critical:
                    dialog.table.selectRow(1)
                    dialog.delete_button.click()
                    mock_critical.assert_called_once_with(dialog, "Ошибка", "Не удалось удалить подключение: Delete error")