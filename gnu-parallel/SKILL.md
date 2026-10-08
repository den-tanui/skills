---
name: gnu-parallel
description: >-
  Master GNU Parallel for running jobs in parallel — from the official GNU Parallel 2018 manual. Use when the user asks to parallelize commands, process input in parallel, use --pipe/--pipepart, run jobs remotely over SSH, control output/ordering/buffering, retry/fail-fast/termination, use semaphores, use profiles, debug parallel commands, or when the user mentions GNU Parallel, parallel, --pipe, --pipepart, --xargs, --joblog.
license: CC-BY-SA-4.0
---

# GNU Parallel 2018

GNU Parallel is a command-line tool for running jobs in parallel. It is written by Ole Tange,
version 2018, first edition. This skill is derived from the official GNU Parallel 2018 manual
(DOI 10.5281/zenodo.1146014, ISBN 978-1-387-50988-1, CC-BY-SA-4.0).

GNU Parallel has 6 major areas:

- **Ch 4 Input sources** — files, command line, stdin, multiple sources, linking
- **Ch 5 Build the command line** — replacement strings, positional args, xargs mode
- **Ch 6 Control the output** — tagging, ordering, buffering, saving output, CSV/TSV, SQL
- **Ch 7 Control the execution** — job count, shuffle, interactivity, timing, progress, retry, termination
- **Ch 8 Remote execution** — SSH, sshlogin, file transfer, environment
- **Ch 9 Pipe mode** — breaking stdin into blocks, processing large files

On top of that, **Ch 10 Miscellaneous features**: shebang, semaphores, informational, profiles.

The book is written as a 5-in-1 book: you can read it as a beginner, intermediate, advanced,
expert, or developer. Read this if you are level N.

---

## Quick Start — The Minimal Parallel

```bash
# Run a command on each item
parallel echo ::: 1 2 3 4 5

# Run wc on each file
parallel wc ::: example.*

# Pass values into the command anywhere with {}
parallel echo counting {} ';' wc -l {} ::: example.*

# Multiple input sources → all combinations
parallel echo ::: S M L ::: Green Red

# Read values from stdin
find example.* -print | parallel echo File

# Limit concurrency
parallel --jobs 2 sleep {} ';' echo {} done ::: 5 4 3 1 2

# Keep output order
parallel --keep-order sleep {} ';' echo {} done ::: 5 4 3 2 1

# Dry run — see the commands before executing
parallel --dry-run echo count {1} in {2} ';' wc {1} {2} \
  ::: -l -c ::: example.*
```

---

## Conventions in This Skill

- `{}` is the default replacement string (the current input item).
- `:::` separates the command line from input values.
- `-` as an input source reads stdin.
- `-a file` reads input from file.
- `::::` (four colons) separates multiple input file sources.
- `--link` links input sources, taking one item from each.
- `--plus` adds extra replacement strings (e.g. `{+/}`, `{##}`).
- `--colsep` splits input on a regex for positional replacement.
- `--header` uses the first line as column names.

---

## References

- [Input sources (ch 4)](./references/input-sources.md) — single/multiple sources, linking, separators, record delimiter, EOF value, skipping empty lines
- [Build the command line (ch 5)](./references/build-command-line.md) — replacement strings, positional args, quote, trim, respect shell, xargs
- [Control the output (ch 6)](./references/control-output.md) — tagging, dry-run, keep-order, ungroup, linebuffer, files, CSV/TSV, SQL, parset
- [Control the execution (ch 7)](./references/control-execution.md) — jobs, shuffle, interactivity, timing, progress, log, resume, termination, retry, resource limits
- [Remote execution (ch 8)](./references/remote-execution.md) — sshlogin, server groups, file transfer, working dir, ssh delay, env, verbose
- [Pipe mode (ch 9)](./references/pipe-mode.md) — block size, records, record separators, header, fixed-length, --cat, --fifo, --pipepart, --tee
- [Miscellaneous features (ch 10)](./references/miscellaneous.md) — shebang, semaphore, informational, profiles

## Templates

- [Basic command](./templates/basic-plugin.ts) — simple parallelism template
- [Pipe mode](./templates/pipe-mode.ts) — stream large files
- [Remote sshlogin](./templates/remote-execution.ts) — SSH-parallel over multiple hosts
- [Results storage](./templates/results-storage.ts) — --results, CSV, SQL

---

## The GNU Parallel 2018 Manual (full source)

This skill is based on the GNU Parallel 2018 first edition manual, copyright O. Tange,
CC-BY-SA-4.0. DOI: http://dx.doi.org/10.5281/zenodo.1146014. ISBN: 978-1-387-50988-1.
