import pytest

from cloud_tagging_cli.providers.aws import AwsTaggingProvider, TaggingApiError
from tests.fakes import FakeBotoTaggingClient

ARN_1 = "arn:aws:ec2:us-east-1:123456789012:instance/i-1"
ARN_2 = "arn:aws:ec2:us-east-1:123456789012:instance/i-2"


def test_list_resources_parses_tags_and_kind():
    client = FakeBotoTaggingClient({ARN_1: {"Environment": "prod"}})
    provider = AwsTaggingProvider(client)

    resources = provider.list_resources()

    assert len(resources) == 1
    assert resources[0].id == ARN_1
    assert resources[0].kind == "ec2"
    assert resources[0].tags == {"Environment": "prod"}


def test_list_resources_follows_pagination():
    client = FakeBotoTaggingClient(
        {ARN_1: {"Environment": "prod"}, ARN_2: {"Environment": "dev"}}, page_size=1
    )
    provider = AwsTaggingProvider(client)

    resources = provider.list_resources()

    assert {r.id for r in resources} == {ARN_1, ARN_2}


def test_set_tags_calls_tag_resources_with_given_tags():
    client = FakeBotoTaggingClient({ARN_1: {}})
    provider = AwsTaggingProvider(client)

    provider.set_tags(ARN_1, {"Environment": "prod"})

    assert client.tag_resources_calls == [
        {"ResourceARNList": [ARN_1], "Tags": {"Environment": "prod"}}
    ]


def test_set_tags_with_no_changes_does_not_call_api():
    client = FakeBotoTaggingClient({ARN_1: {}})
    provider = AwsTaggingProvider(client)

    provider.set_tags(ARN_1, {})

    assert client.tag_resources_calls == []


def test_set_tags_raises_on_api_failure():
    client = FakeBotoTaggingClient({ARN_1: {}}, fail_resource_id=ARN_1)
    provider = AwsTaggingProvider(client)

    with pytest.raises(TaggingApiError):
        provider.set_tags(ARN_1, {"Environment": "prod"})
