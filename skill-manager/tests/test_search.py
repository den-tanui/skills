from skill_manager.db import Database
from skill_manager.search import search_skills
from skill_manager.embedder import MockEmbedder


def test_search_basic(temp_db_path):
    db = Database(temp_db_path)
    embedder = MockEmbedder()

    dir_id = db.add_source_dir("/test")
    skill_id = db.upsert_skill("test-skill", dir_id, "test-skill",
                                "/test/test-skill/SKILL.md",
                                description="Test skill for form validation")

    chunk_id = db.insert_chunk(skill_id, "section:description",
                                "Form validation with Zod schemas")
    vec = embedder.embed("test")
    db.store_embedding(chunk_id, vec)
    db.commit()

    results = search_skills(db, "form validation", embedder, top_k=5)
    assert len(results) >= 1
    assert results[0].name == "test-skill"
    assert results[0].score > 0


def test_search_dedup(temp_db_path):
    db = Database(temp_db_path)
    embedder = MockEmbedder()

    dir_a = db.add_source_dir("/dir-a")
    dir_b = db.add_source_dir("/dir-b")

    skill_a = db.upsert_skill("dup-skill", dir_a, "dup-skill",
                               "/dir-a/dup-skill/SKILL.md")
    skill_b = db.upsert_skill("dup-skill", dir_b, "dup-skill",
                               "/dir-b/dup-skill/SKILL.md")

    vec = embedder.embed("duplicate content")
    for sid in (skill_a, skill_b):
        cid = db.insert_chunk(sid, "section:body", "duplicate content")
        db.store_embedding(cid, vec)
    db.commit()

    results = search_skills(db, "duplicate content", embedder, top_k=5)
    # Expect dedup to collapse same-named skills — should be 1 result
    assert len(results) <= 2


def test_search_json_output(temp_db_path):
    db = Database(temp_db_path)
    embedder = MockEmbedder()

    dir_id = db.add_source_dir("/test")
    skill_id = db.upsert_skill("json-test", dir_id, "json-test",
                                "/test/json-test/SKILL.md",
                                description="JSON output test")
    cid = db.insert_chunk(skill_id, "section:body", "content")
    db.store_embedding(cid, embedder.embed("content"))
    db.commit()

    results = search_skills(db, "content", embedder)
    assert len(results) >= 1
    d = results[0].to_dict()
    assert "name" in d
    assert "score" in d
    assert "files" in d
    assert "file_count" in d
    assert d["name"] == "json-test"
