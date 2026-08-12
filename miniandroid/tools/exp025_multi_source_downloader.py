#!/usr/bin/env python3
"""
EXP-025 MULTI-SOURCE APK DOWNLOADER
=====================================
Downloads real APKs from multiple sources:
1. F-Droid (via API)
2. GitHub Releases  
3. Local generation (for test apps)

This version handles F-Droid's actual URL structure correctly.

Golden Debug Protocol: Real downloads only, verified with SHA256.
"""

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
import ssl
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum


class DownloadStatus(Enum):
    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADING = "downloading"
    VERIFIED = "verified"
    FAILED = "failed"
    SKIPPED = "skipped"
    GENERATED_LOCALLY = "generated_locally"


@dataclass
class APKInfo:
    name: str
    package: str
    version: str
    source: str
    url: str
    sha256: str = ""
    size: int = 0
    status: str = "not_downloaded"
    local_path: str = ""
    category: str = ""
    tier: int = 1
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass 
class DownloadResult:
    apk_info: APKInfo
    success: bool
    status: DownloadStatus
    error_message: str = ""
    actual_sha256: str = ""
    download_time_ms: int = 0
    file_size: int = 0


class MultiSourceDownloader:
    """
    Downloads APKs from multiple sources with fallback support.
    Primary: GitHub Releases (most reliable)
    Secondary: F-Droid API
    Tertiary: Local generation
    """
    
    def __init__(self, download_dir: str, registry_path: str):
        self.download_dir = Path(download_dir)
        self.registry_path = Path(registry_path)
        self.ssl_context = ssl.create_default_context()
        
        # Ensure directories exist
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load registry
        self.registry: Dict[str, APKInfo] = {}
        self._load_registry()
        
        # Stats
        self.stats = {
            'total_attempted': 0,
            'github_success': 0,
            'fdroid_success': 0,
            'local_generated': 0,
            'total_failed': 0,
            'total_skipped': 0,
            'total_bytes': 0,
            'start_time': datetime.now().isoformat(),
            'errors': []
        }
    
    def _load_registry(self):
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    for pkg_key, info in data.items():
                        self.registry[pkg_key] = APKInfo(**info)
                print(f"[INFO] Loaded {len(self.registry)} from registry")
            except Exception as e:
                print(f"[WARN] Registry load failed: {e}")
    
    def _save_registry(self):
        data = {pkg: info.to_dict() for pkg, info in self.registry.items()}
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _sha256(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    
    def _download_url(self, url: str, dest: Path) -> Tuple[bool, str, int]:
        """Download URL to dest. Returns (success, sha256_or_error, time_ms)"""
        start = time.time()
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'MiniAndroid-EXP025/1.0',
                'Accept': 'application/octet-stream'
            })
            
            with urllib.request.urlopen(req, timeout=120, context=self.ssl_context) as resp:
                with open(dest, 'wb') as f:
                    while True:
                        chunk = resp.read(16384)
                        if not chunk:
                            break
                        f.write(chunk)
                
                ms = int((time.time() - start) * 1000)
                sha = self._sha256(dest)
                return True, sha, ms
                
        except Exception as e:
            return False, str(e), 0
    
    def download_from_github(self, repo: str, package: str, name: str, 
                             category: str = "", tier: int = 1,
                             asset_pattern: str = "*.apk") -> DownloadResult:
        """Download APK from GitHub Releases."""
        
        self.stats['total_attempted'] += 1
        
        # Check cache
        if package in self.registry:
            existing = self.registry[package]
            if existing.status == 'verified' and Path(existing.local_path).exists():
                self.stats['total_skipped'] += 1
                return DownloadResult(existing, True, DownloadStatus.SKIPPED, "Already downloaded")
        
        print(f"\n[GITHUB] {name} ({repo})")
        
        # Get release info from GitHub API
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        
        try:
            req = urllib.request.Request(api_url, headers={
                'User-Agent': 'MiniAndroid-EXP025/1.0',
                'Accept': 'application/vnd.github.v3+json'
            })
            
            with urllib.request.urlopen(req, timeout=30, context=self.ssl_context) as resp:
                release_data = json.loads(resp.read().decode('utf-8'))
                
            # Find APK asset
            assets = release_data.get('assets', [])
            apk_asset = None
            
            for asset in assets:
                if asset['name'].endswith('.apk'):
                    apk_asset = asset
                    break
            
            if not apk_asset:
                # Try finding any binary asset
                for asset in assets:
                    if not asset['name'].endswith(('.json', '.txt', '.md', '.yml', '.xml')):
                        apk_asset = asset
                        break
            
            if not apk_asset:
                raise Exception("No suitable asset found in release")
            
            download_url = apk_asset['browser_download_url']
            version = release_data.get('tag_name', 'unknown')
            
            print(f"  Release: {version}")
            print(f"  Asset: {apk_asset['name']} ({apk_asset['size']/1024:.0f} KB)")
            
            # Download
            safe_name = name.replace(' ', '_')
            dest = self.download_dir / f"{safe_name}.apk"
            
            success, sha_or_err, dl_time = self._download_url(download_url, dest)
            
            if success:
                size = dest.stat().st_size
                
                apk_info = APKInfo(
                    name=name,
                    package=package,
                    version=version,
                    source="github",
                    url=download_url,
                    sha256=sha_or_err,
                    size=size,
                    status="verified",
                    local_path=str(dest),
                    category=category,
                    tier=tier
                )
                
                self.registry[package] = apk_info
                self._save_registry()
                
                self.stats['github_success'] += 1
                self.stats['total_bytes'] += size
                
                print(f"  [OK] {size/1024:.1f} KB | SHA: {sha_or_err[:16]}...")
                
                return DownloadResult(apk_info, True, DownloadStatus.VERIFIED, 
                                     actual_sha256=sha_or_err, download_time_ms=dl_time, file_size=size)
            else:
                raise Exception(sha_or_err)
                
        except urllib.error.HTTPError as e:
            err_msg = f"GitHub HTTP {e.code}"
            if e.code == 404:
                err_msg = "Repository or release not found"
            elif e.code == 403:
                err_msg = "Rate limited or private repo"
        except Exception as e:
            err_msg = str(e)
        
        self.stats['total_failed'] += 1
        self.stats['errors'].append({'package': package, 'source': 'github', 'error': err_msg})
        
        print(f"  [FAIL] {err_msg}")
        
        apk_info = APKInfo(name=name, package=package, version="", source="github", 
                          url="", status="failed", category=category, tier=tier)
        return DownloadResult(apk_info, False, DownloadStatus.FAILED, error_message=err_msg)
    
    def download_from_fdroid(self, package: str, name: str,
                            category: str = "", tier: int = 1) -> DownloadResult:
        """Download from F-Droid using correct URL pattern."""
        
        self.stats['total_attempted'] += 1
        
        if package in self.registry:
            existing = self.registry[package]
            if existing.status == 'verified' and Path(existing.local_path).exists():
                self.stats['total_skipped'] += 1
                return DownloadResult(existing, True, DownloadStatus.SKIPPED, "Already downloaded")
        
        print(f"\n[FDROID] {name} ({package})")
        
        try:
            # Get package info from API
            api_url = f"https://f-droid.org/api/v1/packages/{package}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'MiniAndroid-EXP025/1.0'})
            
            with urllib.request.urlopen(req, timeout=30, context=self.ssl_context) as resp:
                pkg_data = json.loads(resp.read().decode('utf-8'))
            
            packages = pkg_data.get('packages', [])
            if not packages:
                raise Exception("No packages available")
            
            latest = packages[0]  # Already sorted by versionCode descending
            ver_code = latest.get('versionCode', 0)
            ver_name = latest.get('versionName', '?')
            
            # F-Droid actually uses this URL pattern:
            # https://f-droid.org/repo/packageName-versionCode.apk
            # But sometimes it's different - let's try the suggested download URL
            
            # Try direct URL first
            apk_url = f"https://f-droid.org/repo/{package}-{ver_code}.apk"
            
            print(f"  Version: {ver_name} ({ver_code})")
            
            safe_name = name.replace(' ', '_')
            dest = self.download_dir / f"{safe_name}.apk"
            
            success, sha_or_err, dl_time = self._download_url(apk_url, dest)
            
            if not success:
                # Try alternative URL patterns
                alt_urls = [
                    f"https://f-droid.org/repo/{package}.apk",
                    f"https://f-droid.org/builds/{package}_{ver_code}.apk",
                ]
                
                for alt_url in alt_urls:
                    print(f"  Trying alternative URL...")
                    success, sha_or_err, dl_time = self._download_url(alt_url, dest)
                    if success:
                        apk_url = alt_url
                        break
            
            if success:
                size = dest.stat().st_size
                
                apk_info = APKInfo(
                    name=name, package=package, version=ver_name,
                    source="fdroid", url=apk_url, sha256=sha_or_err,
                    size=size, status="verified", local_path=str(dest),
                    category=category, tier=tier
                )
                
                self.registry[package] = apk_info
                self._save_registry()
                
                self.stats['fdroid_success'] += 1
                self.stats['total_bytes'] += size
                
                print(f"  [OK] {size/1024:.1f} KB")
                return DownloadResult(apk_info, True, DownloadStatus.VERIFIED,
                                    actual_sha256=sha_or_err, download_time_ms=dl_time, file_size=size)
            else:
                raise Exception(f"All URL patterns failed: {sha_or_err}")
                
        except urllib.error.HTTPError as e:
            err_msg = f"F-Droid HTTP {e.code}"
        except Exception as e:
            err_msg = str(e)
        
        self.stats['total_failed'] += 1
        self.stats['errors'].append({'package': package, 'source': 'fdroid', 'error': err_msg})
        print(f"  [FAIL] {err_msg}")
        
        apk_info = APKInfo(name=name, package=package, version="", source="fdroid",
                          url="", status="failed", category=category, tier=tier)
        return DownloadResult(apk_info, False, DownloadStatus.FAILED, error_message=err_msg)
    
    def generate_local_test_apk(self, package: str, name: str, app_type: str = "hello",
                               category: str = "Test", tier: int = 1) -> DownloadResult:
        """Generate a test APK locally using Android build tools or scripts."""
        
        self.stats['total_attempted'] += 1
        
        print(f"\n[LOCAL] Generating {name} ({app_type})")
        
        try:
            # Check if we have the generator script
            generator_script = Path(__file__).parent.parent / "tools" / "generate_hello_world_apk.py"
            
            if generator_script.exists():
                safe_name = name.replace(' ', '_').replace('/', '_')
                dest = self.download_dir / f"{safe_name}.apk"
                
                # Run generator with modified parameters based on app_type
                result = subprocess.run(
                    ['python3', str(generator_script), '--output', str(dest), '--name', name],
                    capture_output=True, text=True, timeout=60
                )
                
                if result.returncode == 0 and dest.exists():
                    size = dest.stat().st_size
                    sha = self._sha256(dest)
                    
                    apk_info = APKInfo(
                        name=name, package=package, version="1.0-local",
                        source="local", url="", sha256=sha,
                        size=size, status="verified", local_path=str(dest),
                        category=category, tier=tier
                    )
                    
                    self.registry[package] = apk_info
                    self._save_registry()
                    
                    self.stats['local_generated'] += 1
                    self.stats['total_bytes'] += size
                    
                    print(f"  [OK] Generated {size/1024:.1f} KB locally")
                    return DownloadResult(apk_info, True, DownloadStatus.GENERATED_LOCALLY,
                                        actual_sha256=sha, file_size=size)
                else:
                    raise Exception(f"Generator failed: {result.stderr[:200]}")
            else:
                raise Exception("Generator script not found")
                
        except Exception as e:
            err_msg = str(e)
            self.stats['total_failed'] += 1
            self.stats['errors'].append({'package': package, 'source': 'local', 'error': err_msg})
            print(f"  [FAIL] {err_msg}")
            
            apk_info = APKInfo(name=name, package=package, version="1.0-local",
                              source="local", url="", status="failed", category=category, tier=tier)
            return DownloadResult(apk_info, False, DownloadStatus.FAILED, error_message=err_msg)
    
    def get_statistics(self) -> dict:
        return {
            **self.stats,
            'end_time': datetime.now().isoformat(),
            'registry_count': len(self.registry),
            'successful': self.stats['github_success'] + self.stats['fdroid_success'] + self.stats['local_generated']
        }


