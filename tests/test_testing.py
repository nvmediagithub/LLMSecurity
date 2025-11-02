import pytest
from unittest.mock import Mock

from src.llm_security.features.defense.application.pipeline import DefensePipeline
from src.llm_security.features.defense.domain.entities import Decision, DefenseResult, PromptBundle
from src.llm_security.features.defense.domain.profile import DefenseProfile
from src.llm_security.features.testing.application.evaluator import OutputEvaluator
from src.llm_security.features.testing.application.runner import TestRunner
from src.llm_security.features.testing.application.service import TestSuiteService, ABTestResult
from src.llm_security.features.testing.domain.models import PassCriteria, PromptTest
from src.llm_security.features.testing.infrastructure.repositories.yaml_tests_repository import PromptTestRepository


class MockModelClient:
    def __init__(self, response: str = "Mock response"):
        self.response = response
        self.model_id = "mock-model"

    def generate(self, prompt_bundle: PromptBundle) -> str:
        return self.response


class MockLayer:
    def __init__(self, layer_id: str, decision: Decision = Decision.ALLOW, reason: str = ""):
        self.id = layer_id
        self.enabled = True
        self._decision = decision
        self._reason = reason

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        if self._decision == Decision.BLOCK:
            return DefenseResult.block(self.id, reason=self._reason)
        elif self._decision == Decision.ESCALATE:
            return DefenseResult.escalate(self.id, reason=self._reason)
        elif self._decision == Decision.REWRITE:
            return DefenseResult.rewrite(self.id, rewritten_text="rewritten prompt", reason=self._reason)
        else:
            return DefenseResult.allow(self.id, reason=self._reason)

    def after_recv(self, prompt_bundle: PromptBundle, response_text: str) -> DefenseResult:
        return DefenseResult.allow(self.id)


class TestOutputEvaluator:
    def test_evaluate_pass_must_contain(self):
        evaluator = OutputEvaluator()
        criteria = PassCriteria(must_contain_any=["success", "passed"])
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )
        result = evaluator.evaluate(test, "This test passed successfully")
        assert result.passed is True
        assert result.reason == "ok"
        assert result.matched_criteria["must_contain_any"] is True

    def test_evaluate_fail_must_contain(self):
        evaluator = OutputEvaluator()
        criteria = PassCriteria(must_contain_any=["success"])
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )
        result = evaluator.evaluate(test, "This test failed")
        assert result.passed is False
        assert "must_contain_any" in result.reason
        assert result.matched_criteria["must_contain_any"] is False

    def test_evaluate_pass_must_not_contain(self):
        evaluator = OutputEvaluator()
        criteria = PassCriteria(must_not_contain_any=["error", "fail"])
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )
        result = evaluator.evaluate(test, "This test passed")
        assert result.passed is True
        assert result.reason == "ok"
        assert result.matched_criteria["must_not_contain_any"] is True

    def test_evaluate_fail_must_not_contain(self):
        evaluator = OutputEvaluator()
        criteria = PassCriteria(must_not_contain_any=["error"])
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )
        result = evaluator.evaluate(test, "This test has error")
        assert result.passed is False
        assert "must_not_contain_any" in result.reason
        assert result.matched_criteria["must_not_contain_any"] is False

    def test_evaluate_case_insensitive(self):
        evaluator = OutputEvaluator()
        criteria = PassCriteria(must_contain_any=["SUCCESS"])
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )
        result = evaluator.evaluate(test, "This test success")
        assert result.passed is True

    def test_evaluate_empty_criteria(self):
        evaluator = OutputEvaluator()
        criteria = PassCriteria()
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )
        result = evaluator.evaluate(test, "Any response")
        assert result.passed is True

    def test_evaluate_empty_response(self):
        evaluator = OutputEvaluator()
        criteria = PassCriteria(must_contain_any=["test"])
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )
        result = evaluator.evaluate(test, "")
        assert result.passed is False


