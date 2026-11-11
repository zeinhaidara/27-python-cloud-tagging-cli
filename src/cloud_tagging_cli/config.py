"""Loading and representing the standard-tags configuration file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

VALID_CASES = {"lower", "upper", "kebab", "none"}


class ConfigError(Exception):
    """Raised when the standard-tags config file is malformed."""


@dataclass(frozen=True)
class TagRule:
    key: str
    required: bool = True
    case: str = "none"
    allowed_values: tuple[str, ...] | None = None
    default: str | None = None


@dataclass(frozen=True)
class StandardTagsConfig:
    rules: tuple[TagRule, ...] = field(default_factory=tuple)

    def rule_for(self, key: str) -> TagRule | None:
        for rule in self.rules:
            if rule.key == key:
                return rule
        return None


def load_config(path: str | Path) -> StandardTagsConfig:
    raw_path = Path(path)
    if not raw_path.is_file():
        raise ConfigError(f"standard-tags config not found: {raw_path}")

    with raw_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    rules_data = data.get("tags")
    if not isinstance(rules_data, list) or not rules_data:
        raise ConfigError("config must define a non-empty 'tags' list")

    rules: list[TagRule] = []
    for index, entry in enumerate(rules_data):
        if not isinstance(entry, dict) or "key" not in entry:
            raise ConfigError(f"tags[{index}] must be a mapping with a 'key'")

        case = entry.get("case", "none")
        if case not in VALID_CASES:
            raise ConfigError(f"tags[{index}].case '{case}' must be one of {sorted(VALID_CASES)}")

        allowed_values = entry.get("allowed_values")
        if allowed_values is not None:
            allowed_values = tuple(str(v) for v in allowed_values)

        rules.append(
            TagRule(
                key=str(entry["key"]),
                required=bool(entry.get("required", True)),
                case=case,
                allowed_values=allowed_values,
                default=entry.get("default"),
            )
        )

    return StandardTagsConfig(rules=tuple(rules))
