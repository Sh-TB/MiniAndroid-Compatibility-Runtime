#!/bin/bash
# S25 gate: the law battery, one test at a time (build -> run -> delete),
# because 53 test binaries (each linking the full core) exceed the 5 GB
# free-disk budget of this host. Same suites, same verdicts, sequential.
cd /home/z/my-project/miniandroid
LOG=evidence/s25/s25_testlaw_loop.log
: > "$LOG"
pass=0; fail=0; failed_names=""
while read -r t; do
    [ -z "$t" ] && continue
    if ! make -j2 "build/tests/$t" >> "$LOG" 2>&1; then
        echo "BUILD-FAIL $t" >> "$LOG"
        fail=$((fail+1)); failed_names="$failed_names $t"
        continue
    fi
    if timeout 120 "./build/tests/$t" >> "$LOG" 2>&1; then
        echo "PASS $t" >> "$LOG"
        pass=$((pass+1))
    else
        echo "FAIL $t (rc=$?)" >> "$LOG"
        fail=$((fail+1)); failed_names="$failed_names $t"
    fi
    rm -f "build/tests/$t"
done < /tmp/law_tests.txt
echo "SUMMARY pass=$pass fail=$fail failed:$failed_names" >> "$LOG"
echo "LAW_LOOP_DONE pass=$pass fail=$fail"
