# File and Directory Search Patterns

These patterns demonstrate how to integrate `fzf` with modern CLI tools like `fd`, `ripgrep` (`rg`), and `bat` for high-performance file searching and previewing.

## 1. Fast File Search with `fd` and `bat`

Use `fd` to generate the list of files (respects `.gitignore`, faster than `find`), and `bat` for syntax-highlighted previews.

```bash
# Fallback to find and cat if fd/bat are missing
FINDER=${FZF_DEFAULT_COMMAND:-"fd --type f --hidden --exclude .git || find . -type f -not -path '*/\.git/*'*"}
PREVIEWER="bat --color=always --style=numbers --line-range=:500 {} 2>/dev/null || cat {} 2>/dev/null"

eval "$FINDER" | fzf --preview "$PREVIEWER" \
                     --bind 'enter:become(vim {})'
```

## 2. Interactive `ripgrep` (Search File Contents)

This is a highly advanced pattern. It disables `fzf`'s built-in fuzzy matching (`--disabled`) and instead uses the `change` event to re-run `ripgrep` every time the user types a character. This allows searching through gigabytes of files instantly.

```bash
RG_PREFIX="rg --column --line-number --no-heading --color=always --smart-case"
INITIAL_QUERY="${1:-}"

fzf --ansi --disabled --query "$INITIAL_QUERY" \
    --bind "start:reload:$RG_PREFIX {q} || true" \
    --bind "change:reload:sleep 0.1; $RG_PREFIX {q} || true" \
    --delimiter : \
    --preview 'bat --color=always {1} --highlight-line {2}' \
    --preview-window 'up,60%,border-bottom,+{2}+3/3,~3' \
    --bind 'enter:become(vim {1} +{2})'
```

## 3. Advanced `ripgrep` with Mode Switching

This pattern uses the `transform` action to toggle between "ripgrep mode" (searching file contents) and "fzf mode" (fuzzy filtering the results of the ripgrep search) using a single key binding (`CTRL-T`).

```bash
#!/usr/bin/env bash

rm -f /tmp/rg-fzf-{r,f}
RG_PREFIX="rg --column --line-number --no-heading --color=always --smart-case "
INITIAL_QUERY="${*:-}"

fzf --ansi --disabled --query "$INITIAL_QUERY" \
    --bind "start:reload:$RG_PREFIX {q}" \
    --bind "change:reload:sleep 0.1; $RG_PREFIX {q} || true" \
    --bind 'ctrl-t:transform:[[ ! $FZF_PROMPT =~ ripgrep ]] &&
      echo "rebind(change)+change-prompt(1. ripgrep> )+disable-search+transform-query:echo \{q} > /tmp/rg-fzf-f; cat /tmp/rg-fzf-r" ||
      echo "unbind(change)+change-prompt(2. fzf> )+enable-search+transform-query:echo \{q} > /tmp/rg-fzf-r; cat /tmp/rg-fzf-f"' \
    --color "hl:-1:underline,hl+:-1:underline:reverse" \
    --prompt '1. ripgrep> ' \
    --delimiter : \
    --header 'CTRL-T: Switch between ripgrep/fzf' \
    --preview 'bat --color=always {1} --highlight-line {2}' \
    --preview-window 'up,60%,border-bottom,+{2}+3/3,~3' \
    --bind 'enter:become(vim {1} +{2})'
```

## 4. Directory Navigation (cd)

Find a directory and `cd` into it. Note: Because shell scripts run in a subshell, a script cannot change the directory of the parent shell. This must be implemented as a shell function or alias in `~/.bashrc` or `~/.zshrc`.

```bash
# Put this in ~/.bashrc or ~/.zshrc
fd() {
  local dir
  dir=$(find ${1:-.} -path '*/\.*' -prune -o -type d -print 2> /dev/null | fzf +m) &&
  cd "$dir"
}
```
