# Tmux → Herdr Command Mapping Reference

A comprehensive reference for mapping every tmux command, option, and convention
to its Herdr equivalent. Used by the tmux-herdr-plugin skill.

---

## Commands — Pane Management

| tmux | herdr | Notes |
|------|-------|-------|
| `split-window -h` | `pane split --direction right` | `--ratio FLOAT` for size |
| `split-window -v` | `pane split --direction down` | `--ratio FLOAT` for size |
| `split-window -c PATH` | add `--cwd PATH` | Same flag |
| `select-pane -t :.+` | `pane focus --direction` | Direction-based, not relative |
| `select-pane -t ID` | `pane focus ID` | |
| `select-pane -L/R/U/D` | `pane focus --direction left/right/up/down` | Direct map |
| `resize-pane -L/R/U/D N` | `pane resize --direction --amount N` | `--amount` is ratio, not cells |
| `resize-pane -x W -y H` | No direct equivalent | Herdr uses ratios not absolute |
| `swap-pane -s A -t B` | `pane swap --source-pane A --target-pane B` | |
| `swap-pane -D/U` | `pane swap --direction down/up` | |
| `move-pane -t TARGET` | `pane move --tab` or `pane move --new-tab` | |
| `kill-pane -t TARGET` | `pane close ID` | |
| `break-pane` | No direct equivalent | (moves pane to new window) |
| `join-pane -t TARGET` | `pane move --tab` | |
| `next-layout` | `pane layout` with cycle | |
| `select-layout even-horizontal` | No direct equivalent | Herdr has no layout presets |
| `display-panes` | No equivalent | Herdr shows pane IDs in borders |

## Commands — Window/Tab Management

| tmux | herdr | Notes |
|------|-------|-------|
| `new-window` | `tab create` | |
| `new-window -c PATH` | `tab create --cwd PATH` | |
| `new-window -n NAME` | `tab create --label NAME` | |
| `select-window -t :N` | `tab focus TAB_ID` | |
| `select-window -t :+1` | No direct equivalent | |
| `rename-window NAME` | `tab rename TAB_ID NAME` | |
| `kill-window -t TARGET` | `tab close TAB_ID` | |
| `next-window` / `previous-window` | No direct equivalent | |
| `link-window` / `unlink-window` | No direct equivalent | |

## Commands — Session/Workspace Management

| tmux | herdr | Notes |
|------|-------|-------|
| `new-session -s NAME` | `workspace create --label NAME` | |
| `new-session -c PATH` | `workspace create --cwd PATH` | |
| `has-session -t NAME` | `workspace list \| grep` | Script check |
| `switch-client -t SESSION` | `workspace focus WS_ID` | |
| `rename-session NAME` | `workspace rename WS_ID NAME` | |
| `kill-session -t TARGET` | `workspace close WS_ID` | |
| `list-sessions` | `workspace list` | |
| `send-keys -t SESSION` | `agent send TARGET TEXT` | If agent, else `pane send-text` |
| `send-prefix` | No equivalent | Prefix is handled by herdr |

## Commands — Display and UI

| tmux | herdr | Notes |
|------|-------|-------|
| `display-popup -wW -hH -xX -yY COMMAND` | `[[panes]] placement` | **Ambiguous** — ask user: overlay, split, or tab |
| `display-menu -T TITLE -xX -yY ITEMS` | fzf in overlay pane | **Ambiguous** — ask user: fzf vs multiple actions |
| `display-message TEXT` | `notification show TITLE --body TEXT` | Uses configured toast delivery |
| `display-message -p FORMAT` | Inline echo in script | Format string → shell string |
| `command-prompt -p PROMPT COMMAND` | `read -p` or fzf | Simple → `read`, complex → fzf |
| `confirm-before -p PROMPT COMMAND` | `read -n1 -p` | |

## Commands — Input and Output

| tmux | herdr | Notes |
|------|-------|-------|
| `send-keys -t TARGET KEYS` | `pane send-keys ID KEYS` | Key syntax differs |
| `send-keys -X KEY` | `pane send-keys ID KEY` | Copy-mode keys |
| `capture-pane -p -t TARGET` | `pane read ID --source recent-unwrapped` | |
| `capture-pane -p -S -N` | `pane read ID --lines N` | |
| `capture-pane -p -J` | `pane read ID --source recent` | Reflowed output |
| `capture-pane -p -e` | `pane read ID --ansi` | Preserve ANSI |
| `paste-buffer -t TARGET` | `pane send-text ID TEXT` | No buffer system in herdr |
| `load-buffer PATH` | Read file into var → `send-text` | |
| `save-buffer PATH` | `pane read > file` | |
| `set-buffer DATA` | Store in script variable | |
| `list-buffers` | No equivalent | |

## Commands — Configuration and Options

