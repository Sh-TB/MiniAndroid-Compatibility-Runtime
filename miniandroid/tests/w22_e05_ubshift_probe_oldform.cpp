// AUD-47 (#627 E-05): the PRE-W22-A const/high16 form, deliberately left
// undefined. Under `make UBSAN=1` (-fsanitize=undefined
// -fno-sanitize-recover=all) the negative signed left shift must abort with
// a nonzero exit — the machine reproduction of the hub's
// "UBSan -fsanitize=shift on (int32_t)(int16_t)0xFFFF << 16 -> exit 1"
// evidence (issue #627, comment 6991611630). A clean exit 0 under the
// sanitizer profile means the UBSAN=1 flags are broken: verification FAIL.
#include <cstdint>
#include <cstdio>

int main() {
    int16_t bbbb = static_cast<int16_t>(0xFFFF);  // -1
    // The pre-W22-A form: shift of a NEGATIVE signed value — C++17
    // [expr.shift] UB (E1 must be non-negative). -fno-sanitize-recover
    // aborts here; the printf below is reachable only without the sanitizer.
    int32_t v = static_cast<int32_t>(bbbb) << 16;
    std::printf("oldform computed %08X — UBSan did NOT fire (BAD)\n",
                static_cast<uint32_t>(v));
    return 0;
}
