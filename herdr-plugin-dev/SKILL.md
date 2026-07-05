---
name: herdr-plugin-dev
description: >-
  Develop, modify, test, and publish Herdr plugins from scratch. Use this skill whenever the user
  wants to create a new Herdr plugin, add actions/events/panes/link handlers to an existing plugin,
  understand or write a herdr-plugin.toml manifest, build or test a plugin with `herdr plugin link`,
  debug plugin logs, troubleshoot plugin env vars or HERDR_BIN_PATH issues, learn how plugins call
  back into Herdr via the CLI or socket, or publish a plugin to the Herdr marketplace. Also use
  when asked about herdr-plugin.toml fields, plugin directory structure, plugin build commands,
  [[actions]]/[[events]]/[[panes]]/[[link_handlers]] manifest sections, or the HERDR_PLUGIN_*
  environment variables. Do NOT use this skill for general Herdr usage questions — that's the
  Herdr docs domain.
license: MIT
metadata:
  herdr_min_version: "0.7.0"
  herdr_docs_url: https://herdr.dev/docs/plugins/
  herdr_marketplace_url: https://herdr.dev/plugins/
---

# Herdr Plugin Development

A comprehensive guide to creating, testing, and publishing plugins for Herdr. Herdr plugins are
shareable, executable workflow packages — a directory with a `herdr-plugin.toml` manifest and
commands Herdr can launch. **No SDK is required.** The entire Herdr CLI is the plugin API.

Plugins exist so Herdr stays lean. The core focuses on terminal workspaces, panes, agents, and a
stable CLI/socket API. Plugins turn that extension surface into reusable workflows.

---

## Quick Start — The Minimal Plugin

A plugin is a directory with two files:

```
my-plugin/
├── herdr-plugin.toml      # manifest (required)
└── index.js               # your executable (any language)
```

**herdr-plugin.toml:**

```toml
id = "my-org.my-plugin"
name = "My Plugin"
version = "0.1.0"
min_herdr_version = "0.7.0"
description = "What it does"
platforms = ["linux", "macos", "windows"]

[[actions]]
id = "hello"
title = "Say hello"
command = ["node", "index.js"]
```

**index.js:**

```javascript
const { spawnSync } = require("node:child_process");
const herdr = process.env.HERDR_BIN_PATH ?? "herdr";
spawnSync(herdr, ["workspace", "list"], { encoding: "utf8", stdio: "inherit" });
```

**Link and test:**

```bash
herdr plugin link /path/to/my-plugin
herdr plugin action invoke my-org.my-plugin.hello
herdr plugin log list --plugin my-org.my-plugin
```

---

## The Manifest (`herdr-plugin.toml`)

The manifest is the contract between Herdr and the plugin. Herdr validates it, injects runtime
context, starts declared commands, and records logs.

### Top-level fields

```toml
id = "my-org.my-plugin"       # Required. Dotted kebab-case. Max 64 chars.
name = "My Plugin"            # Required. Human-readable.
version = "0.1.0"             # Required. Semantic version.
min_herdr_version = "0.7.0"   # Required. Oldest Herdr that supports your plugin's APIs.
description = "..."           # Optional. Shown in plugin list.
platforms = ["linux", "macos", "windows"]  # Optional. Item-level overrides exist.
```

**Plugin IDs** use ASCII letters, digits, dot, colon, underscore, and hyphen.  
**Local IDs** (action ids, pane ids, link handler ids) use the same chars **but not dots**.
Each local id type must be unique inside a plugin. Herdr qualifies action IDs as
`plugin-id.action-id` when it needs a globally unique name.

**`min_herdr_version`** is critical: Herdr refuses to link/install a plugin when its min version
is newer than the current binary. Set it to the oldest version that supports the APIs, event names,
and manifest fields your plugin uses.

### Platform overrides

`platforms` at the top level provides defaults. Every item type (build, action, event, pane, link
handler) can declare its own `platforms` to override:

```toml
platforms = ["linux", "macos"]

[[build]]
command = ["npm", "ci"]

[[build]]
command = ["npm", "run", "build:win"]
platforms = ["windows"]
```

### [[build]] — Build commands

Run during `herdr plugin install` after confirmation, before registration. If a build fails,
install aborts. `herdr plugin link` does **not** run builds — local authors build
manually.

