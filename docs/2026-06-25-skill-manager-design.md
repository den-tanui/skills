# Skill Manager — Design Spec

**Date:** 2026-06-25
**Status:** Draft
**Version:** v1 (Local indexing + search)

## Overview

A comprehensive skill management system for OpenCode skills. v1 focuses on local indexing with semantic search. Future versions add remote registry integration and an OpenCode MCP plugin.

**Core problem:** Skills scattered across many directories with no search, no dedup, no provenance tracking, and manual installation workflow.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    skill-manager CLI                      │
│  (Python, installed via pipx/pip)                         │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │  Config  │  │ Scanner  │  │ Embedder │  │ Search  │  │
│  │  Manager │  │ + Parser │  │(sentence │  │ Engine  │  │
│  │          │  │          │  │transform)│  │         │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘  │
│       │              │             │              │       │
│  ┌────┴──────────────┴─────────────┴──────────────┴───┐  │
│  │              SQLite + sqlite-vec DB                  │  │
│  │  ~/.local/share/skill-manager/skills.db              │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │
         ▼ (v2)
┌────────────────────────────────────┐
│  TS MCP Server (opencode plugin)   │
│  shells out to skill-manager CLI   │
└────────────────────────────────────┘
```

### Components

| Component | Responsibility |
|-----------|----------------|
| **Config Manager** | Load/save TOML config. Manages tracked dirs, per-section weights, embedding model, DB path. |
| **Scanner + Parser** | Walks tracked dirs for `SKILL.md` files. Extracts YAML frontmatter. Splits body into sections by markdown heading. Discovers extra files in skill dirs. |
| **Indexer** | Orchestrates scan → parse → chunk → embed → store. Handles incremental updates (mtime check). |
| **Embedder** | Wraps sentence-transformers (`all-MiniLM-L6-v2`). Batches chunks for efficiency. Returns 384-dim vectors. |
| **Search Engine** | Embed query → cosine similarity against all chunks → aggregate per-skill with configurable weights → deduplicate → rank. |
| **Skill Manager** | `check`, `copy`, `symlink`, `edit`, `delete`, `list` commands. |

### Data Flow

**Index:** `Tracked dirs → Scanner → SKILL.md files → Parser → Chunks → Embedder (batch) → sqlite-vec store`

**Search:** `Query → Embedder → sqlite-vec cosine search → Chunk scores × weights → Aggregate per-skill → Ranked results`

## Storage Layout

```
~/.config/skill-manager/
└── config.toml                  # user config

~/.local/share/skill-manager/
├── skills.db                    # SQLite + sqlite-vec database
└── installed/                   # v2: installed skills store
    └── <skill-name>/
        ├── SKILL.md
        ├── scripts/
        └── references/

~/.cache/skill-manager/
└── models/                      # sentence-transformers cache
```

## Config File

`~/.config/skill-manager/config.toml`:

```toml
db_path = "~/.local/share/skill-manager/skills.db"

[dirs]
tracked = [
  "~/.config/opencode/skills",
  "~/my-skills",
]

[weights]
frontmatter = 0.20
"section:description" = 0.20
"section:when to use" = 0.30
"section:trigger when" = 0.25
"section:what it does" = 0.20
"section:*" = 0.10
reference_file = 0.10
script_file = 0.05

[embedding]
model = "all-MiniLM-L6-v2"
batch_size = 32
device = "cpu"
```

## Data Model — SQLite Schema

```sql
-- Tracked source directories
CREATE TABLE source_dirs (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    label TEXT,
    priority INTEGER DEFAULT 0,
    added_at TEXT DEFAULT (datetime('now'))
);

-- Skills with provenance
CREATE TABLE skills (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    source_dir_id INTEGER REFERENCES source_dirs(id),
    dir_path TEXT NOT NULL,          -- relative to source dir
    abs_path TEXT NOT NULL,          -- absolute path to SKILL.md
    content_hash TEXT NOT NULL,      -- SHA256 of SKILL.md content
    description TEXT,
    frontmatter_json TEXT,
    size_bytes INTEGER,
    install_method TEXT DEFAULT 'discovered',  -- 'discovered'|'installed'|'symlinked'
    source_url TEXT,                  -- skillsmp.com URL, GitHub URL, etc.
    source_repo TEXT,                 -- git remote URL
    source_commit_hash TEXT,          -- pinned commit hash when installed
    indexed_at TEXT,
    modified_at TEXT,
    UNIQUE(name, content_hash)
);

-- Skill chunks (one per section / extra file)
CREATE TABLE skill_chunks (
    id INTEGER PRIMARY KEY,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    chunk_type TEXT NOT NULL,          -- 'frontmatter', 'section:when-to-use',
                                       -- 'section:*', 'reference_file', 'script_file'
    section_heading TEXT,              -- original markdown heading, if applicable
    content TEXT NOT NULL,
    content_preview TEXT,
    file_path TEXT,                    -- for extra files: relative path in skill dir
    embedding BLOB,                    -- 384-dim float32 vector
    UNIQUE(skill_id, chunk_type, file_path)
);

