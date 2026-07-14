from pathlib import Path
from skill_manager.scanner import scan_directory
from skill_manager.db import Database


def test_scan_directory_adds_skills(temp_workspace, temp_db_path):
    db = Database(temp_db_path)
    db.add_source_dir(str(temp_workspace))

    scan_directory(db, str(temp_workspace))

    skills = db.get_all_skills()
    skill_names = {s["name"] for s in skills}
    assert "react-form-validation" in skill_names
    assert "code-chunking" in skill_names
    assert len(skills) >= 4


def test_incremental_scan_no_changes(temp_workspace, temp_db_path):
    db = Database(temp_db_path)
    db.add_source_dir(str(temp_workspace))

    scan_directory(db, str(temp_workspace))
    scan_directory(db, str(temp_workspace))

    skills = db.get_all_skills()
    assert len(skills) >= 4


def test_scan_detects_modified_file(temp_workspace, temp_db_path):
    db = Database(temp_db_path)
    db.add_source_dir(str(temp_workspace))

    scan_directory(db, str(temp_workspace))

    skill_dir = temp_workspace / "valid-skill"
    skill_md = skill_dir / "SKILL.md"
    original = skill_md.read_text()
    skill_md.write_text(original + "\n\n## New Section\n\nAdded content.\n")

    scan_directory(db, str(temp_workspace))

    skill = db.get_skill_by_path(str(skill_md.resolve()))
    assert skill is not None
