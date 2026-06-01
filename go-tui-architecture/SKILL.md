---
name: go-tui-architecture
description: >
  Scaffold a Go TUI application with clean architecture — Bubbletea + tview, config, persistence,
  plugin system, themes, and CI/CD. Use when starting a new Go TUI project, scaffolding a Bubbletea
  app, or creating a terminal UI with proper layered architecture. Trigger phrases: "scaffold a Go
  TUI app", "set up a Bubbletea project", "create a Go TUI", "bootstrap Go TUI project".
allowed-tools:
  - Write
  - Read
  - Bash(go:*)
  - Bash(mkdir:*)
  - Bash(git:*)
when_to_use: >
  Use when the user asks to scaffold a new Go TUI application, create a Bubbletea project from
  scratch, or set up a terminal-based app with clean architecture. Trigger phrases: "scaffold a Go
  TUI app", "set up a Bubbletea project", "create a Go TUI", "bootstrap Go TUI project". Use
  whenever someone wants a complete Go TUI project skeleton with MVC-style layered architecture,
  config management, persistence, plugin system, themes, and CI/CD.
argument-hint: "<module-path> [project-dir]"
arguments:
  - module_path (required): Go module path (e.g., github.com/user/project)
  - project_dir (optional): Output directory (defaults to module name)
context: inline
---

# Go TUI Application Scaffold

