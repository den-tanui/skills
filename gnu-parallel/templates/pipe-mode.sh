#!/usr/bin/env bash
# Example template: GNU Parallel pipe mode for large text files
# split stdin into blocks and process each block in parallel

# Basic pipe mode: split by ~1MB blocks, run wc on each
cat large-file.txt | parallel --pipe wc

# Change block size
cat large-file.txt | parallel --pipe --block 2M wc

# Round-robin: only start --jobs instances and distribute records
cat large-file.txt | parallel --pipe -j4 --round-robin wc

# Fixed number of records per job (-N)
cat large-file.txt | parallel --pipe -N140000 wc

# Process fixed number of lines per job (-L)
cat large-file.txt | parallel --pipe -L75 wc

# Custom record separators
cat data.txt | parallel --pipe --recstart / --recend ', ' -kN1 wc

# With regex record separators
cat data.txt | parallel --pipe --regexp --recend ',_*' -kN1 wc

# Header: repeat header for each job
cat data_%header | parallel --header '(%.*\\n)*' --pipe -N3 wc

# Fixed-length records (--recend '' and --block recordsize)
cat fixedlen | parallel --pipe --header .{4} --block 3 --recend '' \
  'echo start; cat; echo'

# Programs that cannot read stdin: use --cat
cat large-file.txt | parallel --pipe --cat wc {}

# Programs that can read a FIFO: use --fifo
cat large-file.txt | parallel --pipe --fifo wc {}

# High-performance mode for seekable files: --pipepart
parallel --pipepart -a large-file.txt --block 3m wc

# Duplicate all input to every job: --tee
seq 30 | parallel -v --pipe --tee --tag grep {} ::: 4 5 6
