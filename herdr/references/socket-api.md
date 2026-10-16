# Socket API Reference

Source: <https://herdr.dev/docs/socket-api/>
Fetched: 2026-07-05

Herdr exposes a local socket API for scripts and agents that need to inspect or control a running session. Uses newline-delimited JSON over a Unix domain socket (Linux/macOS) or named pipe (Windows).

---

## Integration Layers

| Layer | Use it for |
|-------|-----------|
| Agent skill | Teaching a coding agent how to use Herdr from inside a pane |
| CLI wrappers | Shell scripts, simple orchestration, and human debugging |
| Raw socket API | Custom tools, protocol clients, and event subscribers |

All layers share the same control surface.

---

## Raw Socket Methods

Dot notation. Send one JSON request per line over the socket:

```json
{"id": "req_1", "method": "ping", "params": {}}
```

Response includes the same `id`:

```json
{"id": "req_1", "result": {"type": "pong"}}
```

### Server

| Method | Description |
|--------|------------|
| `ping` | Health check, returns protocol version |
| `server.stop` | Stop the server |
| `server.reload_config` | Reload configuration |
| `server.agent_manifests` | List active agent detection manifest sources and remote update diagnostics |
| `server.reload_agent_manifests` | Reload agent detection rules |

### Notification

| Method | Description |
|--------|------------|
| `notification.show` | Show a user notification through configured toast delivery |

### Client

| Method | Description |
|--------|------------|
| `client.window_title.set` | Set foreground client's outer terminal window title |
| `client.window_title.clear` | Restore Herdr's default terminal window title |

### Workspace

| Method | Description |
|--------|------------|
| `workspace.create` | Create a workspace |
| `workspace.list` | List workspaces |
| `workspace.get` | Get workspace details |
| `workspace.focus` | Focus a workspace |
| `workspace.rename` | Rename a workspace |
| `workspace.close` | Close a workspace |

### Worktree

| Method | Description |
|--------|------------|
| `worktree.list` | List worktrees |
| `worktree.create` | Create a Git worktree checkout as a Herdr workspace |
| `worktree.open` | Open an existing checkout |
| `worktree.remove` | Remove a linked checkout |

### Tab

| Method | Description |
|--------|------------|
| `tab.create` | Create a tab |
| `tab.list` | List tabs |
| `tab.get` | Get tab details |
| `tab.focus` | Focus a tab |
| `tab.rename` | Rename a tab |
| `tab.close` | Close a tab |

### Pane

| Method | Description |
|--------|------------|
| `pane.split` | Split a pane |
| `pane.swap` | Swap panes (same-tab only) |
| `pane.move` | Move a pane to another tab, new tab, or new workspace |
| `pane.zoom` | Toggle, enable, or disable pane zoom |
| `pane.layout` | Get tab layout snapshot |
| `pane.process_info` | Get pane's shell pid, foreground process group, processes |
| `pane.neighbor` | Get pane neighbor (includes layout snapshot) |
| `pane.edges` | Get pane edges (includes layout snapshot) |
| `pane.focus_direction` | Focus pane in a direction |
| `pane.resize` | Resize a pane |
| `pane.list` | List panes |
| `pane.current` | Get current pane (`PaneInfo`) |
| `pane.get` | Get pane details |
| `pane.rename` | Rename a pane |
| `pane.send_text` | Send text to a pane |
| `pane.send_keys` | Send key combos to a pane |
| `pane.send_input` | Send input to a pane |
| `pane.read` | Read pane output |
| `pane.report_agent` | Report agent state (semantic) |
| `pane.report_agent_session` | Report native session reference |
| `pane.report_metadata` | Report display-only metadata |
| `pane.clear_agent_authority` | Clear agent authority |
| `pane.release_agent` | Release agent |
| `pane.close` | Close a pane |
| `pane.wait_for_output` | Wait for pane output |

### Layout

| Method | Description |
|--------|------------|
| `layout.export` | Export portable tab layout tree |
| `layout.apply` | Create a fresh tab from a declarative tree |

### Agent

| Method | Description |
|--------|------------|
| `agent.list` | List agents |
| `agent.get` | Get agent details |
| `agent.read` | Read agent output |
| `agent.explain` | Evaluate pane's detection snapshot |
| `agent.send` | Send to agent |
| `agent.rename` | Rename an agent |
| `agent.focus` | Focus an agent |
| `agent.start` | Start an agent |

### Events

| Method | Description |
|--------|------------|
| `events.subscribe` | Subscribe to lifecycle events (long-lived stream) |
| `events.wait` | Wait for a specific event |

### Integrations

| Method | Description |
|--------|------------|
| `integration.install` | Install a built-in integration |
| `integration.uninstall` | Uninstall an integration |

### Plugins

