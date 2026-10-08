# Pipe mode (ch 9)

Instead of putting values in a command template, GNU Parallel passes stdin to commands.

```text
command_A | command_B | command_C
# command_B is slow -> speed it up by running many instances in parallel
```

## Block size

By default, GNU Parallel reads a block of ~1 MB, finds the closest record, and passes it:

```bash
cat num1000000 | parallel --pipe wc
# ~1MB blocks, full lines only

# Change block size
cat num1000000 | parallel --pipe --block 2M wc

# --round-robin: start --jobs instances, distribute records
cat num1000000 | parallel --pipe -j4 --round-robin wc

# --keep-order with --round-robin: strict order
cat num1000000 | parallel --pipe -j4 --keep-order --round-robin wc
```

## Records

```bash
# -N: read N records at a time
cat num1000000 | parallel --pipe -N140000 wc

# -L: process at least N lines at a time
cat num1000000 | parallel --pipe -L75 wc
```

## Record separators

`--recstart` (record start), `--recend` (record end). Default: `--recend '\n'`, `--recstart ""`.

If both are given, the record only splits if recend is immediately followed by recstart:

```bash
echo /foo, bar/, /baz, qux/, | \
  parallel -kN1 --recend ', ' --pipe echo JOB{#}\;cat\;echo END
# JOB1 /foo, END  (the separator is included in the record)
# JOB2 bar/, END
# JOB3 /baz, END
# JOB4 qux/, END

# With --recstart set to "/"
echo /foo, bar/, /baz, qux/, | \
  parallel -kN1 --recstart / --pipe echo JOB{#}\;cat\;echo END
# JOB1 /foo, barEND
# JOB2 /, END
# JOB3 /baz, quxEND
# JOB4 /, END

# Both set
echo /foo, bar/, /baz, qux/, | \
  parallel -kN1 --recend ', ' --recstart / --pipe \
  echo JOB{#}\;cat\;echo END
# JOB1 /foo, bar/, END
# JOB2 /baz, qux/, END
```

With `--regexp`, recend and recstart are regular expressions:

```bash
echo foo,bar,_baz,__qux | \
  parallel -kN1 --regexp --recend ',_*' --pipe \
  echo JOB{#}\;cat\;echo END
# JOB1 fooEND
# JOB2 barEND
# JOB3 bazEND
# JOB4 quxEND
```

Remove record separators with `--remove-rec-sep` / `--rrs`:

```bash
echo foo,bar,_baz,__qux | \
  parallel -kN1 --rrs --regexp --recend ',_*' --pipe \
  echo JOB{#}\;cat\;echo END
# JOB1 fooEND
# JOB2 barEND
# JOB3 bazEND
# JOB4 quxEND
```

## Header

```bash
cat num_%header | \
  parallel --header '(%.*\\n)*' --pipe -N3 echo JOB{#}\;cat
# JOB1 %head1 %head2 1 2 3
# JOB2 %head1 %head2 4 5 6
# JOB3 %head1 %head2 7 8 9
# JOB4 %head1 %head2 10

# Or specify header line count: --header 2
```

## Fixed-length records

```bash
# 4-byte header, 3-byte record size
cat fixedlen | parallel --pipe --header .{4} --block 3 --recend '' \
  'echo start; cat; echo'
# start HHHHAAA start
# start HHHHCCC start
# start HHHHBBB start
```

## Programs not reading from stdin

### --cat

Creates a temporary file for the command:

```bash
cat num1000000 | parallel --pipe --cat wc {}
# GNU Parallel creates /tmp/parXXXXX, puts a chunk in each, runs wc, then removes them
```

### --fifo

FIFO/named pipe, avoids disk writes:

```bash
cat num1000000 | parallel --pipe --fifo wc {}
# Faster than --cat, but the program must read the whole file from start to finish
```

## Use --pipepart for high performance

`--pipe` maxes out at ~500 MB/s. `--pipepart` delivers >5 GB/s but has limitations:

- Input must be a normal file or block device (not a pipe/fifo)
- Given by `-a` or `::::`
- `-L/-l/-N` do not work
- `--recend`/`--recstart` do work

```bash
# Basic
parallel --pipepart -a num1000000 --block 3m wc

# Negative block = number of blocks per job slot
parallel --pipepart -a num1000000 --block -3 -j5 wc

# With --keep-order for ordered output
```

## Duplicate all input using --tee

```bash
seq 30 | parallel -v --pipe --tee --tag grep {} ::: 4 5 6
# 4 grep 4, 4 4, 4 14
# 5 grep 5, 5 5, 5 15
# 6 grep 6, 6 6, 6 16
```
