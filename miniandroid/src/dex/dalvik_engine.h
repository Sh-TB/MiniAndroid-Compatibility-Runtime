/*
 * MiniAndroid Runtime - Real Dalvik Execution Engine (public contract)
 *
 * W23-03 header-cascade redesign: the public header now carries ONLY the
 * stable shared surface — opcode constants, value/register/frame/heap/
 * call-stack types, execution traces and DalvikExecutionResult — verbatim
 * relocated from the former monolithic header (see
 * dalvik_engine_types.h). The DalvikExecutionEngine class definition is
 * implementation detail and lives in dalvik_engine_impl.h, included only
 * by the engine-family translation units and their tests. A change to
 * engine internals therefore no longer recompiles unrelated consumers
 * (evidence/w23/W23_DEPENDENCY_ANALYSIS.md).
 */

#ifndef MINIANDROID_REAL_DALVIK_ENGINE_H
#define MINIANDROID_REAL_DALVIK_ENGINE_H

#include "dalvik_engine_types.h"

namespace miniandroid {
namespace dalvik {

class DalvikExecutionEngine;  // definition: dalvik_engine_impl.h

} // namespace dalvik
} // namespace miniandroid

#endif  // MINIANDROID_REAL_DALVIK_ENGINE_H
// W23-BENCH op=G run=1 t=1795118471
// W23-BENCH op=G run=2 t=1795118472
// W23-BENCH op=G run=3 t=1795118473
// W23-BENCH op=G run=1 t=1795125724
// W23-BENCH op=G run=2 t=1795125725
