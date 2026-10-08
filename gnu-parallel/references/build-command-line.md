# Build the command line (ch 5)

GNU Parallel normally runs commands based on a template with values from input sources inserted.

## No command means arguments are commands

```bash
parallel ::: ls 'echo foo' pwd
# Runs ls, echo foo, pwd as commands
```

The command can be a script, binary, or a Bash function (export it first):

```bash
my_func() { echo in my_func $1; }
export -f my_func
parallel my_func ::: 1 2 3
```

## Replacement strings

The 7 predefined replacement strings:

| String | Value |
|--------|-------|
| `{}` | full path (e.g. `mydir/mysubdir/myfile.myext`) |
| `{.}` | path without extension |
| `{/}` | basename with extension |
| `{//}` | dirname only |
| `{/.}` | basename without extension |
| `{#}` | job sequence number (starts at 1) |
| `{%}` | job slot number (1..n, reused when a job finishes) |

```bash
parallel echo {} ::: A/B.C
parallel echo {.} ::: A/B.C
parallel echo {/} ::: A/B.C
parallel echo {//} ::: A/B.C
parallel echo {/.} ::: A/B.C
parallel echo {#} ::: A B C
parallel -j2 echo {%} ::: A B C
```

If no replacement string is used, the default is to append `{}`:

```bash
parallel echo ::: A/B.C
# A/B.C
```

The replacement strings are **quoted** when inserted — no need to worry about quoting:

```bash
echo 'No " needed' | parallel echo {}
```

## Change the replacement strings

| String | Option |
|--------|--------|
| `{}` | `-I ,,` |
| `{.}` | `--extensionreplace ,,` |
| `{/}` | `--basenamereplace ,,` |
| `//` | `--dirnamereplace ,,` |
| `{/.}` | `--basenameextensionreplace` / `--bner ,,` |
| `{#}` | `--seqreplace ,,` |
| `{%}` | `--slotreplace ,,` |

```bash
parallel -I ,, echo ,, ::: A/B.C
parallel --extensionreplace ,, echo ,, ::: A/B.C
```

## Perl expression replacement

For anything not covered by the predefined strings:

```bash
parallel echo '{= s:\\.[^.]+$::;s:\\.[^.]+$::; =}' ::: foo.tar.gz
# foo

# Access internal functions
parallel echo Job {#} of {= '$_=total_jobs()' =} ::: {1..5}
parallel -j2 echo The slot is {= '$_=slot()' =} ::: {1..5}

# Skip a job
parallel echo {= 'if($_==3) { skip() }' =} ::: {1..5}
# 1, 2, 4, 5

# Shell quotes
parallel echo {} shell quoted is {= '$_=Q($_)' =} ::: '*/!#$'

# @arg contains input source variables
parallel echo {= 'if($arg[1]==$arg[2]) { skip() }' =} ::: {1..3} ::: {1..3}
```

Use `--parens` to replace `{=` and `=`:

```bash
parallel --parens ,,,, echo ',, s:\\.[^.]+$::;s:\\.[^.]+$::; ,,' ::: foo.tar.gz
```

Use `--rpl` to define shorthand replacement strings:

```bash
parallel --rpl '.. s:\\.[^.]+$::;s:\\.[^.]+$::;' echo '..' ::: foo.tar.gz
```

## Dynamic replacement strings

A shorthand containing matching parentheses becomes a dynamic replacement string:

```bash
# Remove string passed as argument
parallel --rpl '{%(.+?)} s/$$1$//;' echo {%.tar.gz}.zip ::: foo.tar.gz
# foo.zip

# Replace first string with second
parallel --rpl '{/(.+?)/(.*?)} s/$$1/$$2/;' echo {/tar.gz/zip} ::: foo.tar.gz
# foo.zip
```

## Positional replacement strings

With multiple input sources, access individual sources with `{number}`:

```bash
parallel echo {1} and {2} ::: A B ::: C D
# A and C, A and D, B and C, B and D
```

The positional strings can be modified with `/`, `//`, `/.`:

| String | Value |
|--------|-------|
| `{3}` | full path |
| `{3.}` | without extension |
| `{3/}` | basename |
| `{3//}` | dirname |
| `{3/.}` | basename without extension |

