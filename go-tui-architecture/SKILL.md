---
name: go-tui-architecture
description: >
  Scaffold a Go TUI application with clean layered architecture — Bubbletea + tview, config,
  persistence, plugin system, themes, and CI/CD. Use when starting a new Go TUI project, scaffolding
  a Bubbletea app, or creating a terminal UI with separation of concerns.
allowed-tools:
  - Write
  - Read
  - Bash(go:*)
  - Bash(mkdir:*)
  - Bash(git:*)
when_to_use: >
  Use when the user asks to scaffold a new Go TUI application, create a Bubbletea project from
  scratch, or set up a terminal-based app with clean architecture. Trigger phrases: "scaffold a Go
  TUI app", "set up a Bubbletea project", "create a Go TUI", "bootstrap Go TUI project".
argument-hint: "<module-path> [project-dir]"
arguments:
  - module_path (required): Go module path (e.g., github.com/user/project)
  - project_dir (optional): Output directory (defaults to module name)
context: inline
---

# Go TUI Application Scaffold

Scaffold a complete Go TUI application with clean layered architecture — config, model, store,
service, controller, view, and bootstrap wiring. Not prescriptive about the domain: adapt the
directory names and entity types to fit your problem.

## Inputs

- `$module_path` (required): Go module path, e.g. `github.com/user/project`
- `$project_dir` (optional): Output directory. Defaults to the last segment of `$module_path`.

## Goal

Generate a fully scaffolded Go TUI project directory with:

- Working `go build`, `go test`, and `golangci-lint` targets
- CLI dispatch (version, help, init, run TUI, exec)
- Layered architecture with clean separation of concerns
- Store/persistence abstraction (in-memory + file-backed)
- Viper-based config with YAML, theme/color system
- Bubbletea + tview view layer with terminal detection
- Extensibility via plugin system or configuration
- GitHub Actions CI/CD, Dockerfile, GoReleaser, Makefile
- Development workflow: feature branches → PRs → merge commits

## Steps

### 1. Define the Domain

Before writing code, name the domain entity the TUI manages. This determines package names
throughout the scaffold. For example, a task tracker uses `task/`, a note app uses `note/`,
a server dashboard uses `server/` or `service/`.

**Execution**: Direct

**Decision**: Choose a domain name (e.g., `entity` as a placeholder). All subsequent steps
use `$domain` for this name — substitute it when creating directories and files.

**Success criteria**: A clear domain name is chosen. Every `$domain` reference below is
replaced consistently.

After you choose the domain, also decide which optional features the app needs:

| Layer | Capability | When to include |
|-------|-----------|-----------------|
| Store | Git-backed persistence | Data needs version history |
| Store | File-backed persistence | Simple CRUD without git |
| View | Markdown viewer | App shows formatted documents |
| View | Action palette / fuzzy search | Keyboard-driven navigation |
| Service | Trigger/event system | Mutations need side-effects |
| Service | AI agent integration | LLM-powered features |
| Plugin | YAML-defined views/actions | User-extensible UI |
| Plugin | Custom DSL parser | Domain-specific query language |

---

### 2. Scaffold Project Structure

Create the directory layout, initialize the Go module, and set up build tooling.

**Execution**: Direct

**Artifacts**: Directory tree, `go.mod`, `Makefile`, `.golangci.yml`, `.goreleaser.yaml`

**Layout by layer** — each directory is a self-contained Go package:

