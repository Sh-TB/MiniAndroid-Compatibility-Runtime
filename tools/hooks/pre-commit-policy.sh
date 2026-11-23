#!/bin/sh
# S-SLIM growth guard — pre-commit policy gate.
#
# Installs as .git/hooks/pre-commit:
#   cp tools/hooks/pre-commit-policy.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
#
# Blocks any commit whose STAGED tree violates the consolidated policy
# (CONSTITUTION_V2 §172.5 + S213 image policy + S214 default-deny path law):
# scratch residue, unregistered directories, frozen-area drift, size budgets,
# >100 KiB duplicates, >1 MiB images, machine paths, forbidden artifact
# classes. The validator reads `git ls-files` (the staged index), so the
# commit is judged on exactly what is about to be committed.
# Exit non-zero = commit rejected with the violation list.
exec python3 tools/policy_validator.py check
