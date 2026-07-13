import pytest
import tempfile
import shutil
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def valid_skill_dir(fixtures_dir) -> Path:
    return fixtures_dir / "valid-skill"


@pytest.fixture
def code_files_dir(fixtures_dir) -> Path:
    return fixtures_dir / "code-files"


@pytest.fixture
def temp_workspace():
    """Provide a temp directory with fixture skills copied in."""
    with tempfile.TemporaryDirectory() as tmp:
        src = FIXTURES_DIR
        for item in src.iterdir():
            if item.is_dir():
                dest = Path(tmp) / item.name
                shutil.copytree(item, dest)
        yield Path(tmp)


@pytest.fixture
def temp_db_path():
    """Provide a temporary SQLite db path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield Path(f.name)
        try:
            Path(f.name).unlink()
        except OSError:
            pass