import pytest

from cloud_tagging_cli.config import ConfigError, load_config


def test_load_valid_config(tmp_path):
    path = tmp_path / "tags.yaml"
    path.write_text(
        "tags:\n"
        "  - key: Environment\n"
        "    required: true\n"
        "    case: lower\n"
        "    allowed_values: [prod, dev]\n"
    )
    config = load_config(path)
    assert len(config.rules) == 1
    assert config.rules[0].allowed_values == ("prod", "dev")


def test_missing_file_raises_config_error(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "missing.yaml")


def test_missing_tags_key_raises_config_error(tmp_path):
    path = tmp_path / "tags.yaml"
    path.write_text("other: true\n")
    with pytest.raises(ConfigError):
        load_config(path)


def test_invalid_case_value_raises_config_error(tmp_path):
    path = tmp_path / "tags.yaml"
    path.write_text("tags:\n  - key: Environment\n    case: screaming\n")
    with pytest.raises(ConfigError):
        load_config(path)


def test_entry_without_key_raises_config_error(tmp_path):
    path = tmp_path / "tags.yaml"
    path.write_text("tags:\n  - required: true\n")
    with pytest.raises(ConfigError):
        load_config(path)