```toml
[[build]]
command = ["npm", "ci"]

[[build]]
command = ["cargo", "build", "--release"]
platforms = ["linux", "macos"]
```

**Gotchas:**

- Build commands do NOT receive runtime plugin context env vars (no `HERDR_SOCKET_PATH`, etc.)
- Changing `herdr-plugin.toml` during a build aborts install
- Herdr does not install missing toolchains — document requirements
- Build commands are plain argv arrays — no shell expansion

### [[actions]] — Entrypoints

Actions are the primary way users interact with a plugin — they appear in Herdr's action menu and
can be bound to keys.

```toml
[[actions]]
id = "list-workspaces"      # Required. Unique within the plugin (no dots).
title = "List workspaces"   # Required. Display name.
description = "..."         # Optional. Shown in action menu.
contexts = ["workspace"]    # Optional. When this action is available.
command = ["node", "index.js"]  # Required. argv array.
platforms = ["linux", "macos"]  # Optional. Inherits top-level if omitted.
```

**`contexts`** controls when the action appears:

- `"workspace"` — available when a workspace is open
- `"pane"` — available when a pane is focused
- `"global"` — always available
- Omit for default behavior (check minimal plugin scope)

**Action invocation** receives these additional env vars:

- `HERDR_PLUGIN_ACTION_ID` — the action id being invoked
- `HERDR_PLUGIN_CONTEXT_JSON` — structured context (workspace, tab, pane, etc.)

### [[events]] — Event hooks

Plugins react to Herdr events. When the event fires, Herdr runs the command.

```toml
[[events]]
on = "worktree.created"
command = ["node", "notify.mjs"]

[[events]]
on = "pane.agent_status_changed"
command = ["bash", "on-agent-status.sh"]
```

**Available events:**

- `worktree.created` — a new git worktree was created and opened as a workspace
- `worktree.opened` — an existing worktree was opened into a workspace
- `pane.agent_status_changed` — an agent pane changed status (done, blocked, etc.)

**Event commands** receive:

- `HERDR_PLUGIN_EVENT` — the event name string
- `HERDR_PLUGIN_EVENT_JSON` — full event payload with context
- `HERDR_PLUGIN_CONTEXT_JSON` — current Herdr state

**Gotchas:**

- Event handlers should be idempotent — they may fire in quick succession
- A handler should no-op if the work is already done (e.g., worktree.created + worktree.opened
  can both fire for the same worktree)
- Keep event handlers fast. Herdr does not wait for them to complete before continuing.
- Do not rely on event ordering. Two near-simultaneous events may arrive in any order.

### [[panes]] — UI panes

Panes open plugin content as a Herdr terminal pane (split, tab, overlay, or zoomed).

```toml
[[panes]]
id = "board"              # Required. Unique within plugin (no dots).
title = "Project Board"   # Required. Shown as pane title.
placement = "overlay"     # Optional. Default: "overlay". One of: overlay, split, tab, zoomed.
command = ["node", "board.mjs"]  # Required. argv array.
platforms = ["linux", "macos"]  # Optional.
```

**Placement options:**

| Placement | Behavior |
|-----------|----------|
| `overlay` (default) | Temporary zoomed overlay over the active pane. Restores focus when closed. |
| `split` | Opens as a split pane beside the current pane. |
| `tab` | Opens as a new tab in the current workspace. |
| `zoomed` | Opens zoomed to full workspace size. |

Panes are opened via:

```bash
herdr plugin pane open --plugin <id> --entrypoint <pane-id> [--placement <type>] [--direction <dir>]
```

**Pane commands** receive `HERDR_PLUGIN_ENTRYPOINT_ID`. Once opened, they're normal Herdr panes —
you can call `pane.move`, `pane.swap`, `pane.resize`, `pane.zoom` through the CLI or socket.

On Windows, pane commands use Herdr's normal Windows pane launcher and must be valid Windows
argv commands.

### [[link_handlers]] — URL click routing

Route modified-clicks (Ctrl+click on every platform) on terminal URLs to a plugin action.

```toml
[[link_handlers]]
id = "github-issue-or-pr"     # Required. Unique within plugin (no dots).
title = "Preview GitHub issue" # Required.
pattern = "^https://github\\.com/[^/]+/[^/]+/(issues|pull)/[0-9]+/?$"  # Rust regex.
action = "open"               # Required. References an action ID in the SAME plugin.
```

