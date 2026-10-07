#!/bin/bash
# cont12_fetch_matrix.sh — CONT-12 PHASE 1: fetch the EXACT real Compose
# dependency set matching the dooz APK (versions from the APK's META-INF
# *.version files). KMP artifacts resolved via the -android coordinate
# (the root AAR on Google Maven is an empty stub). Every artifact is
# SHA-recorded; classes.jar extracted for the oracle build.
set -uo pipefail
BASE=/home/z/my-project
GM=https://dl.google.com/android/maven2
MC=https://repo1.maven.org/maven2
OUT=$BASE/upstream/cont12_maven
RAW=$OUT/raw
CLS=$OUT/classes
mkdir -p "$RAW" "$CLS"

fetch() { # fetch <group-path> <artifact> <version> <ext> <repo>
  local gp="$1" art="$2" ver="$3" ext="$4" repo="$5"
  local name="${art}-${ver}.${ext}"
  local url="${repo}/${gp}/${art}/${ver}/${name}"
  local dst="$RAW/${name}"
  if [ ! -s "$dst" ] || [ -s "$dst" ] && head -c 15 "$dst" | grep -qv "PK"; then
    curl -sf --retry 2 --max-time 120 -o "$dst" "$url" || { echo "FETCH-FAIL $name"; return 1; }
  fi
  # AAR stub detection: capture listing first (grep -q SIGPIPEs big listings under pipefail)
  local cjar="$CLS/${art}.jar"
  if [ "$ext" = "aar" ]; then
    local listing; listing=$(unzip -l "$dst" 2>/dev/null)
    if echo "$listing" | grep -q "classes.jar"; then
      unzip -o -j "$dst" classes.jar > /dev/null 2>&1 && mv classes.jar "$cjar" 2>/dev/null
    else
      echo "STUB-AAR $name (no classes.jar)"
      return 2
    fi
  else
    cp "$dst" "$cjar" 2>/dev/null
  fi
  local aarsha csha ncls
  aarsha=$(sha256sum "$dst" | cut -c1-16)
  csha=$(sha256sum "$cjar" | cut -c1-16)
  ncls=$(unzip -l "$cjar" 2>/dev/null | grep -c "\.class$")
  echo "OK $name aar=$aarsha classes.jar=$csha nclasses=$ncls"
}

C12="1.11.4"
echo "=== COMPOSE $C12 (android variants) ==="
for a in runtime runtime-saveable runtime-retain ui ui-geometry ui-graphics ui-text ui-unit ui-util \
         foundation foundation-layout animation animation-core; do
  fetch androidx/compose/${a%%-*} "${a}-android" "$C12" aar "$GM"
done
fetch androidx/compose/material material-ripple-android "$C12" aar "$GM"
fetch androidx/compose/material material-icons-core-android "1.7.8" aar "$GM"
fetch androidx/compose/material3 material3-android "1.4.0" aar "$GM"
fetch androidx/compose/material3 material3-window-size-class-android "1.4.0" aar "$GM"

echo "=== ACTIVITY 1.13.0 ==="
fetch androidx/activity activity "1.13.0" aar "$GM"
fetch androidx/activity activity-compose-android "1.13.0" aar "$GM" || \
  fetch androidx/activity activity-compose "1.13.0" aar "$GM"
fetch androidx/activity activity-ktx "1.13.0" aar "$GM"

echo "=== LIFECYCLE 2.11.0 ==="
for a in lifecycle-runtime lifecycle-runtime-ktx lifecycle-runtime-compose lifecycle-viewmodel \
         lifecycle-viewmodel-compose lifecycle-viewmodel-savedstate lifecycle-livedata \
         lifecycle-livedata-core lifecycle-process; do
  fetch androidx/lifecycle "${a}-android" "2.11.0" aar "$GM" || fetch androidx/lifecycle "$a" "2.11.0" aar "$GM"
done
fetch androidx/lifecycle lifecycle-common "2.11.0" jar "$MC"

echo "=== NAVIGATION 2.9.8 + NAVIGATIONEVENT 1.0.0 ==="
for a in navigation-compose navigation-runtime navigation-common; do
  fetch androidx/navigation "${a}-android" "2.9.8" aar "$GM" || fetch androidx/navigation "$a" "2.9.8" aar "$GM"
done
fetch androidx/navigationevent navigationevent-android "1.0.0" aar "$GM" || fetch androidx/navigationevent navigationevent "1.0.0" aar "$GM"
fetch androidx/navigationevent navigationevent-compose-android "1.0.0" aar "$GM" || fetch androidx/navigationevent navigationevent-compose "1.0.0" aar "$GM"

echo "=== CORE / SAVEDSTATE / MISC ==="
fetch androidx/core core "1.19.0" aar "$GM"
fetch androidx/core core-ktx "1.19.0" aar "$GM"
fetch androidx/core core-viewtree "1.0.0" aar "$GM"
fetch androidx/savedstate savedstate-android "1.4.0" aar "$GM" || fetch androidx/savedstate savedstate "1.4.0" aar "$GM"
fetch androidx/savedstate savedstate-compose-android "1.4.0" aar "$GM" || fetch androidx/savedstate savedstate-compose "1.4.0" aar "$GM"
fetch androidx/annotation annotation-jvm "1.4.1" aar "$GM" || fetch androidx/annotation annotation "1.4.1" aar "$GM"
fetch androidx/annotation annotation-experimental "1.4.1" aar "$GM"
fetch androidx/customview customview-poolingcontainer "1.0.0" aar "$GM"
fetch androidx/emoji2 emoji2 "1.4.0" aar "$GM"
fetch androidx/startup startup-runtime "1.1.1" aar "$GM"
fetch androidx/tracing tracing-android "1.2.0" aar "$GM" || fetch androidx/tracing tracing "1.2.0" aar "$GM"
fetch androidx/profileinstaller profileinstaller "1.4.0" aar "$GM"
fetch androidx/autofill autofill "1.0.0" aar "$GM"
fetch androidx/arch/core core-runtime "2.2.0" aar "$GM"
fetch androidx/arch/core core-common "2.2.0" jar "$GM"

echo "=== KOTLINX COROUTINES 1.9.0 + ATOMICFU ==="
fetch org/jetbrains/kotlinx kotlinx-coroutines-core-jvm "1.9.0" jar "$MC"
fetch org/jetbrains/kotlinx kotlinx-coroutines-android "1.9.0" jar "$MC"
fetch org/jetbrains/kotlinx atomicfu-jvm "0.23.2" jar "$MC"
fetch org/jetbrains/kotlinx kotlinx-collections-immutable-jvm "0.3.7" jar "$MC" || true

echo "=== KOTLIN STDLIB (version compose 1.11.4 built against) ==="
fetch org/jetbrains/kotlin kotlin-stdlib "2.2.0" jar "$MC" || true
fetch org/jetbrains/kotlin kotlin-stdlib "2.1.20" jar "$MC" || true
