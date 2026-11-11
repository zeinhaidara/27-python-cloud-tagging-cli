from click.testing import CliRunner

from cloud_tagging_cli import cli
from tests.fakes import FakeBotoTaggingClient

ARN = "arn:aws:ec2:us-east-1:123456789012:instance/i-1"

CONFIG_YAML = (
    "tags:\n"
    "  - key: Environment\n"
    "    required: true\n"
    "    case: lower\n"
    "    allowed_values: [prod, dev]\n"
    "  - key: Owner\n"
    "    required: true\n"
    "    case: lower\n"
    "    default: unassigned\n"
)


def write_config(tmp_path):
    path = tmp_path / "standard_tags.yaml"
    path.write_text(CONFIG_YAML)
    return str(path)


def test_check_command_exits_nonzero_on_violations(tmp_path, monkeypatch):
    client = FakeBotoTaggingClient({ARN: {"Environment": "PROD"}})
    monkeypatch.setattr(cli, "build_client", lambda region: client)

    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--config", write_config(tmp_path)])

    assert result.exit_code == 1
    assert "wrong_case" in result.output


def test_check_command_exits_zero_when_compliant(tmp_path, monkeypatch):
    client = FakeBotoTaggingClient({ARN: {"Environment": "prod", "Owner": "jane"}})
    monkeypatch.setattr(cli, "build_client", lambda region: client)

    runner = CliRunner()
    result = runner.invoke(cli.main, ["check", "--config", write_config(tmp_path)])

    assert result.exit_code == 0
    assert "conform" in result.output


def test_apply_without_flag_is_dry_run(tmp_path, monkeypatch):
    client = FakeBotoTaggingClient({ARN: {"Environment": "PROD"}})
    monkeypatch.setattr(cli, "build_client", lambda region: client)

    runner = CliRunner()
    result = runner.invoke(cli.main, ["apply", "--config", write_config(tmp_path)])

    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert client.tag_resources_calls == []


def test_apply_with_flag_writes_tags(tmp_path, monkeypatch):
    client = FakeBotoTaggingClient({ARN: {"Environment": "PROD"}})
    monkeypatch.setattr(cli, "build_client", lambda region: client)

    runner = CliRunner()
    result = runner.invoke(cli.main, ["apply", "--apply", "--config", write_config(tmp_path)])

    assert result.exit_code == 0
    assert client.tag_resources_calls == [
        {"ResourceARNList": [ARN], "Tags": {"Environment": "prod", "Owner": "unassigned"}}
    ]


def test_apply_reports_unfixable_violation_as_failure(tmp_path, monkeypatch):
    client = FakeBotoTaggingClient({ARN: {"Environment": "qa", "Owner": "jane"}})
    monkeypatch.setattr(cli, "build_client", lambda region: client)

    runner = CliRunner()
    result = runner.invoke(cli.main, ["apply", "--apply", "--config", write_config(tmp_path)])

    assert result.exit_code == 1
    assert "disallowed_value" in result.output


def test_azure_provider_is_rejected_as_unimplemented(tmp_path, monkeypatch):
    runner = CliRunner()
    result = runner.invoke(
        cli.main, ["check", "--provider", "azure", "--config", write_config(tmp_path)]
    )

    assert result.exit_code != 0
    assert "not implemented" in str(result.exception) or "not implemented" in result.output
