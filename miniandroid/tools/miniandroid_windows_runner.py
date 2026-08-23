"""
MiniAndroid Windows Runner — Minimal APK loader.

Usage: python miniandroid_windows_runner.py <apk_path> [<output_dir>]

This script provides a minimal Windows-compatible interface for running
MiniAndroid on an APK. It requires the miniandroid_exp042.exe binary
to be in the same directory.

On Windows, the user can:
1. Place miniandroid_exp042.exe and this script in a folder
2. Run: python miniandroid_windows_runner.py MyApp.apk
3. View the screenshot, logs, and diagnostic output

The script generates a diagnostic ZIP with all evidence.
"""
import sys
import os
import json
import hashlib
import zipfile
import subprocess
import platform
from pathlib import Path
from datetime import datetime

def get_runtime_binary():
    """Find the runtime binary."""
    for name in ['miniandroid_exp042.exe', 'miniandroid_exp042', 'miniandroid.exe', 'miniandroid']:
        p = Path(__file__).parent / name
        if p.exists():
            return str(p)
    return None

def run_apk(apk_path, output_dir, timeout=60):
    """Run an APK through MiniAndroid."""
    binary = get_runtime_binary()
    if not binary:
        return {"error": "Runtime binary not found. Place miniandroid_exp042.exe in the same directory."}
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [binary, str(apk_path), str(output_dir)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"error": "TIMEOUT", "exit_code": -1}
    except Exception as e:
        return {"error": str(e), "exit_code": -2}

def collect_diagnostics(apk_path, output_dir, run_result):
    """Collect diagnostics into a ZIP."""
    diag = {
        "runtime_version": "0.2.0-exp079",
        "git_commit": "unknown",
        "os": platform.system(),
        "architecture": platform.machine(),
        "timestamp": datetime.now().isoformat(),
        "apk": {
            "path": str(apk_path),
            "sha256": hashlib.sha256(Path(apk_path).read_bytes()).hexdigest() if Path(apk_path).exists() else "MISSING",
            "size": Path(apk_path).stat().st_size if Path(apk_path).exists() else 0,
        },
    }
    
    # Add run results
    if "exit_code" in run_result:
        diag["execution"] = {
            "exit_code": run_result["exit_code"],
            "stdout_lines": len(run_result.get("stdout", "").splitlines()),
            "stderr_lines": len(run_result.get("stderr", "").splitlines()),
        }
    
    # Check for artifacts
    output_dir = Path(output_dir)
    for fname in ["view_tree.json", "screenshot.png", "application_runtime.json", "report.md"]:
        p = output_dir / fname
        if p.exists():
            diag.setdefault("artifacts", {})[fname] = {
                "size": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest()[:16],
            }
    
    # Save diagnostic JSON
    diag_path = output_dir / "diagnostic.json"
    diag_path.write_text(json.dumps(diag, indent=2))
    
    # Create ZIP
    zip_path = output_dir / "miniandroid_diagnostic.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in ["diagnostic.json", "view_tree.json", "screenshot.png", 
                       "application_runtime.json", "report.md", "run.log"]:
            p = output_dir / fname
            if p.exists():
                zf.write(p, fname)
        # Add stdout/stderr
        if "stdout" in run_result:
            zf.writestr("stdout.log", run_result["stdout"])
        if "stderr" in run_result:
            zf.writestr("stderr.log", run_result["stderr"])
    
    return diag

def main():
    if len(sys.argv) < 2:
        print("MiniAndroid Windows Runner v0.2.0")
        print("Usage: python miniandroid_windows_runner.py <apk_path> [<output_dir>]")
        print()
        print("This tool runs MiniAndroid on an APK and collects diagnostics.")
        print("The runtime binary (miniandroid_exp042.exe) must be in the same directory.")
        sys.exit(1)
    
    apk_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    print(f"MiniAndroid Windows Runner v0.2.0")
    print(f"APK: {apk_path}")
    print(f"Output: {output_dir}")
    print()
    
    binary = get_runtime_binary()
    if not binary:
        print("ERROR: Runtime binary not found.")
        print("Place miniandroid_exp042.exe in the same directory as this script.")
        sys.exit(1)
    
    print(f"Runtime: {binary}")
    print("Running...")
    
    result = run_apk(apk_path, output_dir)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    
    print(f"Exit code: {result['exit_code']}")
    
    # Collect diagnostics
    diag = collect_diagnostics(apk_path, output_dir, result)
    print(f"\nDiagnostics collected:")
    print(f"  APK SHA256: {diag['apk']['sha256'][:16]}...")
    print(f"  Artifacts: {len(diag.get('artifacts', {}))}")
    print(f"  Diagnostic ZIP: {output_dir}/miniandroid_diagnostic.zip")
    
    # Print execution summary
    print(f"\nExecution Summary:")
    print(f"  Exit code: {result.get('exit_code', 'N/A')}")
    print(f"  Output lines: {len(result.get('stdout', '').splitlines())}")
    
    # Check for view tree
    vt_path = Path(output_dir) / "view_tree.json"
    if vt_path.exists():
        vt = json.loads(vt_path.read_text())
        nodes = vt.get("nodes", [])
        text_nodes = [n for n in nodes if n.get("text", "").strip()]
        print(f"  View tree nodes: {len(nodes)}")
        print(f"  Text-bearing nodes: {len(text_nodes)}")
    
    print(f"\nDiagnostic ZIP: {output_dir}/miniandroid_diagnostic.zip")

if __name__ == "__main__":
    main()
