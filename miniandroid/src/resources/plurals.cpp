// plurals.cpp — C9-20 (CODER 9) implementation. See plurals.h for the
// source-backed contract and the documented CLDR rule subset.

#include "plurals.h"

namespace miniandroid {
namespace resources {

PluralsQuantity cldr_quantity_law(const std::string& locale, int64_t n) {
    // primary language subtag: strip region/script ("-IR", "-Latn"),
    // lowercase (locale tags are case-insensitive for the subtag).
    std::string lang;
    for (char c : locale) {
        if (c == '-' || c == '_') break;
        lang += (char)((c >= 'A' && c <= 'Z') ? c + 32 : c);
    }
    if (lang == "fa") {
        // CLDR fa: one for i = 0..1 (Persian counts zero as "one").
        return (n == 0 || n == 1) ? PluralsQuantity::ONE
                                  : PluralsQuantity::OTHER;
    }
    if (lang == "ar") {
        if (n == 0) return PluralsQuantity::ZERO;
        if (n == 1) return PluralsQuantity::ONE;
        if (n == 2) return PluralsQuantity::TWO;
        const int64_t m = n % 100;
        if (m >= 3 && m <= 10) return PluralsQuantity::FEW;
        if (m >= 11 && m <= 99) return PluralsQuantity::MANY;
        return PluralsQuantity::OTHER;
    }
    if (lang == "ru") {
        const int64_t i10 = n % 10, i100 = n % 100;
        if (i10 == 1 && i100 != 11) return PluralsQuantity::ONE;
        if (i10 >= 2 && i10 <= 4 && !(i100 >= 12 && i100 <= 14))
            return PluralsQuantity::FEW;
        return PluralsQuantity::MANY;
    }
    // default (en + every unlisted language): one iff n == 1.
    return (n == 1) ? PluralsQuantity::ONE : PluralsQuantity::OTHER;
}

uint32_t plurals_bag_key(PluralsQuantity q) {
    const uint8_t i = (uint8_t)q;
    return i < 6 ? kPluralsKey[i] : kPluralsKey[5];
}

}  // namespace resources
}  // namespace miniandroid
