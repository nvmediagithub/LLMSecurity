import pytest
from unittest.mock import Mock

from src.llm_security.features.defense.application.pipeline import DefensePipeline
from src.llm_security.features.defense.application.profiles_service import ProfileRepository
from src.llm_security.features.defense.domain.entities import Decision, DefenseResult, PromptBundle
from src.llm_security.features.defense.domain.profile import DefenseProfile
from src.llm_security.features.defense.domain.policy import PolicyRules
from src.llm_security.features.defense.infrastructure.factory import DefensePipelineBuilder
from src.llm_security.features.defense.infrastructure.layers.base import BaseDefenseLayer


# Mock layers for testing
class MockLayer(BaseDefenseLayer):
    def __init__(self, layer_id: str, decision_before: Decision = Decision.ALLOW, decision_after: Decision = Decision.ALLOW, reason: str = ""):
        self.id = layer_id
        self.enabled = True
        self._decision_before = decision_before
        self._decision_after = decision_after
        self._reason = reason

    def before_send(self, prompt_bundle: PromptBundle) -> DefenseResult:
        if self._decision_before == Decision.BLOCK:
            return DefenseResult.block(self.id, reason=self._reason)
        elif self._decision_before == Decision.ESCALATE:
            return DefenseResult.escalate(self.id, reason=self._reason)
        elif self._decision_before == Decision.REWRITE:
            return DefenseResult.rewrite(self.id, rewritten_text="rewritten prompt", reason=self._reason)
        else:
            return DefenseResult.allow(self.id, reason=self._reason)

    def after_recv(self, prompt_bundle: PromptBundle, response_text: str) -> DefenseResult:
        if self._decision_after == Decision.BLOCK:
            return DefenseResult.block(self.id, reason=self._reason)
        elif self._decision_after == Decision.ESCALATE:
            return DefenseResult.escalate(self.id, reason=self._reason)
        elif self._decision_after == Decision.REWRITE:
            return DefenseResult.rewrite(self.id, rewritten_text="rewritten response", reason=self._reason)
        else:
            return DefenseResult.allow(self.id, reason=self._reason)


class TestDefenseResult:
    def test_allow_creation(self):
        result = DefenseResult.allow("L1", reason="test")
        assert result.decision == Decision.ALLOW
        assert result.layer_id == "L1"
        assert result.reason == "test"
        assert result.rewritten_text is None

    def test_block_creation(self):
        result = DefenseResult.block("L1", reason="blocked")
        assert result.decision == Decision.BLOCK
        assert result.layer_id == "L1"
        assert result.reason == "blocked"

    def test_rewrite_creation(self):
        result = DefenseResult.rewrite("L1", rewritten_text="new text", reason="rewritten")
        assert result.decision == Decision.REWRITE
        assert result.layer_id == "L1"
        assert result.rewritten_text == "new text"
        assert result.reason == "rewritten"

    def test_escalate_creation(self):
        result = DefenseResult.escalate("L1", reason="escalated")
        assert result.decision == Decision.ESCALATE
        assert result.layer_id == "L1"
        assert result.reason == "escalated"


class TestPromptBundle:
    def test_update_method(self):
        bundle = PromptBundle(system_prompt="system", user_prompt="user", context={"key": "value"})
        updated = bundle.update(user_prompt="new user")
        assert updated.system_prompt == "system"
        assert updated.user_prompt == "new user"
        assert updated.context == {"key": "value"}


