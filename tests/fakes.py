"""Hand-written fakes used across the test suite. No moto, no real SDKs."""

from __future__ import annotations

from dataclasses import dataclass, field

from cloud_tagging_cli.provider import Resource


@dataclass
class InMemoryProvider:
    """In-memory stand-in for the TaggingProvider interface."""

    resources: dict[str, Resource]
    set_tags_calls: list[tuple[str, dict[str, str]]] = field(default_factory=list)

    def list_resources(self) -> list[Resource]:
        return list(self.resources.values())

    def set_tags(self, resource_id: str, tags: dict[str, str]) -> None:
        self.set_tags_calls.append((resource_id, dict(tags)))
        current = self.resources[resource_id]
        merged = {**current.tags, **tags}
        self.resources[resource_id] = Resource(id=current.id, kind=current.kind, tags=merged)


class FakeBotoTaggingClient:
    """Hand-written fake of the boto3 resourcegroupstaggingapi client.

    Mirrors the shapes GetResources / TagResources return, including
    pagination and a configurable per-resource failure.
    """

    def __init__(
        self,
        resources: dict[str, dict[str, str]],
        page_size: int = 50,
        fail_resource_id: str | None = None,
    ) -> None:
        self._resources = dict(resources)
        self._page_size = page_size
        self._fail_resource_id = fail_resource_id
        self.tag_resources_calls: list[dict] = []

    def get_resources(self, PaginationToken: str = "", **_: object) -> dict:
        arns = sorted(self._resources)
        start = int(PaginationToken) if PaginationToken else 0
        page = arns[start : start + self._page_size]
        next_start = start + self._page_size

        mapping_list = [
            {
                "ResourceARN": arn,
                "Tags": [{"Key": k, "Value": v} for k, v in self._resources[arn].items()],
            }
            for arn in page
        ]

        result = {"ResourceTagMappingList": mapping_list}
        if next_start < len(arns):
            result["PaginationToken"] = str(next_start)
        return result

    def tag_resources(self, ResourceARNList: list[str], Tags: dict[str, str]) -> dict:
        self.tag_resources_calls.append({"ResourceARNList": ResourceARNList, "Tags": Tags})
        failed = {}
        for arn in ResourceARNList:
            if arn == self._fail_resource_id:
                failed[arn] = {"ErrorCode": "ThrottlingException", "ErrorMessage": "rate exceeded"}
            else:
                self._resources[arn] = {**self._resources.get(arn, {}), **Tags}
        return {"FailedResourcesMap": failed} if failed else {}
