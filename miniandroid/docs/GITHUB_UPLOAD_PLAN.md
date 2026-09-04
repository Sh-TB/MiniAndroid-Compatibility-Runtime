# GitHub Upload Plan

**Generated**: 2026-08-12  
**Status**: ✅ READY FOR EXECUTION  
**Phase**: 7 of 9 (Preservation & Migration)

---

## Repository Information

### Recommended Repository Name
```
miniandroid-runtime
```

### Alternative Names
- `MiniAndroid` (simple)
- `android-apk-runtime` (descriptive)
- `dex-interpreter` (technical focus)

### Repository Description
```
A lightweight Android APK execution runtime built in C++ for research, 
testing, and compatibility analysis. Features DEX bytecode interpreter, 
Android runtime simulation, and comprehensive diagnostics.
```

### Topics/Tags
```
android, dex, apk, runtime, interpreter, c++, compatibility-testing, 
research, mobile-security, bytecode, dalvik
```

---

## Branch Strategy

### Main Branches

| Branch | Purpose | Protection |
|--------|---------|------------|
| `main` | Stable, production-ready code | Required PR reviews |
| `development` | Active development work | Optional CI checks |
| `backup/exp023-pre-validation` | Safety checkpoint (read-only) | No direct pushes |

### Branch Creation Flow

```bash
# Development workflow
git checkout main
git pull origin main
git checkout -b development
# ... work ...
git push origin development

# Feature branches from development
git checkout development
git pull origin development
git checkout -b feature/new-feature
# ... work ...
# PR to development

# Hotfixes from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix
# ... work ...
# PR to main
```

---

## First Push Content

### Commit Summary (4 logical commits)

| Commit | Hash | Description | Files Changed |
|--------|------|-------------|---------------|
| 1 | `7f48e00` | Remove build artifacts + update .gitignore | 41 files (deletions) |
| 2 | `52fa232` | Add README and audit documentation | +690 lines |
| 3 | `9ed43a1` | Add experiment history READMEs | +475 lines |
| 4 | `4c6669f` | Add evidence integrity index | +1 file |

### Total Repository Contents After Push

| Category | Files | Size (est.) |
|----------|-------|-------------|
| Source Code (.cpp/.h) | 44 | 1.2MB |
| Python Scripts | 15 | 460KB |
| Documentation | 11 | 820KB |
| JSON Databases/Evidence | ~95 | 2.1MB |
| Test Files | 1 | 12KB |
| Tools | 3 | 72KB |
| Third Party | 1 | 900KB |
| Build Configs | 2 | 9KB |
| **TOTAL** | **~172** | **~5.5MB** |

---

## Excluded Files (Not Pushed)

### Build Artifacts (~90MB) - Rebuildable
```
miniandroid/build/           # CMake build output
miniandroid/build_exp002/    # EXP-002 build
miniandroid/build_exp003a/   # EXP-003a build
miniandroid/build_exp003a1/  # EXP-003a1 build
miniandroid/build_exp003batch/# Batch build
miniandroid/build_exp004/    # EXP-004 build
miniandroid/build_exp005/    # EXP-005 build
miniandroid/build_exp006/    # EXP-006 build
miniandroid/build_exp019/    # EXP-019 build
*.o                          # All object files
```

### Transient/Temporary Directories
```
temp_apk_downloads/          # Empty, for temporary APK storage
upload/                      # Transient upload area
tool-results/                # Temporary tool output
node_modules/                # Node dependencies (if any)
skills/                      # External skill definitions
```

### Environment Files (Security)
```
.env                         # May contain secrets/tokens
```

---

## Large Files Analysis

### Files Over 1MB in Repository

| File | Size | Action | Reason |
|------|------|--------|--------|
| `run/screenshot.png` | 1.1MB | ✅ Keep | Visual evidence, important proof |

### Git LFS Recommendation

**Current Status**: NOT REQUIRED

All tracked files are under GitHub's 100MB limit. The largest file is 1.1MB (screenshot).

**Future Consideration**: If adding:
- More screenshots (>5MB each)
- APK files for testing
- Binary test fixtures

Then consider Git LFS for:
```
*.apk
*.png
*.jpg
*.gif
```

---

## Pre-Push Checklist

### Before First Push

- [x] `.gitignore` updated with all patterns
- [x] Build artifacts removed from tracking
- [x] Working tree clean (`git status` shows clean)
- [x] Logical commit history created (4 commits)
- [x] README.md with project overview
- [x] Documentation complete (audit, safety reports)
- [x] Experiment history preserved
- [x] Evidence index created
- [ ] Remote URL configured
- [ ] Authentication configured (SSH token or HTTPS credentials)
- [ ] Repository created on GitHub (or use `gh repo create`)

### Commands to Execute

```bash
# Option A: Create new repository on GitHub first, then add remote
git remote add origin https://github.com/<USERNAME>/miniandroid-runtime.git
git push -u origin main

# Option B: Use GitHub CLI (if authenticated)
gh repo create miniandroid-runtime --public --source=. --push
```

### Setting Up Remote

```bash
# Using HTTPS (recommended for simplicity)
git remote add origin https://github.com/<USERNAME>/miniandroid-runtime.git

# Or using SSH (if SSH keys configured)
git remote add origin git@github.com:<USERNAME>/miniandroid-runtime.git

# Verify remote
git remote -v
```

---

## Post-Push Actions

### Immediately After Push

1. **Verify on GitHub**
   - Open repository URL
   - Check all files visible
   - Verify README renders correctly
   - Confirm no sensitive data exposed

2. **Set Branch Protections** (on GitHub)
   - Settings → Branches → Add rule
   - Protect `main` branch
   - Require PR reviews
   - Require status checks (when CI added)

3. **Add .gitattributes** (optional)
   ```
   * text=auto eol=lf
   *.png binary
   *.jpg binary
   ```

4. **Create Development Branch**
   ```bash
   git checkout -b development
   git push origin development
   ```

---

## Security Considerations

### Sensitive Data Check

✅ **Safe to Push**:
- Source code (no hardcoded secrets)
- Documentation (public info)
- Evidence JSON files (test data)
- Experiment reports (analysis results)

⚠️ **Review Before Push**:
- `.env` file (should be gitignored)
- Any API keys or tokens in scripts
- Personal information in reports

### Credential Handling

The user provided a GitHub token: `github_pat_<redacted-before-handoff>`

**IMPORTANT**: This token should:
1. NOT be committed to the repository
2. Be used only for authentication during push
3. Have minimal required permissions (repo access)
4. Be revoked if compromised

---

## Rollback Plan

If anything goes wrong during push:

```bash
# Emergency rollback to pre-push state
git reset --hard backup/exp023-pre-validation
git push --force origin main  # Use with caution!

# Or simply delete remote and start fresh
# (On GitHub: Settings → Delete this repository)
```

---

## Success Criteria

Push is successful when:

- [ ] All 223 tracked files appear on GitHub
- [ ] README.md renders correctly with architecture diagram
- [ ] No build artifacts in remote
- [ ] No sensitive files exposed
- [ ] Clone works: `git clone <repo-url> && cd miniandroid-runtime && ls`
- [ ] Build works from clone: `cd miniandroid && mkdir build && cd build && cmake .. && make`

---

## Next Phase

After upload verification (Phase 8), proceed to:

**Phase 9**: Future Roadmap
- EXP-024+ planning
- Real APK download infrastructure
- F-Droid integration
- Continued development priorities

---

**Plan Created By**: Super Z AI Agent  
**Timestamp**: 2026-08-12T14:45:00Z  
**Ready For**: Phase 8 - Remote Backup Verification
