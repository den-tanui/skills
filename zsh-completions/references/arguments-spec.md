# _arguments spec reference (from zshcompsys(1))

Each spec is one quoted word. General form: `(exclusions)optspec[explanation]:optarg:message:action`

## _arguments own options

- `-s` — enable single-letter option stacking (`-xy` = `-x -y`)
- `-w` — with `-s`, allow stacking even when options take arguments
- `-S` — don't complete options after `--`
- `-C` — modify `$curcontext` for `->state` actions
- `-A pat` — don't complete options after the first non-option argument matching `pat` (commonly `-A "-*"`)
- `-n` — set `$NORMARG` to position of first normal argument
- `-M matchspec` — match spec for option names/values (default `r:|[_-]=* r:|=*`)

Typical preamble (clap-generated): `-s -S -C` on zsh >= 5.2, else `-s -C`.

## Option forms

- `'--flag[description]'` — flag, no argument
- `'-f+[desc]:MSG:action'` — arg may be same word (`-fval`) or next word (`-f val`)
- `'-f-[desc]:MSG:action'` — arg MUST be in same word (`-fval`)
- `'--flag=[desc]:MSG:action'` — arg as `--flag=val` or `--flag val`
- `'--flag=-[desc]:MSG:action'` — arg only after `=` in same word
- `'*--flag=[desc]:MSG:action'` — repeatable option (leading `*`)
- `'(-a --long)-a[desc]'` / `'(-a --long)--long[desc]'` — put short+long in each other's exclusion list so they aren't offered twice
- `'(--json --yaml)--json[desc]'` — mutually exclusive options
- Exclusion list specials: `*` excludes rest-args, `:` excludes positionals, `-` excludes all options, numbers exclude that positional
- Prefix a spec with `!` to skip-but-not-complete it (used when re-calling `_arguments !$^global_options` in subcommand handlers)
- Multiple optargs: `'--opt:msg1:action1:msg2:action2'` — option takes two arguments
- `':*pattern:MSG:action'` — multiple args up to (and including) a word matching `pattern`; empty pattern = all remaining words

## Positional args

- `'1:MSG:action'` — first positional (required); `'1::MSG:action'` — optional
- `'::MSG:action'` — next positional, whatever number (optional with two colons)
- `'*:MSG:action'` — all remaining positionals
- `'*::MSG:action'` — also narrows `words`/`CURRENT` to normal args during the action
- `'*:::MSG:->state'` — narrows `words`/`CURRENT` to only the args covered by this spec (used for subcommand dispatch)

## Actions

- `(a b c)` — plain list of matches
- `((a\:desc1 b\:desc2))` — matches with descriptions (escape the colon)
- `_files` — files; `_files -/` — directories; `_files -g '*.json'` — glob
- `_default` — fall back to default completion
- `_guard PATTERN MSG` — complete only if input matches pattern (e.g. `_guard "[0-9]#" port`)
- `_alternative 'users:user:_users' 'hosts:host:_hosts'` — multiple match sources (specs are `tag:descr:action`; no `->state` support)
- `_values -s , 'desc' 'one[desc]' 'two[desc]:arg:(1 2 3)'` — comma-separated value lists; `-w` checks other words too, `-S` sets value/arg separator (default `=`)
- `_describe -t TAG 'group descr' array` — array elements are `'item:description'`; use `-o` when completing option names
- ` ` (single space) — no completion, just show the message
- `->state` — hand control back; `_arguments` sets `$state`, `$state_descr`, `$line`, `$context`, `$opt_args`; dispatch on `$state` in a `case`

## Escaping

- Literal colons in optnames/messages/actions must be `\:`
- Embedded single quotes in descriptions: `'\''`
- Literal `+`/`=` in option names must be quoted: `'-\+'`

## Deriving specs from --help automatically

For GNU-style tools where hand-maintaining isn't worth it, `_arguments --` parses the command's own `--help` output at completion time:

```zsh
#compdef mycmd
_mycmd() {
    _arguments -- \
        '*=FILE*:file:_files' \
        '*=DIR*:directory:_files -/' \
        '*:toggle:(yes no)'
}
_mycmd "$@"
```

- Helpspecs are `pattern:message:action`; the pattern is matched against each option's help text
- `=FILE`/`=DIR`/`=PATH` hints are handled by default; a pattern ending in `(-)` applies only directly after `=`
- `-i '(patterns)'` — ignore matching options; `-s "(pattern repl ...)"` — option aliases (e.g. derive `--disable-foo` from `--enable-foo`)
- `-l` — run `--help` in the current locale instead of `C`
- Only use when `cmd --help` is safe and fast
