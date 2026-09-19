#!/usr/bin/env python3
"""S62: line-timestamp a child's stderr so PROGRESS lines become a rate curve."""
import subprocess, sys, time

cmd = sys.argv[1:]
t0 = time.time()
p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
for raw in iter(p.stderr.readline, b''):
    line = raw.decode('utf-8', 'replace').rstrip('\n')
    print("%8.1f %s" % (time.time() - t0, line), flush=True)
p.stderr.close()
rc = p.wait()
print("%8.1f [EXIT rc=%d]" % (time.time() - t0, rc), flush=True)