class TestTestRunner:
    def test_run_test_successful(self):
        mock_client = MockModelClient("Positive response")
        evaluator = OutputEvaluator()
        pipeline = DefensePipeline([MockLayer("L1")])

        def pipeline_factory(profile):
            return pipeline

        runner = TestRunner(mock_client, evaluator, pipeline_factory)

        criteria = PassCriteria(must_contain_any=["positive"])
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )
        profile = DefenseProfile(id="profile1", title="Profile 1", description="", enabled_layers=["L1"], params={})

        result = runner.run_test(test, profile)

        assert result.test == test
        assert result.response == "Positive response"
        assert result.passed is True
        assert result.defense_decision == "allow"
        assert len(result.defense_logs_before) == 1
        assert len(result.defense_logs_after) == 1
        assert result.duration_ms > 0

    def test_run_test_blocked_before_send(self):
        mock_client = Mock()
        evaluator = OutputEvaluator()
        blocking_layer = MockLayer("L1", Decision.BLOCK, "blocked")

        def pipeline_factory(profile):
            return DefensePipeline([blocking_layer])

        runner = TestRunner(mock_client, evaluator, pipeline_factory)

        criteria = PassCriteria(must_contain_any=["test"])
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )
        profile = DefenseProfile(id="profile1", title="Profile 1", description="", enabled_layers=["L1"], params={})

        result = runner.run_test(test, profile)

        assert result.response == ""
        assert result.passed is True
        assert result.evaluation.reason == "blocked_by:L1"
        assert result.defense_decision == "block"
        mock_client.generate.assert_not_called()

    def test_run_test_escalated_before_send(self):
        mock_client = Mock()
        evaluator = OutputEvaluator()
        escalating_layer = MockLayer("L1", Decision.ESCALATE, "escalated")

        def pipeline_factory(profile):
            return DefensePipeline([escalating_layer])

        runner = TestRunner(mock_client, evaluator, pipeline_factory)

        criteria = PassCriteria(must_contain_any=["test"])
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )
        profile = DefenseProfile(id="profile1", title="Profile 1", description="", enabled_layers=["L1"], params={})

        result = runner.run_test(test, profile)

        assert result.response == ""
        assert result.passed is False
        assert result.evaluation.reason == "escalated"
        assert result.defense_decision == "escalate"
        mock_client.generate.assert_not_called()

    def test_run_test_baseline_profile(self):
        mock_client = MockModelClient("Response")
        evaluator = OutputEvaluator()

        def pipeline_factory(profile):
            return DefensePipeline([])  # Empty pipeline for baseline

        runner = TestRunner(mock_client, evaluator, pipeline_factory)

        criteria = PassCriteria(must_contain_any=["response"])
        test = PromptTest(
            id="test1",
            category="test",
            name="Test 1",
            system_prompt="system",
            user_prompt="prompt",
            pass_criteria=criteria
        )

        result = runner.run_test(test)  # No profile provided

        assert result.response == "Response"
        assert result.passed is True

    def test_collect_layer_ids(self):
        # Test the static method _collect_layer_ids
        from src.llm_security.features.testing.application.runner import TestRunner

        results = [
            DefenseResult.allow("L1"),
            DefenseResult.block("L2", reason="blocked"),
            DefenseResult.allow("L3")
        ]
        # Use pytest to access private method for testing
        ids = TestRunner._collect_layer_ids(results)
        assert ids == "L1,L2,L3"