```
$project_dir/
├── main.go                          # Entry point, CLI dispatch
├── main_test.go
├── go.mod
├── Makefile
├── .golangci.yml
├── .goreleaser.yaml
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .github/workflows/
│   ├── ci.yml                       # Test + lint + build + coverage
│   └── release.yml                  # GoReleaser on tag
│
├── config/                          # Configuration subsystem
│   ├── build.go                     # Version ldflags
│   ├── paths.go                     # XDG dirs, project detection
│   ├── loader.go                    # Viper config bootstrap
│   ├── system.go                    # Store type, feature flags
│   ├── colors.go                    # Color role definitions
│   ├── themes.go                    # Theme loading, light/dark
│   └── ...
│
├── model/                           # UI state models
│   ├── view_id.go                   # View identification
│   ├── layout_model.go              # Screen layout state
│   ├── header_config.go             # Header/statusline state
│   ├── edit_field.go                # Field editing state
│   └── ...
│
├── $domain/                         # Domain types (rename to your domain)
│   ├── entity.go                    # Core struct
│   ├── type.go                      # Enum-like wrappers
│   └── validation.go                # Business validation
│
├── store/                           # Persistence abstraction
│   ├── store.go                     # Store interface
│   ├── memory_store.go              # In-memory impl (testing)
│   └── filestore/                   # File-backed impl
│       ├── store.go
│       ├── crud.go
│       └── persistence.go
│
├── service/                         # Business rules
│   ├── mutation_gate.go             # Validation before write
│   ├── validators.go                # Field constraints
│   └── trigger_engine.go            # Event system (optional)
│
├── controller/                      # Input handling + navigation
│   ├── interfaces.go                # View/Focus interfaces
│   ├── input_router.go              # Keyboard dispatch
│   ├── navigation.go                # View stack
│   ├── actions.go                   # Action registry
│   └── ...
│
├── view/                            # TUI rendering
│   ├── factory.go                   # View construction
│   ├── root_layout.go               # Screen regions
│   ├── list_view.go                 # List component
│   ├── detail_view.go               # Detail/edit view
│   ├── header/                      # Top bar
│   ├── statusline/                  # Bottom bar
│   └── palette/                     # Command palette (optional)
│
├── plugin/                          # Extensibility (optional)
│   ├── definition.go                # Plugin interface
│   ├── loader.go                    # Plugin discovery
│   └── parser.go                    # Config parsing
│
├── internal/                        # Private implementation
│   ├── bootstrap/
│   │   ├── config.go                # Config loading
│   │   ├── init.go                  # Application bootstrap
│   │   ├── controllers.go           # Wiring controllers
│   │   ├── stores.go                # Store init
│   │   └── logging.go               # Log setup
│   ├── app/
│   │   └── app.go                   # tview.Application wrapper
│   └── pipe/
│       └── create.go                # Piped input handler
│
├── testutil/                        # Shared test helpers
│   ├── fixtures.go
│   └── integration_helpers.go
│
├── integration/                     # End-to-end tests
│   └── navigation_test.go
│
└── util/
    └── terminal.go                  # Terminal detection
```

**Rules**:
- Go 1.25+ (use latest stable)
- Module path must be valid (e.g., `github.com/user/project`)
- Packages in `internal/` are private; everything else is importable
- Replace `$domain` with your actual domain name everywhere

**Success criteria**: `mkdir -p` creates all directories, `go mod init $module_path` succeeds,
`go build` compiles with zero errors.

---

### 3. Build CLI Dispatch

Create `main.go` with subcommand handling that gates the TUI launch behind setup commands.

**Execution**: Direct

**Key libraries**: `github.com/spf13/pflag` for flag parsing

**Pattern** below uses `$name` for the binary name (module basename). Adapt to your needs.

```
func main() {
    // Version/help flags exit early
    // 'init' subcommand runs before path initialization
    // 'exec' runs after path init, CLI-only output
    // Piped stdin creates an entity and exits
    // Default path: bootstrap → app.Run()
}
```

**Typical subcommands**:
- `--version`, `--help` — print and exit
- `init [dir]` — initialize project directory
- `demo` — extract demo data and launch
- `exec '<query>'` — CLI query/command mode
- `tui` (default) — launch the TUI
- Piped input (`echo "foo" | $name`) — quick-create an entity

**Success criteria**: `go build` succeeds. Running `./$name --help` prints usage.
Running `./$name --version` prints version info.

---

### 4. Implement Config System

Viper-based configuration loader handling app config, theme/colors, and any domain-specific settings.

**Execution**: Direct

**Key libraries**: `github.com/spf13/viper`, `gopkg.in/yaml.v3`

**Sub-steps**:
1. `config/build.go` — Version, GitCommit, BuildDate injected via `-ldflags`
2. `config/paths.go` — XDG config/data/cache directory resolution, project detection
3. `config/loader.go` — Viper bootstrap: search paths, config name, env overrides
4. `config/system.go` — Store backend selection, feature flags
5. `config/colors.go` — Color role system (primary, secondary, accent, surface, text, border, etc.)
6. `config/themes.go` — Theme loading, light/dark mode detection, user theme overrides

**Artifacts**: Config loader, path manager, color/theme system

**Success criteria**: `config.LoadConfig()` reads a YAML config file, color roles resolve
correctly for both light and dark themes.

---

### 5. Build Domain Model and State Models