| Method | Description |
|--------|------------|
| `plugin.link` | Link a local plugin manifest |
| `plugin.list` | List linked plugins |
| `plugin.unlink` | Unlink a plugin |
| `plugin.enable` | Enable a linked plugin |
| `plugin.disable` | Disable a linked plugin |
| `plugin.action.list` | List plugin actions |
| `plugin.action.invoke` | Invoke a plugin action |
| `plugin.log.list` | List recent action/event command logs |
| `plugin.pane.open` | Open a managed plugin terminal pane |
| `plugin.pane.focus` | Focus a plugin pane |
| `plugin.pane.close` | Close a plugin pane |

---

## Key Method Details

### Pane control

Pane IDs use public id format: `w1:p1`. Methods with optional `pane_id` use the server's active focused pane when omitted. `pane.move` always requires source `pane_id`.

#### pane.send_keys / pane.send_input.keys

Accepts Herdr key-combo strings:

- Plain printable keys
- Special keys: `enter`, `esc`
- Modifier chords: `ctrl+h`, `control+j`, `alt+x`, `shift+tab`
- Function keys: `f1`–`f12`
- Named punctuation: `minus`, `plus`

Does **not** accept `prefix+` binding strings.

#### pane.swap

Directional and explicit forms:

```json
{"method": "pane.swap", "params": {"pane_id": "w1:p1", "direction": "right"}}
{"method": "pane.swap", "params": {"source_pane_id": "w1:p1", "target_pane_id": "w1:p2"}}
```

Same-tab only. Preserves split shape, ratios, pane ids, and running processes.
Response includes `changed`, optional `reason`, `source_pane_id`, optional `target_pane_id`, `focused_pane_id`, `layout`.
Reasons: `no_neighbor`, `same_pane`, `not_found`, `cross_tab`.

#### pane.move

```json
{"method": "pane.move", "params": {"pane_id": "w1:p2", "destination": {"type": "tab", "tab_id": "w1:t2", "target_pane_id": "w1:p3", "split": "right", "ratio": 0.5}, "focus": true}}
{"method": "pane.move", "params": {"pane_id": "w1:p2", "destination": {"type": "new_tab", "workspace_id": "w1", "label": "logs"}, "focus": true}}
{"method": "pane.move", "params": {"pane_id": "w1:p2", "destination": {"type": "new_workspace", "label": "logs", "tab_label": "main"}, "focus": true}}
```

Moves a running pane to another tab, new tab, or new workspace. Cross-workspace moves keep the internal pane and terminal alive but assign a new public pane id.

#### pane.zoom

```json
{"method": "pane.zoom", "params": {"pane_id": "w1:p1", "mode": "toggle"|"on"|"off"}}
```

Omitting `pane_id` targets the server's active focused pane. Response includes `changed`, `zoom_changed`, `focus_changed`, optional `reason`, `pane_id`, `focused_pane_id`, `zoomed`, `layout`.

#### pane.read

CLI convenience:

```bash
herdr pane read w1:p1 --source visible --lines 80
herdr pane read w1:p1 --source recent --lines 120
herdr pane read w1:p1 --source recent-unwrapped --lines 120
herdr pane read w1:p1 --source detection
```

`recent-unwrapped` ignores soft wrapping (good for logs). `detection` returns the bottom-buffer snapshot used by agent screen detection.

#### pane.report_agent

```json
{"method": "pane.report_agent", "params": {
  "pane_id": "w1:p1",
  "source": "custom:docs",
  "agent": "docs-bot",
  "state": "working",
  "message": "building docs",
  "custom_status": "indexing"
}}
```

`state` is semantic (affects waits, notifications, rollups). `custom_status` is visual (short activity label).

### Layout

#### layout.export

```json
{"method": "layout.export", "params": {"tab_id": "w1:t1"}}
```

Returns a BSP tree of pane and split nodes. Pane nodes include `pane_id`, `label`, `cwd`, `argv command`. Split nodes use `direction` (`right`/`down`), `ratio`, `first`, `second`.

#### layout.apply

```json
{"method": "layout.apply", "params": {
  "workspace_id": "wabc",
  "tab_label": "dev",
  "focus": true,
  "root": {
    "type": "split",
    "direction": "right",
    "ratio": 0.65,
    "first": {"type": "pane", "label": "editor", "cwd": "/repo"},
    "second": {"type": "pane", "label": "tests", "cwd": "/repo", "command": ["sh", "-c", "just test"], "env": {"HERDR_ROLE": "tests"}}
  }
}}
```

Creates a fresh tab from a declarative tree. Replaces tab if `tab_id` provided. Restores structure, labels, cwd, env, optional argv; does **not** preserve live PTYs, scrollback, or running processes.

### Notification

```json
{"method": "notification.show", "params": {
  "title": "build failed",
  "body": "api workspace",
  "position": "top-left",
  "sound": "request"  // none, done, request
}}
```

`title` required (80 char max after sanitization). `body` optional (240 char max). `position` only applies when `ui.toast.delivery = "herdr"`. Response: `{"type": "notification_show", "shown": true/false, "reason": "shown"|"disabled"|"rate_limited"|"no_foreground_client"|"busy"}`.

### Agent

