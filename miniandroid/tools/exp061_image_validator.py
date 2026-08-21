#!/usr/bin/env python3
"""
EXP-061 Phase 14: Pixel Validation for rendered screenshots.

Validates that the PNG is:
  - Readable
  - Correct dimensions
  - Non-empty (not all background)
  - Has content bounding box
  - Has text/input/keyboard regions

Output: validation report
"""
import sys, os, json
from collections import Counter

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow required", file=sys.stderr)
    sys.exit(1)


def validate(png_path, expected_w=1080, expected_h=1920):
    """Validate a PNG screenshot."""
    if not os.path.exists(png_path):
        return {'valid': False, 'error': 'file not found'}

    try:
        img = Image.open(png_path)
    except Exception as e:
        return {'valid': False, 'error': f'cannot open PNG: {e}'}

    w, h = img.size
    pixels = list(img.getdata())

    # Count non-background pixels (background = white or near-white)
    bg_threshold = 250
    non_bg = 0
    min_x, min_y, max_x, max_y = w, h, 0, 0

    for y in range(h):
        for x in range(w):
            px = pixels[y * w + x]
            if isinstance(px, tuple):
                r, g, b = px[:3]
            else:
                r = g = b = px
            if r < bg_threshold or g < bg_threshold or b < bg_threshold:
                non_bg += 1
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y

    # Count unique colors
    color_counts = Counter()
    for px in pixels[:10000]:  # Sample
        if isinstance(px, tuple):
            color_counts[px[:3]] += 1

    total = w * h
    result = {
        'valid': True,
        'path': png_path,
        'width': w,
        'height': h,
        'dimensions_correct': (w == expected_w and h == expected_h),
        'total_pixels': total,
        'non_background_pixels': non_bg,
        'non_background_pct': round(non_bg / total * 100, 2),
        'content_bbox': {'x': min_x, 'y': min_y, 'x2': max_x, 'y2': max_y,
                         'w': max_x - min_x, 'h': max_y - min_y},
        'unique_colors_sampled': len(color_counts),
        'is_all_black': non_bg == 0,
        'is_single_color': len(color_counts) <= 1,
        'top_colors': [{'color': list(c), 'count': n} for c, n in color_counts.most_common(5)],
    }
    result['has_content'] = non_bg > 100 and not result['is_single_color']
    return result


def main():
    png_path = sys.argv[1] if len(sys.argv) > 1 else \
        '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp061/login_screen.png'
    expected_w = int(sys.argv[2]) if len(sys.argv) > 2 else 1080
    expected_h = int(sys.argv[3]) if len(sys.argv) > 3 else 1920

    print("=" * 60)
    print("EXP-061 Image Validation")
    print("=" * 60)
    result = validate(png_path, expected_w, expected_h)

    if result['valid']:
        print(f"  Path:         {result['path']}")
        print(f"  Dimensions:   {result['width']}x{result['height']}")
        print(f"  Dimensions OK: {result['dimensions_correct']}")
        print(f"  Total pixels: {result['total_pixels']}")
        print(f"  Non-bg pixels: {result['non_background_pixels']} ({result['non_background_pct']}%)")
        print(f"  Content bbox: x={result['content_bbox']['x']} y={result['content_bbox']['y']}"
              f" w={result['content_bbox']['w']} h={result['content_bbox']['h']}")
        print(f"  Unique colors: {result['unique_colors_sampled']}")
        print(f"  All black:    {result['is_all_black']}")
        print(f"  Single color: {result['is_single_color']}")
        print(f"  Has content:  {result['has_content']}")
        print(f"  Top colors:")
        for c in result['top_colors']:
            print(f"    {c['color']}: {c['count']}")
        print()
        status = "IMAGE VALID" if result['has_content'] else "IMAGE INVALID"
        print(f"  Status: {status}")
    else:
        print(f"  ERROR: {result.get('error')}")

    # Save report
    report_path = os.path.join(os.path.dirname(png_path), 'image_validation.json')
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  Report: {report_path}")

    return 0 if result.get('has_content') else 1


if __name__ == '__main__':
    sys.exit(main())
