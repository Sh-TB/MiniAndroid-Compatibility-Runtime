# EXP-067 Decisions Log

Record architectural decisions with rationale.

## D001: Keep resolve_*_for_dex() pattern, no DexContext refactor
**Date:** EXP-066
**Decision:** Keep the existing `resolve_string_for_dex / resolve_type_for_dex / resolve_method_name_for_dex / resolve_method_class_for_dex` helper pattern.
**Rationale:** EXP-066 audit confirmed 0 remaining UNSAFE occurrences. A full DexContext refactor would touch many files for no semantic gain. The helpers are well-tested and the pattern is clear.
**Revisit if:** A new opcode handler is added that needs per-DEX resolution and the helper pattern becomes unwieldy.

## D002: Use Pillow + DejaVuSans for text rasterization
**Date:** EXP-064
**Decision:** Renderer uses Pillow (PIL) + DejaVuSans TTF for CPU-only text rasterization.
**Rationale:** Pillow is widely available, CPU-only, supports freetype. No GPU required. DejaVuSans has good Latin coverage.
**Revisit if:** Need CJK/Arabic/emoji glyph coverage, or vector drawable rendering requires a different raster path.
