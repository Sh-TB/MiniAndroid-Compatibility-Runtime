#!/usr/bin/env python3
"""
EXP-024: F-Droid APK Collector Tool

Downloads real open-source Android APKs from F-Droid repository.
Follows Golden Debug Protocol - only records real downloads, no fabrications.

Usage:
    python tools/fdroid_apk_collector.py [--count 20] [--output-dir run/exp024/apks]
"""

import json
import os
import sys
import hashlib
import urllib.request
import urllib.error
import ssl
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET

# ============================================================================
# Configuration
# ============================================================================

class Config:
    BASE_DIR = Path("/home/z/my-project/miniandroid")
    OUTPUT_DIR = BASE_DIR / "run" / "exp024" / "apks"
    INVENTORY_FILE = BASE_DIR / "database" / "exp024_apk_inventory.json"
    
    # F-Droid Repository URLs
    FDROID_REPO_URL = "https://f-droid.org/repo"
    FDROID_API_URL = "https://f-droid.org/api/v1/packages"
    
    # Categories to target
    TARGET_CATEGORIES = [
        "Calculator", "Notes", "Todo", "File Manager", "Browser",
        "Clock", "Weather", "Games", "Media", "Utility"
    ]
    
    # Known good F-Droid apps (package names)
    KNOWN_APPS = [
        # Calculators
        {"name": "OpenCalc", "package": "org.fossasia.calc", "category": "Calculator"},
        {"name": "Calculator", "package": "com.simplemobiletools.calculator", "category": "Calculator"},
        
        # Notes & Todo
        {"name": "Simple Notes", "package": "com.simplemobiletools.notes", "category": "Notes"},
        {"name": "Joplin", "package": "net.cozic.joplin", "category": "Notes"},
        {"name": "Tasks.org", "package": "org.tasks", "category": "Todo"},
        {"name": "OpenTodoList", "package": "se.sjoertvik.opentodolist", "category": "Todo"},
        
        # File Manager
        {"name": "File Manager+", "package": "com.filemanagerplus.notes", "category": "File Manager"},
        {"name": "Simple File Manager", "package": "com.simplemobiletools.filemanager", "category": "File Manager"},
        {"name": "Material Files", "package": "me.zhanghai.android.files", "category": "File Manager"},
        
        # Browser
        {"name": "Eternal Browser", "package": "com.eternal.browser", "category": "Browser"},
        {"name": "Lightning Browser", "package": "acr.browser.lightning", "category": "Browser"},
        
        # Clock/Time
        {"name": "Simple Clock", "package": "com.simplemobiletools.clock", "category": "Clock"},
        {"name": "Timer", "package": "com.github.premnirmal.timer", "category": "Clock"},
        {"name": "Stopwatch", "package": "com.yocto.stopwatch", "category": "Clock"},
        
        # Weather
        {"name": "FairWeather", "package": "me.gmazz.fairweather", "category": "Weather"},
        {"name": "Geometric Weather", "package": "wangdaye.com.geometricweather", "category": "Weather"},
        
        # Games (simple ones)
        {"name": "Connect Four", "package": "de.markusfisch.android.connectfour", "category": "Games"},
        {"name": "Minesweeper", "package": "de.markusfisch.android.minesweeper", "category": "Games"},
        {"name": "Reversi", "package": "de.markusfisch.android.reversi", "category": "Games"},
        {"name": "TicTacToe", "package": "de.markusfisch.android.tictactoe", "category": "Games"},
        
        # Media
        {"name": "Simple Gallery", "package": "com.simplemobiletools.gallery", "category": "Media"},
        {"name": "VLC for Android", "package": "org.videolan.vlc", "category": "Media"},
        {"name": "Music Player", "package": "com.simplemobiletools.musicplayer", "category": "Media"},
        
        # Utility
        {"name": "Flashlight", "package": "com.simplemobiletools.flashlight", "category": "Utility"},
        {"name": "Barcode Scanner", "package": "com.svenjacobs.zephyr", "category": "Utility"},
        {"name": "Unit Converter", "package": "com.nutometer.unitconverter", "category": "Utility"},
        {"name": "PDF Viewer", "package": "com.github.barteksc.pdfviewer", "category": "Utility"},
    ]
    
    # SSL context (handle certificate issues gracefully)
    SSL_CONTEXT = ssl.create_default_context()

# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class APKMetadata:
    """Metadata for a downloaded or attempted APK"""
    application_name: str
    package_name: str
    version: str
    source_url: str
    download_url: Optional[str]
    file_size: int
    category: str
    sha256: Optional[str]
    download_status: str  # SUCCESS, NOT_AVAILABLE, FAILED
    local_path: Optional[str]
    error_message: Optional[str]
    download_timestamp: str

# ============================================================================
# F-Droid Client
# ============================================================================