class TestDefensePipeline:
    def test_empty_pipeline(self):
        pipeline = DefensePipeline([])
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = pipeline.guard_before(bundle)
        assert result.decision == Decision.ALLOW
        assert result.payload == bundle

    def test_allow_layers(self):
        layer1 = MockLayer("L1", Decision.ALLOW)
        layer2 = MockLayer("L2", Decision.ALLOW)
        pipeline = DefensePipeline([layer1, layer2])
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = pipeline.guard_before(bundle)
        assert result.decision == Decision.ALLOW
        assert len(result.logs) == 2

    def test_block_layer_stops_pipeline(self):
        layer1 = MockLayer("L1", Decision.ALLOW)
        layer2 = MockLayer("L2", Decision.BLOCK, reason="blocked")
        layer3 = MockLayer("L3", Decision.ALLOW)  # Should not be reached
        pipeline = DefensePipeline([layer1, layer2, layer3])
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = pipeline.guard_before(bundle)
        assert result.decision == Decision.BLOCK
        assert len(result.logs) == 2  # Only L1 and L2
        assert result.logs[1].decision == Decision.BLOCK

    def test_escalate_layer_stops_pipeline(self):
        layer1 = MockLayer("L1", Decision.ALLOW)
        layer2 = MockLayer("L2", Decision.ESCALATE, reason="escalated")
        layer3 = MockLayer("L3", Decision.ALLOW)
        pipeline = DefensePipeline([layer1, layer2, layer3])
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = pipeline.guard_before(bundle)
        assert result.decision == Decision.ESCALATE
        assert len(result.logs) == 2

    def test_rewrite_layer_modifies_bundle(self):
        layer1 = MockLayer("L1", Decision.REWRITE, reason="rewritten")
        layer2 = MockLayer("L2", Decision.ALLOW)
        pipeline = DefensePipeline([layer1, layer2])
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = pipeline.guard_before(bundle)
        assert result.decision == Decision.ALLOW
        assert isinstance(result.payload, PromptBundle)
        assert result.payload.user_prompt == "rewritten prompt"
        assert len(result.logs) == 2

    def test_disabled_layers_are_ignored(self):
        layer1 = MockLayer("L1", Decision.ALLOW)
        layer2 = MockLayer("L2", Decision.BLOCK)
        layer2.enabled = False
        pipeline = DefensePipeline([layer1, layer2])
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = pipeline.guard_before(bundle)
        assert result.decision == Decision.ALLOW
        assert len(result.logs) == 1

    def test_guard_after_allow(self):
        layer1 = MockLayer("L1", Decision.ALLOW)
        pipeline = DefensePipeline([layer1])
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = pipeline.guard_after(bundle, "response")
        assert result.decision == Decision.ALLOW
        assert result.payload == "response"

    def test_guard_after_block(self):
        layer1 = MockLayer("L1", decision_after=Decision.BLOCK, reason="blocked")
        pipeline = DefensePipeline([layer1])
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = pipeline.guard_after(bundle, "response")
        assert result.decision == Decision.BLOCK
        assert result.payload == ""

    def test_guard_after_escalate(self):
        layer1 = MockLayer("L1", decision_after=Decision.ESCALATE, reason="escalated")
        pipeline = DefensePipeline([layer1])
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = pipeline.guard_after(bundle, "response")
        assert result.decision == Decision.ESCALATE
        assert result.payload == "response"


class TestProfileRepository:
    def test_load_all_caches_results(self):
        mock_loader = Mock()
        mock_loader.load_profiles.return_value = {
            "profiles": {
                "profile1": {"title": "Profile 1", "enabled_layers": ["L1"]},
                "profile2": {"title": "Profile 2", "enabled_layers": ["L1", "L2"]}
            }
        }
        repo = ProfileRepository(mock_loader)
        profiles = repo.load_all()
        assert len(profiles) == 2
        assert profiles["profile1"].id == "profile1"

        # Second call should use cache
        mock_loader.load_profiles.reset_mock()
        profiles2 = repo.load_all()
        assert profiles == profiles2
        mock_loader.load_profiles.assert_not_called()

    def test_load_all_force_reload(self):
        mock_loader = Mock()
        mock_loader.load_profiles.return_value = {"profiles": {}}
        repo = ProfileRepository(mock_loader)
        repo.load_all()  # Cache
        repo.load_all(force=True)  # Force reload
        assert mock_loader.load_profiles.call_count == 2

    def test_get_existing_profile(self):
        mock_loader = Mock()
        mock_loader.load_profiles.return_value = {
            "profiles": {"test": {"title": "Test Profile", "enabled_layers": ["L1"]}}
        }
        repo = ProfileRepository(mock_loader)
        profile = repo.get("test")
        assert profile.id == "test"
        assert profile.title == "Test Profile"

    def test_get_nonexistent_profile_raises_keyerror(self):
        mock_loader = Mock()
        mock_loader.load_profiles.return_value = {"profiles": {}}
        repo = ProfileRepository(mock_loader)
        with pytest.raises(KeyError, match="Unknown defense profile"):
            repo.get("nonexistent")

    def test_ids_method(self):
        mock_loader = Mock()
        mock_loader.load_profiles.return_value = {
            "profiles": {"p1": {}, "p2": {}}
        }
        repo = ProfileRepository(mock_loader)
        ids = list(repo.ids())
        assert set(ids) == {"p1", "p2"}