**How it works:**

1. User Ctrl+clicks a URL in their terminal
2. Herdr matches the URL against each link handler's `pattern` (in manifest order)
3. On match, Herdr runs the linked action with `invocation_source = "link_click"`,
   `clicked_url`, and `link_handler_id` in `HERDR_PLUGIN_CONTEXT_JSON`
4. Shell plugins can also read `HERDR_PLUGIN_CLICKED_URL` and `HERDR_PLUGIN_LINK_HANDLER_ID`

**Gotchas:**

- `pattern` is a Rust regular expression. Use `\\.` for literal dots, not `\.`
- The pattern is matched against the **full** URL string
- Link handlers are checked in manifest order **within each plugin** — define more specific
  patterns before general ones
- The modified-click modifier is **Ctrl on every platform** (terminal mouse reports don't
  expose Cmd/Super separately from plain clicks)
- The referenced action must be declared by the same plugin (cannot point to another plugin)

---

## Choosing a Language

Herdr plugins work with any argv command. Choose based on what the plugin needs:

| Use case | Good choices |
|----------|-------------|
| Simple CLI wrappers, shell integration | **Bash** — no runtime deps, works everywhere |
| File manipulation, data processing | **Python** — rich stdlib, `pip` installable |
| Event-driven, HTTP, config files | **Node.js/TypeScript** — npm ecosystem, good for event handlers |
| TUI, performance-sensitive | **Rust** — binary, zero deps at runtime, great for TUIs |
| CLI that calls back to Herdr heavily | **Go** — compiles to single binary, good stdlib |
| Quick layout/tooling scripts | **Lua** — lightweight, embedded in system tools |

**Key principle:** Herdr injects env vars for context. Your language choice only affects how you
read `process.env` (or equivalent) and call the Herdr CLI. Everything else is the same.

---

## Runtime Environment

Herdr injects these environment variables when running plugin commands:

### Always available

| Variable | Description |
|----------|-------------|
| `HERDR_ENV=1` | Confirms this is a Herdr plugin context |
| `HERDR_BIN_PATH` | Path to the running Herdr binary (use this for CLI calls) |
| `HERDR_SOCKET_PATH` | Socket path for raw JSON API calls |
| `HERDR_PLUGIN_ID` | The plugin's manifest id |
| `HERDR_PLUGIN_ROOT` | Plugin directory (installed or linked) |
| `HERDR_PLUGIN_CONFIG_DIR` | User-editable config directory (persists across reinstalls) |
| `HERDR_PLUGIN_STATE_DIR` | Runtime state directory (plugin owns lifecycle) |
| `HERDR_PLUGIN_CONTEXT_JSON` | Structured JSON with workspace, tab, pane, agent, etc. |
| `HERDR_PLUGIN_CLICKED_URL` | Link handler: the clicked URL |
| `HERDR_PLUGIN_LINK_HANDLER_ID` | Link handler: which handler matched |

### Context-dependent

| Variable | When set |
|----------|----------|
| `HERDR_WORKSPACE_ID` | When invoked from a workspace context |
| `HERDR_TAB_ID` | When a tab is active |
| `HERDR_PANE_ID` | When a pane is focused |
| `HERDR_PLUGIN_ACTION_ID` | During action invocation |
| `HERDR_PLUGIN_EVENT` | During event hook |
| `HERDR_PLUGIN_EVENT_JSON` | During event hook (full payload) |
| `HERDR_PLUGIN_ENTRYPOINT_ID` | During pane command |

### `HERDR_PLUGIN_CONTEXT_JSON` shape

The context JSON can include these fields (only the ones relevant to the invocation):

```json
{
  "workspace_id": "w-xxx",
  "workspace_label": "my-project",
  "tab_id": "t-yyy",
  "tab_label": "terminal",
  "focused_pane_id": "p-zzz",
  "focused_pane_agent": "my-agent",
  "focused_pane_status": "done",
  "agent_status": "done",
  "invocation_source": "link_click",
  "clicked_url": "https://github.com/...",
  "link_handler_id": "github-issue-or-pr"
}
```

### Storage guidance

- **`HERDR_PLUGIN_ROOT`** — Do NOT store user credentials or durable state here.
  GitHub-installed roots are managed source checkouts that get replaced on reinstall.
