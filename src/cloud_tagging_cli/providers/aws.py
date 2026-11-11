"""AWS adapter, backed by the Resource Groups Tagging API.

This is the one real adapter in the project. It only depends on a boto3
client object passed in by the caller (see ``build_client``), so it can be
exercised in tests against a hand-written fake with no network access and
no real AWS account.
"""

from __future__ import annotations

from typing import Any, Protocol

from cloud_tagging_cli.provider import Resource


class TaggingApiError(Exception):
    """Raised when the Resource Groups Tagging API reports a failure."""


class BotoTaggingClient(Protocol):
    """The subset of the boto3 resourcegroupstaggingapi client we use."""

    def get_resources(self, **kwargs: Any) -> dict: ...

    def tag_resources(self, **kwargs: Any) -> dict: ...


def build_client(region: str = "us-east-1"):
    """Create a real boto3 client. Only called outside of tests."""
    import boto3

    return boto3.client("resourcegroupstaggingapi", region_name=region)


class AwsTaggingProvider:
    """Real adapter: AWS via the Resource Groups Tagging API."""

    def __init__(self, client: BotoTaggingClient) -> None:
        self._client = client

    def list_resources(self) -> list[Resource]:
        resources: list[Resource] = []
        token = None
        while True:
            kwargs = {"PaginationToken": token} if token else {}
            page = self._client.get_resources(**kwargs)
            for mapping in page.get("ResourceTagMappingList", []):
                arn = mapping["ResourceARN"]
                tags = {t["Key"]: t["Value"] for t in mapping.get("Tags", [])}
                resources.append(Resource(id=arn, kind=_kind_from_arn(arn), tags=tags))
            token = page.get("PaginationToken") or None
            if not token:
                break
        return resources

    def set_tags(self, resource_id: str, tags: dict[str, str]) -> None:
        if not tags:
            return
        response = self._client.tag_resources(ResourceARNList=[resource_id], Tags=tags)
        failures = response.get("FailedResourcesMap", {})
        if resource_id in failures:
            error = failures[resource_id]
            raise TaggingApiError(
                f"failed to tag {resource_id}: "
                f"{error.get('ErrorCode')} {error.get('ErrorMessage')}"
            )


def _kind_from_arn(arn: str) -> str:
    parts = arn.split(":")
    if len(parts) >= 3:
        return parts[2]
    return "unknown"