#### agent.explain

Evaluates the target pane's detection snapshot in the running server. Returns the final state, manifest source and version, matched rule, evaluated rule evidence, skip-state reason, idle fallback reason, and screen detection skip reason.

### Worktree

```json
{"method": "worktree.create", "params": {"workspace_id": "w1", "branch": "worktree/api", "focus": false}}
{"method": "worktree.open", "params": {"workspace_id": "w1", "branch": "worktree/api", "focus": true}}
{"method": "worktree.remove", "params": {"workspace_id": "2", "force": false}}
```

Use at most one of `workspace_id` or `cwd`; omit both to use the active workspace. Worktree commands emit lifecycle events (`worktree.created`, `worktree.opened`, `worktree.removed`).

### Plugin API

Full manifest shape:

```toml
id = "example.worktree-bootstrap"
name = "Worktree Bootstrap"
version = "0.1.0"
min_herdr_version = "0.7.0"
description = "Prepare new worktrees"
platforms = ["linux", "macos", "windows"]

[[build]]
command = ["bun", "install"]

[[actions]]
id = "bootstrap"
title = "Bootstrap worktree"
contexts = ["workspace"]
command = ["bun", "run", "bootstrap.ts"]

[[events]]
on = "worktree.created"
command = ["bun", "run", "bootstrap.ts"]

[[panes]]
id = "board"
title = "Worktree board"
placement = "overlay"
command = ["bun", "run", "board.ts"]

[[link_handlers]]
id = "github-issue"
title = "Open GitHub issue"
pattern = "^https://github\\.com/[^/]+/[^/]+/(issues|pull)/[0-9]+$"
action = "bootstrap"
```

`min_herdr_version` is required. Server refuses to link if missing, invalid, or newer than running Herdr. Platforms can be per-item (overrides plugin-level) or inherited.

#### Plugin env vars injected at runtime

- `HERDR_SOCKET_PATH`
- `HERDR_BIN_PATH`
- `HERDR_ENV=1`
- `HERDR_PLUGIN_ID`
- `HERDR_PLUGIN_ROOT`
- `HERDR_PLUGIN_CONFIG_DIR`
- `HERDR_PLUGIN_STATE_DIR`
- `HERDR_PLUGIN_CONTEXT_JSON`
- `HERDR_WORKSPACE_ID`, `HERDR_TAB_ID`, `HERDR_PANE_ID` (when available)
- Action commands: `HERDR_PLUGIN_ACTION_ID`
- Event hooks: `HERDR_PLUGIN_EVENT`, `HERDR_PLUGIN_EVENT_JSON`
- Pane commands: `HERDR_PLUGIN_ENTRYPOINT_ID`

#### plugin.pane.open

```json
{"method": "plugin.pane.open", "params": {
  "plugin_id": "example.board",
  "entrypoint": "board",
  "placement": "zoomed",  // overlay (default), split, tab, zoomed
  "target_pane_id": "w1:p1",
  "env": {"HERDR_ROLE": "board"},
  "focus": true
}}
```

Overrides manifest `placement`. Overlay targets active pane. Split/zoomed target an existing pane. Tab can target a workspace. `plugin.pane.focus` and `plugin.pane.close` only operate on panes opened through the plugin API.

---

## Event Subscriptions

```json
{"method": "events.subscribe", "params": {
  "subscriptions": [
    {"type": "pane.agent_status_changed", "pane_id": "w1:p1", "agent_status": "blocked"}
  ]
}}
```

First response acknowledges subscription. Later lines are pushed events.

**Workspace events:** `workspace.created`, `workspace.updated`, `workspace.renamed`, `workspace.closed`, `workspace.focused`

**Pane events:** `pane.created`, `pane.closed`, `pane.focused`, `pane.moved`, `pane.exited`, `pane.agent_detected`, `pane.output_matched`, `pane.agent_status_changed`

**Worktree events:** `worktree.created`, `worktree.opened`, `worktree.removed`

---

## Socket Paths

| Scope | Path |
|-------|------|
| Default | `~/.config/herdr/herdr.sock` |
| Named session | `~/.config/herdr/sessions/<name>/herdr.sock` |

Resolution order:

1. Explicit CLI `--session <name>`
2. `HERDR_SOCKET_PATH` env var (for low-level overrides only)
3. `HERDR_SESSION=<name>` env var
4. Default session socket

---

## Response Shapes

Success:

```json
{"id": "req_1", "result": {"type": "pane_info", "pane": {"pane_id": "w1:p1", ...}}}
```

Error:

```json
{"id": "req_1", "error": {"code": "not_found", "message": "pane not found"}}
```

---

## Protocol Stability

Herdr has a protocol version for client/server compatibility. Check with `ping` or `herdr status` before depending on new behavior. Handle unknown fields gracefully.

Pane control response types include: `pane_info`, `pane_swap`, `pane_move`, `pane_zoom`, `notification_show`, `client_window_title`, `agent_manifest_status`, `agent_manifest_reload`.