class TestTestSuiteService:
    def test_list_tests(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {
                    "id": "test1",
                    "category": "injection",
                    "name": "Test 1",
                    "system_prompt": "system",
                    "user_prompt": "prompt",
                    "pass_criteria": {"must_contain_any": ["success"]},
                    "severity": "high"
                }
            ],
            "categories": [{"id": "injection", "title": "Injection Tests"}],
            "controls": []
        }
        mock_loader.load_policy.return_value = {"policy": {}}

        service = TestSuiteService(config_loader=mock_loader)
        tests = service.list_tests()
        assert len(tests) == 1
        assert tests[0].id == "test1"
        assert tests[0].category == "injection"

    def test_list_profiles(self):
        mock_loader = Mock()
        mock_loader.load_profiles.return_value = {
            "profiles": {
                "profile1": {"title": "Profile 1", "enabled_layers": ["L1"]},
                "profile2": {"title": "Profile 2", "enabled_layers": ["L1", "L2"]}
            }
        }
        mock_loader.load_policy.return_value = {"policy": {}}

        service = TestSuiteService(config_loader=mock_loader)
        profiles = service.list_profiles()
        assert len(profiles) == 2
        assert profiles[0].id == "profile1"

    def test_run_suite_with_filters(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {
                    "id": "test1",
                    "category": "injection",
                    "name": "Test 1",
                    "system_prompt": "system",
                    "user_prompt": "prompt",
                    "pass_criteria": {"must_contain_any": ["success"]},
                    "severity": "high"
                },
                {
                    "id": "test2",
                    "category": "other",
                    "name": "Test 2",
                    "system_prompt": "system",
                    "user_prompt": "prompt",
                    "pass_criteria": {"must_contain_any": ["success"]},
                    "severity": "high"
                }
            ],
            "categories": [
                {"id": "injection", "title": "Injection Tests"},
                {"id": "other", "title": "Other Tests"}
            ],
            "controls": []
        }
        mock_loader.load_profiles.return_value = {
            "profiles": {"profile1": {"title": "Profile 1", "enabled_layers": []}}
        }
        mock_loader.load_policy.return_value = {"policy": {}}

        service = TestSuiteService(config_loader=mock_loader, model_client=MockModelClient("success response"))
        result = service.run_suite("profile1", categories=["injection"])

        assert len(result.runs) == 1
        assert result.runs[0].test.id == "test1"

    def test_run_suite_with_test_ids(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {
                    "id": "test1",
                    "category": "injection",
                    "name": "Test 1",
                    "system_prompt": "system",
                    "user_prompt": "prompt",
                    "pass_criteria": {"must_contain_any": ["success"]},
                    "severity": "high"
                },
                {
                    "id": "test2",
                    "category": "injection",
                    "name": "Test 2",
                    "system_prompt": "system",
                    "user_prompt": "prompt",
                    "pass_criteria": {"must_contain_any": ["success"]},
                    "severity": "high"
                }
            ],
            "categories": [{"id": "injection", "title": "Injection Tests"}],
            "controls": []
        }
        mock_loader.load_profiles.return_value = {
            "profiles": {"profile1": {"title": "Profile 1", "enabled_layers": []}}
        }

        mock_loader.load_policy.return_value = {"policy": {}}

        service = TestSuiteService(config_loader=mock_loader, model_client=MockModelClient("success response"))
        result = service.run_suite("profile1", test_ids=["test1"])

        assert len(result.runs) == 1
        assert result.runs[0].test.id == "test1"

    def test_run_baseline(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {
                    "id": "test1",
                    "category": "injection",
                    "name": "Test 1",
                    "system_prompt": "system",
                    "user_prompt": "prompt",
                    "pass_criteria": {"must_contain_any": ["success"]},
                    "severity": "high"
                }
            ],
            "categories": [{"id": "injection", "title": "Injection Tests"}],
            "controls": []
        }

        mock_loader.load_policy.return_value = {"policy": {}}

        service = TestSuiteService(config_loader=mock_loader, model_client=MockModelClient("success response"))
        result = service.run_baseline()

        assert result.profile.id == "baseline"
        assert len(result.runs) == 1
        assert result.runs[0].passed is True

    def test_run_ab(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {
                    "id": "test1",
                    "category": "injection",
                    "name": "Test 1",
                    "system_prompt": "system",
                    "user_prompt": "prompt",
                    "pass_criteria": {"must_contain_any": ["success"]},
                    "severity": "high"
                }
            ],
            "categories": [{"id": "injection", "title": "Injection Tests"}],
            "controls": []
        }
        mock_loader.load_profiles.return_value = {
            "profiles": {"profile1": {"title": "Profile 1", "enabled_layers": []}}
        }

        mock_loader.load_policy.return_value = {"policy": {}}

        service = TestSuiteService(config_loader=mock_loader, model_client=MockModelClient("success response"))
        result = service.run_ab("profile1")

        assert isinstance(result, ABTestResult)
        assert result.baseline.profile.id == "baseline"
        assert result.protected.profile.id == "profile1"
        assert result.delta_pass_rate == 0.0  # Both should have 100% pass rate

    def test_select_tests_no_filters(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {"id": "test1", "category": "cat1", "system_prompt": "", "user_prompt": "", "pass_criteria": {}, "severity": "medium"},
                {"id": "test2", "category": "cat2", "system_prompt": "", "user_prompt": "", "pass_criteria": {}, "severity": "medium"}
            ],
            "categories": [],
            "controls": []
        }

        mock_loader.load_policy.return_value = {"policy": {}}

        service = TestSuiteService(config_loader=mock_loader)
        tests = service._select_tests()
        assert len(tests) == 2

    def test_select_tests_with_categories(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {"id": "test1", "category": "cat1", "system_prompt": "", "user_prompt": "", "pass_criteria": {}, "severity": "medium"},
                {"id": "test2", "category": "cat2", "system_prompt": "", "user_prompt": "", "pass_criteria": {}, "severity": "medium"}
            ],
            "categories": [],
            "controls": []
        }

        mock_loader.load_policy.return_value = {"policy": {}}

        service = TestSuiteService(config_loader=mock_loader)
        tests = service._select_tests(categories=["cat1"])
        assert len(tests) == 1
        assert tests[0].id == "test1"

    def test_select_tests_with_test_ids(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {"id": "test1", "category": "cat1", "system_prompt": "", "user_prompt": "", "pass_criteria": {}, "severity": "medium"},
                {"id": "test2", "category": "cat1", "system_prompt": "", "user_prompt": "", "pass_criteria": {}, "severity": "medium"}
            ],
            "categories": [],
            "controls": []
        }

        mock_loader.load_policy.return_value = {"policy": {}}

        service = TestSuiteService(config_loader=mock_loader)
        tests = service._select_tests(test_ids=["test2"])
        assert len(tests) == 1
        assert tests[0].id == "test2"


