# Development Workflow Guide

**Generated**: 2026-08-12  
**Phase**: 5 of 8 (GitHub Full Backup Migration)  
**Status**: ✅ ACTIVE

---

## Overview

This document defines the mandatory workflow for all future development on the MiniAndroid project. Following this workflow ensures:

- Continuous synchronization with GitHub
- No loss of work
- Clear experiment history
- Reproducible results
- Clean collaboration

---

## Branching Strategy

### Main Branches

```
main                    ← Stable, production-ready code
  │
  └── development       ← Active development branch
        │
        ├── feature/EXP-024    ← Feature branches
        ├── feature/EXP-025
        ├── fix/issue-name     ← Bug fix branches
        └── hotfix/critical    ← Emergency fixes
```

### Branch Rules

| Branch | Purpose | Protection |
|--------|---------|------------|
| `main` | Stable releases, tags | Required PR, CI pass |
| `development` | Integration, testing | Recommended CI pass |
| `feature/*` | Individual experiments/work | None required |
| `fix/*` | Bug fixes | Recommended review |
| `hotfix/*` | Emergency fixes to main | Required review |

---

## Experiment Workflow (Mandatory)

Every new experiment (EXP-XXX) MUST follow this workflow:

### Step 1: Create Experiment Branch

```bash
# Always start from development (or main if no development branch)
git checkout development
git pull origin development

# Create feature branch for your experiment
git checkout -b feature/EXP-024-real-apk-execution
```

### Step 2: Implement Changes

```bash
# Make your changes
# - Add source code to src/
# - Add scripts to scripts/
# - Run experiments
# - Generate evidence in run/
```

**Important**: Commit frequently during implementation!

### Step 3: Generate Evidence

For every experiment, generate:

```
run/expXXX_<evidence_type>.json   # Execution traces, results
run/expXXX_report.md              # Analysis report
database/expXXX_*.json            # Database updates
```

**Golden Debug Protocol Rules**:
- ❌ No fake PASS results
- ❌ No estimated APK names without [PROJECTED] label
- ✅ Separate STATIC_ONLY from REAL_EXECUTED
- ✅ Preserve raw traces always
- ✅ Report discrepancies honestly

### Step 4: Run Validation

```bash
# Run golden tests (HelloWorld must always pass)
./build/miniandroid_megabatch test_apks/HelloWorld.apk

# Verify regression protection
python scripts/run_regression_test.py
```

### Step 5: Update Documentation

Create/update:
```
experiments/EXP-XXX/README.md      # Experiment summary
docs/AI_AGENT_CONTEXT.md           # If architecture changed
database/EVIDENCE_INDEX.json      # Add new evidence files
```

### Step 6: Commit All Changes

```bash
# Stage all relevant files
git add src/ scripts/ run/ database/ docs/ experiments/

# Create meaningful commit message
git commit -m "EXP-024: Add real F-Droid APK execution campaign

- Downloaded and executed 10 real APKs from F-Droid
- Generated execution traces for each APK
- Updated compatibility metrics with real data
- Added evidence to EVIDENCE_INDEX.json

Co-Authored-By: Your Name <email>"
```

### Step 7: Push to Remote

```bash
# Push feature branch
git push -u origin feature/EXP-024-real-apk-execution
```

### Step 8: Merge Request

```bash
# Create PR (via GitHub CLI or website)
gh pr create --base development --title "EXP-024: Real APK Execution" \
          --body "## Summary
                  Real F-Droid APK execution campaign with 10 apps.
                  
                  ## Evidence
                  - run/exp024_execution_matrix.json
                  - run/exp024_report.md
                  
                  ## Validation
                  - [x] HelloWorld regression test passes
                  - [x] Golden Debug Protocol followed
                  - [x] No fabricated results"
```

### Step 9: Merge and Cleanup

```bash
# After PR approval and merge:
git checkout development
git pull origin development

# Delete local feature branch
git branch -d feature/EXP-024-real-apk-execution

# Delete remote feature branch (optional)
git push origin --delete feature/EXP-024-real-apk-execution
```

---

## Commit Message Format

### Standard Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(dex): add invoke-virtual-fast opcode` |
| `fix` | Bug fix | `fix(interpreter): correct register handling` |
| `docs` | Documentation only | `docs(readme): add build instructions` |
| `style` | Code style (no logic change) | `style(format): fix indentation` |
| `refactor` | Code refactor | `refactor(parser): simplify DEX header parsing` |
| `test` | Adding tests | `test(helloworld): add screenshot comparison` |
| `chore` | Maintenance | `chore(build): update CMakeLists.txt` |
| `exp` | Experiment results | `exp(024): add real APK execution data` |

### Experiment Commits

For experiment-specific commits, use format:

```
exp(EXP-XXX): <brief description>

<details of what was done>

Evidence generated:
- <file1>
- <file2>

Co-Authored-By: Author Name <email>
```

---

## Frequency Guidelines

### When to Commit

| Situation | Action |
|-----------|--------|
| Completed a feature/function | ✅ COMMIT |
| Fixed a bug | ✅ COMMIT |
| Generated experiment evidence | ✅ COMMIT |
| Updated documentation | ✅ COMMIT |
| End of work session | ✅ COMMIT PUSH |
| Before switching tasks | ✅ COMMIT |
| Made any meaningful progress | ✅ COMMIT |

### When NOT to Commit

