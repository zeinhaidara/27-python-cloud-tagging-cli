from cloud_tagging_cli.config import StandardTagsConfig, TagRule
from cloud_tagging_cli.rules import evaluate

CONFIG = StandardTagsConfig(
    rules=(
        TagRule(key="Environment", required=True, case="lower", allowed_values=("prod", "dev")),
        TagRule(key="Owner", required=True, case="lower", default="unassigned"),
        TagRule(key="CostCenter", required=False, case="upper"),
    )
)


def test_fully_compliant_resource_has_no_violations():
    plan = evaluate({"Environment": "prod", "Owner": "jane"}, CONFIG)
    assert plan.is_compliant
    assert plan.desired_tags == {}


def test_missing_required_with_default_is_fixable():
    plan = evaluate({"Environment": "prod"}, CONFIG)
    assert plan.desired_tags == {"Owner": "unassigned"}
    violation = next(v for v in plan.violations if v.key == "Owner")
    assert violation.kind == "missing_required"
    assert violation.fixable


def test_missing_required_without_default_is_unfixable():
    plan = evaluate({"Owner": "jane"}, CONFIG)
    violation = next(v for v in plan.violations if v.key == "Environment")
    assert violation.kind == "missing_required"
    assert not violation.fixable
    assert "Environment" not in plan.desired_tags


def test_wrong_case_is_fixed_in_desired_tags():
    plan = evaluate({"Environment": "PROD", "Owner": "jane"}, CONFIG)
    assert plan.desired_tags == {"Environment": "prod"}
    violation = next(v for v in plan.violations if v.key == "Environment")
    assert violation.kind == "wrong_case"
    assert violation.fixable


def test_disallowed_value_is_unfixable_and_not_overwritten():
    plan = evaluate({"Environment": "qa", "Owner": "jane"}, CONFIG)
    violation = next(v for v in plan.violations if v.key == "Environment")
    assert violation.kind == "disallowed_value"
    assert not violation.fixable
    assert "Environment" not in plan.desired_tags


def test_optional_missing_tag_is_not_a_violation():
    plan = evaluate({"Environment": "prod", "Owner": "jane"}, CONFIG)
    assert all(v.key != "CostCenter" for v in plan.violations)
