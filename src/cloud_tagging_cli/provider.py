"""Provider-agnostic interface that every cloud adapter implements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Resource:
    id: str
    kind: str
    tags: dict[str, str]


class TaggingProvider(Protocol):
    """Minimal contract the CLI needs from any cloud's tagging API."""

    def list_resources(self) -> list[Resource]:
        """Return every taggable resource with its current tags."""
        ...

    def set_tags(self, resource_id: str, tags: dict[str, str]) -> None:
        """Merge the given key/value pairs into the resource's existing tags."""
        ...