Define the domain types and UI state models. This is split into two packages:
- `$domain/` — your business entities, validation, and field types
- `model/` — UI state (which view is active, edit state, header state)

**Execution**: Direct

**Sub-steps for `$domain/`:**
1. `entity.go` — Core struct with ID, metadata, and a generic fields map or typed fields
2. Validator functions for business rules
3. Any enum-like type wrappers with validation

**Sub-steps for `model/`:**
1. `view_id.go` — View identification (typed ID with params)
2. `layout_model.go` — Which view occupies which screen region
3. `header_config.go` — Header state (stat values, filtering)
4. `edit_field.go` — Field editing state (cursor, validation errors)

**Artifacts**: Domain types, UI state models

**Success criteria**: All types compile, entity validation works, model state transitions are correct.

---

### 6. Implement Store Layer

Data persistence with a `Store` interface so controllers and views never depend on the
storage backend.

**Execution**: Direct

**Key libraries**: `github.com/go-git/go-git/v5` (if git-backed)

**Sub-steps**:
1. `store/store.go` — `Store` interface (Create/Read/Update/Delete + ChangeListener)
2. `store/read_store.go` — Read-only query interface (GetByID, GetAll, filtering, sorting)
3. `store/memory_store.go` — Thread-safe in-memory implementation for tests
4. `store/filestore/store.go` — File-backed implementation (plain files or git repo)

**Store interface pattern**:
```go
type Store interface {
    ReadStore
    Create(entity *domain.Entity) error
    Update(entity *domain.Entity) error
    Delete(id string)
}

type ReadStore interface {
    GetByID(id string) (*domain.Entity, bool)
    GetAll() []*domain.Entity
    // Filter, sort, count as needed
}
```

**Artifacts**: Store interface + in-memory + file/git implementations

**Success criteria**: `Store` interface compiles, CRUD round-trips work with both backends,
in-memory store is usable in unit tests without setup.

---

### 7. Build Service Layer (Optional)

Business rules layer between controllers and store — gate, validators, event system.

**Execution**: Direct

**Sub-steps**:
1. `service/mutation_gate.go` — Middleware that intercepts writes, runs validators
2. `service/validators.go` — Composable validation functions
3. `service/trigger_engine.go` — Event-driven side-effects (on create, on update, timed)

**Rules**:
- Gate is optional — skip if the domain has simple validation
- Trigger engine is optional — include only if mutations need side-effects
- Both depend only on the `Store` interface, not on concrete implementations

**Success criteria**: Gate rejects invalid mutations, validators compose, triggers fire.

---

### 8. Add Extensibility (Optional)

Plugin system for user-defined views/actions, or a custom DSL for querying/scripting.

**Execution**: Direct

**Key libraries**: `github.com/alecthomas/participle/v2` (if building a DSL parser)

**Plugin system sub-steps**:
1. `plugin/definition.go` — Plugin interface and configuration types
2. `plugin/loader.go` — Plugin discovery from config files
3. `plugin/parser.go` — YAML definition parser

**Custom DSL sub-steps** (if applicable):
1. Define grammar with participle
2. Build AST types
3. Write evaluator/interpreter
4. Implement runtime with access to the Store

**Artifacts**: Plugin loader or DSL parser + runtime

**Success criteria**: YAML plugin definitions parse, plugins are loadable and executable
(or DSL statements parse and evaluate against the store).

---

### 9. Build Controller Layer

Input routing, navigation stack, and view controllers that mediate between views and services.

**Execution**: Direct

**Sub-steps**:
1. `controller/interfaces.go` — View interface (render, focus, input handling)
2. `controller/navigation.go` — Navigation controller (push/pop/replace views)
3. `controller/input_router.go` — Routes keyboard input to active controller
4. `controller/actions.go` — Action registry with keybindings
5. `controller/view_controller.go` — Per-view controller (one per view type)
6. `controller/edit_coordinator.go` — Multi-step form/edit session management (optional)

**Controller pattern**:
- Each view type has a corresponding controller
- Controllers receive input events and delegate to service/store
- Navigation controller manages view stack and history
- Input router dispatches global keybindings (Ctrl+P, Ctrl+Q, etc.)

**Success criteria**: Navigation pushes/pops views correctly, input routing dispatches
to the right controller, actions wire end-to-end.

---

### 10. Build View Layer

Bubbletea + tview rendering — layouts, reusable components, header, statusline.

