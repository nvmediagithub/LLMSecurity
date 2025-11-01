from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml


@dataclass(slots=True)
class ConfigPaths:
    """Абстракция местоположений конфигурационных файлов."""

    profiles: Path
    policy: Path
    tests: Path

    @classmethod
    def default(cls, root: Path | None = None) -> "ConfigPaths":
        root = root or Path.cwd()
        return cls(
            profiles=root / "config" / "profiles.yaml",
            policy=root / "config" / "policy.yaml",
            tests=root / "data" / "prompt_tests.yaml",
        )


class ConfigLoader:
    """Загрузчик YAML/JSON конфигураций с простым кэшированием."""

    def __init__(self, paths: ConfigPaths | None = None):
        self._paths = paths or ConfigPaths.default()
        self._cache: dict[str, Any] = {}

    def load_profiles(self) -> Mapping[str, Any]:
        return self._load_yaml("profiles", self._paths.profiles)

    def load_policy(self) -> Mapping[str, Any]:
        return self._load_yaml("policy", self._paths.policy)

    def load_tests(self) -> Mapping[str, Any]:
        # Поддерживаем YAML и JSON (для интеграции с внешними генераторами).
        suffix = self._paths.tests.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            return self._load_yaml("tests", self._paths.tests)
        if suffix == ".json":
            return self._load_json("tests", self._paths.tests)
        raise ValueError(f"Unsupported tests format: {suffix}")

    def _load_yaml(self, key: str, path: Path) -> Mapping[str, Any]:
        if key not in self._cache:
            self._cache[key] = self._read_yaml(path)
        return self._cache[key]

    def _load_json(self, key: str, path: Path) -> Mapping[str, Any]:
        if key not in self._cache:
            self._cache[key] = self._read_json(path)
        return self._cache[key]

    @staticmethod
    def _read_yaml(path: Path) -> Mapping[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, Mapping):
            raise TypeError(f"YAML root must be a mapping: {path}")
        return data

    @staticmethod
    def _read_json(path: Path) -> Mapping[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, Mapping):
            raise TypeError(f"JSON root must be a mapping: {path}")
        return data

    def invalidate(self, keys: Iterable[str] | None = None) -> None:
        """Сбрасывает кэш (весь или по ключам)."""

        if keys is None:
            self._cache.clear()
            return
        for key in keys:
            self._cache.pop(key, None)

