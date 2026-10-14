#!/usr/bin/env python3
"""cont46_daemon.py — run a shell command as a double-fork daemon so it
survives the tool session's process-group cleanup.
Usage: cont46_daemon.py <logfile> <command...>
"""
import os, sys, subprocess

log = sys.argv[1]
cmd = sys.argv[2:]
logfd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)

pid = os.fork()
if pid == 0:
    os.setsid()
    pid2 = os.fork()
    if pid2 == 0:
        os.dup2(logfd, 1)
        os.dup2(logfd, 2)
        os.close(0)
        fd = os.open('/dev/null', os.O_RDONLY)
        os.dup2(fd, 0)
        os.execvp(cmd[0], cmd)
    os._exit(0)
else:
    os.waitpid(pid, 0)
    print(f"daemon pid={pid} log={log}")
