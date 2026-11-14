// A-R6 R30 — KOTLIN WELL-KNOWN-TYPES SHADOW — roadmap §8 F (Kotlin/JVM
// interop) family law carrier.
//
// ROOT GAP (the A-R6 first-ever family review, base 1a0fa259):
// roadmap §8 F1 carries 9 unchecked rows (Unit · Pair · Triple · default
// arguments · synthetic $default · generated component methods · copy ·
// sequence basics) audited unchecked at the reconciliation pass, the
// runtime source carried ZERO Kotlin-specific dispatch surface (no shadow
// claimed any Lkotlin/* class), and the kotlin_family_probe census at
// 1a0fa259 measured the host-boundary world (the Kotlin class absent from
// the DexReport — every R8-minified APK and every synthetic/probe report):
//
//   a1 Unit.INSTANCE identity .......... null (the unresolved-static law
//                                        answers NULL silently)
//   b1 Pair component identity ......... dead (no <init>/component bodies)
//   b2 Pair.toString ................... dead
//   c1 interface default body dispatch . answers 0 (the engine's own
//                                        EXP-071 comments name this face:
//                                        "invoke-interface dispatch for
//                                        $default methods fails")
//   d1 Intrinsics non-null ............. no-op (accidentally correct)
//   d2 Intrinsics null ................. SILENT SUCCESS (Kotlin law:
//                                        NullPointerException) — every
//                                        "parameter specified as non-null"
//                                        contract is unenforceable
//
// LAWS TRANSFERRED (Tier 1 — kotlin stdlib public API contracts):
//   * kotlin.Unit — object declaration: exactly ONE instance per runtime;
//     `Unit` is loaded from the static INSTANCE field. MiniAndroid law:
//     get_or_create_singleton("Lkotlin/Unit;") — one heap object per
//     engine, identity-stable across reads and static-field roundtrips.
//   * kotlin.Pair(first, second) — constructor stores both arguments
//     VERBATIM; component1()/component2() return them (data-class-like
//     product semantics); toString() == "($first, $second)" with String
//     arguments printed as content (Kotlin string templates never quote).
//   * kotlin.Triple(first, second, third) — same product semantics,
//     component3() returns the third; toString() == "($first, $second,
//     $third)".
//   * kotlin.jvm.internal.Intrinsics.checkNotNullParameter(ref, name) /
//     checkNotNullExpressionValue(ref, name) / checkNotNull(ref, message):
//     null reference → NullPointerException("Parameter specified as
//     non-null is null: " + name) — the compiler-minted null-safety
//     contract; non-null → no-op. The engine's exception channel (the
//     CallResult is_exc face, the Thread.setPriority convention) delivers
//     the throw.
//
// DOCUMENTED BOUNDARIES (honest, per K-6):
//   * Only the FOUR well-known types are claimed (Unit · Pair · Triple ·
//     Intrinsics). Broader kotlin.* classes (collections, sequences,
//     coroutines) execute as guest DEX when the APK bundles the stdlib —
//     the #380 hypothesis-A path — and stay untouched here.
//   * toString() for non-String, non-null arguments renders the runtime
//     class's readable form (no fabricated content); the value-carrying
//     identity semantics live in componentN(), which is what consumers
//     destructure through.
//   * Intrinsics variants that need more than the message argument
//     (throwUninitializedPropertyAccessException) keep their DEX body when
//     the stdlib is bundled and are NOT claimed here.

#ifndef MINIANDROID_FRAMEWORK_KOTLIN_SHADOW_H_
#define MINIANDROID_FRAMEWORK_KOTLIN_SHADOW_H_

#include "shadow_registry.h"

#include <string>
#include <vector>

namespace miniandroid {
namespace framework {

class KotlinShadow : public Shadow {
public:
    std::string name() const override { return "KotlinShadow"; }

    bool handles_class(const std::string& class_name) const override;
    CallResult dispatch(const CallContext& ctx) override;

    std::vector<std::string> implemented_methods() const override;
    std::vector<std::string> stubbed_methods() const override;
};

}  // namespace framework
}  // namespace miniandroid

#endif  // MINIANDROID_FRAMEWORK_KOTLIN_SHADOW_H_
