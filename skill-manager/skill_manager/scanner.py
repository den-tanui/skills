from __future__ import annotations
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import List, Optional

from .chunker import chunk_file
from .config import Config
from .db import Database
from .embedder import MockEmbedder

logger = logging.getLogger(__name__)


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_file_mtime(file_path: str) -> float:
    return os.path.getmtime(file_path)


def _parse_frontmatter(content: str):
    """Parse YAML frontmatter from SKILL.md content. Returns (name, description, frontmatter_json)."""
    name = ""
    description = ""
    frontmatter_json = ""
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        try:
            import yaml
            fm_data = yaml.safe_load(fm_match.group(1))
            if isinstance(fm_data, dict):
                name = fm_data.get("name", name) or ""
                description = fm_data.get("description", description) or ""
                frontmatter_json = json.dumps(fm_data)
        except Exception:
            pass
    return name, description, frontmatter_json


def _gather_skill_files(skill_dir: Path) -> List[tuple]:
    """Return list of (relative_path, absolute_path) for all files in skill dir."""
    files = []
    for root, dirs, fnames in os.walk(skill_dir):
        for fname in fnames:
            abs_fpath = Path(root) / fname
            rel_fpath = abs_fpath.relative_to(skill_dir)
            files.append((str(rel_fpath), str(abs_fpath.resolve())))
    return files


def _prune_missing(db: Database, source_dir: str):
    """Remove skills from DB whose SKILL.md no longer exists."""
    skills = db.get_all_skills()
    for skill in skills:
        if skill.get("source_dir_path") == source_dir:
            if not Path(skill["abs_path"]).exists():
                db.delete_skill(skill["id"])
                logger.info(f"Pruned missing skill: {skill['name']} at {skill['abs_path']}")


def _process_skill(db, skill_md_path: Path, skill_dir: Path,
                   rel_dir: str, source_dir: str,
                   source_dir_id: int, embedder, config) -> bool:
    """Process a single skill dir. Returns True if changed."""
    abs_path = str(skill_md_path.resolve())

    content = skill_md_path.read_text(encoding="utf-8", errors="replace")
    name, description, frontmatter_json = _parse_frontmatter(content)
    if not name:
        name = skill_dir.name

    skill_id = db.upsert_skill(
        name=name,
        source_dir_id=source_dir_id,
        dir_path=rel_dir,
        abs_path=abs_path,
        description=description,
        frontmatter_json=frontmatter_json,
        size_bytes=skill_md_path.stat().st_size,
    )

    all_files = _gather_skill_files(skill_dir)

    existing_hashes = {h["file_path"]: h["sha256"]
                       for h in db.get_file_hashes(skill_id)}
    changed = False

    for file_rel_path, file_abs_path in all_files:
        new_hash = compute_file_hash(file_abs_path)
        old_hash = existing_hashes.pop(file_rel_path, None)

        if new_hash != old_hash:
            changed = True
            db.delete_chunks_for_file(skill_id, file_rel_path)
            chunks = chunk_file(file_abs_path)
            for chunk in chunks:
                chunk.file_path = file_rel_path
                chunk_id = db.insert_chunk(
                    skill_id=skill_id,
                    chunk_type=chunk.chunk_type,
                    content=chunk.content,
                    section_heading=chunk.section_heading,
                    file_path=file_rel_path,
                )
                if chunk.content.strip():
                    vec = embedder.embed(chunk.content[:2000])
                    db.store_embedding(chunk_id, vec)

            mtime = get_file_mtime(file_abs_path)
            db.upsert_file_hash(skill_id, file_rel_path, new_hash, mtime)

    for stale_path in existing_hashes:
        db.delete_file_hash(skill_id, stale_path)
        db.delete_chunks_for_file(skill_id, stale_path)
        changed = True

    return changed


def scan_directory(db: Database, dir_path: str,
                   embedder=None, config: Optional[Config] = None) -> int:
    """Scan a single tracked directory for skills. Returns count of skills indexed."""
    if embedder is None:
        embedder = MockEmbedder()
    if config is None:
        config = Config()

    dir_path = str(Path(dir_path).expanduser().resolve())
    source_dir_id = db.add_source_dir(dir_path)
    skills_found = 0

    for root, dirs, files in os.walk(dir_path, followlinks=False):
        if "SKILL.md" in files:
            skill_dir = Path(root)
            skill_md_path = skill_dir / "SKILL.md"
            rel_dir = str(skill_dir.relative_to(Path(dir_path)))

            changed = _process_skill(
                db, skill_md_path, skill_dir, rel_dir,
                dir_path, source_dir_id, embedder, config
            )
            if changed:
                skills_found += 1

    _prune_missing(db, dir_path)

    db.commit()
    return skills_found


def scan_all(db: Database, config: Config, embedder=None) -> int:
    """Scan all tracked directories. Returns total skills indexed."""
    total = 0
    for dir_path in config.dirs.tracked:
        expanded = str(Path(dir_path).expanduser())
        if Path(expanded).exists():
            total += scan_directory(db, expanded, embedder, config)
        else:
            logger.warning(f"Tracked directory not found: {expanded}")
    return total
