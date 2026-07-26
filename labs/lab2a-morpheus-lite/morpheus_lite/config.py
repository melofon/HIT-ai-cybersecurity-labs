from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@dataclass(frozen=True)
class Settings:
    raw: dict[str, Any]
    topics: dict[str, str]
    policies: dict[str, Any]

    @property
    def bootstrap_servers(self) -> str:
        return os.getenv(
            "MORPHEUS_KAFKA_BOOTSTRAP",
            self.raw.get("kafka", {}).get("bootstrap_servers", "localhost:9092"),
        )

    def topic(self, name: str) -> str:
        try:
            return self.topics[name]
        except KeyError as exc:
            raise KeyError(f"Unknown topic alias: {name}") from exc


def load_settings(config_dir: str | Path | None = None) -> Settings:
    base = Path(config_dir) if config_dir else ROOT / "config"
    return Settings(
        raw=_load_yaml(base / "settings.yaml"),
        topics=_load_yaml(base / "topics.yaml"),
        policies=_load_yaml(base / "policies.yaml"),
    )
