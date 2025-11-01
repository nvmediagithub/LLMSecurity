from __future__ import annotations

from typing import Dict, Iterable, Mapping

from ....core.config.loader import ConfigLoader
from ..domain.profile import DefenseProfile


class ProfileRepository:
    """Загружает и кэширует профили защиты из YAML."""

    def __init__(self, loader: ConfigLoader | None = None):
        self._loader = loader or ConfigLoader()
        self._cache: Dict[str, DefenseProfile] = {}

    def load_all(self, force: bool = False) -> Dict[str, DefenseProfile]:
        if force or not self._cache:
            raw = self._loader.load_profiles().get("profiles", {})
            self._cache = {pid: self._hydrate(pid, data) for pid, data in raw.items()}
        return self._cache

    def get(self, profile_id: str) -> DefenseProfile:
        profiles = self.load_all()
        if profile_id not in profiles:
            raise KeyError(f"Unknown defense profile: {profile_id}")
        return profiles[profile_id]

    def ids(self) -> Iterable[str]:
        return self.load_all().keys()

    @staticmethod
    def _hydrate(profile_id: str, data: Mapping[str, object]) -> DefenseProfile:
        return DefenseProfile(
            id=profile_id,
            title=str(data.get("title", profile_id)),
            description=str(data.get("description", "")),
            enabled_layers=list(data.get("enabled_layers", [])),
            params=dict(data.get("params", {})),
        )

