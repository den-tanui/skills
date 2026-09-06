---
name: zsh-completions
description: Write a zsh completion script (_cmd) for a CLI tool from its --help output or man page. Use when the user asks to create, generate, or improve zsh completions for a command.
---

# Writing zsh completions from help text or a man page

## Workflow

1. **Check for built-in generation first.** Many CLIs emit their own zsh completions — prefer these over hand-writing:
   - `cmd completion zsh` / `cmd completions zsh` / `cmd generate-completion zsh`
   - Cobra (Go): `cmd completion zsh`; hidden `cmd __complete` protocol exists
   - clap (Rust): often ships a `completions` subcommand or build-time generation
   - yargs (Node): `cmd completion`
   If one exists, suggest installing its output instead of writing a static file.

2. **Gather the interface.** Run the tool and read the docs:
   - `cmd --help` (and `cmd <sub> --help` for every subcommand, recursively)
   - `man cmd` / `man cmd-<sub>` for flags the help hides
   - Record: subcommands (+ descriptions), flags (short/long, whether they take args, optional vs required args, repeatable, mutually exclusive), positional args, and value types (file, dir, enum list, number).

3. **Write the file** using the skeleton below. Consult `references/arguments-spec.md` for the full `_arguments` spec syntax, `references/patterns.md` for dynamic-completion wrapper patterns, and `references/testing.md` for testing and debugging.

4. **Install & test:**
   - File must be named `_<cmd>` (underscore prefix) in a directory on `$fpath` (e.g. `/usr/share/zsh/site-functions`, `~/.zfunc`, or a zinit completions dir).
   - First line must be `#compdef <cmd>`.
   - Reload: `rm -f ~/.zcompdump*(N) && autoload -U compinit && compinit`
   - Test interactively: `cmd <TAB>`, `cmd --<TAB>`, `cmd sub --flag <TAB>`.
   - See `references/testing.md` for debugging widgets (`_complete_help`, `_complete_debug`), isolated test shells, scripted testing with zpty, and a full test-case checklist.

## File skeleton (static, _arguments-based)

This is the clap-generated style used by real completions like `_tree-sitter` and `_sk`:

```zsh
#compdef mycmd

autoload -U is-at-least

_mycmd() {
    typeset -A opt_args
    typeset -a _arguments_options
    local ret=1

    if is-at-least 5.2; then
        _arguments_options=(-s -S -C)
    else
        _arguments_options=(-s -C)
    fi

    local context curcontext="$curcontext" state line
    _arguments "${_arguments_options[@]}" : \
        '-h[Print help]' \
        '--help[Print help]' \
        '-v[Verbose output]' \
        '--config=[Path to config file]:FILE:_files' \
        "::: :_mycmd_commands" \
        "*::: :->mycmd" \
        && ret=0

    case $state in
    (mycmd)
        words=($line[1] "${words[@]}")
        (( CURRENT += 1 ))
        curcontext="${curcontext%:*:*}:mycmd-command-$line[1]:"
        case $line[1] in
        (serve)
            _arguments "${_arguments_options[@]}" : \
                '-p+[Port to listen on]:PORT:_guard "[0-9]#" port' \
                '--port=[Port to listen on]:PORT:_guard "[0-9]#" port' \
                '(-d --detach)-d[Run in background]' \
                '(-d --detach)--detach[Run in background]' \
                && ret=0
            ;;
        (add)
            _arguments "${_arguments_options[@]}" : \
                '*:file:_files' \
                && ret=0
            ;;
        esac
        ;;
    esac
    return ret
}

(( $+functions[_mycmd_commands] )) ||
_mycmd_commands() {
    local commands; commands=(
        'serve:Start the server'
        'add:Add an item'
    )
    _describe -t commands 'mycmd commands' commands "$@"
}

_mycmd "$@"
```

## Conventions checklist

- [ ] Filename `_<cmd>`, first line `#compdef <cmd>`
- [ ] End with `_mycmd "$@"` (or `compdef _mycmd mycmd`) so it works both autoloaded and sourced
- [ ] Every flag from `--help` and the man page is present, with its description
- [ ] Short/long pairs exclude each other; conflicting options exclude each other
- [ ] Options taking values use the right arg form (`+`, `=`, `=-`) and a typed action (`_files`, enum list, `_guard`)
- [ ] Repeatable options marked with leading `*`
- [ ] Subcommands listed via `_describe` with descriptions; each subcommand gets its own `_arguments` block
- [ ] `-h/--help` (and `-V/--version` if present) always included