| Situation | Action |
|-----------|--------|
| Mid-debug (broken state) | ⏸️ Wait or stash |
| Only whitespace/formatting | 🤔 Consider if needed |
| Sensitive/temporary data | ❌ Never commit |

### Minimum Frequency

```
Recommended:    Commit every 30-60 minutes of active work
Required:       At least once per work session
Maximum gap:    Never leave uncommitted overnight
```

---

## Workflow Templates

### Quick Start New Experiment

```bash
#!/bin/bash
# Template for starting new experiment

EXP_NUM="EXP-024"
EXP_NAME="experiment-name"
BRANCH="feature/${EXP_NUM}-${EXP_NAME}"

echo "Starting ${EXP_NUM}: ${EXP_NAME}"

# 1. Update and create branch
git checkout development && git pull origin development
git checkout -b $BRANCH

# 2. Create experiment directory
mkdir -p experiments/${EXP_NUM}
cat > experiments/${EXP_NUM}/README.md << EOF
# ${EXP_NUM}: ${EXP_NAME}

## Goal
<TBD>

## Implemented
- 

## Source Files
- 

## Evidence
- 

## Status
🔄 IN PROGRESS
EOF

# 3. Initial commit
git add experiments/${EXP_NUM}/README.md
git commit -m "${EXP_NUM}: Initialize experiment"

echo "Experiment ${EXP_NUM} initialized on branch ${BRANCH}"
echo "Ready to implement!"
```

### End of Session Push

```bash
#!/bin/bash
# Run at end of every work session

echo "End of session checklist:"

# Check status
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Uncommitted changes found!"
    git status --short
    
    read -p "Commit and push? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        git commit -m "chore: end of session $(date +%Y-%m-%d)"
        git push
        echo "✅ Committed and pushed"
    fi
else
    echo "✅ Working tree clean"
fi
```

---

## Safety Checks

### Pre-Push Checklist

Before every push, verify:

- [ ] Working tree clean (or intentional staged changes)
- [ ] Commit messages follow format
- [ ] No sensitive data in staged files
- [ ] Build artifacts not included
- [ ] HelloWorld test still passes (if code changed)
- [ ] Evidence follows Golden Debug Protocol

### Pre-Merge Checklist

Before merging to development/main:

- [ ] All commits pushed to remote branch
- [ ] PR created with description
- [ ] Evidence files listed in PR
- [ ] Regression tests pass
- [ ] At least one reviewer approved (for main)
- [ ] CI checks pass (when configured)

---

## Emergency Procedures

### If Something Goes Wrong

#### Recover Lost Work
```bash
# Check reflog for lost commits
git reflog

# Recover specific commit
git checkout <commit-hash>

# Create branch from recovered state
git checkout -b recovery-branch
```

#### Undo Bad Push
```bash
# Revert last push (preserves history)
git revert HEAD
git push

# Or reset to before bad commit (destructive)
git reset --hard <good-commit-hash>
git push --force  # Use with caution!
```

#### Restore from GitHub
```bash
# If local is corrupted, clone fresh
cd /tmp
git clone https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime.git fresh-copy
# Then manually merge any uncommitted work
```

---

## Tools and Automation

### Recommended Git Aliases

```bash
# Add to ~/.gitconfig
[alias]
    # Status shortcuts
    st = status -sb
    co = checkout
    br = branch
    
    # Commit shortcuts
    save = commit -am "chore: save work $(date +%Y-%m-%d_%H%M)"
    exp = commit -am "exp"
    
    # Log views
    lg = log --oneline --graph -15
    mine = log --author=\"$(git config user.name)\" --oneline
    
    # Sync shortcuts
    sync = !git pull && git push
    uncommit = reset HEAD~1
```

### GitHub CLI Commands

```bash
# View PRs
gh pr list

# Create PR from current branch
gh pr create --base development

# View issues
gh issue list

# Create issue
gh issue create --title "Bug: description" --body "Details..."
```

---

## Collaboration Rules

### For Single Developer (Current)
- Use `development` branch for active work
- Keep `main` stable at all times
- Push daily minimum
- Document all experiments thoroughly

### For Multiple Contributors (Future)
- Always create PR for `main` merges
- Never force push to `main` or `development`
- Discuss major changes in issues first
- Review each other's code
- Resolve conflicts collaboratively

---

## Quality Gates

### Every Experiment Must Have

1. **README.md** in `experiments/EXP-XXX/`
2. **Report** (`run/expXXX_report.md`)
3. **Evidence** (JSON traces, outputs)
4. **Database updates** (if applicable)
5. **EVIDENCE_INDEX.json** entry updated

### Code Quality

- Follow existing code style
- Comment complex logic
- No hardcoded paths
- Error handling where appropriate

### Documentation Quality

- Clear goal statement
- Honest status reporting
- List assumptions made
- Note remaining blockers
- Include lessons learned

---

## Conclusion

Following this workflow ensures:

✅ **No work loss** - Frequent commits and pushes  
✅ **Clear history** - Meaningful commit messages  
✅ **Reproducibility** - Complete evidence trails  
✅ **Collaboration readiness** - Branch-based workflow  
✅ **Quality assurance** - Validation checkpoints  

**This workflow is MANDATORY for all future development.**

---

**Document Created By**: Super Z AI Agent  
**Effective Date**: 2026-08-12  
**Version**: 1.0  
**Review Date**: As needed
