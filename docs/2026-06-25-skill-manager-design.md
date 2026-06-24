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
1. Split YAML frontmatter (`---` delimited) from body → one `frontmatter` chunk.
2. Split body by `##` headings → one chunk per h2 section. Chunk type = `section:<normalized-heading>` (lowercase, hyphenated). Original heading stored in `section_heading`.

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
| `.js`, `.jsx` | JavaScript | `javascript` | `function_declaration`, `class_declaration`, `method_definition`, `arrow_function`, `variable_declarator` (const fn =) |
| `.ts`, `.tsx` | TypeScript | `typescript` | `function_declaration`, `class_declaration`, `interface_declaration`, `type_alias_declaration`, `method_definition` |
| `.go` | Go | `go` | `function_declaration`, `method_declaration`, `type_declaration`, `struct_type` |
| `.rs` | Rust | `rust` | `function_item`, `struct_item`, `impl_item`, `trait_item`, `enum_item`, `type_item`, `mod_item` |
| `.sh`, `.bash` | Bash | `bash` | `function_definition` |
| `.java` | Java | `java` | `method_declaration`, `class_declaration`, `interface_declaration` |
| `.c`, `.h` | C | `c` | `function_definition`, `struct_specifier` |
| `.cpp`, `.hpp` | C++ | `cpp` | `function_definition`, `class_specifier`, `struct_specifier` |

**Files with no top-level definitions** (e.g., a flat config script): The entire file becomes one chunk.

**Edge cases handled by tree-sitter natively:**
- Nested functions/classes → only top-level defs become separate chunks
- Braces inside strings → parsed correctly as string nodes, not scope tokens
- Comments and docstrings → included in preceding chunk
- Template literals (JS) → parsed correctly
- Decorators (Python) → captured via `decorated_definition` node as part of the definition

**Fallback for unsupported languages:** Use line-based chunks of ~50 lines with 10-line overlap (only for files >100 lines; smaller files stay as one chunk). This covers `.rb`, `.php`, `.swift`, `.kt`, `.lua`, and any other uncommon languages.

**Markdown/docs files** (`.md`, `.rst`, `.txt`):
- Split by `##` headings (same as SKILL.md body).
- Each section → one chunk with heading in `section_heading`.
- No headings → full file as one chunk.

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
│   └── _extract_top_level_defs()  # walk AST, extract definition nodes
├── DEFINITION_QUERIES             # tree-sitter S-expressions per language
│   ├── python: "(function_definition) @def (class_definition) @def ..."
│   ├── javascript: "(function_declaration) @def (class_declaration) @def ..."
│   └── ...
├── _line_fallback()               # line-based with overlap for unknown languages
└── _extract_name()                # get function/class name from AST node
```

Tree-sitter grammars are loaded lazily and cached in a dict keyed by language name. A scan of 100 skill dirs might touch 5-6 languages — only those grammars get loaded.

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
| `skill-manager add <dir> [--label]` | Add a directory to tracked dirs and immediately scan it. `--label` sets an optional nickname. |
| `skill-manager remove <dir>` | Remove a directory from tracking. Does not delete files, just removes from index. |
| `skill-manager list [--json]` | List all indexed skills. Default output: grouped by source_dir, showing skill name + description per group. `--json`: flat array with `{skill_name, description, source_dir, abs_path, commit_hash, source_url, install_method}` per entry. |
| `skill-manager scan` | Run incremental scan: walk tracked dirs, hash all files, compare against DB, re-embed changed/new files, prune removed. Safe to run repeatedly. |
| `skill-manager scan --full` | Full re-index: force re-hash + re-embed all files regardless of hash state. |
| `skill-manager search <query> [--json] [--section] [--dir] [--top N]` | Semantic search. Reads from DB only — no indexing work. `--json` for programmatic use. `--section` filters by chunk type. `--dir` scopes to a source dir. `--top` limits results (default 10). |
| `skill-manager check [name]` | Check a skill for updates: for installed skills (v2), compares `source_commit_hash` against remote HEAD. For discovered skills: validate dir structure + frontmatter only. |
| `skill-manager check --dir <path>` | Validate a skill directory's structure/frontmatter without registering it. Exit 0 if valid, non-zero with errors if not. |
| `skill-manager copy <name> [target] --force` | Copy skill dir to `target/<skill-name>` (default: cwd). `--force` overwrites existing. |
| `skill-manager symlink <name> [target] --force` | Symlink skill dir to `target/<skill-name>` (default: cwd). `--force` overwrites existing. |
| `skill-manager edit <name>` | Open the skill's SKILL.md in `$EDITOR`. |
| `skill-manager delete <name>` | Remove skill from registry (does not delete files on disk). |
| `skill-manager install-timer [--interval 15]` | Generate and install systemd user timer + service units for periodic scan. |
| `skill-manager remove-timer` | Remove the installed systemd timer and service units. |
| `skill-manager status [--json]` | Index health: total skills, chunks, last scan time, tracked dirs, parse error count. |
| `skill-manager config` | Print current config (with sensitive defaults resolved). |
| `skill-manager config --show-paths` | Print resolved paths for config, DB, cache, model dirs. |

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

| Layer | Approach |
|-------|----------|
| **Parser** | Unit tests with fixture SKILL.md files (valid frontmatter, malformed, no frontmatter, various heading structures). |
| **Scanner** | Temp directory integration tests for incremental indexing, dedup, dir removal detection. |
| **Embedder** | Mock sentence-transformers for unit tests. One acceptance test with real model. |
| **Search** | Index known fixture skills, assert ranking, test weight effects, test dedup. |
| **CLI** | Subprocess calls to CLI entry point. Assert exit codes, stdout, json output. |
| **sqlite-vec** | Write known vectors, verify cosine similarity, test edge cases (zero vectors, empty DB). |

## v2/v3 Preview (not in scope for v1)

### v2 — Remote Registry + fzf
- Remote registry integration (skillsmp.com API)
- `skill-manager install <name>` — download and install remote skills
- `skill-manager update [name]` — update installed skills from source
- `skill-manager publish` — publish a skill to the registry
- fzf-based interactive search (`skill-manager search --fzf`)

### v3 — OpenCode MCP Plugin (TypeScript)
The plugin runs as an MCP server that shells out to `skill-manager search --json`.

When injecting a skill into a running session, the plugin:
1. Calls `skill-manager search <context> --json --top 1` to find the best-matching skill
2. Reads the skill's SKILL.md content from disk
3. **Prepends a metadata block** to the injected content with the full info from the search result (name, description, score, source_dir, files list with abs paths), then appends the SKILL.md body
4. The injected block looks like:

```
## skill:react-form-validation (score: 0.87)
- source: ~/.config/opencode/skills
- description: Validates React forms with Zod
- files: SKILL.md, scripts/setup.sh, references/api-patterns.md

<SKILL.md content>
```

The full `files` list (with absolute paths resolved from `source_dir`) lets the agent also load any extra scripts, references, or docs into context as needed.

### Future considerations
- Security scanning for malicious skills (content review, sandbox checks)
- Skill dependency resolution (a skill that depends on another skill)
