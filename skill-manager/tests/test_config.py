from skill_manager.config import Config, load_config, save_config


def test_default_config_values():
    config = Config()
    assert config.db_path is not None
    assert config.dirs.tracked == []
    assert hasattr(config.weights, "frontmatter")
    assert config.embedding.model == "all-MiniLM-L6-v2"


def test_weight_lookup():
    config = Config()
    assert config.get_weight("frontmatter") == 0.20
    assert config.get_weight("section:when to use") == 0.30
    assert config.get_weight("section:unknown") == 0.10  # section:* fallback
    assert config.get_weight("code_block:python") == 0.15
    assert config.get_weight("reference_file") == 0.10
    assert config.get_weight("script_file") == 0.05


def test_config_save_load_roundtrip(tmp_path):
    original = Config()
    original.dirs.tracked = ["~/skills", "~/.config/opencode/skills"]
    original.weights.section_wildcard = 0.15

    path = tmp_path / "config.toml"
    save_config(original, path)
    loaded = load_config(path)

    assert loaded.dirs.tracked == original.dirs.tracked
    assert loaded.weights.section_wildcard == 0.15
    assert loaded.embedding.model == "all-MiniLM-L6-v2"
    assert loaded.db_path == str(Config().db_path)
