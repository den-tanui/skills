# Skill Manager — Design Spec

**Date:** 2026-06-25
**Status:** Draft
**Version:** v1 (Local indexing + search)

## Overview

A comprehensive skill management system for OpenCode skills. v1 focuses on local indexing with semantic search. Future versions add remote registry integration and an OpenCode MCP plugin.

**Core problem:** Skills scattered across many directories with no search, no dedup, no provenance tracking, and manual installation workflow.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│  systemd timer (skill-manager-scan.timer)                  │
│  └→ skill-manager-scan.service: skill-manager scan         │
│     (runs every N minutes, hashes all files, updates DB)   │
└─────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                    skill-manager CLI                         │
│  (Python, installed via pipx/pip)                           │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Config  │  │ Scanner  │  │ Embedder │  │  Search   │  │
│  │  Manager │  │ + Parser │  │(sentence │  │  Engine   │  │
│  │          │  │          │  │transform)│  │ (DB only) │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │              │             │               │        │
│  ┌────┴──────────────┴─────────────┴───────────────┴────┐  │
│  │              SQLite + sqlite-vec DB                   │  │
│  │  ~/.local/share/skill-manager/skills.db               │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
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
| **Scanner + Parser** | Walks tracked dirs for `SKILL.md` files. Extracts YAML frontmatter. Splits body into sections by markdown heading. Discovers extra files in skill dirs. Hash-driven incremental detection. |
| **Indexer** | Orchestrates scan → parse → chunk → embed → store. Handles incremental updates via file hash comparison. Embeds only changed/new files. |
| **Embedder** | Wraps sentence-transformers (`all-MiniLM-L6-v2`). Batches chunks for efficiency. Returns 384-dim vectors. |
| **Search Engine** | Read-only from DB. Embed query once → cosine similarity against `vec_chunks` → aggregate per-skill with weights → deduplicate → rank. No indexing work during search. |
| **Skill Manager** | `scan`, `check`, `copy`, `symlink`, `edit`, `delete`, `list`, `install-timer` commands. |

### Data Flow

**Scan (timer-driven):** `Tracked dirs → Scanner → hash all files → compare against file_hashes table → changed/new files → Parser → Chunks → Embedder → upsert into sqlite-vec`

**Search (instant):** `Query → Embedder → sqlite-vec cosine similarity → Chunk scores × weights → Aggregate per-skill → Ranked results`

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
"code_block:*" = 0.15
reference_file = 0.10
script_file = 0.05

[embedding]
model = "all-MiniLM-L6-v2"
batch_size = 32
device = "cpu"

[scan]
interval_minutes = 15

[publish]              # v2: target repo for publishing skills
# repo = "github.com/my-user/my-skills"
# branch = "main"
# local_checkout = "~/.local/share/skill-manager/publish-repo"
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
    description TEXT,
    frontmatter_json TEXT,
    size_bytes INTEGER,
    install_method TEXT DEFAULT 'discovered',  -- 'discovered'|'installed'|'symlinked'
    source_url TEXT,                  -- skillsmp.com URL, GitHub URL, etc.
    source_repo TEXT,                 -- git remote URL
    source_commit_hash TEXT,          -- pinned commit hash when installed
    indexed_at TEXT,
    modified_at TEXT,
    UNIQUE(name, abs_path)
);