class TestPolicyRules:
    def test_from_mapping_default_values(self):
        data = {}
        rules = PolicyRules.from_mapping(data)
        assert rules.forbid_role_change is True
        assert rules.forbid_system_prompt_leak is True
        assert rules.forbidden_roles == []
        assert rules.forbid_direct_harm == []
        assert rules.allow_domains == []
        assert rules.data_marking == "DATA_ONLY"
        assert rules.escalation_keywords == []

    def test_from_mapping_custom_values(self):
        data = {
            "forbid_role_change": False,
            "forbidden_roles": ["admin"],
            "forbid_system_prompt_leak": False,
            "forbid_direct_harm": ["harm"],
            "allow_domains": ["example.com"],
            "data_marking": "SAFE",
            "escalation_keywords": ["urgent"]
        }
        rules = PolicyRules.from_mapping(data)
        assert rules.forbid_role_change is False
        assert rules.forbidden_roles == ["admin"]
        assert rules.forbid_system_prompt_leak is False
        assert rules.forbid_direct_harm == ["harm"]
        assert rules.allow_domains == ["example.com"]
        assert rules.data_marking == "SAFE"
        assert rules.escalation_keywords == ["urgent"]


class TestDefensePipelineBuilder:
    def test_build_empty_profile(self):
        mock_loader = Mock()
        mock_loader.load_policy.return_value = {}
        builder = DefensePipelineBuilder(mock_loader)
        profile = DefenseProfile(id="empty", title="Empty", description="", enabled_layers=[], params={})
        pipeline = builder.build(profile)
        assert len(list(pipeline.iter_layers())) == 0

    def test_build_with_layers(self):
        mock_loader = Mock()
        mock_loader.load_policy.return_value = {}
        builder = DefensePipelineBuilder(mock_loader)
        profile = DefenseProfile(
            id="test",
            title="Test",
            description="",
            enabled_layers=["L1", "L2"],
            params={"L1": {}, "L2": {}}
        )
        pipeline = builder.build(profile)
        layers = list(pipeline.iter_layers())
        assert len(layers) == 2
        assert layers[0].id == "L1"
        assert layers[1].id == "L2"
        assert all(layer.enabled for layer in layers)

    def test_build_ignores_unknown_layer(self):
        mock_loader = Mock()
        mock_loader.load_policy.return_value = {}
        builder = DefensePipelineBuilder(mock_loader)
        profile = DefenseProfile(
            id="test",
            title="Test",
            description="",
            enabled_layers=["L1", "UNKNOWN"],
            params={}
        )
        pipeline = builder.build(profile)
        layers = list(pipeline.iter_layers())
        assert len(layers) == 1
        assert layers[0].id == "L1"


class TestMockLayer:
    def test_mock_layer_allow(self):
        layer = MockLayer("test", Decision.ALLOW)
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = layer.before_send(bundle)
        assert result.decision == Decision.ALLOW
        assert result.layer_id == "test"

    def test_mock_layer_block(self):
        layer = MockLayer("test", decision_before=Decision.BLOCK, reason="blocked")
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = layer.before_send(bundle)
        assert result.decision == Decision.BLOCK
        assert result.reason == "blocked"

    def test_mock_layer_rewrite(self):
        layer = MockLayer("test", decision_before=Decision.REWRITE, reason="rewritten")
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = layer.before_send(bundle)
        assert result.decision == Decision.REWRITE
        assert result.rewritten_text == "rewritten prompt"

    def test_mock_layer_escalate(self):
        layer = MockLayer("test", decision_before=Decision.ESCALATE, reason="escalated")
        bundle = PromptBundle(system_prompt="system", user_prompt="prompt")
        result = layer.before_send(bundle)
        assert result.decision == Decision.ESCALATE
        assert result.reason == "escalated"