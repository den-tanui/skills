# Control the output (ch 6)

GNU Parallel normally prints output from a job when it is done.

## Tag output

```bash
# Tag each output line with the argument
parallel --tag echo foo-{} ::: A B C
# A         foo-A
# B         foo-B
# C         foo-C

# Custom tag string
parallel --tagstring {}-bar echo foo-{} ::: A B C
# A-bar     foo-A
# B-bar     foo-B
# C-bar     foo-C
```

## See what is being run

```bash
# Dry run — show commands without running
parallel --dryrun echo {} ::: A B C

# Print the command before running
parallel --verbose echo {} ::: A B C
```

## Force same order as input

```bash
# --keep-order / -k: output in input order, still runs in parallel
parallel -j2 -k half_line_print ::: 4 2 1
# 4-start, 4-middle, 4-end, 2-start, ...
```

## Output before jobs complete

- `--group` (default): output postponed until the job completes
- `--ungroup / -u`: output as soon as possible — **disables --tag**
- `--linebuffer`: only outputs full lines, prevents mixing

```bash
parallel -j2 --ungroup half_line_print ::: 4 2 1
parallel -j2 --linebuffer half_line_print ::: 4 2 1
parallel -j4 -k --line-buffer 'echo {}-a;sleep {};echo {}-b' ::: 1 3 2 4
```

**Buffer on disk**: with `--group` or `--linebuffer --keep-order`, output is buffered in
temp files. If output exceeds free disk space, the disk will fill. This does *not* apply
to `--linebuffer` without `--keep-order` (buffers a single line in RAM) or `--ungroup`.

## Save output into files

```bash
# Cache output in files in /tmp (change with $TMPDIR or --tmpdir)
parallel --files echo ::: A B C
# /tmp/parXXXXX.par

# Structured results directory
parallel --results outdir echo ::: A B C
# outdir/1/A/seq, outdir/1/A/stderr, outdir/1/A/stdout, ...

# With header: directory structure uses the first value as a name
parallel --header : --results outdir echo ::: f1 A B ::: f2 C D

# Path contains a replacement string -> stdout saved in that filename
parallel --results my{1}-{2}.out echo ::: A B ::: C D

# Path ends in / -> output saved in a directory of that name
parallel --results my{1}-{2}-dir/ echo ::: A B ::: C D
```

```text
outdir/1/A/seq
outdir/1/A/stderr
outdir/1/A/stdout
outdir/1/B/seq
outdir/1/B/stderr
outdir/1/B/stdout
outdir/1/C/seq
outdir/1/C/stderr
outdir/1/C/stdout
```

## Save to CSV/TSV

If the `--results` path ends in `.csv` or `.tsv`, output is a CSV/TSV file:

```bash
parallel --results my.csv echo ::: A B ::: C D
```

```csv
Seq,Host,Starttime,JobRuntime,Send,Receive,Exitval,Signal,Command,V1,V2,Stdout,Stderr
1,:,1519688383.281,0.007,0,4,0,0,"echo A C",A,C,"A C
",...
```

## Save to an SQL base

```bash
# CSV as SQL base
parallel --sqlandworker csv:////%2Ftmp%2Flog.csv \
  seq ::: 10 ::: 12 13 14

# DBURL as table
# vendor://[[user][:password]@][host][:port]/[database[/table]
dburl=sqlite3:///%2Ftmp%2Fmydatabase
dbtableurl=$dburl/mytable
parallel --sqlandworker $dbtableurl echo ::: foo bar ::: baz quux

# Multiple workers
parallel --sqlmaster $dbtableurl echo ::: foo bar ::: baz quux
parallel --sqlworker $dbtableurl echo ::: foo bar ::: baz quux
parallel --sqlmaster +$dbtableurl echo ::: foo2 bar2 ::: baz2 quux2
```

## Save output to shell variables

`parset` sets shell variables to the output of GNU Parallel. **Important:** parset cannot
be part of a pipe and cannot read from stdin.

```bash
# Activate parset (run in a fresh shell)
env_parallel --install

# Set variables
parset myvar1,myvar2 -j2 echo ::: a b
echo $myvar1
echo $myvar2
# a
# b

# Single variable is an array
parset myarray seq {} 5 ::: 1 2 3
echo "${myarray[1]}"
# 2, 3, 4, 5

# Commands can be an array
cmd=("echo '<<Joe ...>>'" "pwd")
parset data -j2 ::: "${cmd[@]}"
```

**Workarounds** for the "cannot read from a pipe" limitation:

```bash
# Use a temporary file
seq 3 > parallel_input
parset res1,res2,res3 echo :::: parallel_input
# ...
rm parallel_input

# Or process substitution (Bash/Zsh/Ksh)
parset res echo :::: <(seq 100)
echo "${res[1]}"
echo "${res[99]}"

# Or a FIFO
mkfifo input_fifo
seq 3 > input_fifo &
parset res1,res2,res3 echo :::: input_fifo
# ...
rm input_fifo
```

## env_parset

`env_parset` works like `parset` but uses `env_parallel`, so you have access to aliases,
unexported functions, and unexported variables.
