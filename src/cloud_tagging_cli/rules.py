"""Tag validation and standardization logic, independent of any provider."""

from __future__ import annotations

from dataclasses import dataclass

from cloud_tagging_cli.config import StandardTagsConfig


def normalize_value(value: str, case: str) -> str:
    if case == "lower":
        return value.lower()
    if case == "upper":
        return value.upper()
    if case == "kebab":
        return value.strip().lower().replace("_", "-").replace(" ", "-")
    return value


@dataclass(frozen=True)
class Violation:
    key: str
    kind: str  # "missing_required", "wrong_case", "disallowed_value"
    detail: str
    fixable: bool


@dataclass(frozen=True)
class Plan:
    """Result of checking one resource's tags against the standard-tags config."""

    violations: tuple[Violation, ...]
    desired_tags: dict[str, str]  # only the keys that should change

    @property
    def has_unfixable_violations(self) -> bool:
        return any(not v.fixable for v in self.violations)

    @property
    def is_compliant(self) -> bool:
        return not self.violations


def evaluate(current_tags: dict[str, str], config: StandardTagsConfig) -> Plan:
    """Compare current_tags against every rule and compute what should change.

    Returns the violations found plus a minimal set of tag keys/values that
    need to be written to bring the resource into compliance. Keys already
    correct are left out of desired_tags so callers can skip no-op updates.
    """
    violations: list[Violation] = []
    desired: dict[str, str] = {}

    for rule in config.rules:
        current_value = current_tags.get(rule.key)

        if current_value is None:
            if rule.required:
                if rule.default is not None:
                    desired[rule.key] = normalize_value(rule.default, rule.case)
                    violations.append(
                        Violation(
                            key=rule.key,
                            kind="missing_required",
                            detail=f"missing, will set default '{rule.default}'",
                            fixable=True,
                        )
                    )
                else:
                    violations.append(
                        Violation(
                            key=rule.key,
                            kind="missing_required",
                            detail="missing and no default configured",
                            fixable=False,
                        )
                    )
            continue

        normalized = normalize_value(current_value, rule.case)

        if rule.allowed_values is not None and normalized not in rule.allowed_values:
            violations.append(
                Violation(
                    key=rule.key,
                    kind="disallowed_value",
                    detail=f"'{current_value}' not in {list(rule.allowed_values)}",
                    fixable=False,
                )
            )
            continue

        if normalized != current_value:
            desired[rule.key] = normalized
            violations.append(
                Violation(
                    key=rule.key,
                    kind="wrong_case",
                    detail=f"'{current_value}' should be '{normalized}'",
                    fixable=True,
                )
            )

    return Plan(violations=tuple(violations), desired_tags=desired)