-- File-level hashes for incremental change detection
CREATE TABLE file_hashes (
    id INTEGER PRIMARY KEY,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,          -- relative to skill dir (e.g. "SKILL.md", "scripts/foo.sh")
    sha256 TEXT NOT NULL,             -- SHA256 of file content
    mtime REAL,                       -- last known mtime
    UNIQUE(skill_id, file_path)
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

## Incremental Scan (skill-manager scan)

The scan command is the heart of the indexer, designed to be run periodically via systemd timer.

### Scan Algorithm

```
for each tracked_dir in config:
  walk tracked_dir → find every SKILL.md

  for each SKILL.md found:
    compute sha256_hash of SKILL.md and all extra files in its dir
    look up skill + file_hashes in DB by abs_path

    if SKILL.md NOT in DB:
      → NEW skill: insert skill record, hash all files, chunk + embed everything

    else:
      → EXISTING skill: compare each file's sha256 against file_hashes table
         ├── hash matches → skip (unchanged)
         ├── hash differs → re-chunk file, re-embed, update hash record
         ├── new file found → chunk + embed + insert hash
         └── stored file missing → delete chunk + hash record

  for each skill in DB whose abs_path no longer exists on disk:
    → REMOVED: cascade-delete skill + chunks + hashes
```

The scan is designed so the common case (nothing changed) is very fast: walk the tracked dirs, hash each SKILL.md, no reads of extra files unless SKILL.md changed.

### Chunking Strategy

Chunks are created by splitting files at **semantic boundaries** — never splitting a function, class, or logical block in half. Strategy depends on file type:

**SKILL.md:**

Parsed with `tree-sitter-markdown` to get proper AST nodes for sections and code blocks.

1. Split YAML frontmatter (`---` delimited) from body → one `frontmatter` chunk.
2. Walk the markdown AST:
   - Each `section` node (h2 heading `##`) is the top-level grouping.
   - Within a section, `fenced_code_block` nodes are extracted as **separate chunks** with type `code_block:<language>` (e.g. `code_block:python`, `code_block:javascript`). The language tag is read from the code fence info string.
   - Prose text between code blocks stays as the section chunk (type `section:<normalized-heading>`).
   - Inline code spans (`` ` ``) stay with their surrounding prose — not split out.
3. Each code block chunk includes the fenced code block markers and language tag (so the embedding captures the language context).

Example — given a SKILL.md body section like:

```markdown
## Usage

Call `validate()` to check your data.

```python
def validate(data):
    return schema.parse(data)
```

For advanced cases, use the options parameter:

```python
validate(data, strict=True)
```
```

This produces **three chunks** for the "Usage" section:
- `section:usage` — prose: "Call `validate()`..." + "For advanced cases..." (inline code stays)
- `code_block:python` — the first code block
- `code_block:python` — the second code block

This way, searching "validate with schema.parse" matches the Python code block directly, while searching "explain the validate function" matches the prose section. Both contribute to the skill's overall score via their respective weights.

**Code files** (`.sh`, `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, etc.):

Chunked by AST node boundaries using **tree-sitter**. This gives us exact start/end positions for every function, class, method, and type definition — correctly handling nested scopes, strings with braces, comments, and all edge cases.

**Dependencies:**
- `tree-sitter` — Python bindings for tree-sitter
- `tree_sitter_languages` — pre-compiled grammars for ~50 languages

Grammars are loaded on demand per file extension and cached in memory for the duration of the scan.

**Chunking algorithm:**

```
parser = Language(extension)  # e.g. Language("python"), Language("javascript")
tree = parser.parse(bytes(content, "utf8"))
root = tree.root_node

defs = find_top_level_definitions(root_node)
# Queries for each language target: function_definition, class_definition,
# method_definition, interface_declaration, type_alias, etc.

for def_node in defs:
    name = extract_definition_name(def_node)     # e.g. "validateForm"
    start_line = def_node.start_point[0]
    end_line = def_node.end_point[0]
    content = lines[start_line : end_line + 1]

    # Include preceding comments/docstrings by checking previous sibling nodes
    prev = def_node.prev_sibling or def_node.parent
    preceding = extract_preceding_doc_comment(prev, def_node)
    if preceding:
        content = preceding + content

    chunks.append({
        "name": name,
        "content": content,
        "type": "script_file" or "reference_file",
        "start_line": start_line,
        "end_line": end_line,
    })
```

**Supported languages (v1):**

| Extension | Language | Tree-sitter grammar | Top-level nodes captured |
|-----------|----------|-------------------|--------------------------|
| `.py` | Python | `python` | `function_definition`, `class_definition`, `decorated_definition` |
| `.js`, `.jsx` | JavaScript | `javascript` | `function_declaration`, `class_declaration`, `arrow_function`, `variable_declarator` (const fn =) |
| `.ts`, `.tsx` | TypeScript | `typescript` | `function_declaration`, `class_declaration`, `interface_declaration`, `type_alias_declaration` |
| `.go` | Go | `go` | `function_declaration`, `method_declaration`, `type_declaration` |
| `.rs` | Rust | `rust` | `function_item`, `struct_item`, `impl_item`, `trait_item`, `enum_item` |
| `.sh`, `.bash` | Bash | `bash` | `function_definition` |
| `.java` | Java | `java` | `method_declaration`, `class_declaration`, `interface_declaration` |
| `.c`, `.h` | C | `c` | `function_definition`, `struct_specifier` |
| `.cpp`, `.hpp` | C++ | `cpp` | `function_definition`, `class_specifier`, `struct_specifier` |
| `.md`, `.mdx` | Markdown | `markdown` | `section` (h2 heading), `fenced_code_block` (extracted as separate chunks) |

**Files with no top-level definitions** (e.g., a flat config script): The entire file becomes one chunk.

**Edge cases handled by tree-sitter natively:**
- Nested functions/classes → only top-level defs become separate chunks
- Braces inside strings → parsed correctly as string nodes, not scope tokens
- Comments and docstrings → included in preceding chunk
- Template literals (JS) → parsed correctly
- Decorators (Python) → captured via `decorated_definition` node as part of the definition

**Fallback for unsupported languages:** Use line-based chunks of ~50 lines with 10-line overlap (only for files >100 lines; smaller files stay as one chunk). This covers `.rb`, `.php`, `.swift`, `.kt`, `.lua`, and any other uncommon languages.

**Markdown/docs files** (`.md`, `.mdx`, `.rst`):
- Parsed with `tree-sitter-markdown` — same approach as SKILL.md:
  - Split by `##` headings → one chunk per section.
  - Within each section, extract fenced code blocks as separate `code_block:<language>` chunks.
  - Inline code stays with prose.
- No headings → full file as one chunk (still extracting code blocks).

**Config/data files** (`.json`, `.toml`, `.yaml`, `.csv`):
- Full file as one chunk (typically small).

**Key invariant:** A single function/class/block is never divided across chunks. If the chunking heuristic can't find safe boundaries, err on the side of larger chunks (full file) rather than splitting a definition.

SHA256 hash is computed per-file (not per-chunk) for change detection. If a file's hash changes, all its chunks get re-computed and re-embedded.

### Chunker Implementation

The chunker lives in a single module `skill_manager/chunker.py`:

```
chunker.py
├── Chunker class                  # entry point: chunk_file(path) → list[Chunk]
│   ├── _load_grammar()            # load tree-sitter grammar for extension (cached)
│   ├── _parse_tree()              # parse file → CST
│   └── _extract_defs()            # walk AST, extract definition/code-block nodes
├── DEFINITION_QUERIES             # tree-sitter S-expressions per language
│   ├── python: "(function_definition) @def (class_definition) @def ..."
│   ├── javascript: "(function_declaration) @def (class_declaration) @def ..."
│   └── markdown: "(section [  (#heading) @header (fenced_code_block) @code ... ]) @sec"
├── _code_block_fallback()          # regex-based code block extraction if tree-sitter-markdown unavailable
└── _line_fallback()               # line-based with overlap for unknown code languages
```

Tree-sitter grammars are loaded lazily and cached in a dict keyed by language name. A scan of 100 skill dirs might touch 5-6 languages — only those grammars get loaded.

For SKILL.md files, the markdown grammar provides `fenced_code_block` nodes with their language tag. Embedded code blocks are extracted as separate chunks. For each code block whose language has a tree-sitter grammar available (e.g., a ````python` block inside a SKILL.md), we optionally parse it further with tree-sitter to split into function-level chunks. This is deferred to v2 — v1 treats each fenced code block as one chunk.

## Systemd Timer Integration

On `skill-manager install-timer`, the CLI generates and installs two systemd user units:

**`~/.config/systemd/user/skill-manager-scan.service`:**
```ini
[Unit]
Description=Skill Manager — scan and index skills

[Service]
Type=oneshot
ExecStart=%h/.local/bin/skill-manager scan
```

**`~/.config/systemd/user/skill-manager-scan.timer`:**
```ini
[Unit]
Description=Periodic skill index scan (every 15 minutes)

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
```

The scan interval is configurable via `config.toml`:
```toml
[scan]
interval_minutes = 15
```

On each trigger, `skill-manager scan` runs the full incremental scan (hash all files, update changed entries). Since the common case (nothing changed) is fast, the service completes quickly. Search always returns results from the DB without any indexing work.

## Search Engine

### Algorithm

1. Encode query → 384-dim vector (same model as indexing).
2. sqlite-vec finds top-K nearest chunks (K=100, configurable).
3. Per-skill score:

   ```
   score = Σ(chunk_cosine_sim × chunk_weight) / Σ(chunk_weight)
   ```

   Weights looked up from config by `chunk_type`. Unmatched section headings fall through to `section:*` weight.
4. Dedup: if the same skill content (detected via file-level SHA256 hashes) exists in multiple `source_dirs`, only the highest-priority entry is shown.
5. Return sorted by score descending.

### Output

Default (human-readable table):
```
name              score  source_dir
react-validation  0.87   ~/.config/opencode/skills
fzf-advanced      0.62   ~/my-skills
```

JSON (per result — for plugin/agent consumption):
```json
{
  "name": "react-form-validation",
  "description": "Validates React forms with Zod",
  "score": 0.87,
  "source_dir": "~/.config/opencode/skills",
  "abs_path": "/home/user/.config/opencode/skills/react-form-validation/SKILL.md",
  "files": [
    "SKILL.md",
    "scripts/setup.sh",
    "scripts/teardown.sh",
    "references/api-patterns.md"
  ],
  "file_count": 4,
  "source_url": null,
  "source_commit_hash": null,
  "install_method": "discovered"
}
```

The `files` list contains all indexed files in the skill dir, relative to the skill's directory. Assembled from the `file_hashes` table at query time. An agent (or MCP plugin in v3) can use these paths to load additional context beyond SKILL.md.

### Output Formats

- Default: human-readable table
- `--json`: JSON array with full fields including the `files` map

### Filters

- `--section <name>` — restrict to a specific section type
- `--dir <path>` — restrict to a specific source directory
- `--top N` — limit results (default: 10)

## CLI Commands

| Command | Description |
|---------|-------------|
| **Config & Setup** | |
| `skill-manager add <dir> [--label]` | Add a directory to tracked dirs and immediately scan it. `--label` sets an optional nickname. |
| `skill-manager remove <dir>` | Remove a directory from tracking. Does not delete files, just removes from index. |
| `skill-manager install-timer [--interval 15]` | Generate and install systemd user timer + service units for periodic scan. |
| `skill-manager remove-timer` | Remove the installed systemd timer and service units. |
| `skill-manager config` | Print current config (with sensitive defaults resolved). |
| `skill-manager config --show-paths` | Print resolved paths for config, DB, cache, model dirs. |
| | |
| **Indexing** | |
| `skill-manager scan` | Run incremental scan: walk tracked dirs, hash all files, compare against DB, re-embed changed/new files, prune removed. Safe to run repeatedly. |
| `skill-manager scan --full` | Full re-index: force re-hash + re-embed all files regardless of hash state. |
| `skill-manager status [--json]` | Index health: total skills, chunks, last scan time, tracked dirs, parse error count. |
| | |
| **Search & Browse** | |
| `skill-manager search <query> [--json] [--section] [--dir] [--top N]` | Semantic search. Reads from DB only — no indexing work. `--json` for programmatic use. |
| `skill-manager list [--json]` | List all indexed skills. Default: grouped by source_dir. `--json`: flat array with full fields. |
| | |
| **Local Management** | |
| `skill-manager copy <name> [target] --force` | Copy skill dir to `target/<skill-name>` (default: cwd). `--force` overwrites. |
| `skill-manager symlink <name> [target] --force` | Symlink skill dir to `target/<skill-name>`. `--force` overwrites. |
| `skill-manager edit <name>` | Open the skill's SKILL.md in `$EDITOR`. |
| `skill-manager delete <name>` | Remove skill from registry (does not delete files on disk). |
| `skill-manager check [--files] [--security] [--updates] [name\|--dir <path>]` | Validate a skill or all skills. `--files`: verify files exist + hash integrity (default: on). `--security`: re-run security checks (stub until v4, default: on). `--updates`: check for updates from source repo (default: on for installed skills). Last arg is skill name, or `--dir <path>` to check any dir without registering. Without name: runs against all registered skills. |
| | |
| **Remote & Publish (v2)** | |
| `skill-manager install <repo> [skill-name]` | Install a skill from a GitHub repo. If `skill-name` provided, install that specific skill. If omitted, scan the repo and list available skills (dirs with SKILL.md). |
| `skill-manager publish [skill-name]` | Publish a local skill to the configured publish repo. Without arguments, show an interactive checklist of all local skills with ones already in the publish repo pre-checked. |
| `skill-manager update [name]` | Update installed skills from their source repo (compares stored `source_commit_hash`). |

## Deduplication

- Skills are uniquely identified by `(name, abs_path)` — same skill in different directories = separate entries.
- When the same skill (matching by name and content) exists across multiple tracked dirs:
  1. File-level SHA256 hashes are compared to detect identical content.
  2. In search results, duplicate content is collapsed: only the entry from the highest-priority `source_dir` is shown.
- Priority is set by the order in `config.toml [dirs].tracked` (first = highest priority) or an explicit `priority` field on source_dirs.

## Error Handling

| Scenario | Handling |
|----------|----------|
| Corrupt/invalid SKILL.md | Log warning, skip file, continue indexing. Reported in `status`. |
| Invalid frontmatter | Skip file, log parse error details. |
| Embedding model download fails | Fall back to keyword search (SQLite LIKE). `scan --full` retries later. |
| sqlite-vec not installed | Print clear install instructions on first run. |
| Concurrent access | SQLite WAL mode. Writes use locking. |
| File(s) deleted from disk | Detected on next `scan`. Cascade-delete from DB. |
| Circular symlinks | Resolve with max depth of 3. |
| Large skill dirs | Incremental indexing by mtime; batch embeddings (32 chunks/batch). |

## Testing Strategy

### Framework & Tooling

- **Test runner:** pytest with `--cov` for coverage, `-x` for fail-fast
- **Fixtures:** `tests/fixtures/` directory with miniature skill trees
- **Mocking:** `unittest.mock` for sentence-transformers; real model in acceptance tests only
- **DB tests:** in-memory SQLite + sqlite-vec for speed; temp file for persistence tests
- **CI:** runs on every push via GitHub Actions (pytest, lint, typecheck)

### Fixture Layout

```
tests/fixtures/
├── valid-skill/
│   ├── SKILL.md              # valid frontmatter + 3 h2 sections + 2 code blocks
│   ├── scripts/
│   │   └── setup.sh          # bash functions to test code chunking
│   └── references/
│       └── api-patterns.md   # markdown with headings + code blocks
├── no-frontmatter/
│   └── SKILL.md              # no YAML frontmatter — tests error handling
├── malformed-frontmatter/
│   └── SKILL.md              # invalid YAML — tests graceful skip
├── code-files/
│   ├── SKILL.md              # basic skill with no code blocks
│   ├── sample.py             # 3 functions + 1 class — tests Python chunking
│   ├── sample.js             # arrow functions + classes — tests JS chunking
│   ├── sample.go             # func + struct + method — tests Go chunking
│   ├── nested.py             # outer function with inner function — tests nesting
│   └── sample.sh             # bash functions — tests shell chunking
├── large-no-defs/
│   ├── SKILL.md
│   └── data.csv              # 200 lines, no definitions — tests line fallback
└── empty-dir/
    └── SKILL.md              # valid frontmatter, empty body
```

### Test Layers

#### 1. Parser / Chunker (`tests/test_chunker.py`)

| Test | What it verifies |
|------|-----------------|
| `test_frontmatter_extraction` | Parses valid YAML frontmatter; returns name, description |
| `test_no_frontmatter` | Returns no frontmatter chunk, logs warning |
| `test_malformed_frontmatter` | Returns error, skips file gracefully |
| `test_markdown_section_splitting` | Each `##` heading becomes one `section:*` chunk |
| `test_code_block_extraction` | Fenced code blocks are separate `code_block:<lang>` chunks |
| `test_inline_code_stays_in_prose` | `` `code` `` spans remain in their section chunk |
| `test_python_function_boundaries` | Each top-level `def` / `class` is its own chunk |
| `test_js_function_boundaries` | `function`, `class`, `const fn = () =>` each its own chunk |
| `test_go_function_boundaries` | `func` each its own chunk |
| `test_nested_functions_not_split` | Inner function stays inside outer chunk |
| `test_decorators_included` | `@decorator` lines folded into preceding Python chunk |
| `test_comments_before_definition` | Docstrings/comments above a def are included in that chunk |
| `test_unsupported_language_fallback` | Unknown extension with >100 lines → line-based chunks |
| `test_small_files_one_chunk` | Files <100 lines with no defs → single chunk |
| `test_empty_file` | Empty file → no chunks (skipped) |
| `test_chunk_metadata` | Every chunk has correct `chunk_type`, `file_path`, `section_heading` |

#### 2. Scanner / Indexer (`tests/test_scanner.py`)

| Test | What it verifies |
|------|-----------------|
| `test_initial_scan_populates_db` | After `scan`, all skills in tracked dirs are in `skills` table |
| `test_incremental_scan_no_changes` | Second `scan` with no changes → no new embeddings computed |
| `test_incremental_scan_file_modified` | Changing a file → `scan` re-embeds only that file's chunks |
| `test_incremental_scan_new_file` | Adding a file → `scan` creates new chunks |
| `test_incremental_scan_file_deleted` | Removing a file → `scan` deletes its chunks + hash record |
| `test_incremental_scan_new_skill` | Adding a new skill dir → `scan` indexes it fully |
| `test_incremental_scan_skill_removed` | Deleting a SKILL.md → `scan` cascade-deletes skill |
| `test_full_reindex` | `scan --full` re-embeds all chunks regardless of hash state |
| `test_hash_change_detection` | Modifying a file changes its sha256; scan detects and re-embeds |
| `test_directory_walk_depth` | Nested skill dirs at depth 1-3 are found; depth >3 requires explicit path |
| `test_circular_symlink_handling` | Symlink loop doesn't crash scanner |
| `test_scan_empty_tracked_dir` | No SKILL.md files → empty result, no crash |

#### 3. Embedder (`tests/test_embedder.py`)

| Test | What it verifies |
|------|-----------------|
| `test_model_loads` | sentence-transformers model loads successfully |
| `test_embed_dimension` | Output vectors are 384-dim float32 |
| `test_batch_embedding` | Batch of 32 returns 32 vectors |
| `test_deterministic_output` | Same input → same embedding (seed consistency) |
| `test_model_fallback` | Model download fails → returns None, scanner falls back gracefully |
| `test_embed_edge_cases` | Empty string, very long string, unicode, code snippets |

#### 4. Search Engine (`tests/test_search.py`)

| Test | What it verifies |
|------|-----------------|
| `test_search_returns_results` | Known query returns expected skill in top results |
| `test_search_empty_index` | Search before any scan → empty results, no crash |
| `test_weight_effect` | Two skills with different section matches: higher-weighted section match scores higher |
| `test_dedup_collapse` | Same skill in two dirs → only higher-priority one in results |
| `test_dedup_priority_order` | Config dir order determines priority |
| `test_section_filter` | `--section "when to use"` only returns chunks of that type |
| `test_dir_filter` | `--dir ~/my-skills` only returns skills from that source |
| `test_top_limit` | `--top 3` returns at most 3 results |
| `test_json_output_structure` | `--json` output has all required fields: name, score, source_dir, abs_path, files, file_count |
| `test_json_file_manifest` | `files` lists all indexed files relative to skill dir |
| `test_keyword_fallback` | Embedder disabled → keyword search returns reasonable results |

#### 5. SQLite + sqlite-vec (`tests/test_db.py`)

| Test | What it verifies |
|------|-----------------|
| `test_vector_insert_and_query` | Known vector inserted → cosine similarity query returns correct ranking |
| `test_vector_dimension_mismatch` | Wrong dimension vector → clear error |
| `test_concurrent_reads` | Multiple readers at once → no crashes |
| `test_write_lock` | Concurrent writes → serialized, no corruption |
| `test_cascade_delete` | Deleting a skill → its chunks and hashes also deleted |
| `test_wal_mode` | DB created with WAL journal mode |
| `test_empty_vec_search` | Empty vec_chunks table → query returns empty |

#### 6. CLI (`tests/test_cli.py`)

| Test | What it verifies |
|------|-----------------|
| `test_add_dir` | `skill-manager add <dir>` updates config and triggers scan |
| `test_add_dir_invalid` | Non-existent dir → error exit code + message |
| `test_remove_dir` | `skill-manager remove <dir>` removes from config, leaves files |
| `test_list_human` | Default output is grouped by source_dir |
| `test_list_json` | `--json` returns valid JSON array |
| `test_list_json_fields` | JSON has skill_name, description, source_dir, abs_path |
| `test_search_cli` | `skill-manager search <query>` prints table to stdout |
| `test_search_json` | `--json` outputs valid JSON |
| `test_search_exit_codes` | No results → exit 0 (empty); error → exit 1 |
| `test_scan_cli` | `skill-manager scan` completes with exit 0 |
| `test_scan_full` | `--full` completes with exit 0 |
| `test_copy` | `skill-manager copy <name>` copies skill dir to cwd |
| `test_copy_conflict` | Target exists without `--force` → error |
| `test_copy_force` | With `--force` → overwrites |
| `test_symlink` | `skill-manager symlink <name>` creates symlink |
| `test_edit` | `skill-manager edit <name>` opens $EDITOR (mock $EDITOR) |
| `test_delete` | `skill-manager delete <name>` removes from DB |
| `test_delete_nonexistent` | Non-existent skill → error |
| `test_install_timer` | `skill-manager install-timer` creates systemd unit files |
| `test_remove_timer` | `skill-manager remove-timer` removes systemd unit files |
| `test_config_show` | `skill-manager config` prints resolved config |
| `test_status` | `skill-manager status` shows counts and health |
| `test_status_json` | `--json` outputs valid JSON |
| `test_help` | `skill-manager --help` lists all commands |

#### 7. Integration (`tests/test_integration.py`)

| Test | What it verifies |
|------|-----------------|
| `test_full_workflow` | `add` → `scan` → `search` → `copy` → `list` → `delete` in sequence |
| `test_index_then_search` | Index fixture dirs, search confirms expected results |
| `test_incremental_then_search` | Modify a fixture file, re-scan, search returns updated content |

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=skill_manager --cov-report=term-missing

# Specific layer
pytest tests/test_chunker.py -v
pytest tests/test_cli.py -v

# Exclude acceptance tests (no model download)
pytest -m "not acceptance"

# Quick smoke test (no real embeddings)
pytest tests/test_chunker.py tests/test_db.py tests/test_cli.py -v
```

## v2/v3/v4 Preview (not in scope for v1)

### v2 — Remote Registry + Publishing + fzf

**Config:** User configures a publish repo in `config.toml`:
```toml
[publish]
repo = "github.com/my-user/my-skills"
branch = "main"
local_checkout = "~/.local/share/skill-manager/publish-repo"
```

**Install from GitHub:**
- `skill-manager install <repo> [skill-name]`
- Clones the repo to a temp dir, scans for dirs containing `SKILL.md`
- If `skill-name` is provided: installs that specific skill into the global install store
- If omitted: lists all available skills in the repo (dir name + description from frontmatter)

**Publish to GitHub:**
- `skill-manager publish [skill-name]`
- Without arguments: shows an interactive checklist of all local skills, with ones already in the publish repo pre-checked. User selects which to publish.
- With a skill name: copies the skill dir into a local checkout of the publish repo, commits, and pushes.
- Tracks `source_commit_hash` so published skills can be updated later.

**fzf:**
- `skill-manager search --fzf` — interactive fzf UI wrapping the search command

### v3 — OpenCode Plugin (TypeScript)

The plugin is more than a passive MCP server — it hooks into OpenCode's session context assembly to **automatically inject** relevant skills, including self-describing skills that teach the agent how to use skill-manager itself.

**Three integration points:**

1. **MCP server** — provides tools for the agent to call explicitly:
   - `search_skills(query)` → returns matching skills with file manifest
   - `get_skill(skill_name)` → returns full skill content + metadata
   - `inject_skill(skill_name)` → explicitly inject a skill into the current context

2. **Context injection hook** — automatically triggered during session setup or topic shifts:
   - Listens for context/topic signals (user request, file being edited, etc.)
   - Calls `skill-manager search "<current context>" --json --top 3`
   - For the best match(es), prepends a metadata block + SKILL.md content into the agent's context
   - The metadata block includes the full file manifest so the agent knows what extra files are available

**Injected format:**
```
## skill:react-form-validation (score: 0.87)
- source: ~/.config/opencode/skills
- description: Validates React forms with Zod
- files:
  - SKILL.md
  - scripts/setup.sh
  - references/api-patterns.md

<SKILL.md content>
```

The agent can then use the file paths to load additional context as needed.

3. **Self-describing meta-skills** — the plugin bundles built-in skills that teach agents how to use skill-manager:

   - **`skill-manager-usage`** — describes all CLI commands, flags, and workflows for skill-manager. Automatically injected at session start so the agent knows what tools are available without being told.
   - **`skill-manager-hooks`** — describes the context injection hook behavior so agents understand why skills appear in their context and how to leverage them.
   - **User-triggered commands** — the plugin can register custom OpenCode commands (e.g., `/search-skills`, `/install-skill`, `/publish-skill`) that the user can invoke from the chat input, which the agent can also call programmatically.

These meta-skills live in the plugin's own skill directory and are indexed alongside user skills for consistent search. A search for "how to install a skill" will find the `skill-manager-usage` meta-skill alongside any other relevant results.

### v4 — Security Scanning (future)
- Reuse tree-sitter parsing infrastructure to analyze code for malicious patterns
- Sandbox checks on installed skills
- Integrated into `skill-manager check` as a re-runnable step
- Skill dependency resolution
