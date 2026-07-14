from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Chunk:
    """A single chunk of content from a skill file."""
    skill_id: int = 0
    chunk_type: str = ""        # 'frontmatter', 'section:*', 'code_block:*', 'reference_file', 'script_file'
    section_heading: str = ""   # original markdown heading (if applicable)
    content: str = ""
    content_preview: str = ""
    file_path: str = ""         # relative path in skill dir (for extra files)
    embedding: Optional[bytes] = None  # 384-dim float32 blob

    def preview(self, max_len: int = 200) -> str:
        return self.content[:max_len] + "..." if len(self.content) > max_len else self.content


@dataclass
class Skill:
    """A skill indexed in the database."""
    id: int = 0
    name: str = ""
    source_dir: str = ""
    dir_path: str = ""           # relative to source dir
    abs_path: str = ""           # absolute path to SKILL.md
    description: str = ""
    frontmatter_json: str = ""
    file_count: int = 0
    files: List[str] = field(default_factory=list)  # relative paths
    install_method: str = "discovered"
    source_url: Optional[str] = None
    source_commit_hash: Optional[str] = None


@dataclass
class SearchResult:
    """A single search result."""
    name: str = ""
    description: str = ""
    score: float = 0.0
    source_dir: str = ""
    abs_path: str = ""
    files: List[str] = field(default_factory=list)
    file_count: int = 0
    source_url: Optional[str] = None
    source_commit_hash: Optional[str] = None
    install_method: str = "discovered"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "score": round(self.score, 4),
            "source_dir": self.source_dir,
            "abs_path": self.abs_path,
            "files": self.files,
            "file_count": self.file_count,
            "source_url": self.source_url,
            "source_commit_hash": self.source_commit_hash,
            "install_method": self.install_method,
        }
