from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "skill-manager"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.toml"
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "skill-manager" / "skills.db"


@dataclass
class DirConfig:
    tracked: List[str] = field(default_factory=list)
    priority: List[int] = field(default_factory=list)


@dataclass
class WeightConfig:
    frontmatter: float = 0.20
    section_wildcard: float = 0.10
    code_block_wildcard: float = 0.15
    reference_file: float = 0.10
    script_file: float = 0.05
    section_overrides: Dict[str, float] = field(default_factory=lambda: {
        "section:description": 0.20,
        "section:when to use": 0.30,
        "section:trigger when": 0.25,
        "section:what it does": 0.20,
    })


@dataclass
class EmbeddingConfig:
    model: str = "all-MiniLM-L6-v2"
    batch_size: int = 32
    device: str = "cpu"


@dataclass
class ScanConfig:
    interval_minutes: int = 15


@dataclass
class Config:
    db_path: str = str(DEFAULT_DB_PATH)
    dirs: DirConfig = field(default_factory=DirConfig)
    weights: WeightConfig = field(default_factory=WeightConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    scan: ScanConfig = field(default_factory=ScanConfig)

    def get_weight(self, chunk_type: str) -> float:
        """Look up weight by chunk_type, falling through wildcards."""
        if chunk_type in self.weights.section_overrides:
            return self.weights.section_overrides[chunk_type]
        if chunk_type.startswith("section:"):
            return self.weights.section_wildcard
        if chunk_type.startswith("code_block:"):
            return self.weights.code_block_wildcard
        return getattr(self.weights, chunk_type, 0.10)


def load_config(path: Path | None = None) -> Config:
    """Load config from TOML file, returning defaults if file doesn't exist."""
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return Config()
    try:
        import tomllib as tomli
    except ImportError:
        import tomli  # Python < 3.11
    try:
        with open(config_path, "rb") as f:
            data = tomli.load(f)
    except (FileNotFoundError, tomli.TOMLDecodeError):
        return Config()
    config = Config()
    if "db_path" in data:
        config.db_path = data["db_path"]
    if "dirs" in data and "tracked" in data["dirs"]:
        config.dirs.tracked = data["dirs"]["tracked"]
    if "embedding" in data:
        for k, v in data["embedding"].items():
            if hasattr(config.embedding, k):
                setattr(config.embedding, k, v)
    if "scan" in data and "interval_minutes" in data["scan"]:
        config.scan.interval_minutes = data["scan"]["interval_minutes"]
    if "weights" in data:
        for k, v in data["weights"].items():
            if k == "code_block:*":
                config.weights.code_block_wildcard = v
            elif k == "section:*":
                config.weights.section_wildcard = v
            elif k.startswith("section:") or k.startswith("code_block:"):
                config.weights.section_overrides[k] = v
            elif hasattr(config.weights, k):
                setattr(config.weights, k, v)
    return config


def save_config(config: Config, path: Path | None = None) -> None:
    """Save config to TOML file."""
    import tomli_w
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "db_path": config.db_path,
        "dirs": {
            "tracked": config.dirs.tracked,
        },
        "weights": {
            "frontmatter": config.weights.frontmatter,
            **config.weights.section_overrides,
            "section:*": config.weights.section_wildcard,
            "code_block:*": config.weights.code_block_wildcard,
            "reference_file": config.weights.reference_file,
            "script_file": config.weights.script_file,
        },
        "embedding": {
            "model": config.embedding.model,
            "batch_size": config.embedding.batch_size,
            "device": config.embedding.device,
        },
        "scan": {
            "interval_minutes": config.scan.interval_minutes,
        },
    }
    with open(config_path, "wb") as f:
        tomli_w.dump(data, f)
