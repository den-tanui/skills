---
name: herdr-cli
description: >-
  Reference for the Herdr CLI — every command, flag, and output format. Use this skill whenever the
  user asks how to do something with the herdr command: construct a specific command invocation,
  control workspaces/tabs/panes/agents programmatically, script Herdr automation, parse JSON output,
  install or link plugins, understand available flags, or figure out the right command for a task.
  Also use when the user wants to pipe herdr output, filter workspace/pane/agent lists, invoke plugin
  actions from scripts, send keys or text to panes, create worktrees, wait for agent status, attach
  the terminal directly, or configure integrations. Do NOT use this skill for plugin development
  questions — that is the herdr-plugin-dev skill's domain.
license: MIT
metadata:
  herdr_docs_url: https://herdr.dev/docs/cli-reference/
---

# Herdr CLI Reference

The Herdr CLI talks to the running server over a local socket. Most commands print JSON — pipe them
into `jq` or your language's JSON parser for scripting.

All commands work identically whether run from a terminal, a script, or inside a plugin via
`HERDR_BIN_PATH`.

---

## Quick Orientation

```bash
herdr                          # launch or attach to default session
herdr --session work           # named session
herdr --remote workbox         # attach through SSH
herdr status                   # server + client status
herdr server stop              # stop server, preserve panes
herdr server reload-config     # hot-reload config
herdr --version                # print version
```

**Output:** most data commands (`list`, `get`, `create`, etc.) return JSON. Human-readable
formatting is the exception — use `--json` explicitly where available.

**Key principle:** everything you can do with mouse/keyboard in Herdr, you can do from the CLI.
The CLI and socket API share the same backend.

---

## Command Groups

### Sessions

```bash
herdr session list             # list sessions
herdr session attach <name>    # attach to a named session
herdr session stop <name>      # stop server for a session
herdr session delete <name>    # delete session state
```

### Workspaces

```bash
herdr workspace list
herdr workspace create [--cwd PATH] [--label TEXT] [--env K=V] [--focus | --no-focus]
herdr workspace get <id>
herdr workspace focus <id>
herdr workspace rename <id> <label>
herdr workspace close <id>
```

Use `--no-focus` to create a workspace without stealing the current focus:

```bash
herdr workspace create --cwd ~/project --label api --no-focus
```

### Worktrees

```bash
herdr worktree list [--workspace ID | --cwd PATH]
herdr worktree create [--workspace ID | --cwd PATH] [--branch NAME] [--base REF]
                     [--path PATH] [--label TEXT] [--focus | --no-focus]
herdr worktree open [--workspace ID | --cwd PATH] (--path PATH | --branch NAME)
herdr worktree remove --workspace ID [--force]
```

Worktrees are normal Herdr workspaces with Git checkout provenance:

- `create` — creates a Git worktree checkout, opens as workspace, groups with parent repo
- If `--branch` names an existing local branch, Herdr checks it out; otherwise creates from `--base`
- Without `--path`, checkout goes under `<worktrees.directory>/<repo>/<branch-slug>`
- `workspace close` closes Herdr state only; `worktree remove` deletes the checkout
- `worktree remove --force` when Git refuses a dirty checkout

### Tabs

```bash
herdr tab list [--workspace <id>]
herdr tab create [--workspace <id>] [--cwd PATH] [--label TEXT] [--env K=V]
                 [--focus | --no-focus]
herdr tab get <id>
herdr tab focus <id>
herdr tab rename <id> <label>
herdr tab close <id>
```

### Panes

**Lifecycle:**

```bash
herdr pane list [--workspace <id>]
herdr pane get <id>
herdr pane current [--pane ID | --current]
herdr pane close <id>
herdr pane rename <id> <label>
```

**Layout:**

```bash
herdr pane split [<id> | --pane ID | --current] --direction right|down
                 [--ratio FLOAT] [--cwd PATH] [--env K=V] [--focus | --no-focus]
herdr pane swap --direction left|right|up|down [--pane ID | --current]
herdr pane swap --source-pane ID --target-pane ID
herdr pane move <id> --tab <tab_id> --split right|down [--target-pane ID] [--ratio FLOAT]
herdr pane move <id> --new-tab [--workspace ID] [--label TEXT]
herdr pane move <id> --new-workspace [--label TEXT] [--tab-label TEXT]
herdr pane resize --direction left|right|up|down [--amount FLOAT] [--pane ID | --current]
herdr pane zoom [<id> | --pane ID | --current] [--toggle | --on | --off]
```

**Reading output:**

```bash
herdr pane read <id> [--source visible|recent|recent-unwrapped|detection] [--lines N]
herdr pane read <id> --source visible --ansi
```

**Sending input:**

```bash
herdr pane send-text <id> <text>
herdr pane send-keys <id> <key> [key ...]
herdr pane run <id> <command>
```

