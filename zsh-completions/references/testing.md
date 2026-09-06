# Testing zsh completions

## Quick checks

- Syntax check without running: `zsh -n _mycmd`
- Isolated test shell that doesn't touch your interactive config:
  ```zsh
  env -i HOME="$HOME" TERM="$TERM" PATH="$PATH" zsh -f
  fpath=(/path/to/completions $fpath)
  autoload -U compinit && compinit -d /tmp/zcompdump-test
  ```
  `-d /tmp/zcompdump-test` avoids clobbering your real dump file.
- After edits, reload: `rm -f ~/.zcompdump*(N) && compinit` (or restart the test shell — the dump caches function lookups)
- Verify the function got picked up: `whence -v _mycmd` and `print ${_comps[mycmd]}`

## Interactive debugging

- Exercise the main paths: `cmd <TAB>`, `cmd -<TAB>`, `cmd --<TAB>`, `cmd sub <TAB>`, `cmd sub --flag <TAB>`, `cmd --flag=<TAB>`, `cmd sub arg1 <TAB>`
- Show descriptions and groups: `zstyle ':completion:*' verbose yes` and `zstyle ':completion:*' group-name ''`
- **Ctrl-x h** (`_complete_help`) — press instead of TAB during completion; lists the tags, contexts, and styles in effect. First stop when matches don't appear
- **Ctrl-x ?** (`_complete_debug`) — performs the completion and writes a numbered trace to a temp file (`${TMPPREFIX}*`); use for "why isn't my spec matching"
- Trace just your function: `functions -T _mycmd` enables xtrace for it (`functions +T _mycmd` to stop); watch stderr while completing

## Common failure modes

- File not named `_cmd`, or missing `#compdef` as the very first line → never autoloaded
- Stale `.zcompdump` → old version keeps loading after edits
- `_arguments` chain returns non-zero with no matches → check `&& ret=0` chaining and that the `case $state` dispatch actually runs
- Unescaped colons in descriptions silently break specs
- Missing `*::: :->state` spec → subcommand arguments never dispatch
- Trailing `\` continuation followed by a blank line or comment → parse error

## Automated / scripted testing

No official unit-test framework exists, but these approaches work:

- **capture.zsh** (Valodim/zsh-capture-completion) — zpty-based script that runs a real completion in a pseudo-terminal and dumps the candidate list; usable in CI:
  `zsh capture.zsh 'mycmd --'` prints the matches compadd would offer
- **zpty harness** — the same technique zsh's own test suite uses (`zsh/Test/comptest`, `Y01completion.ztst`): spawn `zpty zsh -f`, feed keystrokes (`mycmd --\t`), read back the listing and assert on it
- **Assert on internals** — call the completion function in a harness and inspect `$state`, `$line`, `${(k)opt_args}` to verify parsing without a tty

## Test-case checklist

- [ ] Bare `cmd <TAB>` lists subcommands with descriptions
- [ ] `cmd -<TAB>` and `cmd --<TAB>` offer short/long flags
- [ ] Flag with value: `cmd --config <TAB>` completes files; `cmd --mode <TAB>` completes the enum
- [ ] `--flag=<TAB>` (same-word) form works for `=` options
- [ ] Used flags aren't re-offered; repeatable (`*`) flags are
- [ ] Mutually exclusive flags disappear once their rival is on the line
- [ ] Each subcommand's own flags complete after `cmd sub <TAB>`
- [ ] Positionals complete with the right type (files, dirs, nothing)
- [ ] Options after `--` are not offered (with `-S`)
- [ ] Works both sourced directly and autoloaded from `$fpath`