-- Vector search virtual table (sqlite-vec)
CREATE VIRTUAL TABLE vec_chunks USING vec0(
    embedding float[384]
);
```

## Chunking Strategy

1. Read `SKILL.md` → split YAML frontmatter (`---` delimited) from body.
2. **Frontmatter** → one chunk, type `frontmatter`, content = full frontmatter text.
3. **Body** → split by `##` headings → one chunk per h2 section. Chunk type = `section:<normalized-heading>` (lowercase, hyphenated). Original heading stored in `section_heading`.
4. **Extra files** in skill dir → directories named `scripts/`, `references/`, `docs/`, etc. Each file gets its own chunk: type `reference_file` or `script_file`, `file_path` set to relative path.
5. Content hash (SHA256) computed from the raw SKILL.md text for dedup.

## Search Engine

### Algorithm

1. Encode query → 384-dim vector (same model as indexing).
2. sqlite-vec finds top-K nearest chunks (K=100, configurable).
3. Per-skill score:

   ```
   score = Σ(chunk_cosine_sim × chunk_weight) / Σ(chunk_weight)
   ```

   Weights looked up from config by `chunk_type`. Unmatched section headings fall through to `section:*` weight.
4. Dedup: skills with identical `content_hash` from different `source_dirs` — keep the one with highest priority (lowest `priority` value).
5. Return sorted by score descending.

### Output

Each result returns:
- `name` — skill name from frontmatter or directory name
- `source_dir` — tracked directory it was found in
- `path` — absolute path to the SKILL.md file
- `score` — relevance score (0 to 1)

### Output Formats

- Default: human-readable table
- `--json`: JSON array for programmatic use (fzf, MCP plugin)

### Filters

- `--section <name>` — restrict to a specific section type
- `--dir <path>` — restrict to a specific source directory
- `--top N` — limit results (default: 10)

## CLI Commands

| Command | Description |
|---------|-------------|
| `skill-manager add <dir>` | Add a directory to tracked dirs |
| `skill-manager remove <dir>` | Remove a directory from tracking |
| `skill-manager list` | List tracked dirs with skill count |
| `skill-manager search <query> [--json] [--section] [--dir] [--top]` | Semantic search |
| `skill-manager reindex [--full]` | Incremental re-index (or full with `--full`) |
| `skill-manager check [name]` | Check installed skill for updates from source repo (compares `source_commit_hash` against remote HEAD). For discovered skills: validate dir structure only. |
| `skill-manager check --dir <path>` | Validate a skill directory (frontmatter, structure) without registering it |
| `skill-manager copy <name> [target]` | Copy skill dir to target (default: cwd). Fails if target/<skill-name> exists; use `--force` to overwrite. |
| `skill-manager symlink <name> [target]` | Symlink skill dir to target. Fails if target/<skill-name> exists; use `--force` to overwrite. |
| `skill-manager edit <name>` | Open SKILL.md in $EDITOR |
| `skill-manager delete <name>` | Remove skill from registry |
| `skill-manager status` | Index health, counts, parse errors |

## Deduplication

- Primary dedup key: `content_hash` (SHA256 of SKILL.md).
- When two indexed skills have the same content_hash, they're treated as identical.
- In search results, only the highest-priority source_dir's entry is shown.
- Priority is set by the order in `config.toml [dirs].tracked` (first = highest priority) or explicit `priority` field.

## Error Handling

| Scenario | Handling |
|----------|----------|
| Corrupt/invalid SKILL.md | Log warning, skip file, continue indexing. Reported in `status`. |
| Invalid frontmatter | Skip file, log parse error details. |
| Embedding model download fails | Fall back to keyword search (SQLite LIKE). `reindex` retries later. |
| sqlite-vec not installed | Print clear install instructions on first run. |
| Concurrent access | SQLite WAL mode. Writes use locking. |
| File deleted before reindex | Pruned during full reindex; stale entries reported in `status`. |
| Circular symlinks | Resolve with max depth of 3. |
| Large skill dirs | Incremental indexing by mtime; batch embeddings (32 chunks/batch). |

## Testing Strategy

| Layer | Approach |
|-------|----------|
| **Parser** | Unit tests with fixture SKILL.md files (valid frontmatter, malformed, no frontmatter, various heading structures). |
| **Scanner** | Temp directory integration tests for incremental indexing, dedup, dir removal detection. |
| **Embedder** | Mock sentence-transformers for unit tests. One acceptance test with real model. |
| **Search** | Index known fixture skills, assert ranking, test weight effects, test dedup. |
| **CLI** | Subprocess calls to CLI entry point. Assert exit codes, stdout, json output. |
| **sqlite-vec** | Write known vectors, verify cosine similarity, test edge cases (zero vectors, empty DB). |

## v2 Preview (not in scope for v1)

- Remote registry integration (skillsmp.com API)
- `skill-manager install <name>` — download and install remote skills
- `skill-manager update [name]` — update installed skills from source
- `skill-manager publish` — publish a skill to the registry
- OpenCode MCP plugin (TypeScript) — injects matching skills into active sessions
- fzf-based interactive search
- Security scanning for malicious skills (content review, sandbox checks)
