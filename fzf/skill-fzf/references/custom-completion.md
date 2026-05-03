# Custom Completion Patterns

`fzf` can be used to create powerful custom tab-completion scripts for bash and zsh.

## 1. Bash Completion Wrapper

You can use `fzf` to wrap existing bash completion or create entirely new completion logic.

```bash
# Example: Custom completion for a hypothetical 'mycli' command
_mycli_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Generate options dynamically
    opts=$(echo -e "start\nstop\nrestart\nstatus\nlogs")

    # Use fzf for completion if the user presses **<TAB>
    if [[ "$cur" == ** ]]; then
        # Remove the ** from the current word
        local prefix="${cur%**}"
        
        # Run fzf and capture the result
        local selected=$(echo "$opts" | fzf --select-1 --query="$prefix" --height=40% --reverse)
        
        if [[ -n "$selected" ]]; then
            COMPREPLY=( "$selected" )
        fi
    else
        # Standard bash completion fallback
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    fi
}

complete -F _mycli_completion mycli
```

## 2. Zsh Completion with `fzf-tab`

For Zsh, the community standard is to use the `fzf-tab` plugin, which replaces zsh's default completion menu with `fzf`.

If you are writing a script that configures a user's environment, you can configure `fzf-tab` previews:

```zsh
# ~/.zshrc configuration for fzf-tab
# Preview directory contents when completing cd
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always $realpath'

# Preview file contents when completing cat/bat/vim
zstyle ':fzf-tab:complete:(cat|bat|vim):*' fzf-preview 'bat --color=always $realpath'

# Preview systemd unit status
zstyle ':fzf-tab:complete:systemctl-*:*' fzf-preview 'SYSTEMD_COLORS=1 systemctl status $word'
```

## 3. Fzf's Built-in `**` Completion

`fzf` comes with built-in completion for bash and zsh that triggers when you type `**` and press `TAB`.

- `vim **<TAB>` -> fuzzy find files
- `cd **<TAB>` -> fuzzy find directories
- `kill -9 **<TAB>` -> fuzzy find processes
- `ssh **<TAB>` -> fuzzy find hosts from `~/.ssh/config`

When writing scripts, you generally don't need to implement this yourself, as sourcing `fzf`'s completion script (`/usr/share/fzf/completion.bash` or similar) handles it automatically.
