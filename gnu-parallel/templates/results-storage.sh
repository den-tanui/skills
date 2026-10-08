#!/usr/bin/env bash
# Example template: saving GNU Parallel output to files, CSV/TSV, and SQL

# Save each job's stdout/stderr to files in a structured directory
parallel --results outdir echo ::: A B C

# With header: directory structure uses the first value as a name
parallel --header : --results outdir echo ::: f1 A B ::: f2 C D

# Results path can contain a replacement string -> stdout saved in that filename
parallel --results my{1}-{2}.out echo ::: A B ::: C D

# Results path ends in / -> output saved in a directory of that name
parallel --results my{1}-{2}-dir/ echo ::: A B ::: C D

# Save output as CSV
parallel --results my.csv echo ::: A B ::: C D

# Save to an SQL base (DBURL)
# vendor://[[user][:password]@][host][:port]/[database[/table]
dburl=sqlite3:///%2Ftmp%2Fmydatabase
dbtableurl=$dburl/mytable
parallel --sqlandworker $dbtableurl echo ::: foo bar ::: baz quux

# Multiple workers: master submits, workers execute
parallel --sqlmaster $dbtableurl echo ::: foo bar ::: baz quux
parallel --sqlworker $dbtableurl echo ::: foo bar ::: baz quux

# Use --joblog for a text log of completed jobs
parallel --joblog /tmp/log exit ::: 1 2 3 0
cat /tmp/log

# Resume: pick up where you left off
parallel --resume --joblog /tmp/log exit ::: 1 2 3 0 0 0

# Retry failed jobs
parallel --resume-failed --joblog /tmp/log exit ::: 1 2 3 0 0 0

# Retry with --retry-failed (re-runs commands from the joblog)
parallel --retry-failed --joblog /tmp/log

# Save output to shell variables (parset) — must be run in a shell, not a pipe
parset myvar1,myvar2 -j2 echo ::: a b
echo $myvar1
echo $myvar2