class FDroidClient:
    """Client for interacting with F-Droid repository"""
    
    def __init__(self):
        self.repo_url = Config.FDROID_REPO_URL
        self.api_url = Config.FDROID_API_URL
        
    def get_package_info(self, package_name: str) -> Optional[Dict]:
        """Get package information from F-Droid API"""
        try:
            url = f"{self.api_url}/{package_name}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'MiniAndroid-EXP024/1.0',
                'Accept': 'application/json'
            })
            
            with urllib.request.urlopen(req, timeout=30, context=Config.SSL_CONTEXT) as response:
                data = json.loads(response.read().decode())
                return data
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # Package not found
            print(f"  ⚠️ HTTP Error {e.code} for {package_name}")
            return None
        except Exception as e:
            print(f"  ⚠️ Error fetching {package_name}: {e}")
            return None
    
    def get_latest_apk_url(self, package_info: Dict) -> Optional[str]:
        """Extract latest APK download URL from package info"""
        try:
            # Get suggested version code
            suggested = package_info.get("suggestedVersionCode")
            if not suggested:
                # Fall back to highest version code
                packages = package_info.get("packages", {})
                if isinstance(packages, dict):
                    versions = [int(v) for v in packages.keys() if v.isdigit()]
                    if versions:
                        suggested = max(versions)
                    else:
                        return None
                else:
                    return None
            
            # Get APK file info
            packages = package_info.get("packages", {})
            apk_info = None
            
            if isinstance(packages, dict):
                apk_info = packages.get(str(suggested))
            elif isinstance(packages, list):
                # Find matching version
                for p in packages:
                    if isinstance(p, dict) and p.get("versionCode") == suggested:
                        apk_info = p
                        break
                if not apk_info and packages:
                    apk_info = packages[0]  # Fallback to first
            
            if apk_info and isinstance(apk_info, dict):
                apk_name = apk_info.get("apkname")
                if apk_name:
                    return f"{self.repo_url}/{apk_name}"
            
            return None
            
        except Exception as e:
            print(f"  ⚠️ Error extracting APK URL: {e}")
            return None
    
    def get_version_name(self, package_info: Dict) -> str:
        """Get version name from package info"""
        return package_info.get("versionName", "unknown")
    
    def get_source_url(self, package_info: Dict) -> str:
        """Get source code URL"""
        return package_info.get("sourceCode", "")

# ============================================================================
# APK Downloader
# ============================================================================

