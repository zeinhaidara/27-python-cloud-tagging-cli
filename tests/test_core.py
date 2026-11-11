from cloud_tagging_cli.config import StandardTagsConfig, TagRule
from cloud_tagging_cli.core import apply_resources, check_resources
from cloud_tagging_cli.provider import Resource
from tests.fakes import InMemoryProvider

CONFIG = StandardTagsConfig(
    rules=(
        TagRule(key="Environment", required=True, case="lower", allowed_values=("prod", "dev")),
        TagRule(key="Owner", required=True, case="lower", default="unassigned"),
    )
)


def make_provider(**resources: dict[str, str]) -> InMemoryProvider:
    return InMemoryProvider(
        resources={
            rid: Resource(id=rid, kind="instance", tags=tags) for rid, tags in resources.items()
        }
    )


def test_check_resources_only_reports_non_conforming():
    provider = make_provider(
        good={"Environment": "prod", "Owner": "jane"},
        bad={"Environment": "PROD"},
    )

    reports = check_resources(provider, CONFIG)

    assert len(reports) == 1
    assert reports[0].resource_id == "bad"


def test_apply_dry_run_does_not_call_set_tags():
    provider = make_provider(bad={"Environment": "PROD"})

    results = apply_resources(provider, CONFIG, apply=False)

    assert provider.set_tags_calls == []
    changed = [r for r in results if not r.is_noop]
    assert changed[0].applied_tags == {"Environment": "prod", "Owner": "unassigned"}


def test_apply_writes_tags_when_apply_true():
    provider = make_provider(bad={"Environment": "PROD"})

    apply_resources(provider, CONFIG, apply=True)

    assert provider.set_tags_calls == [("bad", {"Environment": "prod", "Owner": "unassigned"})]
    assert provider.resources["bad"].tags["Environment"] == "prod"


def test_apply_is_idempotent_on_second_run():
    provider = make_provider(bad={"Environment": "PROD"})

    apply_resources(provider, CONFIG, apply=True)
    provider.set_tags_calls.clear()
    second_results = apply_resources(provider, CONFIG, apply=True)

    assert provider.set_tags_calls == []
    assert all(r.is_noop for r in second_results)


def test_apply_reports_unfixable_violations_without_crashing():
    provider = make_provider(bad={"Owner": "jane"})

    results = apply_resources(provider, CONFIG, apply=True)

    assert results[0].unfixable[0].key == "Environment"
    assert provider.set_tags_calls == []
