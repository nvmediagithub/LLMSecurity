"""Тесты для унифицированной системы эмуляции атак."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.llm_security.features.attacks import (
    AttackCategory,
    AttackDefinition,
    AttackResult,
    AttackSuite,
    AttackExecutionContext,
    AttackExecutor,
    AttackManager,
    AttackScheduler,
    AttackRegistry,
    AttackFactory,
    InMemoryAttackResultStorage,
    InMemoryAttackRepository,
    InMemoryAttackSuiteRepository,
)
from src.llm_security.features.attacks.infrastructure import (
    HTMLInjectionEmulator,
    MultiLayerAttackExecutor,
)
from src.llm_security.features.defense.domain.entities import PromptBundle
from src.llm_security.features.layers.domain.interfaces import ILayer


class MockLayer(ILayer):
    """Мок слой защиты для тестирования."""

    def __init__(self, layer_id: str, enabled: bool = True):
        self.id = layer_id
        self.enabled = enabled
        self.before_call_count = 0
        self.after_call_count = 0

    def before_send(self, prompt_bundle):
        self.before_call_count += 1
        return MagicMock(decision="allow", reason=f"Layer {self.id} allows")

    def after_recv(self, prompt_bundle, response_text):
        self.after_call_count += 1
        return MagicMock(decision="allow", reason=f"Layer {self.id} allows response")


class TestAttackDomain:
    """Тесты доменного слоя атак."""

    def test_attack_definition_creation(self):
        """Тест создания определения атаки."""
        attack = AttackDefinition(
            id="test_attack",
            name="Test Attack",
            description="A test attack",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert(1)</script>",
            target_layer="l3",
            expected_success=False,
        )

        assert attack.id == "test_attack"
        assert attack.name == "Test Attack"
        assert attack.category == AttackCategory.HTML_INJECTION
        assert attack.payload == "<script>alert(1)</script>"
        assert attack.target_layer == "l3"
        assert attack.expected_success is False

    def test_attack_result_creation(self):
        """Тест создания результата атаки."""
        attack = AttackDefinition(
            id="test_attack",
            name="Test Attack",
            description="A test attack",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert(1)</script>",
            target_layer="l3",
        )

        result = AttackResult(
            attack=attack,
            success=False,
            layer_response={"decision": "block", "reason": "HTML injection detected"},
            metrics={"threats_found": 1},
        )

        assert result.attack == attack
        assert result.success is False
        assert result.layer_decision == "block"
        assert result.layer_reason == "HTML injection detected"


class TestAttackInfrastructure:
    """Тесты инфраструктурного слоя атак."""

    def test_attack_registry(self):
        """Тест реестра атак."""
        registry = AttackRegistry()

        # Создаем атаку и эмулятор
        attack = AttackDefinition(
            id="test_attack",
            name="Test Attack",
            description="A test attack",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert(1)</script>",
            target_layer="l3",
        )

        emulator = HTMLInjectionEmulator()

        # Регистрируем
        registry.register_attack_definition(attack)
        registry.register_emulator("test_attack", emulator)

        # Проверяем регистрацию
        assert registry.is_registered("test_attack")
        assert registry.get_attack_definition("test_attack") == attack
        assert registry.get_emulator("test_attack") == emulator

        # Проверяем получение по категории
        html_attacks = registry.get_attack_definitions_by_category("html_injection")
        assert len(html_attacks) == 1
        assert html_attacks[0] == attack

    @pytest.mark.asyncio
    async def test_in_memory_result_storage(self):
        """Тест in-memory хранилища результатов."""
        storage = InMemoryAttackResultStorage()

        attack = AttackDefinition(
            id="test_attack",
            name="Test Attack",
            description="A test attack",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert(1)</script>",
            target_layer="l3",
        )

        result = AttackResult(
            attack=attack,
            success=False,
            layer_response={"decision": "block"},
        )

        # Сохраняем результат
        await storage.save_result(result)

        # Получаем результаты
        results_by_attack = await storage.get_results_by_attack("test_attack")
        results_by_layer = await storage.get_results_by_layer("l3")
        recent_results = await storage.get_recent_results(10)

        assert len(results_by_attack) == 1
        assert len(results_by_layer) == 1
        assert len(recent_results) == 1
        assert results_by_attack[0] == result

    def test_html_injection_emulator(self):
        """Тест HTML injection эмулятора."""
        emulator = HTMLInjectionEmulator()
        attack = AttackDefinition(
            id="html_script",
            name="Script Injection",
            description="Script tag injection",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert('XSS')</script>",
            target_layer="l3",
        )

        prompt_bundle = PromptBundle(
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello, how are you?",
        )

        context = AttackExecutionContext(
            attack=attack,
            prompt_bundle=prompt_bundle,
            layer_instance=MockLayer("l3"),
        )

        result = emulator.emulate_attack(context)

        assert result.attack == attack
        assert result.success is True  # Атака должна быть успешной (опасный HTML присутствует)
        assert result.layer_response["decision"] == "allow"
        assert "HTML injection allowed" in result.layer_response["reason"]


class TestAttackApplication:
    """Тесты прикладного слоя атак."""

    @pytest.mark.asyncio
    async def test_attack_executor(self):
        """Тест исполнителя атак."""
        # Создаем мок эмулятора
        mock_emulator = MagicMock()
        mock_result = AttackResult(
            attack=AttackDefinition(
                id="test",
                name="Test",
                description="Test attack",
                category=AttackCategory.HTML_INJECTION,
                payload="test",
                target_layer="l3",
            ),
            success=False,
            layer_response={"decision": "block"},
        )
        mock_emulator.emulate_attack.return_value = mock_result

        # Создаем executor
        storage = InMemoryAttackResultStorage()
        executor = AttackExecutor(mock_emulator, storage)

        # Создаем тестовые данные
        attack = AttackDefinition(
            id="test_attack",
            name="Test Attack",
            description="A test attack",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert(1)</script>",
            target_layer="l3",
        )

        prompt_bundle = PromptBundle(
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello",
        )

        layer = MockLayer("l3")

        # Выполняем атаку
        result = await executor.execute_attack(attack, prompt_bundle, layer)

        assert result == mock_result
        mock_emulator.emulate_attack.assert_called_once()

        # Проверяем сохранение в хранилище
        saved_results = await storage.get_results_by_attack("test")
        assert len(saved_results) == 1
        assert saved_results[0] == mock_result

    @pytest.mark.asyncio
    async def test_attack_manager(self):
        """Тест менеджера атак."""
        # Создаем репозитории
        attack_repo = InMemoryAttackRepository()
        suite_repo = InMemoryAttackSuiteRepository()
        storage = InMemoryAttackResultStorage()

        # Создаем executor с мок эмулятором
        mock_emulator = MagicMock()
        mock_result = AttackResult(
            attack=AttackDefinition(
                id="test",
                name="Test",
                description="Test attack",
                category=AttackCategory.HTML_INJECTION,
                payload="test",
                target_layer="l3",
            ),
            success=False,
            layer_response={"decision": "block"},
        )
        mock_emulator.emulate_attack.return_value = mock_result

        executor = AttackExecutor(mock_emulator, storage)
        manager = AttackManager(attack_repo, suite_repo, executor, storage)

        # Добавляем атаку в репозиторий
        attack = AttackDefinition(
            id="test_attack",
            name="Test Attack",
            description="A test attack",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert(1)</script>",
            target_layer="l3",
        )
        attack_repo.add_attack(attack)

        # Выполняем атаку через менеджер
        prompt_bundle = PromptBundle(
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello",
        )
        layer = MockLayer("l3")

        result = await manager.execute_attack("test_attack", prompt_bundle, layer)

        assert result is not None
        assert result.success is False

    @pytest.mark.asyncio
    async def test_attack_scheduler(self):
        """Тест планировщика атак."""
        # Создаем компоненты
        attack_repo = InMemoryAttackRepository()
        suite_repo = InMemoryAttackSuiteRepository()
        storage = InMemoryAttackResultStorage()

        mock_emulator = MagicMock()
        mock_result = AttackResult(
            attack=AttackDefinition(
                id="test",
                name="Test",
                description="Test attack",
                category=AttackCategory.HTML_INJECTION,
                payload="test",
                target_layer="l3",
            ),
            success=False,
            layer_response={"decision": "block"},
        )
        mock_emulator.emulate_attack.return_value = mock_result

        executor = AttackExecutor(mock_emulator, storage)
        scheduler = AttackScheduler(attack_repo, suite_repo, executor, storage)

        # Добавляем атаку
        attack = AttackDefinition(
            id="test_attack",
            name="Test Attack",
            description="A test attack",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert(1)</script>",
            target_layer="l3",
        )
        attack_repo.add_attack(attack)

        # Создаем suite
        suite = AttackSuite(
            id="test_suite",
            name="Test Suite",
            description="A test suite",
            target_layer="l3",
            attacks=[attack],
        )
        suite_repo.add_suite(suite)

        # Выполняем suite
        prompt_bundle = PromptBundle(
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello",
        )
        layer = MockLayer("l3")

        results = await scheduler.schedule_attack_suite("test_suite", prompt_bundle, layer)

        assert len(results) == 1
        assert results[0].success is False


class TestMultiLayerExecution:
    """Тесты многослойного выполнения атак."""

    @pytest.mark.asyncio
    async def test_multi_layer_executor(self):
        """Тест исполнителя многослойных атак."""
        mock_emulator = MagicMock()
        mock_result = MagicMock(
            attack=AttackDefinition(
                id="test",
                name="Test",
                description="Test attack",
                category=AttackCategory.HTML_INJECTION,
                payload="test",
                target_layer="l3",
            ),
            success=False,
            layer_response={"decision": "allow"},  # Меняем на allow для последовательного выполнения
        )
        mock_emulator.emulate_attack.return_value = mock_result

        storage = InMemoryAttackResultStorage()
        executor = MultiLayerAttackExecutor(mock_emulator, storage)

        # Создаем атаки и слои
        attack = AttackDefinition(
            id="test_attack",
            name="Test Attack",
            description="A test attack",
            category=AttackCategory.HTML_INJECTION,
            payload="<script>alert(1)</script>",
            target_layer="l3",
        )

        prompt_bundle = PromptBundle(
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello",
        )

        layers = [MockLayer("l1"), MockLayer("l2"), MockLayer("l3")]

        # Выполняем на конвейере
        result = await executor.execute_on_pipeline(attack, prompt_bundle, layers)

        assert result["attack"] == attack
        assert result["successful"] is True  # Атака проходит через все слои
        assert len(result["layer_results"]) == 3  # Все слои выполняются
        assert result["blocked_at_layer"] is None  # Не заблокирована нигде


if __name__ == "__main__":
    pytest.main([__file__])