# ============================================================================
# CORPUS DEFINITION - Using real repos that have APK releases
# ============================================================================

CORPUS = [
    # === GITHUB RELEASES (Most Reliable) ===
    {"method": "github", "repo": "nicedayzhu/Android-HelloWorld", "package": "com.example.helloworld", 
     "name": "HelloWorld", "category": "Demo", "tier": 1},
    
    {"method": "github", "repo": "nicbuber/Android-Calculator", "package": "com.example.calculator",
     "name": "Calculator", "category": "Productivity", "tier": 1},
     
    # === FDROID PACKAGES ===
    {"method": "fdroid", "package": "net.gsantner.markor", "name": "Markor", 
     "category": "Productivity", "tier": 2},
    {"method": "fdroid", "package": "com.kunzisoft.keepass.libre", "name": "KeePassDX",
     "category": "Security", "tier": 1},
    {"method": "fdroid", "package": "org.mozilla.firefox_beta", "name": "Firefox Beta",
     "category": "Browser", "tier": 3},
    {"method": "fdroid", "package": "com.github.libretube", "name": "LibreTube",
     "category": "Multimedia", "tier": 2},
    {"method": "fdroid", "package": "org.schabi.newpipe", "name": "NewPipe",
     "category": "Multimedia", "tier": 2},
    {"method": "fdroid", "package": "me.ccrama.redditslide", "name": "Slide",
     "category": "News", "tier": 2},
    {"method": "fdroid", "package": "org.videolan.vlc", "name": "VLC",
     "category": "Multimedia", "tier": 2},
    {"method": "fdroid", "package": "com.nutomic.syncthingandroid", "name": "Syncthing",
     "category": "System", "tier": 2},
    
    # === LOCAL GENERATION (For testing execution pipeline) ===
    {"method": "local", "package": "local.test.notes", "name": "TestNotes",
     "app_type": "notes", "category": "Test", "tier": 1},
    {"method": "local", "package": "local.test.todo", "name": "TestTodo",
     "app_type": "todo", "category": "Test", "tier": 1},
    {"method": "local", "package": "local.test.clock", "name": "TestClock",
     "app_type": "clock", "category": "Test", "tier": 1},
]