Scaffold a complete Go TUI application with clean layered architecture. Modeled after the
[tiki](https://github.com/boolean-maybe/tiki) project pattern — Bubbletea + tview rendering,
git-backed persistence, YAML plugin system, custom DSLs, theme/color system, and CI/CD.

## Inputs

- `$module_path` (required): Go module path, e.g. `github.com/user/project`
- `$project_dir` (optional): Output directory. Defaults to the last segment of `$module_path`.

## Goal

Generate a fully scaffolded Go TUI project directory with:

- Working `go build`, `go test`, and `golangci-lint` targets
- CLI dispatch (version, help, init, run TUI, exec)
- Layered architecture: model → store → service → plugin → controller → view → bootstrap
- Git-backed persistence with in-memory fallback
- Viper-based config, YAML workflow fields, theme/color system
- Bubbletea + tview view layer with gradient support and terminal detection
- Plugin system with YAML-defined views/actions
- GitHub Actions CI/CD, Dockerfile, GoReleaser, Makefile
- Development workflow: feature branches → PRs → merge commits

## Steps

### 1. Scaffold Project Structure

Create the directory layout, initialize the Go module, and set up build tooling.

**Execution**: Direct

**Artifacts**: Directory tree, `go.mod`, `Makefile`, `.golangci.yml`, `.goreleaser.yaml`

```
$project_dir/
├── main.go
├── main_test.go
├── go.mod
├── go.sum
├── Makefile
├── .golangci.yml
├── .goreleaser.yaml
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .github/
│   └── workflows/
│       ├── go.yml
│       └── release.yml
├── cmd_demo.go
├── cmd_demo_test.go
├── cmd_init.go
├── cmd_init_test.go
├── cmd_workflow.go
├── cmd_workflow_test.go
├── config/
│   ├── build.go
│   ├── paths.go
│   ├── paths_test.go
│   ├── init.go
│   ├── init_test.go
│   ├── loader.go
│   ├── loader_test.go
│   ├── system.go
│   ├── fields.go
│   ├── fields_test.go
│   ├── statuses.go
│   ├── statuses_test.go
│   ├── color.go
│   ├── colors.go
│   ├── color_test.go
│   ├── themes.go
│   ├── themes_test.go
│   ├── palettes.go
│   ├── palettes_test.go
│   ├── triggers.go
│   ├── triggers_test.go
│   ├── version.go
│   ├── install.go
│   ├── install_test.go
│   ├── reset.go
│   ├── reset_test.go
│   ├── workflows/
│   │   ├── todo.yaml
│   │   ├── kanban.yaml
│   │   └── bug-tracker.yaml
│   └── dimensions.go
├── model/
│   ├── view_id.go
│   ├── view_id_test.go
│   ├── view_params.go
│   ├── view_params_test.go
│   ├── view_context.go
│   ├── layout_model.go
│   ├── layout_model_test.go
│   ├── header_config.go
│   ├── header_config_test.go
│   ├── statusline_config.go
│   ├── edit_field.go
│   ├── edit_field_test.go
│   ├── plugin_config.go
│   ├── plugin_config_test.go
│   ├── action_palette_config.go
│   ├── quick_select_config.go
│   └── search_state.go
├── task/
│   ├── entities.go
│   ├── entities_test.go
│   ├── type.go
│   ├── type_test.go
│   ├── status.go
│   ├── status_test.go
│   ├── priority.go
│   ├── collections.go
│   ├── collections_test.go
│   ├── tags.go
│   ├── tags_test.go
│   ├── due.go
│   ├── due_test.go
│   ├── depends_on.go
│   ├── depends_on_test.go
│   ├── recurrence.go
│   ├── recurrence_test.go
│   └── validation.go
├── workflow/
│   ├── fields.go
│   ├── fields_test.go
│   ├── status.go
│   ├── status_test.go
│   ├── tasktype.go
│   └── tasktype_test.go
├── store/
│   ├── store.go
│   ├── read_store.go
│   ├── parser.go
│   ├── memory_store.go
│   ├── memory_store_test.go
│   ├── user_display.go
│   ├── user_display_test.go
│   ├── history.go
│   └── tikistore/
│       ├── store.go
│       ├── store_test.go
│       ├── crud.go
│       ├── persistence.go
│       ├── paths.go
│       ├── identity.go
│       ├── identity_test.go
│       ├── query.go
│       ├── template.go
│       ├── template_test.go
│       ├── git.go
│       ├── listeners.go
│       ├── legacy_upgrader.go
│       └── internal/git/
│           ├── types.go
│           ├── repo.go
│           └── ops.go
├── service/
│   ├── build.go
│   ├── task_mutation_gate.go
│   ├── task_mutation_gate_test.go
│   ├── validators.go
│   ├── validators_test.go
│   ├── trigger_engine.go
│   ├── trigger_engine_test.go
│   ├── clipboard.go
│   ├── clipboard_test.go
│   └── shell.go
├── plugin/
│   ├── definition.go
│   ├── parser.go
│   ├── parser_test.go
│   ├── loader.go
│   ├── loader_test.go
│   ├── colorparser.go
│   ├── colorparser_test.go
│   ├── keyparser.go
│   ├── keyparser_test.go
│   ├── legacy_convert.go
│   └── integration_test.go
├── controller/
│   ├── interfaces.go
│   ├── input_router.go
│   ├── input_router_test.go
│   ├── actions.go
│   ├── actions_test.go
│   ├── navigation.go
│   ├── view_stack.go
│   ├── deps.go
│   ├── deps_test.go
│   ├── plugin.go
│   ├── plugin_base.go
│   ├── plugin_executor.go
│   ├── plugin_selection_test.go
│   ├── task_detail.go
│   ├── task_detail_test.go
│   ├── task_edit_coordinator.go
│   ├── task_edit_coordinator_test.go
│   ├── agent.go
│   ├── agent_test.go
│   ├── util.go
│   └── testing.go
├── view/
│   ├── factory.go
│   ├── root_layout.go
│   ├── tiki_plugin_view.go
│   ├── tiki_plugin_view_test.go
│   ├── input_box.go
│   ├── input_helper.go
│   ├── tiki_box.go
│   ├── tiki_box_test.go
│   ├── gradient_caption_row.go
│   ├── scrollable_list.go
│   ├── header/
│   │   ├── header.go
│   │   ├── header_layout.go
│   │   ├── header_layout_test.go
│   │   ├── info.go
│   │   ├── context_help.go
│   │   ├── chart.go
│   │   ├── action_converter.go
│   │   └── color_scheme.go
│   ├── statusline/
│   │   ├── statusline.go
│   │   └── statusline_test.go
│   ├── palette/
│   │   ├── action_palette.go
│   │   ├── quick_select.go
│   │   └── fuzzy.go
│   ├── tikidetail/
│   │   ├── base.go
│   │   ├── configurable_detail_view.go
│   │   ├── configurable_detail_edit_test.go
│   │   ├── tiki_edit_view.go
│   │   ├── tiki_edit_nav.go
│   │   ├── tiki_edit_fields.go
│   │   ├── content_provider.go
│   │   ├── render_helpers.go
│   │   ├── metadata_layout.go
│   │   ├── grid_container.go
│   │   ├── grid_helpers.go
│   │   └── field_registry.go
│   └── markdown/
│       ├── navigable_markdown.go
│       └── wikilink.go
├── internal/
│   ├── bootstrap/
│   │   ├── config.go
│   │   ├── init.go
│   │   ├── controllers.go
│   │   ├── plugins.go
│   │   ├── stores.go
│   │   ├── models.go
│   │   ├── project.go
│   │   ├── git.go
│   │   └── logging.go
│   ├── app/
│   │   └── app.go
│   ├── pipe/
│   │   └── create.go
│   ├── ruki/
│   │   └── runtime/
│   │       ├── runner.go
│   │       ├── schema.go
│   │       └── format.go
│   ├── viewer/
│   │   └── markdown_viewer.go
│   ├── repair/
│   │   └── ids.go
│   ├── background/
│   │   └── burndown.go
│   └── teststatuses/
│       └── teststatuses.go
├── testutil/
│   ├── fixtures.go
│   └── integration_helpers.go
├── integration/
│   ├── view_action_test.go
│   ├── tiki_edit_test.go
│   ├── tiki_detail_view_test.go
│   └── plugin_navigation_test.go
└── util/
    └── terminal.go
```

**Rules**:
- Go 1.25+ (use latest stable)
- Module path must be valid (e.g., `github.com/user/project`)
- All packages in `internal/` are private; everything else is importable

**Success criteria**: `mkdir -p` creates all directories, `go mod init $module_path` succeeds, `go build` compiles with zero errors.

---

### 2. Build CLI Dispatch

Create `main.go` with subcommand handling: `--version`, `--help`, `init`, `demo`, `exec`, `workflow`, piped input, viewer mode, and default TUI launch.

**Execution**: Direct

**Key libraries**: `github.com/spf13/pflag` for flag parsing

**Pattern**:
- Version/info flags exit early
- `init` and `demo` run before path initialization (they may `os.Chdir`)
- `exec` runs after path init but uses CLI-only output (table/json)
- Piped input creates a task and exits
- Viewer mode handles `tiki file.md`
- Default path: bootstrap → app.Run()

**Success criteria**: `go build` succeeds. Running `./tiki --help` prints usage. Running `./tiki --version` prints version info.

---

### 3. Implement Config System

Viper-based configuration loader with paths, workflow fields, statuses, types, themes, colors, palettes, triggers, and color/gradient support.

**Execution**: Direct

**Key libraries**: `github.com/spf13/viper`, `gopkg.in/yaml.v3`

**Sub-steps**:
1. `config/build.go` — Version, GitCommit, BuildDate ldflag injection
2. `config/paths.go` — XDG config/data/cache dirs, project init detection
3. `config/init.go` — Project initialization, default workflow installation
4. `config/loader.go` — Viper-based config loading with YAML
5. `config/system.go` — Store name, git enabled, workflow path management
6. `config/fields.go` — Workflow field definitions (statuses, types, priorities)
7. `config/color.go` + `colors.go` — Theme color role system, gradient flags
8. `config/themes.go` — Theme loading, light/dark detection
9. `config/palettes.go` — Color palette definitions
10. `config/triggers.go` — Trigger registration from config
11. `config/workflows/*.yaml` — Bundled workflow definitions

**Artifacts**: All config loading functions, default workflow YAML files, theme/color infrastructure

**Success criteria**: `config.InitPaths()` returns without error, `config.LoadConfig()` reads a config file, color roles resolve correctly.

---

### 4. Build Model Layer

Define the data structures that the application operates on — both domain models and configuration models.

**Execution**: Direct

**Sub-steps**:
1. `task/entities.go` — Core `Task` struct (ID, Title, Status, Type, Priority, fields map, comments, etc.)
2. `task/type.go`, `task/status.go`, `task/priority.go` — Enum-like type wrappers with validation
3. `task/collections.go` — Task collection utilities (filtering, sorting, grouping)
4. `task/tags.go`, `task/due.go`, `task/depends_on.go`, `task/recurrence.go` — Rich field types
5. `workflow/fields.go`, `workflow/status.go`, `workflow/tasktype.go` — Workflow-level registries
6. `model/view_id.go`, `model/view_params.go` — View identification and parameter passing
7. `model/view_context.go` — Active view context for palette and navigation
8. `model/layout_model.go` — Which view is shown in which layout slot
9. `model/header_config.go`, `model/statusline_config.go` — Header/statusline state models
10. `model/plugin_config.go` — Per-plugin configuration model
11. `model/edit_field.go` — Edit field model with validation state
12. `model/action_palette_config.go`, `model/quick_select_config.go` — Palette state models
13. `model/search_state.go` — Search/filter state

**Artifacts**: Domain types, view models, config models

**Success criteria**: All model types compile, tests pass for rich field types (tags, dates, dependencies, recurrence).

---

### 5. Implement Store Layer

Data persistence with `Store` interface, in-memory implementation, and git-backed store.

**Execution**: Direct

**Key libraries**: `github.com/go-git/go-git/v5`

**Sub-steps**:
1. `store/store.go` — `Store` interface (CRUD + ChangeListener)
2. `store/read_store.go` — Read-only query interface (GetByID, GetAll, filtering)
3. `store/parser.go` — Path parsing for task files
4. `store/memory_store.go` — In-memory store for testing
5. `store/user_display.go` — User display name resolution
6. `store/history.go` — Task history tracking
7. `store/tikistore/store.go` — Git-backed store implementation
8. `store/tikistore/crud.go` — Create/Read/Update/Delete operations
9. `store/tikistore/persistence.go` — File I/O with locking and atomic writes
10. `store/tikistore/paths.go` — File path conventions
11. `store/tikistore/identity.go` — ID generation (nanoid) and gap detection
12. `store/tikistore/query.go` — Query building and filtering
13. `store/tikistore/template.go` — Template-based task creation
14. `store/tikistore/git.go` — Git operations (add, commit, diff)
15. `store/tikistore/listeners.go` — Change listener management
16. `store/internal/git/` — Low-level git operation wrappers

**Rules**:
- Store must be thread-safe
- Git backend auto-commits on mutation
- In-memory store must satisfy same interface for testing

**Success criteria**: `store.Store` interface compiles, CRUD round-trips work, git store creates commits on write.

---

### 6. Build Service Layer

Business rules layer sitting between controllers and store — mutation gate, validators, trigger engine.

**Execution**: Direct

**Sub-steps**:
1. `service/build.go` — Factory that builds a fully configured mutation gate
2. `service/task_mutation_gate.go` — Validation gate that checks field constraints before write
3. `service/validators.go` — Individual field validators (status transitions, required fields, etc.)
4. `service/trigger_engine.go` — Event-driven trigger system (on create, on update, timed)
5. `service/clipboard.go` — Clipboard integration
6. `service/shell.go` — Shell command execution

**Artifacts**: Gate + validators + trigger engine + utilities

**Success criteria**: Mutation gate rejects invalid state transitions, trigger engine fires on mutations, validators compose.

---

### 7. Implement Plugin System

Plugin system that loads YAML-defined views and actions, providing extensibility without recompilation.

**Execution**: Direct

**Key libraries**: `github.com/alecthomas/participle/v2` (for plugin DSL parsing)

**Sub-steps**:
1. `plugin/definition.go` — Plugin interface and struct definitions
2. `plugin/parser.go` — YAML plugin definition parser with participle DSL
3. `plugin/loader.go` — Plugin loading from config, builtin registration
4. `plugin/colorparser.go` — Color value parsing in plugin configs
5. `plugin/keyparser.go` — Key binding parsing
6. `plugin/legacy_convert.go` — Backward compatibility converters

**Artifacts**: Plugin loader, definition types, DSL grammar

**Success criteria**: YAML plugin definitions parse correctly, plugins are discoverable and loadable.

---

### 8. Build Controller Layer

Input routing, navigation, action system, and view controllers that mediate between views and services.

**Execution**: Direct

**Sub-steps**:
1. `controller/interfaces.go` — Controller interfaces (`View`, `FocusSettable`, `FocusRestorer`)
2. `controller/input_router.go` — Routes keyboard input to the right handler
3. `controller/navigation.go` — Navigation controller (push/pop/replace views)
4. `controller/view_stack.go` — View stack for navigation history
5. `controller/actions.go` — Action definitions and execution
6. `controller/plugin.go` — Plugin controller (forwards actions to plugin views)
7. `controller/plugin_base.go` — Base controller with common plugin wiring
8. `controller/plugin_executor.go` — Plugin action executor
9. `controller/task_detail.go` — Detail view controller (view/edit modes)
10. `controller/task_edit_coordinator.go` — Multi-step edit session management
11. `controller/deps.go` — Dependencies editor controller
12. `controller/agent.go` — AI agent integration controller

**Artifacts**: All controller implementations and their tests

**Success criteria**: Input routing works, navigation stack pushes/pops correctly, actions wire to controllers.

---

### 9. Build View Layer

Bubbletea + tview rendering layer — layouts, components, detail views, header, statusline, palette.

**Execution**: Direct

**Key libraries**: `github.com/rivo/tview`, `github.com/gdamore/tcell/v2`, `github.com/charmbracelet/lipgloss`, `github.com/charmbracelet/bubbles`, `github.com/alecthomas/chroma/v2`, `github.com/yuin/goldmark`

**Sub-steps**:
1. `view/factory.go` — View factory that creates views by type/name
2. `view/root_layout.go` — Root layout with header/content/statusline regions
3. `view/tiki_box.go` — Reusable flexbox container with layout DSL support
4. `view/tiki_plugin_view.go` — Plugin-rendered view container
5. `view/gradient_caption_row.go` — Caption row with gradient support
6. `view/scrollable_list.go` — Scrollable list component
7. `view/header/` — Header widget (stats, info, context help, chart)
8. `view/statusline/` — Status line widget
9. `view/palette/` — Action palette and quick select overlays with fuzzy matching
10. `view/tikidetail/` — Task detail/edit views with grid layout
11. `view/markdown/` — Navigable markdown viewer with syntax highlighting

**Rules**:
- Use tview for Application/Flex/Layout primitives
- Use Lipgloss for inline styling
- Use tcell for direct screen access (palette overlays)
- Theme colors via config color roles, not hardcoded

**Success criteria**: All view components render, header shows stats, palette opens/closes, detail view shows task data.

---

### 10. Wire Bootstrap

Phased initialization that connects all layers. This is the application's composition root.

**Execution**: Direct

**Key pattern**: 13-phase bootstrap with clear ordering

**Phases**:
0. Config + logging
0.5. Validate store backend
1. Git pre-flight check
2. Project initialization (seed files)
2.5. Install default workflow
2.7. Load workflow registries
2.8. Resolve workflow file location
3.5. System info + gradient support
3.7. Mutation gate
4. Store initialization
5. Model initialization
5.5. Ruki schema
6. Plugin system
6.5. Trigger system
7. Application + controllers
8. Input routing
9. View factory + layout wiring
10. View activation wiring
11. Background tasks
11.5. Action palette
11.6. Quick select
12. Navigation + input wiring
13. Initial view push

**Artifacts**: `internal/bootstrap/init.go` with `Bootstrap()` returning a fully wired `Result` struct

**Success criteria**: `Bootstrap()` returns without error, all components are wired, initial view is shown.

---

### 11. Add CI/CD Pipeline

GitHub Actions for testing/linting/building across platforms, Docker support, and GoReleaser for releases.

**Execution**: Direct

**Sub-steps**:
1. `.github/workflows/go.yml` — CI: test (3 OS × Go 1.25), lint (golangci-lint), build, mod tidy check, coverage upload
2. `.github/workflows/release.yml` — CD: goreleaser on tag push
3. `Dockerfile` — Multi-stage Docker build
4. `.dockerignore` — Docker build context exclusions
5. `.goreleaser.yaml` — GoReleaser config (builds, archives, checksums, Homebrew tap)

**Artifacts**: CI/CD pipeline files

**Success criteria**: GitHub Actions YAML is valid, GoReleaser config validates, Dockerfile builds.

---

## Post-Scaffold

After all steps complete successfully:

1. Run `cd $project_dir && go mod tidy` to resolve all dependencies
2. Run `go build ./...` to verify compilation
3. Run `go test ./...` to verify all tests pass
4. Run `golangci-lint run` to verify lint passes
5. Run `goreleaser check` to verify release config
6. Initialize git: `git init && git add -A && git commit -m "Initial scaffold: Go TUI application"`

The scaffolded project is ready for development. Use the same workflow that built it:
feature branches → PRs → merge commits with the convention:
- `feature/<name>` for new features
- `fix/<name>` for bug fixes
- Merge via PR with squash or merge commit

## Gotchas

- **Terminal color detection**: Handle TERM env variable, 256-color vs truecolor detection, and gradient fallback for limited terminals. Auto-correct TERM=xterm-256color when colors < 256.
- **Module path substitution**: When reusing the scaffold for a different project, replace ALL occurrences of the old module path — go.mod, imports, and embedded strings. Use `find . -name '*.go' -exec sed -i 's|old/path|new/path|g' {} +` to be thorough.
- **Cross-platform test quirks**: tcell behavior differs on macOS/Linux/Windows. Watch for tty-dependent tests and use the in-memory store for unit tests instead of git-backed.
- **Dependency version bumps**: Bubbletea, Bubbles, and Lipgloss APIs change frequently. Pin to known-good versions in go.mod and test after upgrades.
- **Test isolation**: Use the in-memory store in tests, not the git store. Create test helpers (`testutil/fixtures.go`, `testutil/integration_helpers.go`) with reusable test data factories.
