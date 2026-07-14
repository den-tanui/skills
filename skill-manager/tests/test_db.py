import numpy as np
from pathlib import Path
from skill_manager.db import Database


def test_schema_creation(temp_db_path):
    db = Database(temp_db_path)
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = {row[0] for row in tables}
    assert "source_dirs" in table_names
    assert "skills" in table_names
    assert "file_hashes" in table_names
    assert "skill_chunks" in table_names
    assert "vec_chunks" in table_names


def test_skill_crud(temp_db_path):
    db = Database(temp_db_path)
    dir_id = db.add_source_dir("/test/skills")
    skill_id = db.upsert_skill(
        name="test-skill",
        source_dir_id=dir_id,
        dir_path="test-skill",
        abs_path="/test/skills/test-skill/SKILL.md",
        description="A test skill",
        frontmatter_json='{"name":"test-skill"}',
        size_bytes=100,
    )
    assert skill_id > 0

    skill = db.get_skill_by_path("/test/skills/test-skill/SKILL.md")
    assert skill is not None
    assert skill["name"] == "test-skill"

    db.delete_skill(skill_id)
    assert db.get_skill_by_path("/test/skills/test-skill/SKILL.md") is None


def test_vector_search(temp_db_path):
    db = Database(temp_db_path)
    dir_id = db.add_source_dir("/test")
    skill_id = db.upsert_skill("vec-test", dir_id, "vec-test",
                                "/test/vec-test/SKILL.md")

    chunk1_id = db.insert_chunk(skill_id, "section:description",
                                 "Form validation with Zod")
    chunk2_id = db.insert_chunk(skill_id, "code_block:python",
                                 "def validate(): pass")

    v1 = np.random.randn(384).astype(np.float32)
    v1 = v1 / np.linalg.norm(v1)
    v2 = np.random.randn(384).astype(np.float32)
    v2 = v2 / np.linalg.norm(v2)

    db.store_embedding(chunk1_id, v1)
    db.store_embedding(chunk2_id, v2)
    db.commit()

    results = db.vector_search(v1, top_k=5)
    assert len(results) >= 1
    top_id, top_score = results[0]
    assert top_id == chunk1_id
    assert top_score > 0.99


def test_file_hash_crud(temp_db_path):
    db = Database(temp_db_path)
    dir_id = db.add_source_dir("/test")
    skill_id = db.upsert_skill("hash-test", dir_id, "hash-test",
                                "/test/hash-test/SKILL.md")

    db.upsert_file_hash(skill_id, "SKILL.md", "abc123", 1000.0)
    db.upsert_file_hash(skill_id, "scripts/setup.sh", "def456", 1001.0)
    db.commit()

    hashes = db.get_file_hashes(skill_id)
    assert len(hashes) == 2
    assert hashes[0]["sha256"] in ("abc123", "def456")

    paths = db.get_skill_file_paths(skill_id)
    assert "SKILL.md" in paths

    db.delete_file_hash(skill_id, "SKILL.md")
    assert len(db.get_file_hashes(skill_id)) == 1