Key syntax: plain keys (`a`), special (`enter`, `tab`, `esc`, `backspace`, `left`, `right`,
`up`, `down`), modifiers (`ctrl+h`, `alt+x`, `shift+tab`), function keys (`f1`),
punctuation (`minus`, `plus`, `backtick`). `C-c` and `c-c` accepted as aliases for `ctrl+c`.

**Prefer `pane run`** over `send-text` + `send-keys Enter` — it submits text plus Enter atomically.

**Agent state reporting:**

```bash
herdr pane report-agent <id> --source ID --agent LABEL
                           --state idle|working|blocked|unknown
                           [--message TEXT] [--custom-status TEXT]
                           [--seq N] [--agent-session-id ID]

herdr pane report-metadata <id> --source ID
                           [--agent LABEL] [--display-agent TEXT]
                           [--title TEXT | --clear-title]
                           [--custom-status TEXT | --clear-custom-status]
                           [--state-label STATUS=TEXT]
                           [--ttl-ms N] [--seq N]
```

**Pane metadata normalization:** Herdr trims whitespace, removes control chars,
caps `--custom-status` at 32 chars, caps `--title`/`--display-agent`/`--state-label` at 80.
Empty values are ignored. `--source` and `--applies-to-source` max 80 chars, ASCII only.

### Agents

```bash
herdr agent list
herdr agent get <target>
herdr agent read <target> [--source visible|recent|recent-unwrapped|detection]
                          [--lines N] [--format text|ansi]
herdr agent send <target> <text>
herdr agent rename <target> <name> | --clear
herdr agent focus <target>
herdr agent wait <target> --status idle|working|blocked|unknown [--timeout MS]
herdr agent attach <target> [--takeover]
herdr agent start <name> [--cwd PATH] [--workspace ID] [--tab ID]
                         [--split right|down] [--env K=V] [--focus | --no-focus]
                         -- <argv...>
herdr agent explain <target> [--json | --verbose]
herdr agent explain --file PATH --agent LABEL [--json | --verbose]
```

**Target resolution:** agent targets accept terminal IDs, unique agent names, detected/reported
agent labels, or legacy pane IDs. Names/labels are agent identities. Terminal IDs and legacy pane
IDs are low-level escape hatches.

**agent start** launches a new process in a new pane under the given name.
Everything after `--` is the argv to run.

**agent explain** classifies a pane's bottom-buffer snapshot using the active manifest cache.
Use `--file PATH --agent LABEL` to test against a saved fixture. `--verbose` shows manifest source,
matched rules, region evidence, fallback reasons, and remote update status. `--json` for tests.

### Notifications

```bash
herdr notification show <title> [--body TEXT]
                               [--position top-left|top-right|bottom-left|bottom-right]
                               [--sound none|done|request]
```

Uses the configured `[ui.toast]` delivery. `--position` only affects in-app Herdr toasts.
`--sound` defaults to `none`.

### Waits (for scripting)

```bash
herdr wait output <pane_id> --match <text>
                  [--source visible|recent|recent-unwrapped]
                  [--lines N] [--timeout MS] [--regex] [--raw]

herdr wait agent-status <pane_id> --status idle|working|blocked|done|unknown
                        [--timeout MS]
```

Use `wait output` for normal commands and servers. Use `wait agent-status` for coding agents.

### Plugins

**Install & manage:**

```bash
herdr plugin install <owner>/<repo>[/subdir...] [--ref REF] [--yes]
herdr plugin list [--plugin ID] [--json]
herdr plugin uninstall <plugin_id | owner/repo[/subdir...]>
herdr plugin enable <plugin_id>
herdr plugin disable <plugin_id>
```

**Local development:**

```bash
herdr plugin link <path> [--disabled]
herdr plugin unlink <plugin_id>
herdr plugin config-dir <plugin_id>
```

**Actions:**

```bash
herdr plugin action list [--plugin ID]
herdr plugin action invoke <action_id> [--plugin ID]
```

Use the qualified action id (`plugin.id.action`) when multiple plugins share the same action id.

**Logs:**

```bash
herdr plugin log list [--plugin ID] [--limit N]
```

**Panes:**

```bash
herdr plugin pane open --plugin ID --entrypoint ID
                       [--placement overlay|split|tab|zoomed]
                       [--workspace ID] [--target-pane PANE]
                       [--direction right|down] [--cwd PATH]
                       [--env K=V] [--focus | --no-focus]
herdr plugin pane focus <pane_id>
herdr plugin pane close <pane_id>
```

### Integrations

```bash
herdr integration install <name>    # pi, omp, claude, codex, copilot, devin, droid,
                                    # kimi, opencode, kilo, hermes, qodercli, cursor
herdr integration uninstall <name>
herdr integration status [--outdated-only]
```

### Direct Terminal Attach

```bash
herdr terminal attach <terminal_id> [--takeover]
herdr terminal title set <title>
herdr terminal title clear
```

