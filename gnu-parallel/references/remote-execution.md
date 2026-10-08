# Remote execution (ch 8)

GNU Parallel can run jobs on remote servers using SSH.

## Prerequisites

```bash
ssh $SERVER1 echo works
ssh $SERVER2 echo works
# Set up passwordless login:
ssh-keygen -t dsa; ssh-copy-id $SERVER1; ssh-copy-id $SERVER2
```

## Sshlogin

```bash
# Basic sshlogin
parallel --sshlogin $SERVER1 echo running on ::: server1
# running on server1

# Different username
parallel -S username@$SERVER1 echo running on ::: username@server1

# The special sshlogin ':' is the local machine
parallel -S : echo running on ::: the_local_machine
```

## SSH command to use

```bash
# Prepend ssh path to the server
parallel -S '/usr/bin/ssh '$SERVER1 echo custom ::: ssh

# Use --ssh
parallel --ssh /usr/bin/ssh -S $SERVER1 echo custom ::: ssh

# Or set $PARALLEL_SSH
export PARALLEL_SSH=/usr/bin/ssh
parallel -S $SERVER1 echo custom ::: ssh
```

## Multiple servers

```bash
# Multiple -S
parallel -S $SERVER1 -S $SERVER2 echo ::: running on more hosts

# Comma-separated
parallel -S $SERVER1,$SERVER2 echo ::: running on more hosts

# Newline-separated
SERVERS="`echo $SERVER1; echo $SERVER2`"
parallel -S "$SERVERS" echo ::: running on more hosts

# From a file (sshloginfile)
echo $SERVER1 > nodefile
echo /usr/bin/ssh user@$SERVER2 >> nodefile
parallel --sshloginfile nodefile echo ::: running on more hosts
# The file is re-read after each job finishes, so hosts can be added/removed

# Special: --sshloginfile .. reads from ~/.parallel/sshloginfile

# Force a specific number of CPUs on a remote host
parallel -S 4/$SERVER1 echo force {} CPUs on server ::: 4
```

## Divide servers into groups

```bash
# Group by prefix @groupname on the sshlogin
parallel --hostgroup -S @grp1/$SERVER1 -S @grp2/$SERVER2 echo {} \
  ::: run_on_grp1@grp1 run_on_grp2@grp2
# run_on_grp1, run_on_grp2

# Host in multiple groups (+, and -S limits)
parallel -S @grp1 -S @grp1+grp2/$SERVER1 -S @grp2/$SERVER2 echo {} \
  ::: run_on_grp1 also_grp1
# run_on_grp1, also_grp1

# Host group defined by the argument itself
parallel --hostgroup echo {} \
  ::: run_on_server1@$SERVER1 run_on_server2@$SERVER2
# run_on_server1, run_on_server2
```

## Transfer files

```bash
# --transferfile: transfer input file(s) to remote
echo "This is input_file" > input_file
parallel -S $SERVER1 --transferfile {} cat ::: input_file
# This is input_file

# --return: transfer result file back
parallel -S $SERVER1 --transferfile {} --return {}.out \
  cat {} ">"{}.out ::: input_file
cat input_file.out

# --cleanup: remove transferred files from remote
parallel -S $SERVER1 --transferfile {} --return {}.out --cleanup \
  cat {} ">"{}.out ::: input_file
cat input_file.out

# --trc shorthand (--transferfile {} --return foo --cleanup)
parallel -S $SERVER1 --trc {}.out cat {} ">"{}.out ::: input_file

# --basefile: transfer once before the first job
echo "common data" > common_file
parallel --basefile common_file -S $SERVER1 \
  cat common_file\; echo {} ::: foo

# Transfer relative to a directory with /./
parallel -S $server1 --transfer wc {//} ::: foo/./bar/file
```

## Working dir

```bash
# Default: remote login dir
parallel -S $SERVER1 pwd :::

# --workdir mydir: use mydir as working dir
parallel --workdir mydir -S $SERVER1 pwd :::

# ...: create working dirs under ~/.parallel/tmp on remote
parallel --workdir ... -S $SERVER1 pwd :::

# . uses current working dir (treated as relative to home if below home)
```

## Avoid overloading sshd

```bash
# Delay between jobs on the same server
parallel -S $SERVER1 --sshdelay 0.2 echo ::: 1 2 3

# Multiplex ssh connections
parallel --controlmaster -S $SERVER1 echo ::: 1 2 3
```

## Ignore hosts that are down

```bash
parallel --filter-hosts -S 173.194.32.46,$SERVER1 echo ::: bar
```

## Run the same command on all hosts

```bash
# --onall: run the command with arguments on all hosts
parallel --onall -S $SERVER1,$SERVER2 echo ::: foo bar
# foo, bar, foo, bar

# --nonall: no arguments on all hosts
parallel --nonall -S $SERVER1,$SERVER2 echo foo bar
# foo bar, foo bar

# --tag with --nonall/--onall uses the host as --tagstring
parallel --nonall --tag -S $SERVER1,$SERVER2 echo foo bar
# $SERVER1 foo bar, $SERVER2 foo bar
```

## Transfer environment variables and functions

```bash
# env_parallel: transfer all aliases, functions, variables, arrays
source `which env_parallel.bash`   # bash
source `which env_parallel.sh`     # other shells
env_parallel -S $SERVER1 'myecho $myvar' ::: green
# Joe's var is green

# --env: transfer only specific names
MYVAR='foo bar'
env_parallel --env MYVAR -S $SERVER1 echo '$MYVAR' ::: baz
# foo bar baz

# Transfer functions (Bash only)
my_func() { echo in my_func $1; }
env_parallel --env my_func -S $SERVER1 my_func ::: baz

# Record names to ignore, then transfer the rest
env_parallel --record-env
# ~/.parallel/ignored_vars lists variables to ignore (incl. $PATH, $HOME)
env_parallel --env _ -S $SERVER1 foo_func ::: copied
# aliases, variables, functions, and arrays are all copied
```

## Show what is actually run

```bash
# -vv shows the wrapped commands (useful for debugging)
parallel -vv --pipepart --block 1M wc :::: num30000
```
