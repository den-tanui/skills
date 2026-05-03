# Tmux Integration Patterns

`fzf` has deep integration with `tmux`. In older versions, this was handled by a separate `fzf-tmux` bash script. In modern `fzf` (0.53.0+), this is built directly into the `fzf` binary via the `--tmux` flag.

## 1. The `--tmux` Flag

The `--tmux` flag tells `fzf` to open in a tmux popup window instead of taking over the current terminal pane. This provides a much cleaner UX, especially for background tasks or global hotkeys.

**Syntax:**
`--tmux [center|top|bottom|left|right][,SIZE[%]][,SIZE[%]][,border-native]`

**Examples:**
```bash
# Open a popup in the center, 80% width, 80% height
fzf --tmux center,80%,80%

# Open a popup at the bottom, taking up 40% of the height
fzf --tmux bottom,40%

# Open a popup on the right side, 30% width
fzf --tmux right,30%
```

**Fallback Pattern:**
If you want to use a tmux popup when inside tmux, but fall back to a standard height-constrained window when outside tmux, specify both `--height` and `--tmux`. The `--tmux` option is silently ignored if you are not in tmux.

```bash
# Uses tmux popup if in tmux, otherwise uses 70% height
fzf --height 70% --tmux 70%
```

## 2. Global Tmux Hotkeys with Fzf

You can bind tmux keys to run shell scripts that use `fzf --tmux`.

**In `~/.tmux.conf`:**
```tmux
# Bind prefix + f to search files and open in vim
bind f display-popup -E "fd --type f | fzf --tmux center,80% --preview 'bat --color=always {}' --bind 'enter:become(vim {})'"

# Bind prefix + g to an interactive git log
bind g display-popup -w 90% -h 90% -E "git log --oneline --color=always | fzf --tmux --ansi --preview 'git show --color=always {1}'"
```
*Note: `display-popup -E` is tmux's native way to run a command in a popup. If you use `fzf --tmux` inside a script called by tmux, `fzf` will handle the popup creation itself.*

## 3. Sending Commands to Tmux Panes

A common pattern is using `fzf` in one pane to select a file or command, and then sending that command to a different tmux pane.

```bash
# Select a file and open it in the pane to the right
selected_file=$(fd --type f | fzf --tmux center,50%)

if [[ -n "$selected_file" ]]; then
  # Send the vim command to the right pane ('{right-of}')
  tmux send-keys -t '{right-of}' "vim \"$selected_file\"" C-m
  # Focus the right pane
  tmux select-pane -t '{right-of}'
fi
```

## 4. Tmux Session Switcher

A classic `fzf` script to switch between active tmux sessions.

```bash
#!/usr/bin/env bash

# Get list of sessions
session=$(tmux list-sessions -F "#{session_name}" | \
  fzf --tmux center,30%,30% \
      --header "Switch Session" \
      --reverse)

if [[ -n "$session" ]]; then
  # If we are already inside tmux, switch client
  if [[ -n "$TMUX" ]]; then
    tmux switch-client -t "$session"
  else
    # If outside tmux, attach
    tmux attach-session -t "$session"
  fi
fi
```