Detach with `ctrl+b q`. Send literal `ctrl+b` with `ctrl+b ctrl+b`.

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `HERDR_CONFIG_PATH` | Override config file path |
| `HERDR_SESSION` | Select named session for CLI commands |
| `HERDR_SOCKET_PATH` | Low-level socket path override |
| `HERDR_ENV=1` | Set inside Herdr-managed pane processes |
| `HERDR_PANE_ID` | Public pane id for the running pane |
| `HERDR_TAB_ID` | Public tab id for the running tab |
| `HERDR_WORKSPACE_ID` | Public workspace id for the running workspace |
| `HERDR_LOG` | Log filter, e.g. `HERDR_LOG=herdr=debug` |
| `HERDR_DISABLE_SOUND` | Disable sound playback |

---

## Scripting Patterns

### Listing and filtering

```bash
# List workspaces (JSON)
herdr workspace list | jq '.[] | {id, label}'

# List panes in a workspace
herdr pane list --workspace <id> | jq '.[] | {id, label, cwd}'

# List all plugins with ids
herdr plugin list --json | jq '.[] | {id, name, version}'

# Get current pane info
herdr pane current | jq '{id, label, cwd, foreground_cwd}'
```

### Creating resources

```bash
# Create workspace and capture the id
ws=$(herdr workspace create --cwd ~/project --label my-project --no-focus | jq -r '.workspace_id')

# Create a tab in that workspace
tab=$(herdr tab create --workspace "$ws" --label logs --no-focus | jq -r '.tab_id')

# Split a pane
pane=$(herdr pane split --direction right --ratio 0.5 --no-focus | jq -r '.pane_id')
```

### Running commands in panes

```bash
# Run a command in a pane (with Enter)
herdr pane run <pane_id> "npm test"

# Send keys (without Enter)
herdr pane send-keys <pane_id> "git commit -m " ctrl+v enter

# Wait for output
herdr wait output <pane_id> --match "PASS" --timeout 30000
```

### Working with agents

```bash
# Wait for an agent to finish
herdr agent wait my-agent --status done --timeout 120000

# Read agent output
herdr agent read my-agent --source recent-unwrapped --lines 50

# Send input to an agent
herdr agent send my-agent "continue with the refactor"

# Start a new agent
herdr agent start my-coder --cwd ~/project -- claude
```

### Plugin automation

```bash
# Invoke a plugin action from a script
herdr plugin action invoke my-org.my-plugin.do-thing

# Check plugin logs
herdr plugin log list --plugin my-org.my-plugin --limit 5

# Open a plugin pane
herdr plugin pane open --plugin my-org.my-plugin --entrypoint dashboard --placement split
```

### Worktree workflow

```bash
# Create a worktree for a feature branch
herdr worktree create --cwd ~/repo --branch feature/new-thing

# Open an existing worktree
herdr worktree open --cwd ~/repo --branch feature/new-thing

# Remove a worktree (deletes checkout)
herdr worktree remove --workspace <id>
# Add --force if Git refuses due to dirty state
```

---

## Gotchas

- **`pane run` vs `send-text`**: `pane run` appends Enter atomically. Prefer it for commands.
  `send-text` writes text without Enter. `send-keys` sends key combos.

- **JSON is the default**: Most data commands return JSON. `--json` flags exist where the default
  is human-readable (e.g., `plugin list`). Pipe to `jq` or parse in your language.

- **Agent targets are flexible**: You can use agent names, labels, terminal IDs, or legacy pane IDs.
  Names and labels are preferred. Terminal IDs are escape hatches.

- **Plugin action IDs**: Use the qualified form `plugin-id.action-id` when multiple plugins
  share the same action id. Local action ids can't contain dots, so qualified ids are unambiguous.

- **`worktree remove` vs `workspace close`**: `workspace close` only closes Herdr state (tabs/panes).
  `worktree remove` actually deletes the Git checkout. The checkout is NOT deleted on workspace
  close.

- **`plugin install` vs `plugin link`**: `install` clones from GitHub, runs builds, stores under
  Herdr-managed data. `link` registers a local directory — no clone, no build. Use `link` for
  development.

- **`plugin uninstall` vs `plugin unlink`**: `uninstall` removes Herdr-managed checkout files
  (GitHub installs). `unlink` just unregisters, leaves files alone.

- **Notification positions only affect in-app toasts**: `--position` on `notification show` does
  nothing for terminal or system delivery.

- **`HERDR_SOCKET_PATH` vs `HERDR_BIN_PATH`**: Use `HERDR_BIN_PATH` in scripts for portability
  (works across Unix sockets and Windows named pipes). `HERDR_SOCKET_PATH` is for raw JSON API calls.

- **Pane read sources**: `visible` = current screen (best for UI feedback), `recent` = with wrapping,
  `recent-unwrapped` = without soft wrapping (best for logs), `detection` = bottom-buffer snapshot
  (used by agent screen detection).

- **`pane report-metadata` normalization**: Values are trimmed, control chars removed,
  `--custom-status` capped at 32 chars, `--title`/`--display-agent`/`--state-label` at 80 chars.
  Empty values are silently ignored.
