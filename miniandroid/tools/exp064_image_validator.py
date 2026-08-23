#!/usr/bin/env python3
"""
EXP-064 Phase 14: Automated image validator.

Inspects the rendered login_ui.png and determines whether expected text
is actually visible. Combines multiple heuristics so success does not
depend on a single fragile check:

  1. File exists, dimensions, freshness
  2. Non-background pixel density
  3. OCR via Tesseract
  4. Bounding-box-aware text check (cross-reference render_provenance.json)
  5. Contrast / darkness check inside expected text regions

Outputs:
  run/exp064/image_validation.json
"""
import json
import os
import sys
import time
import argparse
import hashlib
from PIL import Image, ImageDraw

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("WARNING: pytesseract not available. OCR check will be skipped.", file=sys.stderr)


def validate(png_path, provenance_path, expected_strings, max_age_seconds=600):
    result = {
        'png_valid': False,
        'fresh': False,
        'png_path': png_path,
        'png_dimensions': None,
        'png_sha256': None,
        'png_size_bytes': 0,
        'non_background_pixel_count': 0,
        'non_background_pixel_percent': 0.0,
        'text_expected': list(expected_strings),
        'text_detected': [],
        'match_rate': 0.0,
        'login_ui_confidence': 'NOT_PROVEN',
        'checks': {},
    }

    # 1. File exists
    if not os.path.exists(png_path):
        result['checks']['file_exists'] = False
        result['checks']['error'] = f'PNG not found: {png_path}'
        return result
    result['checks']['file_exists'] = True

    # 2. Dimensions + size
    img = Image.open(png_path)
    w, h = img.size
    result['png_dimensions'] = [w, h]
    result['png_size_bytes'] = os.path.getsize(png_path)
    result['checks']['dimensions_ok'] = (w > 0 and h > 0)

    # 3. Freshness
    mtime = os.path.getmtime(png_path)
    age = time.time() - mtime
    result['fresh'] = age < max_age_seconds
    result['checks']['fresh'] = result['fresh']
    result['checks']['age_seconds'] = round(age, 1)

    # 4. SHA256
    with open(png_path, 'rb') as f:
        result['png_sha256'] = hashlib.sha256(f.read()).hexdigest()

    # 5. Non-background pixel density (sample grid)
    pixels = img.load()
    non_bg = 0
    sample_step = max(1, w // 200)
    total_samples = 0
    bg_color = (255, 255, 255)
    for y in range(0, h, sample_step):
        for x in range(0, w, sample_step):
            total_samples += 1
            p = pixels[x, y]
            if isinstance(p, tuple) and len(p) >= 3:
                r, g, b = p[0], p[1], p[2]
                # Not background if any channel differs by > 20
                if abs(r - 255) > 20 or abs(g - 255) > 20 or abs(b - 255) > 20:
                    non_bg += 1
    result['non_background_pixel_count'] = non_bg
    result['non_background_pixel_percent'] = round(100.0 * non_bg / max(total_samples, 1), 2)
    result['checks']['has_content_pixels'] = non_bg > 100

    # 6. Load provenance for bounding-box-aware check
    text_regions = []
    if provenance_path and os.path.exists(provenance_path):
        with open(provenance_path) as f:
            prov = json.load(f)
        for tr in prov.get('text_rendered', []):
            text_regions.append({
                'text': tr.get('text', ''),
                'bounds': tr.get('bounds', []),
                'object_id': tr.get('object_id'),
                'class': tr.get('class', ''),
            })
    result['text_regions_count'] = len(text_regions)

    # 7. Pixel-density check inside each text region
    region_findings = []
    for r in text_regions:
        if not r['bounds'] or len(r['bounds']) != 4:
            continue
        x, y, rw, rh = r['bounds']
        if rw <= 0 or rh <= 0:
            continue
        dark_pixels = 0
        total = 0
        for yy in range(y, min(y + rh, h), 2):
            for xx in range(x, min(x + rw, w), 2):
                total += 1
                p = pixels[xx, yy]
                if isinstance(p, tuple) and len(p) >= 3:
                    # Dark = text-like pixel
                    if p[0] < 100 and p[1] < 100 and p[2] < 100:
                        dark_pixels += 1
                    elif p[0] > 100 and p[1] < 100 and p[2] < 100:
                        # Yellow label (debug mode) — also non-background
                        dark_pixels += 1
        density = dark_pixels / max(total, 1)
        region_findings.append({
            'object_id': r['object_id'],
            'text_snippet': r['text'][:50],
            'bounds': r['bounds'],
            'dark_pixel_density': round(density, 4),
            'has_text_pixels': density > 0.005,
        })
    result['region_findings'] = region_findings
    result['checks']['text_regions_have_pixels'] = sum(1 for r in region_findings if r['has_text_pixels']) > 0

    # 8. OCR
    if HAS_OCR:
        try:
            # Use --psm 11 (sparse text) for UI screenshots
            text = pytesseract.image_to_string(img, config='--psm 11')
            result['ocr_raw_text'] = text.strip()
            # Normalize for matching
            normalized = ' '.join(text.split())
            result['ocr_normalized'] = normalized

            detected = []
            for expected in expected_strings:
                # Match case-insensitively, allow partial (substring)
                exp_lower = expected.lower()
                norm_lower = normalized.lower()
                # Try exact substring, or fuzzy (Levenshtein-ish: token overlap)
                if exp_lower in norm_lower:
                    detected.append(expected)
                else:
                    # Token overlap: count shared words
                    exp_tokens = set(exp_lower.split())
                    norm_tokens = set(norm_lower.split())
                    overlap = len(exp_tokens & norm_tokens)
                    if overlap >= 1 and overlap / max(len(exp_tokens), 1) >= 0.5:
                        detected.append(expected)
            result['text_detected'] = detected
            result['match_rate'] = round(len(detected) / max(len(expected_strings), 1), 2)
            result['checks']['ocr_ran'] = True
        except Exception as e:
            result['checks']['ocr_ran'] = False
            result['checks']['ocr_error'] = str(e)
    else:
        result['checks']['ocr_ran'] = False

    # 9. Final confidence
    has_pixels = result['checks'].get('has_content_pixels', False)
    has_text_regions = result['checks'].get('text_regions_have_pixels', False)
    ocr_match_rate = result.get('match_rate', 0.0)

    if ocr_match_rate >= 0.5 and has_pixels and has_text_regions:
        result['login_ui_confidence'] = 'PROVEN'
    elif has_pixels and has_text_regions and ocr_match_rate > 0:
        result['login_ui_confidence'] = 'PARTIAL'
    elif has_pixels:
        result['login_ui_confidence'] = 'WEAK'
    else:
        result['login_ui_confidence'] = 'NOT_PROVEN'

    result['png_valid'] = (result['checks'].get('file_exists') and
                            result['checks'].get('dimensions_ok') and
                            has_pixels)

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--png',         default='run/exp064/login_ui.png')
    ap.add_argument('--provenance', default='run/exp064/render_provenance.json')
    ap.add_argument('--out',        default='run/exp064/image_validation.json')
    ap.add_argument('--expected',   default='Please confirm your country code and enter your phone number,Start Messaging',
                    help='Comma-separated list of expected strings')
    args = ap.parse_args()

    expected = [s.strip() for s in args.expected.split(',') if s.strip()]
    result = validate(args.png, args.provenance, expected)
    with open(args.out, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(json.dumps(result, indent=2, default=str)[:4000])
    print(f"\n[EXP064-VALIDATOR] Validation written to {args.out}")
    print(f"[EXP064-VALIDATOR] Confidence: {result['login_ui_confidence']}")
    sys.exit(0 if result['login_ui_confidence'] in ('PROVEN',) else 1)


if __name__ == '__main__':
    main()
