# Input sources (ch 4)

GNU Parallel reads input from input sources. These can be files, the command line, and stdin.

## Single input source

```bash
# From the command line
parallel echo ::: A B C

# From a file
parallel -a abc-file echo

# From stdin
cat abc-file | parallel echo

# From a FIFO
mkfifo myfifo
cat abc-file > myfifo &
parallel -a myfifo echo
rm myfifo

# From command substitution (Bash/Zsh/Ksh)
parallel echo :::: <(cat abc-file)
```

## Multiple input sources

```bash
# Multiple values on the command line -> all combinations
parallel echo ::: A B C ::: D E F

# From files
parallel -a abc-file -a def-file echo

# Stdin as one of the sources
cat abc-file | parallel -a - -a def-file echo
cat abc-file | parallel echo :::: - def-file

# Mix ::: and ::::
parallel echo ::: A B C :::: def-file
```

**Link arguments from input sources** — `--link` takes one item from each source in order:

```bash
parallel --link echo ::: A B C ::: D E F
# A D, B E, C F  (C is dropped if shorter)
```

`:::+` and `::::+` link the *previous* input source to this one:

```bash
parallel echo :::: abc-file :::+ G H I :::: def-file
# A G D, A G E, A G F, B H D, ...
```

If the linked source is too short, the rest is ignored:

```bash
parallel echo ::: A B C D E :::+ F G
# A F, B G
```

## Change the argument separator

```bash
# Custom argument separator
parallel --arg-sep ,, echo ,, A B C :::: def-file

# Custom argument file separator
parallel --arg-file-sep // echo ::: A B C // def-file
```

## Change the record delimiter

By default each line is one record (`\n`). Change with `-d`:

```bash
# Underscore separator
parallel -d _ echo :::: abc_-file

# NUL separator
parallel -d '\0' echo :::: abc0-file
parallel -0 echo :::: abc0-file   # shorthand for -d '\0'
```

## End-of-file value

```bash
parallel -E stop echo ::: A B stop C D
# A, B  (stops reading at "stop")
```

## Skipping empty lines

```bash
(echo 1; echo; echo 2) | parallel --no-run-if-empty echo
# 1, 2 (empty line skipped)
```

---

## Reference table

| Syntax | Meaning |
|--------|---------|
| `parallel cmd ::: a b c` | values on command line |
| `parallel -a file cmd` | read values from file |
| `cat f \| parallel cmd` | read values from stdin |
| `parallel cmd :::: f1 f2` | read from multiple files |
| `parallel cmd ::: - f2` or `:::: - f2` | `-` means stdin |
| `parallel --link cmd ::: a ::: b` | one item from each source |
| `parallel :::+ cmd :::: a ::: b` | link previous source to this one |
| `parallel -d SEP cmd :::: f` | custom record delimiter |
| `parallel -0 cmd :::: f` | NUL-delimited (shorthand `-d '\0'`) |
| `parallel -E val cmd :::: f` | stop at EOF value |
| `parallel --no-run-if-empty cmd :::: f` | skip empty lines |