**Execution**: Direct

**Key libraries**: `github.com/rivo/tview`, `github.com/gdamore/tcell/v2`,
`github.com/charmbracelet/lipgloss`, `github.com/charmbracelet/bubbles`

**Sub-steps**:
1. `view/factory.go` — Constructs view primitives from view config
2. `view/root_layout.go` — Flex layout: header / content / statusline
3. `view/list_view.go` — Scrollable list of entities with selection
4. `view/detail_view.go` — Entity detail and inline edit
5. `view/input_box.go` — Reusable text input
6. `view/header/` — Top bar (stats, info, chart)
7. `view/statusline/` — Bottom bar (keybinding hints, mode indicator)
8. `view/palette/` — Command palette overlay with fuzzy matching (optional)

**Rules**:
- Use `tview` for Application, Flex, Pages primitives
- Use Lipgloss for inline styling (colors, borders, alignment)
- Use tcell for direct screen access (overlays, popups)
- Theme colors via config color roles, not hardcoded values
- Wrap tview primitives in your own types so views don't import tview directly

**Success criteria**: All view components render, header shows live stats, palette
opens/closes, detail view shows entity data.

---

### 11. Wire Bootstrap

Phased initialization that connects all layers.

**Execution**: Direct

**Phases** (order matters — each depends on previous):
1. Config loading + logging setup
2. Theme/color initialization + terminal detection
3. Store initialization (config tells which backend)
4. Service layer (gate + validators)
5. Model instantiation
6. Plugin loading (if applicable)
7. Controller wiring
8. View factory + layout construction
9. Input routing + navigation
10. Initial view push

**Artifacts**: `internal/bootstrap/init.go` with a `Bootstrap()` function returning a
wired `Result` struct containing all components.

```go
type Result struct {
    Config      *config.Config
    Store       store.Store
    App         *tview.Application
    Navigation  *controller.NavigationController
    RootLayout  *view.RootLayout
    // ... other wired components
}
```

**Success criteria**: `Bootstrap()` returns without error, all components are wired,
initial view is shown.

---

### 12. Add CI/CD Pipeline

GitHub Actions, Docker, GoReleaser.

**Execution**: Direct

**Sub-steps**:
1. `.github/workflows/ci.yml` — Test (3 OS × Go latest), lint (golangci-lint), build,
   mod tidy check, coverage upload
2. `.github/workflows/release.yml` — GoReleaser on version tag push
3. `Dockerfile` — Multi-stage build (build → scratch or distroless)
4. `.goreleaser.yaml` — Builds, archives, checksums, Homebrew tap

**Success criteria**: CI YAML is valid, GoReleaser config validates, Dockerfile builds.

---

## Post-Scaffold

After all steps complete:

1. `cd $project_dir && go mod tidy` — resolve all dependencies
2. `go build ./...` — verify compilation
3. `go test ./...` — verify all tests pass
4. `golangci-lint run` — verify lint passes
5. `goreleaser check` — verify release config
6. `git init && git add -A && git commit -m "Initial scaffold: Go TUI application"`

The scaffolded project is ready for domain-specific development. Use:
- `feature/<name>` branches for features
- `fix/<name>` branches for bug fixes
- Merge via PRs with squash or merge commits

## Gotchas

- **Module path substitution**: When reusing the scaffold for a different project, replace
  ALL occurrences of the old module path — go.mod, imports, and embedded strings.
  Use `find . -name '*.go' -exec sed -i 's|old/path|new/path|g' {} +`.
- **Terminal color detection**: Handle `TERM` env variable, detect 256-color vs truecolor,
  provide gradient fallback for limited terminals. Auto-correct `TERM=xterm-256color`
  when detected colors < 256.
- **tview + Bubbletea coexistence**: Use tview for the application shell (layout, focus,
  pages) and Bubbletea/Bubbles components inside tview primitives via `tview.Embed`.
  Don't mix two event loops.
- **Cross-platform test quirks**: tcell behavior differs on macOS/Linux/Windows. Use the
  in-memory store for unit tests. Keep integration tests behind build tags.
- **Dependency version bumps**: Bubbletea, Bubbles, and Lipgloss APIs change frequently.
  Pin versions in `go.mod` and test after upgrades.
- **Test helpers**: Create `testutil/fixtures.go` with reusable test data factories and
  `testutil/integration_helpers.go` with a test app bootstrap to avoid duplicating setup
  across test files.
