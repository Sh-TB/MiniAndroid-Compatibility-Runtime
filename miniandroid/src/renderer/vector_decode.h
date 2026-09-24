// vector_decode.h — S95 Wave-A (L-S95-VECTOR-1): binary-AXML VectorDrawable
// → RGBA raster inside the ONE format-detecting decoder (S68 §13 law:
// every image consumer goes through decode_image_bytes; a container this
// decoder refuses must be NAMED, never silently dropped).
//
// ROOT CAUSE PROVENANCE (S95 §3, real-APK evidence):
//   bouncy_43 + urlchecker_28 ImageView/ImageButton android:src resources
//   carry BOTH density-bucketed PNGs AND an (anydpi-v21) vector variant.
//   AOSP resource selection (AssetManager2/ResourceTypes.cpp isBetterThan)
//   correctly picks the anydpi-v21 XML on a v21+ device — the runtime then
//   failed at the DECODE bit (no vector rasterizer) and drew the 0xCCCCCC
//   "IMG?" placeholder, classified WRONG_COLOR by the S93 semantic layer.
//
// LAW SOURCES (checked in the S94 registry before writing code — §170):
//   * AOSP frameworks/base graphics/drawable/VectorDrawable.java —
//     viewport mapping, group matrix composition, tint application,
//     getIntrinsicWidth = declared dp × density/160.
//   * AOSP android.util.PathParser — pathData grammar handling
//     (separators, implicit repeats, scientific notation, S/T reflection).
//   * W3C SVG 1.1 spec §F.6 — elliptical-arc endpoint→center conversion.
//   * CDroid src/gui/drawable/{vectordrawable,hwpathparser}.cc @
//     da89e06bc0c7d04e3586f7dfb3f83fe4e658f0fc (LGPL-2.1) — behavioral
//     REFERENCE ONLY (S94 license gate); this file is an independent MIT
//     implementation, no code copied.
//
// Supported subset (deliberate, evidence-driven): <vector> root attrs,
// <group> transforms, <path> pathData/fillColor/fillAlpha/fillType/
// strokeColor/strokeAlpha/strokeWidth, android:tint on the root,
// framework color references (0x0106xxxx). UNSUPPORTED features are
// NAMED errors (never silent): <gradient>, <clip-path>, animated vectors,
// app-package color references that the renderer cannot resolve.
#ifndef MINIANDROID_VECTOR_DECODE_H
#define MINIANDROID_VECTOR_DECODE_H

#include <cstdint>
#include <vector>

#include "software_renderer.h"  // DecodedImage

namespace miniandroid {
namespace renderer {

// Raster size law: declared (width/height dp) × density_dpi/160. When
// density_dpi == 0 (caller has no device context) the viewport is used
// with a 4× density factor clamped to [32, 512] px. Hard cap 2048 px.
// resolver: optional app-resource reference resolver (L-S95-ADAPTIVE-1) —
// needed for <adaptive-icon> layers and app-color fill references.
bool decode_vector_drawable(const std::vector<uint8_t>& axml_bytes,
                            int density_dpi, DecodedImage* out,
                            const VectorRefResolver* resolver = nullptr,
                            int depth = 0);

}  // namespace renderer
}  // namespace miniandroid

#endif  // MINIANDROID_VECTOR_DECODE_H
