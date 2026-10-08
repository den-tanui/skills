# Spec 0002 — Skill Scanner (Rust)

## 1. Overview

Convert the Apache 2.0-licensed bash skill scanner (spec 0001) into a fast, self-contained
binary built in Rust. The Rust version keeps the same user-facing interface and output formats,
replacing the Bash/Python implementation with a single-binary Rust CLI.

**Goal:** same functionality, materially faster scanning/parsing, no runtime dependencies
(bash, python), and a clean architecture suitable for future extension.

**License:** Apache 2.0 (same as 0001).

---

## 2. Scope

- Scan directories for skill files.
- Parse frontmatter (YAML between `---` fences) into structured metadata.
- Present results as JSON or aligned-table output.
- Support recursive/flat scanning, filtering, sorting, and include/exclude flags.

Out of scope (future iterations): watch-mode (file watching), live updates, remote skill
registries, plugin system, and a full YAML library (use a minimal custom parser for the
common `---` frontmatter pattern).

---

## 3. Architecture

```
src/
├── main.rs           # entry point, CLI arg parsing, pipeline wiring
├── cli.rs            # clap struct: args, flags, output options
├── scanner.rs        # directory traversal (recursive + flat mode)
├── parser.rs         # frontmatter extraction (streaming, no regex)
├── model.rs          # Skill, FrontmatterMetadata structs
├── presenter.rs      # JSON + table rendering
└── filter_sort.rs    # filtering + sorting application
```

**Pipeline (data flow):**

```
CLI args
  → scan dirs (collect candidate paths)
  → filter by SGI + extension
  → parse frontmatter per file (streaming read)
  → normalize metadata (known fields + raw map)
  → apply sort / filter
  → render (json | table)
  → stdout
```

**Threading model:**

- **Scanning** I/O-bound → parallel walk of multiple roots (rayon or std `thread::scope`).
- **Parsing** CPU-light, stateless → parallel per-file if the candidate list is large.
- **Presenting** single producer (collect `Skill`) → single consumer (render).

**Performance characteristics:**

| Concern | Design |
|---------|--------|
| Disk I/O | Sequential single-pass read per file |
| Allocations | Byte-slice scanning on the read buffer; no regex, no per-line `String` allocation in the hot path |
| Memory | `O(#skills)` retained; `O(max file bytes)` read buffer |
| Multi-root | Parallel directory walk |

---

## 4. CLI interface

See spec 0001 for the full flag description. The Rust CLI maps 1:1:

### General options

```
Usage: skillsmp [OPTIONS] [DIRS]...

Arguments:
  [DIRS]...  Directories to scan (default: current directory)

Options:
  -r, --recursive          Recursive scan (default: true)
  -R, --no-recursive       Flat scan (top-level only)
  -f, --format <FORMAT>    Output format: json or table
  -i, --include <GCI>      Also include GCI pattern (e.g. *.skill.md)
  -e, --exclude <GCI>      Exclude files matching GCI pattern
  -s, --sort <FIELD>       Sort by: name, path, date
      --sort-order <ORDER> Ascending or descending
  -F, --filter <TEXT>      Filter rows (case-insensitive substring)
  -n, --name-only          Only print the skill name (no other columns)
  -m, --meta-only          Print only metadata (no names)
  -o, --output <FILE>      Write output to FILE instead of stdout
  -h, --help               Print help
  -V, --version            Print version
```

### Examples (same as 0001)

```
$ skillsmp /path/to/skills
$ skillsmp -f json /path/to/skills
$ skillsmp -f json --sort name --filter yaml /path/to/skills
$ skillsmp -n /path/to/skills
$ skillsmp -f json -o skills.json /path/to/skills
```

---

## 5. Data model

### `Skill`

```rust
pub struct Skill {
    pub path: PathBuf,           // absolute file path
    pub name: String,            // from frontmatter (required)
    pub description: Option<String>, // from frontmatter (optional)
    pub meta: FrontmatterMetadata, // all other frontmatter keys
}
```

### `FrontmatterMetadata`

```rust
pub struct FrontmatterMetadata {
    pub data: BTreeMap<String, String>, // key -> value (raw, as parsed)
}
```

This preserves arbitrary keys (e.g. `license`, `category`, `tags`) while providing the known
fields (`name`, `description`) for the standard output columns.

### `ParseResult` (filter flag for pipeline)

```rust
pub struct ParseResult {
    pub skill: Option<Skill>,     // None if no frontmatter / no `name`
    pub had_frontmatter: bool,
    pub had_name: bool,
}
```

---

## 6. Scanner module

### Inputs
- `Vec<PathBuf>` — root directories (from CLI args).
- `recursive: bool` — whether to descend into subdirectories.

### Behavior
1. Iterate each root with `std::fs::read_dir` (or ` WalkDir` for simpler recursion).
2. Collect `DirEntry` paths into a `Vec<PathBuf>`.
3. When `recursive = false`, only include top-level entries.
4. Optionally sort the resulting path list for deterministic output.

### Outputs
- `Vec<PathBuf>` — candidate files.

### Notes
- Use `read_dir` (not `std::fs::metadata`) to avoid extra syscalls where possible.
- If `recursive` is off, do not descend into any subdirectory.
- Sorting is optional and only applied at the end of discovery.

