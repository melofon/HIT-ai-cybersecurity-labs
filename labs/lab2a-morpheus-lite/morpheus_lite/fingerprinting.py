from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import math


FEATURES = ("failed_logins", "bytes_out", "process_count", "login_hour")


class FingerprintStore:
    def __init__(self, path: str | Path, minimum_samples: int = 8) -> None:
        self.path = Path(path)
        self.minimum_samples = minimum_samples
        self.profiles: dict[str, dict[str, list[float]]] = {}
        if self.path.exists():
            self.profiles = json.loads(self.path.read_text(encoding="utf-8"))

    @staticmethod
    def _values(event: dict[str, Any]) -> dict[str, float]:
        timestamp = event.get("timestamp")
        try:
            hour = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour if timestamp else 12
        except ValueError:
            hour = 12
        return {
            "failed_logins": float(event.get("failed_logins", 0)),
            "bytes_out": float(event.get("bytes_out", 0)),
            "process_count": float(event.get("process_count", 0)),
            "login_hour": float(hour),
        }

    def score(self, event: dict[str, Any]) -> dict[str, Any]:
        user = str(event.get("user", "unknown"))
        values = self._values(event)
        profile = self.profiles.get(user, {})
        z_scores: dict[str, float] = {}
        for name, value in values.items():
            samples = profile.get(name, [])
            if len(samples) < self.minimum_samples:
                z_scores[name] = 0.0
                continue
            mean = sum(samples) / len(samples)
            variance = sum((x - mean) ** 2 for x in samples) / max(len(samples) - 1, 1)
            std = math.sqrt(variance)
            z_scores[name] = 0.0 if std == 0 else abs(value - mean) / std
        max_z = max(z_scores.values(), default=0.0)
        return {
            "user": user,
            "profile_samples": max((len(v) for v in profile.values()), default=0),
            "z_scores": z_scores,
            "max_z_score": round(max_z, 4),
            "user_specific": bool(profile) and max((len(v) for v in profile.values()), default=0) >= self.minimum_samples,
        }

    def update(self, event: dict[str, Any], *, trusted_normal: bool) -> None:
        if not trusted_normal:
            return
        user = str(event.get("user", "unknown"))
        profile = self.profiles.setdefault(user, defaultdict(list))
        for name, value in self._values(event).items():
            values = profile.setdefault(name, [])
            values.append(value)
            del values[:-200]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.profiles, indent=2), encoding="utf-8")