class TestPromptTestRepository:
    def test_load_and_cache(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {
                    "id": "test1",
                    "category": "injection",
                    "name": "Test 1",
                    "system_prompt": "system",
                    "user_prompt": "prompt",
                    "pass_criteria": {"must_contain_any": ["success"]},
                    "severity": "high"
                }
            ],
            "categories": [{"id": "injection", "title": "Injection Tests"}],
            "controls": []
        }

        repo = PromptTestRepository(mock_loader)
        categories, tests = repo.load()
        assert len(tests) == 1
        assert "test1" in tests
        assert tests["test1"].category == "injection"

        # Second load should be from cache
        mock_loader.load_tests.reset_mock()
        categories2, tests2 = repo.load()
        assert categories == categories2
        assert tests == tests2
        mock_loader.load_tests.assert_not_called()

    def test_load_force_reload(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {"tests": [], "categories": [], "controls": []}

        repo = PromptTestRepository(mock_loader)
        repo.load()  # Cache
        repo.load(force=True)  # Force reload
        assert mock_loader.load_tests.call_count == 2

    def test_tests_and_categories_iterators(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {
                    "id": "test1",
                    "category": "injection",
                    "name": "Test 1",
                    "system_prompt": "system",
                    "user_prompt": "prompt",
                    "pass_criteria": {"must_contain_any": ["success"]},
                    "severity": "high"
                }
            ],
            "categories": [{"id": "injection", "title": "Injection Tests"}],
            "controls": []
        }

        repo = PromptTestRepository(mock_loader)
        tests = list(repo.tests())
        categories = list(repo.categories())
        assert len(tests) == 1
        assert len(categories) == 1
        assert categories[0].id == "injection"

    def test_get_existing_test(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {
            "tests": [
                {
                    "id": "test1",
                    "category": "injection",
                    "name": "Test 1",
                    "system_prompt": "system",
                    "user_prompt": "prompt",
                    "pass_criteria": {"must_contain_any": ["success"]},
                    "severity": "high"
                }
            ],
            "categories": [],
            "controls": []
        }

        repo = PromptTestRepository(mock_loader)
        test = repo.get("test1")
        assert test.id == "test1"
        assert test.category == "injection"

    def test_get_nonexistent_test_raises_keyerror(self):
        mock_loader = Mock()
        mock_loader.load_tests.return_value = {"tests": [], "categories": [], "controls": []}

        repo = PromptTestRepository(mock_loader)
        with pytest.raises(KeyError, match="Unknown test id"):
            repo.get("nonexistent")