---

## 7. Parser module

### Input
- `PathBuf` — file to parse.

### Behavior
1. Open with `OpenOptions::new().read(true).open()`.
2. Read into a `Vec<u8>` buffer (or `BufReader` for large files). For this use case, files are
   small (typically < 10 KB), so a full read is fine.
3. Scan the buffer for the first line that is exactly `---` (the frontmatter fence).
4. If `---` is found, scan forward for the closing `---` on its own line.
5. Extract the bytes between the two fences (the YAML frontmatter).
6. Parse the YAML into a `BTreeMap<String, String>` (simple key/value only; no nested YAML).
   - Split each line on the first `: ` or `:` (trailing values allowed).
   - Strip surrounding quotes from values if present.
7. Return the parsed metadata + a flag indicating whether frontmatter was found.

### Handling
- **No frontmatter**: return `ParseResult { skill: None, had_frontmatter: false, had_name: false }`.
- **Empty frontmatter**: return `None` (no `name` key).
- **Missing `name`**: return `None` (after parsing frontmatter but finding no `name` key).
- **Unicode**: use lossy or UTF-8 validation; skill frontmatter is expected to be UTF-8.
- **Malformed YAML**: return the raw key-value pairs as best-effort; do not fail the whole run.

### Output
- `Option<Skill>` + parse flags.

---

## 8. Presenter module

### JSON mode
- Serialize the list of `Skill` as a JSON array (or NDJSON if streaming is needed for huge
  inputs). Use `serde_json`.
- Fields: `path`, `name`, `description`, `meta` (all other keys).

### Table mode
- Compute column widths from headers + data.
- Render aligned columns with fixed-width layout.
- Columns: `Path`, `Name`, `Description` (and optionally `Meta` / arbitrary keys).
- `--name-only` shows only the `Name` column.
- `--meta-only` shows only the `Meta` (all keys as a compact representation).

### Output sink
- Default: `stdout`.
- `--output <FILE>`: write to a file instead.

---

## 9. Pipeline wiring

```
1. parse CLI args (cli.rs)
2. scan dirs (scanner.rs) -> Vec<PathBuf>
3. filter by include/exclude GCI + file extension (filter_sort.rs)
4. parse each file (parser.rs) -> Vec<Skill> (skip None results)
5. apply sort (filter_sort.rs)
6. apply filter (filter_sort.rs)
7. render (presenter.rs) -> String
8. write to stdout or --output file
```

---

## 10. Error handling

- **Per-file errors** (permission denied, IO error): print a warning to stderr, skip the file,
  continue scanning.
- **Parse errors** (malformed frontmatter): best-effort parse; if `name` is missing, skip the file.
- **CLI errors** (invalid args): clap handles; on error, print message + usage to stderr, exit
  with a non-zero status.
- **IO errors** (stdout write, file write): print to stderr, exit non-zero.

---

## 11. Testing strategy

- **Unit tests** (parser.rs, presenter.rs):
  - Basic frontmatter extraction (`---` / `---`).
  - Missing frontmatter returns `None`.
  - Missing `name` returns `None`.
  - YAML with quoted values, trailing values, multi-line values.
  - JSON output round-trip.
  - Table width computation.
- **Integration tests** (cli.rs, scanner.rs):
  - Create a temp directory with nested skill files in varying layouts.
  - Run the full binary with a few flags and assert output.
  - Compare against the bash 0001 implementation's output for the same inputs (regression).
- **Benchmarks** (optional but recommended):
  - Scan a large directory tree (10k+ files) and measure wall time + memory.
  - Compare against the bash version to document the speedup.

---

## 12. Implementation steps

1. Scaffold: `cargo init` + `clap`, `serde`, `serde_json`, `rayon` (or std threading), `anyhow`/`thiserror`.
2. Write `model.rs` + `parser.rs` (parser first — it's the hardest part).
3. Write `scanner.rs` + `filter_sort.rs`.
4. Write `presenter.rs` (JSON + table).
5. Wire in `main.rs`.
6. Add unit + integration tests.
7. Benchmark against the bash 0001 version.
8. Write usage examples and a README (copy from 0001, update for Rust).
9. Run `cargo build --release`; verify binary size and startup time.
10. Smoke-test all example commands from spec 0001.

---

## 13. Acceptance criteria

- [ ] `skillsmp <dir>` prints a table of skill names + descriptions.
- [ ] `skillsmp -f json <dir>` prints a valid JSON array.
- [ ] `skillsmp -f json --sort name --filter yaml <dir>` filters + sorts correctly.
- [ ] `skillsmp -n <dir>` prints only names (one per line).
- [ ] `skillsmp -i "*.skill.md" <dir>` includes the GCI pattern.
- [ ] `skillsmp -e "*.bak" <dir>` excludes the GCI pattern.
- [ ] `skillsmp --recursive --no-recursive` behave as documented.
- [ ] No files missing frontmatter are emitted in the output.
- [ ] Binary runs without external dependencies (bash, python, jq).
- [ ] Speedup vs bash version is measurable (scan a 10k-file tree).
- [ ] Exit status 0 on success; non-zero on CLI error.
- [ ] Output written to `--output <file>` matches stdout output.
