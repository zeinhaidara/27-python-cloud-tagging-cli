"""Interface-only stubs for clouds without a real adapter yet.

These exist to show the provider interface is multi-cloud by design, not
to claim working support. Every method raises immediately.
"""

from __future__ import annotations

from cloud_tagging_cli.provider import Resource


class UnsupportedProvider:
    name = "unsupported"

    def list_resources(self) -> list[Resource]:
        raise NotImplementedError(f"{self.name} provider is interface-only, not implemented")

    def set_tags(self, resource_id: str, tags: dict[str, str]) -> None:
        raise NotImplementedError(f"{self.name} provider is interface-only, not implemented")


class AzureProvider(UnsupportedProvider):
    name = "azure"


class GcpProvider(UnsupportedProvider):
    name = "gcp"
