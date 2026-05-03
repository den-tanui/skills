---
name: fzf
description: Comprehensive patterns and documentation for building advanced, interactive CLI tools using fzf in shell scripts.
---

# fzf Advanced Scripting Skill

This skill provides comprehensive patterns and documentation for building advanced, interactive CLI tools using `fzf`. It is optimized for AI agents writing shell scripts (bash/zsh/fish).

## Core Concepts

`fzf` is a general-purpose command-line fuzzy finder. It reads a list of items from STDIN, allows the user to filter and select items interactively, and prints the selected items to STDOUT.

### Exit Codes
Always handle `fzf` exit codes in your scripts to prevent unexpected behavior when a user cancels:
- `0`: Normal exit (match selected)
- `1`: No match
- `2`: Error
- `126`: Permission denied error from `become` action
- `127`: Invalid shell command for `become` action
- `130`: Interrupted with `CTRL-C` or `ESC`

**Pattern:**
```bash
selected=$(fzf)
exit_code=$?
if [ $exit_code -eq 130 ]; then
  echo "Cancelled"
  exit 0
elif [ $exit_code -ne 0 ]; then
  echo "Error"
  exit $exit_code
fi
```

## Environment Variables & Built-in Walkers

- `FZF_DEFAULT_COMMAND`: The default command to use when input is a tty (e.g., `export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git'`).
- `FZF_DEFAULT_OPTS`: Default options applied to every `fzf` invocation (e.g., `export FZF_DEFAULT_OPTS='--layout=reverse --inline-info'`).
- **Built-in Walkers**: Instead of `FZF_DEFAULT_COMMAND`, modern `fzf` supports built-in directory traversal:
  - `--walker file,dir,follow,hidden`
  - `--walker-root=DIR`
  - `--walker-skip=.git,node_modules`

## Key Bindings & Events (`--bind`)

The `--bind` option is the most powerful feature for scripting. It maps keys or events to actions.
Format: `--bind 'KEY:ACTION,EVENT:ACTION'`

### Common Events
- `start`: Triggered when fzf starts.
- `change`: Triggered when the query string changes.
- `focus`: Triggered when the focused item changes.
- `enter`: Triggered when the user presses Enter.

### Powerful Actions
- `execute(...)`: Runs a command without exiting fzf.
- `execute-silent(...)`: Runs a command in the background without showing output.
- `become(...)`: Replaces the current fzf process with the specified command (exec). Great for opening editors. Handles empty results and multiple selections (`{+}`) better than `vim "$(fzf)"`.
- `reload(...)`: Replaces the current input list with the output of the command.
- `change-prompt(...)`: Changes the prompt string dynamically.
- `transform(...)`: Dynamically evaluates a script to return the next action to perform.
- `unbind(...)` / `rebind(...)`: Dynamically enable or disable bindings (useful for mode switching).
- `search(...)`: Trigger an fzf search with an arbitrary query string.

**Placeholders:**
- `{}`: The current highlighted line.
- `{+}`: All selected lines (when using `-m`).
- `{q}`: The current query string.
- `{1}`, `{2}`: The 1st, 2nd field of the line (split by `--delimiter`).

**Example: Dynamic Mode Switching with Transform**
```bash
# Toggle between searching files and directories
fzf --prompt 'Files> ' \
    --header 'CTRL-T: Switch between Files/Directories' \
    --bind 'ctrl-t:transform:[[ ! $FZF_PROMPT =~ Files ]] &&
            echo "change-prompt(Files> )+reload(fd --type file)" ||
            echo "change-prompt(Directories> )+reload(fd --type directory)"'
```

## Preview Window

Use `--preview` to show details about the currently focused item.
- `--preview 'bat --color=always {}'`
- `--preview-window 'up,60%,border-bottom,+{2}+3/3,~3'` (Advanced layout: up 60%, scroll to line `{2}`, keep 3 lines of context).
- **Log Tailing**: Use `follow` to tail logs. Clear the preview window by printing `\033[2J`.
  - `--preview-window follow`
- **Image Preview**: `fzf` supports image previews via Kitty graphics protocol, iTerm2 inline images, or Sixel.

## Multi-selection

Enable with `-m` or `--multi`. Users can select multiple items with `TAB` and `SHIFT-TAB`.
When using `--bind`, use `{+}` to pass all selected items to a command.

**Pattern:**
```bash
# Delete multiple branches
git branch | fzf -m | xargs git branch -d
```

## Advanced Features

### Tmux Integration (`--tmux`)
In fzf 0.53.0+, you can use `--tmux` to open fzf in a tmux popup instead of taking over the terminal.
- `--tmux center,80%,80%` (Center popup, 80% width, 80% height)
- `--tmux bottom,40%` (Bottom pane)
- **Fallback Pattern**: `fzf --height 70% --tmux 70%` (Uses tmux popup if in tmux, otherwise falls back to height).

### HTTP Server (`--listen`)
Start an HTTP server to control fzf externally.
- `--listen=4444` (Listen on port 4444)
- Send commands: `curl localhost:4444 -d 'reload(ls)'`

### Color Themes
Customize the UI with `--color`:
- `--color 'fg:#bbccdd,bg:#334455,hl:#719872,prompt:#0099BD'`

## References

For specific use cases and copy-pasteable script templates, see the `references/` directory:
- [Git Integration](references/git-integration.md)
- [File/Directory Search](references/file-search.md)
- [Process Management](references/process-management.md)
- [Custom Completion](references/custom-completion.md)
- [Tmux Scripts](references/tmux-scripts.md)