- **`HERDR_PLUGIN_CONFIG_DIR`** — User-editable config (`.env` files, configs, user prefs).
  Herdr creates this directory but does not touch its contents. The plugin owns the file format
  and lifecycle.
- **`HERDR_PLUGIN_STATE_DIR`** — Local runtime state (caches, temp data, generated files).
  Plugin owns lifecycle.

There is no Herdr-managed storage API in v1. Plugins that need durable state own their files.

---

## Calling Back Into Herdr

Plugins communicate with Herdr through two channels:

### 1. CLI (recommended) — `HERDR_BIN_PATH`

Use `HERDR_BIN_PATH` for portability across platforms (Unix socket vs Windows named pipe).
The entire Herdr CLI is available.

**Bash:**

```bash
herdr_bin="${HERDR_BIN_PATH:-herdr}"
"$herdr_bin" workspace list
"$herdr_bin" pane split "$HERDR_PANE_ID" --direction right --ratio 0.5
"$herdr_bin" plugin pane open --plugin my-plugin --entrypoint board
```

**Node.js:**

```javascript
const { spawnSync } = require("node:child_process");
const herdr = process.env.HERDR_BIN_PATH ?? "herdr";
const result = spawnSync(herdr, ["workspace", "list"], { encoding: "utf8" });
```

**Python:**

```python
import subprocess, os
herdr = os.environ.get("HERDR_BIN_PATH", "herdr")
result = subprocess.run([herdr, "workspace", "list"], capture_output=True, text=True)
```

**Lua:**

```lua
local herdr = os.getenv("HERDR_BIN_PATH") or "herdr"
local handle = io.popen(herdr .. " workspace list 2>&1", "r")
local output = handle:read("*a")
handle:close()
```

**Go:**

```go
import "os/exec"
herdr := os.Getenv("HERDR_BIN_PATH")
if herdr == "" { herdr = "herdr" }
cmd := exec.Command(herdr, "workspace", "list")
```

### 2. Socket API (advanced) — `HERDR_SOCKET_PATH`

For raw JSON requests directly over the Herdr socket. Unix: Unix domain socket.
Windows: named pipe. Use the CLI approach unless you need the raw transport.

