# Miscellaneous features (ch 10)

## Shebang

### Input data and parallel command in the same file

```bash
#!/usr/bin/parallel --shebang -r echo

foo
bar
baz
# Output: foo, bar, baz (order may vary)
```

### Parallelize existing scripts with --shebang-wrap

```bash
#!/usr/bin/parallel --shebang-wrap /usr/bin/perl
print "@ARGV\n";
```

Run as: `perl_echo foo bar` — output in parallel.

**Language examples:**

```bash
# Perl
#!/usr/bin/parallel --shebang-wrap /usr/bin/perl
print "Arguments @ARGV\n";

# Python
#!/usr/bin/parallel --shebang-wrap /usr/bin/python
import sys
print('Arguments', str(sys.argv))

# Bash/sh/zsh/Korn
#!/usr/bin/parallel --shebang-wrap /bin/bash
echo Arguments "$@"

# csh/tcsh
#!/usr/bin/parallel --shebang-wrap /bin/csh
echo Arguments "$argv"

# Tcl
#!/usr/bin/parallel --shebang-wrap /usr/bin/tclsh
puts "Arguments $argv"

# R
#!/usr/bin/parallel --shebang-wrap /usr/bin/Rscript --vanilla --slave
args <- commandArgs(trailingOnly = TRUE)
print(paste("Arguments ", args))

# GNUplot
#!/usr/bin/parallel --shebang-wrap ARG={} /usr/bin/gnuplot
print "Arguments", system('echo $ARG')

# Ruby
#!/usr/bin/parallel --shebang-wrap /usr/bin/ruby
print "Arguments "; puts ARGV

# Octave
#!/usr/bin/parallel --shebang-wrap /usr/bin/octave
printf ("Arguments");
arg_list = argv();
for i = 1:nargin, printf(" %s", arg_list{i}); endfor, printf("\n");

# Common LISP
#!/usr/bin/parallel --shebang-wrap /usr/bin/clisp
(format t "~&~S~&" 'Arguments)
(format t "~&~S~&" *args*)

# PHP
#!/usr/bin/parallel --shebang-wrap /usr/bin/php
<?php
echo "Arguments";
foreach(array_slice($argv,1) as $v) { echo " $v"; }
echo "\n";
?>

# Node.js
#!/usr/bin/parallel --shebang-wrap /usr/bin/node
var myArgs = process.argv.slice(2);
console.log('Arguments ', myArgs);

# LUA
#!/usr/bin/parallel --shebang-wrap /usr/bin/lua
io.write "Arguments"
for a = 1, #arg do io.write(" "), io.write(arg[a]) end
print("")

# C#
#!/usr/bin/parallel --shebang-wrap ARGV={} /usr/bin/csharp
var argv = Environment.GetEnvironmentVariable("ARGV");
print("Arguments "+argv);
```

## Semaphore

GNU Parallel can work as a counting semaphore — like a row of toilets:

```bash
# Alias for parallel --semaphore
sem
```

- `sem --fg`: follow a person, wait until available, stay with them, exit when done
- `sem --wait`: wait for all sems to finish
- No queue discipline (next person chosen randomly)
- `-j` sets the number of "toilets"

### Mutex (single toilet)

```bash
# Run in background
sem 'sleep 1; echo The first finished' && \
  echo The first is now running in the background && \
  sem 'sleep 1; echo The second finished' && \
  echo The second is now running in the background
sem --wait
```

### Named semaphore

```bash
sem --id my_id -u 'echo First started; sleep 10; echo First done'
# In another terminal:
sem --id my_id -u 'echo Second started; sleep 10; echo Second done'
```

### Counting semaphore

```bash
sem --jobs 3 --id my_id -u 'echo Start 1; sleep 5; echo 1 done' && \
  sem --jobs 3 --id my_id -u 'echo Start 2; sleep 6; echo 2 done' && \
  sem --jobs 3 --id my_id -u 'echo Start 3; sleep 7; echo 3 done' && \
  sem --jobs 3 --id my_id -u 'echo Start 4; sleep 8; echo 4 done' && \
  sem --wait --id my_id
```

### Semaphore with timeout

```bash
sem --id foo -u 'echo Slow started; sleep 5; echo Slow ended' && \
  sem --id foo --semaphoretimeout 1 'echo Forced running after 1 sec' && \
  sem --id foo --semaphoretimeout -2 'echo Give up after 2 secs'
sem --id foo --wait
# Slow started
# Warning: Semaphore timed out. Stealing the semaphore.
# Forced running after 1 sec
# Warning: Semaphore timed out. Exiting.
# Slow ended
# (The "Give up" was not run)
```

## Informational

```bash
# --help
parallel --help

# --version
parallel --version
# GNU parallel 20160323
# Copyright (C) 2007-2017 Ole Tange and Free Software Foundation, Inc.

# --minversion
parallel --minversion 20130722 && echo Your version is at least 20130722.

# --citation
parallel --citation

# --max-line-length-allowed
parallel --max-line-length-allowed
# 131071

# --number-of-cpus / --number-of-cores
parallel --number-of-cpus
parallel --number-of-cores
```

## Profiles

```bash
# System-wide defaults: /etc/parallel/config
# User defaults: ~/.parallel/config

# Named profile
echo '--nice 17' > ~/.parallel/nicetimeout
echo '--timeout 300%' >> ~/.parallel/nicetimeout
parallel --profile nicetimeout echo ::: A B C

# Combine profiles
echo '-vv --dry-run' > ~/.parallel/dryverbose
parallel --profile dryverbose --profile nicetimeout echo ::: A B C
```
