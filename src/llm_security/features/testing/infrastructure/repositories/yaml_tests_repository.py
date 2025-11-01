from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Tuple

from .....core.config.loader import ConfigLoader
from ...domain.models import PassCriteria, PromptTest, TestCategory, TestSeverity


class PromptTestRepository:
    """Загружает сценарии prompt-инъекций из YAML."""

    def __init__(self, loader: ConfigLoader | None = None):
        self._loader = loader or ConfigLoader()
        self._categories: Dict[str, TestCategory] = {}
        self._tests: Dict[str, PromptTest] = {}

    def load(self, force: bool = False) -> Tuple[Dict[str, TestCategory], Dict[str, PromptTest]]:
        if force or not self._tests:
            raw = self._loader.load_tests()
            self._categories = {
                data["id"]: TestCategory(id=data["id"], title=data.get("title", data["id"]), description=data.get("description", ""))
                for data in raw.get("categories", [])
            }
            tests: Dict[str, PromptTest] = {}
            for data in raw.get("tests", []):
                criteria_data = data.get("pass_criteria", {})
                criteria = PassCriteria(
                    must_contain_any=list(criteria_data.get("must_contain_any", [])),
                    must_not_contain_any=list(criteria_data.get("must_not_contain_any", [])),
                )
                severity = TestSeverity(data.get("severity", TestSeverity.MEDIUM.value))
                tests[data["id"]] = PromptTest(
                    id=data["id"],
                    category=data["category"],
                    name=data.get("name", data["id"]),
                    system_prompt=data.get("system_prompt", ""),
                    user_prompt=data.get("user_prompt", ""),
                    pass_criteria=criteria,
                    severity=severity,
                )
            for data in raw.get("controls", []):
                criteria_data = data.get("pass_criteria", {})
                criteria = PassCriteria(
                    must_contain_any=list(criteria_data.get("must_contain_any", [])),
                    must_not_contain_any=list(criteria_data.get("must_not_contain_any", [])),
                )
                severity = TestSeverity(data.get("severity", TestSeverity.LOW.value))
                tests[data["id"]] = PromptTest(
                    id=data["id"],
                    category=data.get("category", "control"),
                    name=data.get("name", data["id"]),
                    system_prompt=data.get("system_prompt", ""),
                    user_prompt=data.get("user_prompt", ""),
                    pass_criteria=criteria,
                    severity=severity,
                    metadata={"control": "true"},
                )
            self._tests = tests
        return self._categories, self._tests

    def categories(self) -> Iterable[TestCategory]:
        self.load()
        return self._categories.values()

    def tests(self) -> Iterable[PromptTest]:
        self.load()
        return self._tests.values()

    def get(self, test_id: str) -> PromptTest:
        self.load()
        if test_id not in self._tests:
            raise KeyError(f"Unknown test id: {test_id}")
        return self._tests[test_id]