See the [Herdr socket API docs](https://herdr.dev/docs/api/) for request shapes.

---

## Testing and Debugging

### Linking a local plugin

```bash
herdr plugin link /path/to/my-plugin
# Output: Plugin linked successfully
```

Unlike `herdr plugin install`, `plugin link` does NOT run build commands — build manually.

### Listing and invoking actions

```bash
# List all registered plugins
herdr plugin list

# List actions for your plugin
herdr plugin action list --plugin my-org.my-plugin

# Invoke an action
herdr plugin action invoke my-org.my-plugin.hello

# Pass context to test an action
herdr plugin action invoke --context '{"workspace_id":"w-xxx"}' my-org.my-plugin.hello
```

### Opening panes

```bash
# Open a pane
herdr plugin pane open --plugin my-org.my-plugin --entrypoint board

# With placement override
herdr plugin pane open --plugin my-org.my-plugin --entrypoint board --placement split --direction right

# With environment
herdr plugin pane open --plugin my-org.my-plugin --entrypoint board --env "MY_VAR=value"
```

### Viewing logs

```bash
# List log files
herdr plugin log list --plugin my-org.my-plugin

# View specific log
herdr plugin log view --plugin my-org.my-plugin <log-id>
```

### Getting config and state directories

```bash
herdr plugin config-dir my-org.my-plugin
# Prints: /home/user/.local/share/herdr/plugins/my-org.my-plugin/config
```

### Keybinding an action in herdr config

In `~/.config/herdr/config.toml`:

```toml
[[keys.command]]
key = "prefix+l"
type = "plugin_action"
command = "my-org.my-plugin.hello"
description = "Run my plugin action"
```

### Unlinking

```bash
herdr plugin unlink my-org.my-plugin   # Unregisters, leaves files
herdr plugin uninstall my-org.my-plugin # Unregisters + removes checkout (GitHub installs)
```

---

## Publishing to the Marketplace

1. **Create a public GitHub repository** with your plugin code
2. **Add the GitHub topic `herdr-plugin`** to the repository (Settings → Topics)
3. Users install with:

   ```bash
   herdr plugin install owner/repo[/subdir]
   ```

4. The marketplace index at <https://herdr.dev/plugins/> refreshes every 30 minutes
   and discovers repositories with the `herdr-plugin` topic automatically

**For multi-plugin repos** (a monorepo with several plugins in subdirectories):

```bash
herdr plugin install owner/repo/subdir-1
herdr plugin install owner/repo/subdir-2
```

The [example cookbook repo](https://github.com/ogulcancelik/herdr-plugin-examples) demonstrates
this pattern.

---

## Common Patterns and Examples

### Pattern 1: Action that opens a pane

A common pattern: an action opens a pane programmatically via the Herdr CLI.

**Action command (open.sh):**

```bash
#!/usr/bin/env bash
set -euo pipefail
herdr_bin="${HERDR_BIN_PATH:-herdr}"
exec "$herdr_bin" plugin pane open \
  --plugin my-org.my-plugin \
  --entrypoint viewer \
  --placement split \
  --direction right \
  --focus
```

**Pane entry (manifest):**

```toml
[[panes]]
id = "viewer"
title = "Viewer"
placement = "split"
command = ["node", "viewer.mjs"]
```

### Pattern 2: Event-driven notification

React to agent status changes. The event handler checks if the notification is relevant,
then sends an alert (Telegram, desktop notification, etc.).

**Event handler key points:**

- Check `HERDR_PLUGIN_EVENT_JSON` for the agent status
- Exit early if the status isn't interesting (e.g., only notify on "done" or "blocked")
- Read config from `HERDR_PLUGIN_CONFIG_DIR`
- Use `HERDR_BIN_PATH` if you need to query Herdr for more context

```javascript
// notify.mjs
const event = JSON.parse(process.env.HERDR_PLUGIN_EVENT_JSON || "{}");
const status = event?.data?.agent_status?.toLowerCase();
if (!["done", "blocked"].includes(status)) process.exit(0);
// ... send notification
```

### Pattern 3: Layout/worskpace bootstrap

Create a multi-pane development layout around the current pane:

```lua
-- setup.lua
local herdr = os.getenv("HERDR_BIN_PATH") or "herdr"
local root = os.getenv("HERDR_PANE_ID")

-- Rename the current pane
os.execute(herdr .. " pane rename " .. root .. " editor")

-- Split right for file browser
local handle = io.popen(herdr .. " pane split " .. root ..
  " --direction right --ratio 0.58 --no-focus 2>&1", "r")
local files_pane = handle:read("*a"):match('"pane_id"%s*:%s*"([^"]+)"')
handle:close()

-- Split down for tasks
handle = io.popen(herdr .. " pane split " .. files_pane ..
  " --direction down --ratio 0.5 --no-focus 2>&1", "r")
local tasks_pane = handle:read("*a"):match('"pane_id"%s*:%s*"([^"]+)"')
handle:close()

-- Rename and launch
os.execute(herdr .. " pane rename " .. files_pane .. " files")
os.execute(herdr .. " pane rename " .. tasks_pane .. " tasks")
os.execute(herdr .. " pane run " .. root .. " nvim .")
```

### Pattern 4: Link handler with preview pane

Ctrl+click a GitHub issue/PR URL → open a preview pane showing the issue.

**Manifest:**

```toml
[[link_handlers]]
id = "github-issue-or-pr"
title = "Preview GitHub issue or PR"
pattern = "^https://github\\.com/[^/]+/[^/]+/(issues|pull)/[0-9]+/?$"
action = "open"
```

**Handler script:**

```bash
#!/usr/bin/env bash
set -euo pipefail
herdr_bin="${HERDR_BIN_PATH:-herdr}"
url="${HERDR_PLUGIN_CLICKED_URL:-}"
exec "$herdr_bin" plugin pane open \
  --plugin my-org.my-plugin \
  --entrypoint preview \
  --placement split \
  --env "GITHUB_URL=$url" \
  --focus
```

### Pattern 5: Multi-language build (Rust + binary)

Build a Rust binary at install time, then use it in actions:

```toml
[[build]]
command = ["cargo", "build", "--release"]

[[actions]]
id = "check"
title = "Run check"
command = ["./target/release/my-check-binary"]

[[panes]]
id = "dashboard"
title = "Dashboard"
placement = "split"
command = ["./target/release/my-dashboard-binary"]
```

For faster installs, consider a script that downloads a prebuilt binary matching the
version/platform, falling back to `cargo build`:

```bash
# scripts/fetch-or-build.sh — downloads prebuilt or builds from source
```

### Pattern 6: Config-driven plugin

Store user configuration in `HERDR_PLUGIN_CONFIG_DIR`:

```javascript
const fs = require("fs");
const path = require("path");

const configDir = process.env.HERDR_PLUGIN_CONFIG_DIR;
const configPath = path.join(configDir, "config.json");

// Load or create config
let config = {};
if (fs.existsSync(configPath)) {
  config = JSON.parse(fs.readFileSync(configPath, "utf8"));
} else {
  config = { theme: "dark", enabled: true };
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
}
```

---

## Full Example: A Complete Plugin

Here's a complete, working plugin that demonstrates everything together:

**Directory:**

```
my-herdr-plugin/
├── herdr-plugin.toml
├── notify.mjs        # Event handler
├── open.js           # Link handler action
├── preview.sh        # Pane command
└── lib.mjs           # Shared utilities
```

**herdr-plugin.toml:**

```toml
id = "my-org.my-herdr-plugin"
name = "My Herdr Plugin"
version = "0.2.0"
min_herdr_version = "0.7.0"
description = "A full-featured example plugin"
platforms = ["linux", "macos"]

# --- Actions ---

[[actions]]
id = "open-viewer"
title = "Open viewer pane"
contexts = ["workspace"]
command = ["node", "open.js"]

# --- Events ---

[[events]]
on = "pane.agent_status_changed"
command = ["node", "notify.mjs"]

# --- Panes ---

[[panes]]
id = "preview"
title = "Preview"
placement = "split"
command = ["bash", "preview.sh"]

# --- Link Handlers ---

[[link_handlers]]
id = "github-link"
title = "Preview GitHub URL"
pattern = "^https://github\\.com/[^/]+/[^/]+/.+$"
action = "open-viewer"
```

---

## Gotchas

- **No shell expansion**: `command` values are argv arrays. Herdr does NOT run them through
  a shell. `command = ["echo", "$HOME"]` prints literal `$HOME`, not the variable value.
  Use a shell (`bash -c "..."`) when you need expansion.

- **Build commands ≠ runtime commands**: Build commands run in a different environment.
  They don't receive `HERDR_SOCKET_PATH`, `HERDR_BIN_PATH`, or any plugin context env vars.
  Don't rely on plugin env vars in your build scripts.

- **Manifest mutability during install**: Changing `herdr-plugin.toml` during the build step
  aborts the installation. The manifest preview is captured before builds run.

- **Plugin root is a managed checkout**: On GitHub-installed plugins, `HERDR_PLUGIN_ROOT` is a
  git checkout. Reinstalling replaces it. Store user data in `HERDR_PLUGIN_CONFIG_DIR`.

- **Link handlers match in order**: Herdr checks link handlers in manifest order across ALL
  installed plugins. Put more specific patterns before general ones.

- **Environment variable injection**: Herdr injects env vars before running the command, but
  the command's own child processes inherit them. If your command starts a long-lived process,
  it will inherit Herdr env vars — be aware of env var namespace pollution.

- **Windows pane commands**: On Windows, pane commands use Herdr's normal Windows pane launcher
  and must be valid Windows argv commands. `npm.cmd`, `bun.cmd`, `pnpm.cmd` resolve correctly
  when on PATH.

- **Event handlers should be fast and idempotent**: Herdr does not wait for event handlers to
  complete. A slow handler doesn't block Herdr, but it may get killed if it takes too long.
  Design handlers to be safe to run multiple times.

- **Link handler actions receive extra context**: In addition to `HERDR_PLUGIN_CONTEXT_JSON`,
  link handler actions set `HERDR_PLUGIN_CLICKED_URL` and `HERDR_PLUGIN_LINK_HANDLER_ID` as
  separate env vars for shell script convenience.

- **Testing pane opening**: When testing a pane-opening action locally, the action's command
  runs with the plugin directory as cwd. If your pane binary isn't on PATH, use the full path
  or `$HERDR_PLUGIN_ROOT/bin/...` to reference it.

- **Logs are your friend**: Use `herdr plugin log list --plugin <id>` to see output and errors.
  Both stdout and stderr from plugin commands are captured.
