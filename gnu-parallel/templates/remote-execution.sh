#!/usr/bin/env bash
# Example template: GNU Parallel remote execution over SSH

SERVER1=server.example.com
SERVER2=server2.example.net

# Ensure passwordless SSH works
# ssh-keygen -t dsa; ssh-copy-id $SERVER1; ssh-copy-id $SERVER2

# Basic remote command
parallel --sshlogin $SERVER1 echo running on ::: server1

# Different username
parallel -S username@$SERVER1 echo running on ::: username@server1

# The special sshlogin ':' is the local machine
parallel -S : echo running on ::: the_local_machine

# Multiple servers
parallel -S $SERVER1 -S $SERVER2 echo ::: running on more hosts

# From a file (sshloginfile)
echo $SERVER1 > nodefile
echo /usr/bin/ssh user@$SERVER2 >> nodefile
parallel --sshloginfile nodefile echo ::: running on more hosts

# Force a specific number of CPUs on a remote host
parallel -S 4/$SERVER1 echo force {} CPUs on server ::: 4

# Server groups
parallel --hostgroup -S @grp1/$SERVER1 -S @grp2/$SERVER2 echo {} \
  ::: run_on_grp1@grp1 run_on_grp2@grp2

# Transfer files to the remote host before running
echo "This is input_file" > input_file
parallel -S $SERVER1 --transferfile {} cat ::: input_file

# Transfer, return result, cleanup (shorthand: --trc)
parallel -S $SERVER1 --trc {}.out cat {} ">"{}.out ::: input_file
cat input_file.out

# Base file transferred before the first job
echo "common data" > common_file
parallel --basefile common_file -S $SERVER1 \
  cat common_file\; echo {} ::: foo

# Avoid overloading sshd
parallel -S $SERVER1 --sshdelay 0.2 echo ::: 1 2 3
parallel --controlmaster -S $SERVER1 echo ::: 1 2 3

# Ignore hosts that are down
parallel --filter-hosts -S 173.194.32.46,$SERVER1 echo ::: bar

# Run the same command on all hosts
parallel --onall -S $SERVER1,$SERVER2 echo ::: foo bar

# Run with no arguments on all hosts
parallel --nonall -S $SERVER1,$SERVER2 echo foo bar

# Transfer environment variables and functions
alias myecho=echo
myvar="Joe's var is"
env_parallel -S $SERVER1 'myecho $myvar' ::: green

# Transfer specific variables/functions with --env
MYVAR='foo bar'
env_parallel --env MYVAR -S $SERVER1 echo '$MYVAR' ::: baz
