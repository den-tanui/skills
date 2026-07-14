from skill_manager.chunker import chunk_file


def test_chunk_skill_md_sections(valid_skill_dir):
    """Test that SKILL.md is split into frontmatter + sections + code blocks."""
    skill_md = valid_skill_dir / "SKILL.md"
    chunks = chunk_file(str(skill_md))
    assert len(chunks) >= 4
    types = {c.chunk_type for c in chunks}
    assert "frontmatter" in types
    assert any(t.startswith("section:") for t in types)
    assert any(t.startswith("code_block:") for t in types)


def test_no_frontmatter_skill(fixtures_dir):
    """Test a skill file without YAML frontmatter."""
    path = fixtures_dir / "no-frontmatter" / "SKILL.md"
    chunks = chunk_file(str(path))
    assert len(chunks) >= 1
    assert all(c.chunk_type != "frontmatter" for c in chunks)


def test_empty_skill(fixtures_dir):
    """Test a skill file with only frontmatter and no body."""
    path = fixtures_dir / "empty-dir" / "SKILL.md"
    chunks = chunk_file(str(path))
    assert len(chunks) == 1
    assert chunks[0].chunk_type == "frontmatter"


def test_reference_markdown_chunking(valid_skill_dir):
    """Test that reference .md files are chunked into sections and code blocks."""
    path = valid_skill_dir / "references" / "api-patterns.md"
    chunks = chunk_file(str(path))
    assert len(chunks) >= 2
    code_blocks = [c for c in chunks if c.chunk_type.startswith("code_block:")]
    assert len(code_blocks) >= 1


def test_python_function_chunking(code_files_dir):
    """Test Python file is chunked by function/class definitions."""
    path = code_files_dir / "sample.py"
    chunks = chunk_file(str(path))
    # Expect 3+ chunks (validate_email, format_name functions, UserService class)
    assert len(chunks) >= 3


def test_javascript_chunking(code_files_dir):
    """Test JS file is chunked by function/class definitions."""
    path = code_files_dir / "sample.js"
    chunks = chunk_file(str(path))
    # function greet, const add, class Counter
    assert len(chunks) >= 3


def test_go_chunking(code_files_dir):
    """Test Go file is chunked by function/method/type definitions."""
    path = code_files_dir / "sample.go"
    chunks = chunk_file(str(path))
    # func Greet + type Counter + method Increment
    assert len(chunks) >= 2


def test_bash_chunking(code_files_dir):
    """Test Bash file is chunked by function definitions."""
    path = code_files_dir / "sample.sh"
    chunks = chunk_file(str(path))
    # install_deps + run_checks
    assert len(chunks) >= 2