Negative numbers count from the end:

```bash
parallel echo 1={1} 2={2} 3={3} -1={-1} -2={-2} -3={-3} \
  ::: A B ::: C D ::: E F
```

## Positional perl expression replacement

```bash
parallel echo '{=2 s:\\.[^.]+$::;s:\\.[^.]+$::; =} {1}' \
  ::: bar ::: foo.tar.gz
# foo bar
```

If a `--rpl` shorthand starts with `{`, it can be used as a positional replacement string:

```bash
parallel --rpl '{..} s:\\.[^.]+$::;s:\\.[^.]+$::;' echo {2..} {1} \
  ::: bar ::: foo.tar.gz
```

## Input from columns

```bash
parallel --colsep '\t' echo 1={1} 2={2} :::: tsv-file.tsv
# 1=f1 2=f2, 1=A 2=B, 1=C 2=D
```

## Header-defined replacement strings

```bash
parallel --header : echo f1={f1} f2={f2} ::: f1 A B ::: f2 C D
# f1=A f2=C, f1=A f2=D, f1=B f2=C, f1=B f2=D
```

With `--colsep`:

```bash
parallel --header : --colsep '\t' echo f1={f1} f2={f2} :::: tsv-file.tsv
```

## More predefined replacement strings with --plus

`--plus` adds: `{+/}`, `{+.},` `{+..}`, `{+...}`, `{..}`, `{...}`, `{/..}`, `{/...}`, `{##}`.

```bash
parallel --plus echo {} ::: dir/sub/file.ex1.ex2.ex3
parallel --plus echo {+/}/{/} ::: dir/sub/file.ex1.ex2.ex3
parallel --plus echo {.}.{+.} ::: dir/sub/file.ex1.ex2.ex3
parallel --plus echo {##} ::: {1..5}   # total number of jobs
```

Dynamic strings in `--plus`:

| String | Bash inspiration |
|--------|---------|
| `{:-string}` | `${myvar:-myval}` — default if empty |
| `{:number}` | `${myvar:2}` — substring from number to end |
| `{:n1:n2}` | `${myvar:2:3}` — substring n1..n2 |
| `{#string}` | `${myvar#bc}` — remove prefix |
| `{%string}` | `${myvar%de}` — remove suffix |
| `{/s1/s2}` | `${myvar/def/ghi}` — replace s1 with s2 |
| `{^string}` | `${myvar^a}` — uppercase if starts with |
| `{^^string}` | `${myvar^^a}` — uppercase if contains |
| `{,string}` | `${myvar,A}` — lowercase if starts with |
| `{,,string}` | `${myvar,,A}` — lowercase if contains |

## Insert more than one argument

`-m` = multiple arguments:

```bash
cat num30000 | parallel -j 4 -m 'echo {} | wc -w'
# 23691, 1578, 1578, 1578, 1575  (arguments spread over 4+1 jobs)
```

`-X` = contexts repeated:

```bash
parallel --jobs 4 -X echo pre-{}-post ::: A B C D E F G
# pre-A-post pre-B-post, pre-C-post pre-D-post, ...
```

`-N` = fixed number of arguments:

```bash
parallel -N3 echo ::: A B C D E F G H
# A B C, D E F, G H
```

`-N0` = read one argument but insert none:

```bash
parallel -N0 echo foo ::: 1 2 3
# foo, foo, foo
```

## Quote the command line

```bash
# -q quote (use when special chars inside are a problem)
parallel -q perl -e 'print "@ARGV\n"' ::: This works

# \ quotes the critical part
parallel perl -e 'print "@ARGV\n"' ::: This works, too

# --shellquote for full-line quoting
parallel --shellquote
```

## Trim space from arguments

```bash
parallel --trim r echo pre-{}-post ::: ' A '
parallel --trim l echo pre-{}-post ::: ' A '
parallel --trim lr echo pre-{}-post ::: ' A '
```

## Respect the shell

GNU Parallel respects your shell. In zsh:

```bash
parallel echo \={} ::: zsh bash ls
```

In csh:

```bash
parallel 'set a="{}"; if( { test -d "$a" } ) echo "$a is a dir"' ::: *
```