| tmux | herdr | Notes |
|------|-------|-------|
| `set -g @PLUGIN_OPTION VALUE` | Plugin `config.toml` key | Under `$HERDR_PLUGIN_CONFIG_DIR/` |
| `set -g OPTION VALUE` | Herdr `config.toml` | Only if herdr has equivalent |
| `set -w OPTION VALUE` | Per-workspace config | Not directly supported |
| `set-environment -g VAR VALUE` | Global env in action script | |
| `set-environment -t SESSION VAR` | `--env` on workspace create | |
| `show-options -g` | Read plugin config | |
| `source-file PATH` | Include in script | |

## Commands — Hooks and Execution

| tmux | herdr | Notes |
|------|-------|-------|
| `run-shell COMMAND` | `[[actions]]` command | Or inline in script |
| `run-shell -b COMMAND` | Background process | Use `&` or `nohup` in script |
| `if-shell CONDITION COMMAND` | Bash `if` in script | |
| `wait-for -L NAME` / `wait-for -S NAME` | `herdr wait output` / `wait agent-status` | Signal-based not supported |
| `set-hook -g HOOK COMMAND` | `[[events]]` | Limited event set |

## Commands — Keybindings

| tmux | herdr | Notes |
|------|-------|-------|
| `bind-key KEY COMMAND` | `[[keys.command]]` in herdr `config.toml` | type = `plugin_action` |
| `bind-key -n KEY COMMAND` | Direct chord in `[[keys.command]]` | No prefix needed |
| `bind-key -T TABLE KEY COMMAND` | Only one table in herdr | Copy mode not applicable |
| `unbind-key KEY` | Omit from herdr config | Override defaults by rebinding |
| `bind-key -r KEY COMMAND` | No repeat in herdr | Single-press only |

## Commands — Information

| tmux | herdr | Notes |
|------|-------|-------|
| `list-keys` | Herdr default keybindings | |
| `list-commands` | `herdr --help` | |
| `list-panes` | `pane list` | |
| `list-windows` | `tab list` | |
| `list-clients` | `status client` | |

## Other

| tmux | herdr | Notes |
|------|-------|-------|
| `choose-tree` | fzf workspace picker | |
| `choose-client` | No equivalent | |
| `copy-mode` | `pane read` | Read, not enter mode |
| `refresh-client` | `server reload-config` | |
| `clock-mode` | No equivalent | |
| `set -g status-*` | **Non-portable** | Herdr has own sidebar/theme |
| `set -g status-xxx-bg COLOUR` | Herdr `[theme]` colors | Only if herdr supports the color |
| `if -F FORMAT COMMAND` | Bash conditionals | Tmux formats not supported |

## Plugin Infrastructure

| Tmux | Herdr |
|------|-------|
| `tmux set -g @plugin-name-option value` | `$HERDR_PLUGIN_CONFIG_DIR/config.toml` |
| `tmux set -g @plugin-name-option` | TOML config key |
| `#{@plugin-name-option}` | Read from config file in script |
| `$TMUX_PANE` | `$HERDR_PANE_ID` |
| `$TMUX_SESSION_ID` | `$HERDR_WORKSPACE_ID` |
| `$TMUX_SESSION_NAME` | Workspace label |
| `$TMUX_WINDOW_INDEX` | Tab index (not exposed) |
| `$TMUX_PANE_TITLE` | Pane label |
| `tmux -V` version check | `min_herdr_version` in manifest |
| `run-shell "SCRIPT"` at load | Plugin action |
| `set-hook -a` append | Herdr `[[events]]` (separate declarations) |
| tpm (Tmux Plugin Manager) | `herdr plugin install` |

## Tmux Format Variables → Herdr Alternatives

Tmux formats like `#{pane_id}`, `#{session_name}` have equivalents in herdr env vars
or script-level lookups. There is no inline format expansion — resolve values
in the script before using them.

| tmux format | herdr replacement |
|-------------|-------------------|
| `#{pane_id}` | `$HERDR_PANE_ID` |
| `#{pane_index}` | No equivalent |
| `#{window_id}` | `$HERDR_TAB_ID` |
| `#{window_index}` | No equivalent |
| `#{session_id}` | `$HERDR_WORKSPACE_ID` (not same format) |
| `#{session_name}` | Workspace label (query at runtime) |
| `#{pane_current_path}` | `pane get ID \| jq .foreground_cwd` |

## Key Name Mapping

When porting `send-keys` or `bind-key` key names:

| tmux key | herdr key |
|----------|-----------|
| `C-` prefix | `ctrl+` prefix |
| `M-` prefix | `alt+` prefix |
| `S-` prefix | `shift+` prefix |
| `C-c` | `ctrl+c` |
| `C-m` (Enter) | `enter` |
| `Tab` | `tab` |
| `BSpace` | `backspace` |
| `Escape` | `esc` |
| `Left` / `Right` / `Up` / `Down` | Same |
| `F1`..`F12` | Same |
| `Space` | `space` |
| `n (no prefix)` | Plain key (dangerous) |

**Note:** Herdr direct plain keys (without modifier) are unsafe — they intercept typing.
Always use `prefix+key` or a modified chord like `ctrl+alt+key`. See `Keyboard` in herdr docs.