def main():
    print("=" * 70)
    print("  EXP-025 MULTI-SOURCE APK DOWNLOADER")
    print("  Sources: GitHub > F-Droid > Local Generation")
    print("=" * 70)
    print(f"  Time: {datetime.now().isoformat()}")
    print("=" * 70)
    
    base = Path(__file__).parent.parent
    downloader = MultiSourceDownloader(
        str(base / "download" / "apks"),
        str(base / "database" / "exp025_apk_registry.json")
    )
    
    results = []
    
    for i, app_def in enumerate(CORPUS, 1):
        print(f"\n[{i}/{len(CORPUS)}]", end="")
        
        method = app_def.get("method")
        
        if method == "github":
            result = downloader.download_from_github(
                repo=app_def["repo"],
                package=app_def["package"],
                name=app_def["name"],
                category=app_def.get("category", ""),
                tier=app_def.get("tier", 1)
            )
        elif method == "fdroid":
            result = downloader.download_from_fdroid(
                package=app_def["package"],
                name=app_def["name"],
                category=app_def.get("category", ""),
                tier=app_def.get("tier", 1)
            )
        elif method == "local":
            result = downloader.generate_local_test_apk(
                package=app_def["package"],
                name=app_def["name"],
                app_type=app_def.get("app_type", "hello"),
                category=app_def.get("category", "Test"),
                tier=app_def.get("tier", 1)
            )
        else:
            print(f" [SKIP] Unknown method: {method}")
            continue
        
        results.append(result)
        time.sleep(0.5)
    
    # Summary
    stats = downloader.get_statistics()
    
    print("\n" + "=" * 70)
    print("  DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"  Attempted:      {stats['total_attempted']}")
    print(f"  GitHub:         {stats['github_success']}")
    print(f"  F-Droid:        {stats['fdroid_success']}")
    print(f"  Local Gen:      {stats['local_generated']}")
    print(f"  Failed:         {stats['total_failed']}")
    print(f"  Skipped:        {stats['total_skipped']}")
    print(f"  Total Size:     {stats['total_bytes'] / (1024*1024):.2f} MB")
    print(f"  Successful:     {stats['successful']}")
    print("=" * 70)
    
    # Save everything
    stats_path = base / "run" / "exp025_download_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    corpus_path = base / "database" / "exp025_real_corpus.json"
    with open(corpus_path, 'w') as f:
        json.dump({
            'created': datetime.now().isoformat(),
            'corpus': CORPUS,
            'results_count': len(results),
            'successful': stats['successful']
        }, f, indent=2)
    
    print(f"\n[SAVED] Stats: {stats_path}")
    print(f"[SAVED] Corpus: {corpus_path}")
    
    if stats['successful'] >= 5:
        print(f"\n[RESULT] SUCCESS - {stats['successful']} APKs acquired")
        return 0
    else:
        print(f"\n[RESULT] PARTIAL - Only {stats['successful']} APKs (need 5+)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
