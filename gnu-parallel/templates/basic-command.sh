#!/usr/bin/env bash
# Example template: basic GNU Parallel command
# Run a command on each item given after :::

# 1. Simple: run a command per item
parallel echo ::: 1 2 3 4 5

# 2. Run a command on files
parallel wc ::: example.*

# 3. Insert the input item into the command with {}
parallel echo counting {} ';' wc -l {} ::: example.*

# 4. Multiple input sources produce all combinations
parallel echo ::: S M L ::: Green Red

# 5. Read values from stdin
find example.* -print | parallel echo File

# 6. Limit concurrency
parallel --jobs 2 sleep {} ';' echo {} done ::: 5 4 3 1 2

# 7. Keep output order
parallel --keep-order sleep {} ';' echo {} done ::: 5 4 3 2 1

# 8. See the commands before running them (dry run)
parallel --dry-run echo count {1} in {2} ';' wc {1} {2} \
  ::: -l -c ::: example.*
