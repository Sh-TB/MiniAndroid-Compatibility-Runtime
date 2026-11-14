#!/usr/bin/env python3
"""Insert the 4 F596-P1 contract rows (r11-r14) into the s236 battery.

r11 Instant identity+value, r12 negative epoch-milli round-trip,
r13 getXml leak-shape -> real empty parser, r14 getXml app-missing ->
deferred NotFoundException (errors stay visible).
"""
from pathlib import Path

P = Path("/tmp/s236_int/miniandroid/tests/s236_port_laws_test.cpp")
s = P.read_text()

FN = '''
// ── F596-P1 contract rows (pre-merge review, #596 paths receipt) ────────
// Executable proofs for the two integrated laws (see the commit message):
static void run_f596_contract_rows(DalvikExecutionEngine& engine,
                                   flw::ShadowRegistry& registry) {
    (void)registry;
    auto& heap = engine.get_heap_public();
    uint32_t res = heap.allocate("Landroid/content/res/Resources;", 0, 0);

    // r11 — Instant identity + value: TWO now() calls are TWO distinct
    // live objects, each answering its OWN real epoch-milli (never null,
    // never shared storage).
    DalvikValue i1, i2, ms1, ms2;
    bool ok1 = bridge(engine, "Ljava/time/Instant;", "now", {}, i1);
    bool ok2 = bridge(engine, "Ljava/time/Instant;", "now", {}, i2);
    bridge(engine, "Ljava/time/Instant;", "toEpochMilli", {i1}, ms1);
    bridge(engine, "Ljava/time/Instant;", "toEpochMilli", {i2}, ms2);
    record("r11_f596_instant_identity_value",
           ok1 && ok2 && i1.type == DalvikType::OBJECT_REF &&
               i2.type == DalvikType::OBJECT_REF && i1.object_id != 0 &&
               i1.object_id != i2.object_id &&
               ms1.type == DalvikType::INT64 &&
               ms2.type == DalvikType::INT64 && ms1.long_val > 0 &&
               ms2.long_val > 0 && ms1.long_val != ms2.long_val,
           "oid1=" + std::to_string(i1.object_id) + " oid2=" +
               std::to_string(i2.object_id) + " ms1=" +
               std::to_string(ms1.long_val) + " ms2=" +
               std::to_string(ms2.long_val) +
               " (distinct identities, distinct real values)");

    // r12 — ofEpochMilli NEGATIVE: verbatim round-trip (OpenJDK:
    // pre-1970 epoch-milli is VALID — no clamp, no exception).
    int64_t neg = -1234567890123LL;
    DalvikValue ni, nms;
    bool okn = bridge(engine, "Ljava/time/Instant;", "ofEpochMilli",
                      {DalvikValue::make_long(neg)}, ni);
    bridge(engine, "Ljava/time/Instant;", "toEpochMilli", {ni}, nms);
    record("r12_f596_instant_negative_epoch",
           okn && ni.type == DalvikType::OBJECT_REF && ni.object_id != 0 &&
               nms.type == DalvikType::INT64 && nms.long_val == neg,
           "roundtrip=" + std::to_string(nms.long_val) +
               " (verbatim -1234567890123)");

    // r13 — getXml on the UPSTREAM-LEAK id (0xFFFFFFFF): a REAL
    // XmlPullParser object over the empty document — never null, never a
    // fabricated throw (the F513-scope law family).
    DalvikValue leak;
    bool okl = bridge(engine, "Landroid/content/res/Resources;", "getXml",
                      {DalvikValue::make_object(
                           res, "Landroid/content/res/Resources;"),
                       DalvikValue::make_int((int32_t)0xFFFFFFFF)},
                      leak);
    record("r13_f596_getxml_leak_empty_parser",
           okl && leak.type == DalvikType::OBJECT_REF &&
               leak.object_id != 0,
           "obj#" + std::to_string(leak.object_id) +
               " (the empty-document parser, no throw)");

    // r14 — getXml on a genuinely-missing APP id (0x7f…): the deferred
    // NotFoundException — legitimate resource errors stay VISIBLE (the
    // honest null answer, no fabricated parser object).
    DalvikValue miss;
    bool okm = bridge(engine, "Landroid/content/res/Resources;", "getXml",
                      {DalvikValue::make_object(
                           res, "Landroid/content/res/Resources;"),
                       DalvikValue::make_int((int32_t)0x7fffff01)},
                      miss);
    record("r14_f596_getxml_app_missing_throws",
           okm && miss.object_id == 0,
           "obj#" + std::to_string(miss.object_id) +
               " (0 == the deferred NotFoundException, nothing fabricated)");
}

int main(int argc, char** argv) {'''

assert "int main(int argc, char** argv) {" in s
s = s.replace("int main(int argc, char** argv) {", FN, 1)

# safer anchor: the exact call line
OLD_CALL2 = "    run_port_rows(engine, registry);\n"
assert OLD_CALL2 in s
s = s.replace(OLD_CALL2,
              "    run_port_rows(engine, registry);\n"
              "    run_f596_contract_rows(engine, registry);\n", 1)

P.write_text(s)
print("contract rows inserted (r11-r14)")