class APKDownloader:
    """Downloads and verifies APKs from F-Droid"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = FDroidClient()
        
    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def download_apk(self, url: str, filename: str) -> tuple[bool, Path, str]:
        """
        Download APK from URL.
        Returns: (success, local_path, error_message)
        """
        output_path = self.output_dir / filename
        
        try:
            print(f"  📥 Downloading: {filename}")
            req = urllib.request.Request(url, headers={
                'User-Agent': 'MiniAndroid-EXP024/1.0'
            })
            
            with urllib.request.urlopen(req, timeout=60, context=Config.SSL_CONTEXT) as response:
                total_size = int(response.headers.get('content-length', 0))
                
                with open(output_path, 'wb') as f:
                    downloaded = 0
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress indicator (only for larger files)
                        if total_size > 0:
                            pct = (downloaded / total_size) * 100
                            if downloaded % 100000 < 8192:  # Print occasionally
                                print(f"     ... {pct:.1f}% ({downloaded//1024}KB/{total_size//1024}KB)")
                
                print(f"  ✅ Downloaded: {output_path.stat().st_size} bytes")
                return True, output_path, ""
                
        except urllib.error.HTTPError as e:
            error = f"HTTP Error {e.code}"
            print(f"  ❌ Download failed: {error}")
            return False, output_path, error
        except Exception as e:
            error = str(e)
            print(f"  ❌ Download failed: {error}")
            return False, output_path, error
    
    def verify_apk(self, file_path: Path) -> bool:
        """Verify downloaded file is a valid APK (ZIP with AndroidManifest)"""
        try:
            if not file_path.exists():
                return False
            
            # Check ZIP format
            if not zipfile.is_zipfile(str(file_path)):
                return False
            
            # Check for AndroidManifest.xml or classes.dex
            with zipfile.ZipFile(str(file_path), 'r') as zf:
                names = zf.namelist()
                has_manifest = 'AndroidManifest.xml' in names
                has_dex = any(n.endswith('.dex') for n in names)
                
                return has_manifest or has_dex
                
        except Exception as e:
            print(f"  ⚠️ Verification error: {e}")
            return False
    
    def process_app(self, app_info: Dict) -> APKMetadata:
        """Process a single app: fetch metadata, download, verify"""
        package_name = app_info["package"]
        app_name = app_info["name"]
        category = app_info["category"]
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        print(f"\n📱 Processing: {app_name} ({package_name})")
        
        # Get package info from F-Droid
        package_info = self.client.get_package_info(package_name)
        
        if not package_info:
            print(f"  ⚠️ Package not found on F-Droid")
            return APKMetadata(
                application_name=app_name,
                package_name=package_name,
                version="N/A",
                source_url=f"https://f-droid.org/packages/{package_name}",
                download_url=None,
                file_size=0,
                category=category,
                sha256=None,
                download_status="NOT_AVAILABLE",
                local_path=None,
                error_message="Package not found on F-Droid",
                download_timestamp=timestamp
            )
        
        # Extract metadata
        version = self.client.get_version_name(package_info)
        source_url = self.client.get_source_url(package_info)
        download_url = self.client.get_latest_apk_url(package_info)
        
        if not download_url:
            print(f"  ⚠️ No APK download URL available")
            return APKMetadata(
                application_name=app_name,
                package_name=package_name,
                version=version,
                source_url=source_url,
                download_url=None,
                file_size=0,
                category=category,
                sha256=None,
                download_status="NOT_AVAILABLE",
                local_path=None,
                error_message="No APK URL available (may be incompatible license)",
                download_timestamp=timestamp
            )
        
        # Generate safe filename
        safe_filename = f"{package_name.replace('.', '_')}.apk"
        
        # Download APK
        success, local_path, error = self.download_apk(download_url, safe_filename)
        
        if not success:
            return APKMetadata(
                application_name=app_name,
                package_name=package_name,
                version=version,
                source_url=source_url,
                download_url=download_url,
                file_size=0,
                category=category,
                sha256=None,
                download_status="FAILED",
                local_path=None,
                error_message=error,
                download_timestamp=timestamp
            )
        
        # Verify APK
        if not self.verify_apk(local_path):
            print(f"  ⚠️ File verification failed - may not be valid APK")
            # Keep file but mark it
            file_size = local_path.stat().st_size if local_path.exists() else 0
            return APKMetadata(
                application_name=app_name,
                package_name=package_name,
                version=version,
                source_url=source_url,
                download_url=download_url,
                file_size=file_size,
                category=category,
                sha256=self.calculate_sha256(local_path) if local_path.exists() else None,
                download_status="FAILED",
                local_path=str(local_path),
                error_message="File verification failed",
                download_timestamp=timestamp
            )
        
        # Success!
        file_size = local_path.stat().st_size
        sha256 = self.calculate_sha256(local_path)
        
        print(f"  🎉 Successfully downloaded and verified!")
        
        return APKMetadata(
            application_name=app_name,
            package_name=package_name,
            version=version,
            source_url=source_url,
            download_url=download_url,
            file_size=file_size,
            category=category,
            sha256=sha256,
            download_status="SUCCESS",
            local_path=str(local_path),
            error_message=None,
            download_timestamp=timestamp
        )

# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("EXP-024: F-Droid APK Acquisition System")
    print("=" * 70)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Output Directory: {Config.OUTPUT_DIR}")
    print()
    
    # Initialize downloader
    downloader = APKDownloader(Config.OUTPUT_DIR)
    
    # Process all known apps
    results: List[APKMetadata] = []
    
    print(f"\n🎯 Target: {len(Config.KNOWN_APPS)} applications")
    print(f"📂 Output: {Config.OUTPUT_DIR}")
    print("\n" + "-" * 50)
    
    for i, app_info in enumerate(Config.KNOWN_APPS, 1):
        print(f"\n[{i}/{len(Config.KNOWN_APPS)}]", end="")
        result = downloader.process_app(app_info)
        results.append(result)
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("📊 DOWNLOAD SUMMARY")
    print("=" * 70)
    
    success_count = sum(1 for r in results if r.download_status == "SUCCESS")
    failed_count = sum(1 for r in results if r.download_status == "FAILED")
    unavailable_count = sum(1 for r in results if r.download_status == "NOT_AVAILABLE")
    
    total_size = sum(r.file_size for r in results if r.download_status == "SUCCESS")
    
    print(f"✅ Successful:   {success_count}/{len(results)}")
    print(f"❌ Failed:       {failed_count}/{len(results)}")
    print(f"⚠️ Unavailable: {unavailable_count}/{len(results)}")
    print(f"💾 Total Size:   {total_size / 1024 / 1024:.2f} MB")
    
    # Save inventory
    inventory = {
        "experiment": "EXP-024",
        "phase": "APK Acquisition",
        "generated": datetime.utcnow().isoformat() + "Z",
        "total_targeted": len(results),
        "summary": {
            "success": success_count,
            "failed": failed_count,
            "unavailable": unavailable_count,
            "total_size_bytes": total_size
        },
        "applications": [asdict(r) for r in results]
    }
    
    with open(Config.INVENTORY_FILE, 'w') as f:
        json.dump(inventory, f, indent=2)
    
    print(f"\n💾 Inventory saved: {Config.INVENTORY_FILE}")
    
    # List successful downloads
    successful = [r for r in results if r.download_status == "SUCCESS"]
    if successful:
        print(f"\n✅ Successfully Downloaded APKs:")
        for r in successful:
            print(f"   • {r.application_name}: {r.local_path}")
    
    return results, inventory

if __name__ == "__main__":
    main()
