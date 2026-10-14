    // ────────────────────────────────────────────────────────────────────────
    // F-NEW-333 (CONT-56b) — Preconditions.checkNotNull IDENTITY law.
    // AOSP support-lib Preconditions.java:
    //     static <T> T checkNotNull(T reference, Object errorMessage) {
    //         if (reference == null)
    //             throw new NullPointerException(String.valueOf(errorMessage));
    //         return reference;                       ← THE LAW: identity
    //     }
    // The EXP-058 STUB-ONLY skip in try_recursive_invoke guards a real
    // recursion, but it left the bridge with NO law for the call — the
    // fallback shadow dispatch answered null and the move-result-object
    // DESTROYED every value passing through checkNotNull. Measured
    // (bmi_402 at the CONT-56b baseline): FragmentHostCallback.<init>
    // received the Handler argument (ARG-TRACE p3 obj#29 — the value
    // survived the field read), the ctor's internal
    // checkNotNull(handler,"handler == null") returned null → iput stored
    // mHandler=<unset> → getHandler() answered null → scheduleCommit's
    // Handler.post ran on a NULL receiver (ROOT-059 null-recv route) → the
    // fragment transaction runnable was dropped → the fragment never
    // instantiated → BMI/alex rendered the uniform dark default frame.
    // The identity law is the generic repair: same contract for the 1-arg
    // and 2-arg overloads, NPE on null (AOSP).
    // ────────────────────────────────────────────────────────────────────────
    if (class_name == "Landroid/support/v4/util/Preconditions;" &&
        method == "checkNotNull" && !args.empty()) {
        bool arg_is_null =
            args[0].is_null ||
            (args[0].type == DalvikType::OBJECT_REF &&
             args[0].object_id == 0);
        if (arg_is_null) {
            std::string msg333 = "null";
            if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF)
                msg333 = args[1].string_val;
            else if (args.size() >= 2 &&
                     args[1].type == DalvikType::OBJECT_REF &&
                     args[1].object_id != 0 &&
                     heap_.has_object(args[1].object_id)) {
                auto s333 = heap_.get_object_field(args[1].object_id,
                                                   "__referent_desc");
                if (s333.has_value())
                    msg333 = s333->string_val;
            }
            throw_deferred("Ljava/lang/NullPointerException;", msg333,
                           "preconditions-checknotnull");
            result = DalvikValue::make_null();
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        result = args[0];
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }
    // ────────────────────────────────────────────────────────────────────────
    // F-NEW-334 (CONT-56b) — android.util.SparseArray container law (the
    // faithful AOSP subset the support FragmentManager bookkeeping needs).
    // SparseArray had NO law: <init>/put/size/valueAt all REC-MISSed to
    // silent defaults — FragmentManagerImpl.makeActive put fragments into
    // mActive (no-op) and moveToState's `for (i < mActive.size())` loop
    // iterated ZERO entries → the committed fragment never advanced past
    // INITIALIZING → performCreateView/onCreateView never ran → the
    // container stayed empty (measured: bmi_402 — transaction executed
    // green after F-NEW-331/332/333, then the mActive walk found nothing).
    // AOSP law (android.util.SparseArray): key-sorted int→Object map;
    // put replaces in place; size counts live entries; valueAt/keyAt
    // index the ASCENDING-KEY order (binary-search insert law); get(key)
    // answers null (or the 2-arg default) when absent; delete/remove/
    // clear maintain the count. Storage: heap fields keyed
    // "__sa:has:<K>" (presence) + "__sa:val:<K>" (value) + "__sa:size".
    // Bounded scan (corpus fragment counts are tens).
    // ────────────────────────────────────────────────────────────────────────
    if (class_name == "Landroid/util/SparseArray;" &&
        (method == "<init>" || method == "put" || method == "append" ||
         method == "size" || method == "get" || method == "valueAt" ||
         method == "keyAt" || method == "indexOfKey" ||
         method == "delete" || method == "remove" || method == "clear")) {
        static thread_local uint64_t f334_arr = 0;
        if (f334_arr < 16) {
            ++f334_arr;
            std::cerr << "[F-NEW-334] SparseArray law: " << method
                      << " recv="
                      << ((!args.empty() &&
                           args[0].type == DalvikType::OBJECT_REF)
                              ? args[0].object_id
                              : 0u)
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
        uint32_t sa334 = (!args.empty() &&
                          args[0].type == DalvikType::OBJECT_REF)
                             ? args[0].object_id
                             : 0;
        if (sa334 != 0 && heap_.has_object(sa334)) {
            auto sa_size334 = [&]() -> int32_t {
                auto v = heap_.get_object_field(sa334, "__sa:size");
                return (v.has_value() &&
                        v->type == DalvikType::INT32)
                           ? v->int_val
                           : 0;
            };
            auto sa_has334 = [&](int32_t k) -> bool {
                auto v = heap_.get_object_field(
                    sa334, "__sa:has:" + std::to_string(k));
                return v.has_value() && v->type == DalvikType::INT32 &&
                       v->int_val != 0;
            };
            if (method == "<init>") {
                heap_.set_object_field(sa334, "__sa:size",
                                       DalvikValue::make_int(0));
                result = DalvikValue::make_void();
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "put" || method == "append") {
                if (args.size() >= 3 &&
                    args[1].type == DalvikType::INT32) {
                    int32_t k334 = args[1].int_val;
                    bool present334 = sa_has334(k334);
                    if (!present334)
                        heap_.set_object_field(
                            sa334, "__sa:size",
                            DalvikValue::make_int(sa_size334() + 1));
                    heap_.set_object_field(
                        sa334, "__sa:has:" + std::to_string(k334),
                        DalvikValue::make_int(1));
                    heap_.set_object_field(
                        sa334, "__sa:val:" + std::to_string(k334), args[2]);
                }
                result = DalvikValue::make_void();
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "size") {
                result = DalvikValue::make_int(sa_size334());
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "get") {
                if (args.size() >= 2 &&
                    args[1].type == DalvikType::INT32) {
                    int32_t k334 = args[1].int_val;
                    if (sa_has334(k334)) {
                        auto v = heap_.get_object_field(
                            sa334, "__sa:val:" + std::to_string(k334));
                        if (v.has_value()) { result = *v;
                            status = ApiCallTrace::Status::IMPLEMENTED;
                            return true; }
                    }
                    // AOSP: absent → null (2-arg: the default)
                    if (args.size() >= 3) result = args[2];
                    else result = DalvikValue::make_null();
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    return true;
                }
            }
            // Ascending-key index law helper: collect present keys.
            auto sa_keys334 = [&]() {
                std::vector<int32_t> ks;
                const auto* hobj334 = heap_.get(sa334);
                if (hobj334) {
                    for (const auto& kv : hobj334->fields) {
                        if (kv.first.rfind("__sa:has:", 0) == 0 &&
                            kv.second.type == DalvikType::INT32 &&
                            kv.second.int_val != 0) {
                            try {
                                ks.push_back(std::stoi(
                                    kv.first.substr(9)));
                            } catch (...) {}
                            if (ks.size() >= 4096) break;
                        }
                    }
                }
                std::sort(ks.begin(), ks.end());
                return ks;
            };
            if (method == "valueAt" || method == "keyAt") {
                int32_t idx334 = (args.size() >= 2 &&
                                  args[1].type == DalvikType::INT32)
                                     ? args[1].int_val
                                     : -1;
                auto ks334 = sa_keys334();
                if (idx334 >= 0 &&
                    idx334 < static_cast<int32_t>(ks334.size())) {
                    if (method == "keyAt") {
                        result = DalvikValue::make_int(ks334[idx334]);
                    } else {
                        auto v = heap_.get_object_field(
                            sa334,
                            "__sa:val:" + std::to_string(ks334[idx334]));
                        result = v.has_value() ? *v
                                               : DalvikValue::make_null();
                    }
                } else if (method == "keyAt") {
                    result = DalvikValue::make_int(0);
                } else {
                    result = DalvikValue::make_null();
                }
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "indexOfKey") {
                int32_t k334 = (args.size() >= 2 &&
                                args[1].type == DalvikType::INT32)
                                   ? args[1].int_val
                                   : 0;
                auto ks334 = sa_keys334();
                int32_t ans334 = -1;
                for (size_t i334 = 0; i334 < ks334.size(); ++i334)
                    if (ks334[i334] == k334) {
                        ans334 = static_cast<int32_t>(i334);
                        break;
                    }
                result = DalvikValue::make_int(ans334);
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "delete" || method == "remove") {
                if (args.size() >= 2 &&
                    args[1].type == DalvikType::INT32) {
                    int32_t k334 = args[1].int_val;
                    if (sa_has334(k334)) {
                        heap_.set_object_field(
                            sa334, "__sa:has:" + std::to_string(k334),
                            DalvikValue::make_int(0));
                        heap_.set_object_field(
                            sa334, "__sa:size",
                            DalvikValue::make_int(sa_size334() - 1));
                    }
                }
                result = DalvikValue::make_void();
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "clear") {
                const auto* hobj334 = heap_.get(sa334);
                if (hobj334) {
                    for (const auto& kv : hobj334->fields) {
                        if (kv.first.rfind("__sa:has:", 0) == 0 &&
                            kv.second.type == DalvikType::INT32 &&
                            kv.second.int_val != 0)
                            heap_.set_object_field(
                                sa334, kv.first,
                                DalvikValue::make_int(0));
                    }
                }
                heap_.set_object_field(sa334, "__sa:size",
                                       DalvikValue::make_int(0));
                result = DalvikValue::make_void();
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
        }
    }
