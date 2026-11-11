"""Provider-agnostic check/apply logic, shared by the CLI and its tests."""

from __future__ import annotations

from dataclasses import dataclass, field

from cloud_tagging_cli.config import StandardTagsConfig
from cloud_tagging_cli.provider import TaggingProvider
from cloud_tagging_cli.rules import Violation, evaluate


@dataclass(frozen=True)
class ResourceReport:
    resource_id: str
    violations: tuple[Violation, ...]


def check_resources(
    provider: TaggingProvider, config: StandardTagsConfig
) -> list[ResourceReport]:
    """Return a report for every resource that is out of compliance."""
    reports = []
    for resource in provider.list_resources():
        plan = evaluate(resource.tags, config)
        if plan.violations:
            reports.append(ResourceReport(resource_id=resource.id, violations=plan.violations))
    return reports


@dataclass(frozen=True)
class ApplyResult:
    resource_id: str
    applied_tags: dict[str, str] = field(default_factory=dict)
    unfixable: tuple[Violation, ...] = ()

    @property
    def is_noop(self) -> bool:
        return not self.applied_tags


def apply_resources(
    provider: TaggingProvider, config: StandardTagsConfig, apply: bool
) -> list[ApplyResult]:
    """Compute (and optionally perform) the tag changes needed on every resource.

    When apply is False, nothing is written and applied_tags describes what
    *would* be written. Resources already compliant produce a no-op result,
    which is what keeps repeated runs idempotent.
    """
    results = []
    for resource in provider.list_resources():
        plan = evaluate(resource.tags, config)
        unfixable = tuple(v for v in plan.violations if not v.fixable)

        if plan.desired_tags and apply:
            provider.set_tags(resource.id, plan.desired_tags)

        results.append(
            ApplyResult(
                resource_id=resource.id,
                applied_tags=plan.desired_tags,
                unfixable=unfixable,
            )
        )
    return results
