# Control the execution (ch 7)

GNU Parallel starts one job per CPU core in parallel and finishes when all jobs are done.

## Number of simultaneous jobs

```bash
# -j / --jobs: number of parallel jobs
parallel --jobs 2 sleep {} ';' echo {} done ::: 5 4 3 1 2

# --jobs 0: run as many as possible
parallel -N0 --jobs 0 sleep 1 :::: num128

# Jobs file (re-read when a job finishes)
echo 50% > my_jobs
parallel -N0 --jobs my_jobs sleep 1 :::: num128 &
sleep 1
echo 0 > my_jobs
wait

# Use CPUs instead of cores
parallel --use-cpus-instead-of-cores -N0 sleep 1 :::: num8
```

## Shuffle job order

```bash
parallel --shuf echo ::: 1 2 3 ::: a b c ::: A B C
# All combinations, different order each run
```

## Interactivity

```bash
# Ask before each job
parallel --interactive echo ::: 1 2 3
# echo 1 ?...y  -> 1
# echo 2 ?...n
# echo 3 ?...y  -> 3

# Interactive tty programs (emacs, vi)
parallel --tty emacs ::: file1 file2 file3
parallel -X --tty vi ::: file1 file2 file3
```

## A terminal for every job

```bash
seq 10 20 | parallel --tmux 'echo start {}; sleep {}; echo done {}'
# attach with: tmux -S /tmp/tmsrPrO0 attach

# Each job in its own pane
parallel --tmuxpane --fg \
  'echo start {}; sleep {}; echo done {}' ::: 10 11 12 13 14 15 16 17
```

## Timing

```bash
# Delay between job starts
parallel --delay 2.5 echo Starting {}\;date ::: 1 2 3

# Timeout per job (accuracy is 2 seconds)
parallel --timeout 4.1 sleep {} ';' echo {} ::: 2 4 6 8
# 2, 4   (jobs 6 and 8 exceed 4.1s)

# Kill jobs slower than 200% of median runtime
parallel --timeout 200% sleep {} ';' echo {} ::: 2.1 2.2 3 7 2.3
# 2.1, 2.2, 3, 2.3  (7 was too slow)
```

## Progress information

```bash
# ETA estimate
parallel --eta sleep ::: 1 3 2 2 1 3 3 2 1

# Progress bar
parallel --progress sleep ::: 1 3 2 2 1 3 3 2 1
parallel --bar sleep ::: 1 3 2 2 1 3 3 2 1

# Graphical progress bar (zenity)
seq 1000 | parallel -j10 --bar '(echo -n {};sleep 0.1)' \
  2> >(zenity --progress --auto-kill --auto-close)
```

## Logfile

```bash
parallel --joblog /tmp/log exit ::: 1 2 3 0
cat /tmp/log
# Seq Host Starttime Runtime Send Receive Exitval Signal Command
# 1   :   ...       0.008   0     0       1       0     exit 1
# 2   :   ...       0.013   0     0       2       0     exit 2
# 3   :   ...       0.013   0     0       3       0     exit 3
# 4   :   ...       0.003   0     0       0       0     exit 0
```

## Resume jobs

```bash
# Run once
parallel --joblog /tmp/log exit ::: 1 2 3 0
cat /tmp/log

# Resume: pick up where it left off
parallel --resume --joblog /tmp/log exit ::: 1 2 3 0 0 0
cat /tmp/log
# seq 1..3 keep same start times; new jobs 5,6 added

# Resume only failed jobs
parallel --resume-failed --joblog /tmp/log exit ::: 1 2 3 0 0 0

# Retry failed jobs (ignores command line, reads joblog)
parallel --retry-failed --joblog /tmp/log
```

## Termination

### Unconditional termination

By default GNU Parallel waits for all jobs to finish. TERM signal = stop spawning new jobs
and wait for remaining jobs. Second TERM = kill all running jobs and exit.

### Termination dependent on job status

```bash
# --halt soon,fail=1: stop spawning new jobs when a job fails
parallel -j2 --halt soon,fail=1 echo {}\; exit {} ::: 0 0 1 2 3
# 0, 0, 1, then "This job failed", waiting for 1 job to finish

# --halt now,fail=1: kill running jobs immediately
parallel -j2 --halt now,fail=1 echo {}\; exit {} ::: 0 0 1 2 3
# 0, 0, 1, then "This job failed", no waiting

# --halt soon,fail=20%: percentage of jobs must fail first
parallel -j2 --halt soon,fail=20% echo {} \; exit {} \
  ::: 0 1 2 3 4 5 6 7 8 9

# --halt now,success=1: finish as soon as first job succeeds
parallel -j2 --halt now,success=1 echo {} \; exit {} ::: 1 2 3 0 4 5 6
# 1, 2, 3, 0, then "This job succeeded"

# --halt now,done=3: first 3 jobs complete
parallel -j2 --halt now,done=3 sleep {} \;echo {} \; exit {} \
  ::: 1 2 3 0 4 5 6
```

## Retry failing commands

```bash
parallel -k --retries 3 \
  'echo tried {} >>/tmp/runs; echo completed {}; exit {}' ::: 1 2 0
# tried 1, 2, 1, 2, 1, 2, 0  (jobs 1,2 retried 3x; 0 succeeded so no retry)
```

## Termination signals

`--termseq` controls the signal sequence used when killing children:

```bash
# Default: TERM,200ms, TERM,100ms, TERM,50ms, KILL,25ms
echo | parallel -u --timeout 1 show_signals
# Got TERM, Got TERM, Got TERM

# Custom sequence
echo | parallel --termseq INT,200,TERM,100,KILL,25 \
  -u --timeout 1 show_signals
# Got INT, Got TERM  (SIGKILL cannot be caught)
```

## Limit the resources

```bash
# Nice value
parallel --nice 17 echo this is being run with nice -n ::: 17

# Load check
parallel --load 100% echo load is less than {} job per CPU ::: 1

# No swap
parallel --noswap echo the system is not swapping ::: now

# Memory check (kills youngest job if free memory falls below 50% of the size)
parallel --memfree 1G --retries 5 echo More than 1 GB is ::: free

# Custom limitation via --limit
# A program that returns:
#   0 = below limit, start another job
#   1 = over limit, start no jobs
#   2 = way over limit, kill youngest job
parallel --limit "io 10" echo ::: less than 10% disk I/O
parallel --limit "mem 10g" echo ::: more than 10G free
parallel --limit "load 3" echo ::: less than 3 procs running
```

**Predefined commands for `--limit`**:

| Command | Meaning |
|---------|---------|
| `io n` | I/O limit 0-100 (n = saturate n% of disk) |
| `mem n` | Memory limit (like `--memfree`) |
| `load n` | Load limit (like `--load`) |
