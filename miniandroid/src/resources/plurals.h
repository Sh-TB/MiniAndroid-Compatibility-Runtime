// plurals.h — C9-20 (CODER 9) — CLDR plural-category selection law.
//
// AOSP contract (frameworks/base, core/java/android/content/res/PluralRules
// ↔ icu4c PluralRules.forLocale().select(quantity)):
//   * Resources.getQuantityString(id, quantity) takes the NUMBER and
//     internally maps it to the CLDR category (zero/one/two/few/many/other)
//     for the resource's locale, THEN reads the matching bag item.
//   * The plurals bag keys are the android attrs (aapt2 8.13.2 ground
//     truth, probe /tmp/plur_probe — resources.arsc byte dump):
//       zero=0x01000004  one=0x01000005  two=0x01000006
//       few=0x01000007   many=0x01000008 other=0x01000009
//
// Documented law subset (CLDR 46 rules, integer operands only — the
// runtime resolves integer quantities; fractional rules are recorded as
// a PENDING divergence, honest-miss to OTHER):
//   default / en: one iff n == 1; else other
//   fa:           one iff n == 0 or n == 1; else other
//   ar:           zero 0 · one 1 · two 2 · few n%100∈[3,10] ·
//                 many n%100∈[11,99] · else other
//   ru:           one (i%10==1 && i%100!=11) · few (i%10∈[2,4] &&
//                 !(i%100∈[12,14])) · many (integral rest) · other
// Unknown locales take the default (en) rules — the same fallback icu4c
// ships for unlisted languages.

#ifndef MINIANDROID_RESOURCES_PLURALS_H
#define MINIANDROID_RESOURCES_PLURALS_H

#include <cstdint>
#include <string>

namespace miniandroid {
namespace resources {

// The CLDR plural categories — bag-key order matches the attr ids above.
enum class PluralsQuantity : uint8_t {
    ZERO = 0, ONE, TWO, FEW, MANY, OTHER,
};

// The aapt2-pinned bag keys (see header comment — ground truth above).
constexpr uint32_t kPluralsKey[6] = {
    0x01000004,  // zero
    0x01000005,  // one
    0x01000006,  // two
    0x01000007,  // few
    0x01000008,  // many
    0x01000009,  // other
};

// CLDR selection law (pure, deterministic). locale is the BCP-47/ISO form
// ("en", "fa-IR", "ar", "ru-RU" — only the primary subtag matters for the
// documented subset). n is the integer quantity.
PluralsQuantity cldr_quantity_law(const std::string& locale, int64_t n);

// Bag-key lookup: the ARSC complex-entry key for a category.
uint32_t plurals_bag_key(PluralsQuantity q);

}  // namespace resources
}  // namespace miniandroid

#endif  // MINIANDROID_RESOURCES_PLURALS_H
