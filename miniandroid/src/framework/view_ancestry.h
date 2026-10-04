// view_ancestry.h — AOSP framework View-class ancestry law (FIX-G12-001).
//
// Law source: AOSP frameworks/base core/java/android/{view,widget}/*.java.
// The Android widget hierarchy is FIXED by the framework — every runtime
// that implements a framework subset must know the ancestry of the classes
// it implements, or superclass-based semantics (container classification,
// measure/layout behavior, dispatch) silently degrade:
//
//   G10 corpus evidence: app classes (CalculatorDisplay extends
//   LinearLayout) were classified through the app-DEX superclass chain, but
//   FRAMEWORK classes (TableLayout/TableRow extend LinearLayout,
//   ScrollView extends FrameLayout, ...) had NO ancestry layer and fell
//   back to descriptor-substring tests — "Landroid/widget/TableRow;" does
//   not contain the substring "Layout", so TableRow was classified as a
//   LEAF and measured 0x0 while its children measured 44px (G11/G12
//   headingcalculator display-grid failure).
//
// This table is the single authority for FRAMEWORK ancestry; app-DEX
// classes resolve through their DEX superclass chain first and fall into
// this table when the chain exits app code (CustomView -> LinearLayout ->
// ViewGroup -> View).
//
// Multi-hop chains work: callers walk one hop at a time
// (TableRow -> LinearLayout -> ViewGroup -> View).
#ifndef MINIANDROID_VIEW_ANCESTRY_H
#define MINIANDROID_VIEW_ANCESTRY_H

#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <map>

namespace miniandroid {
namespace framework {

// Direct-superclass law for the framework classes this runtime implements.
// Values are DEX descriptors exactly as written in AOSP `extends` clauses.
inline const std::unordered_map<std::string, std::string>&
framework_direct_superclass() {
    static const std::unordered_map<std::string, std::string> kTable = {
        // view hierarchy root
        {"Landroid/view/View;", "Ljava/lang/Object;"},
        {"Landroid/view/ViewGroup;", "Landroid/view/View;"},
        // core containers (AOSP: X extends Y as written)
        {"Landroid/widget/FrameLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/LinearLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/RelativeLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/TableLayout;", "Landroid/widget/LinearLayout;"},
        {"Landroid/widget/TableRow;", "Landroid/widget/LinearLayout;"},
        {"Landroid/widget/GridLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/AbsoluteLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/ScrollView;", "Landroid/widget/FrameLayout;"},
        {"Landroid/widget/HorizontalScrollView;", "Landroid/widget/FrameLayout;"},
        {"Landroid/widget/ViewAnimator;", "Landroid/widget/FrameLayout;"},
        {"Landroid/widget/ViewSwitcher;", "Landroid/widget/ViewAnimator;"},
        {"Landroid/widget/ViewFlipper;", "Landroid/widget/ViewAnimator;"},
        // text hierarchy (AOSP: Button extends TextView — NOT View)
        {"Landroid/widget/TextView;", "Landroid/view/View;"},
        {"Landroid/widget/Button;", "Landroid/widget/TextView;"},
        {"Landroid/widget/EditText;", "Landroid/widget/TextView;"},
        {"Landroid/widget/CompoundButton;", "Landroid/widget/Button;"},
        {"Landroid/widget/CheckBox;", "Landroid/widget/CompoundButton;"},
        {"Landroid/widget/RadioButton;", "Landroid/widget/CompoundButton;"},
        {"Landroid/widget/ToggleButton;", "Landroid/widget/CompoundButton;"},
        // image hierarchy
        {"Landroid/widget/ImageView;", "Landroid/view/View;"},
        {"Landroid/widget/ImageButton;", "Landroid/widget/ImageView;"},
        // spinner/adapterview (minimal, law-correct)
        {"Landroid/widget/AdapterView;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/ListView;", "Landroid/widget/AdapterView;"},
        {"Landroid/widget/GridView;", "Landroid/widget/AbsListView;"},
        {"Landroid/widget/AbsListView;", "Landroid/widget/AdapterView;"},
        {"Landroid/widget/Spinner;", "Landroid/widget/AbsSpinner;"},
        {"Landroid/widget/AbsSpinner;", "Landroid/widget/AdapterView;"},
        // ── F-NEW-225c (user campaign §B/§I companion): JDK COLLECTION
        // HIERARCHY (OpenJDK/libcore source — the canonical direct
        // superclass of every core container). The hierarchy walk and the
        // getGenericSuperclass law both need the JDK family, not just the
        // view family: Gson's ReflectiveTypeAdapterFactory.getBoundFields
        // climbs ArrayList → AbstractList → AbstractCollection → Object on
        // every reflective serialization. AOSP android.jar ships the same
        // libcore classes; these edges are the source truth.
        {"Ljava/util/ArrayList;", "Ljava/util/AbstractList;"},
        {"Ljava/util/AbstractList;", "Ljava/util/AbstractCollection;"},
        {"Ljava/util/AbstractCollection;", "Ljava/lang/Object;"},
        {"Ljava/util/LinkedList;", "Ljava/util/AbstractSequentialList;"},
        {"Ljava/util/AbstractSequentialList;", "Ljava/util/AbstractList;"},
        {"Ljava/util/Vector;", "Ljava/util/AbstractList;"},
        {"Ljava/util/Stack;", "Ljava/util/Vector;"},
        {"Ljava/util/HashMap;", "Ljava/util/AbstractMap;"},
        {"Ljava/util/AbstractMap;", "Ljava/lang/Object;"},
        {"Ljava/util/LinkedHashMap;", "Ljava/util/HashMap;"},
        {"Ljava/util/Hashtable;", "Ljava/util/Dictionary;"},
        {"Ljava/util/Dictionary;", "Ljava/lang/Object;"},
        {"Ljava/util/HashSet;", "Ljava/util/AbstractSet;"},
        {"Ljava/util/AbstractSet;", "Ljava/util/AbstractCollection;"},
        {"Ljava/util/LinkedHashSet;", "Ljava/util/HashSet;"},
        {"Ljava/util/TreeSet;", "Ljava/util/AbstractSet;"},
        {"Ljava/util/TreeMap;", "Ljava/util/AbstractMap;"},
        {"Ljava/util/PriorityQueue;", "Ljava/util/AbstractQueue;"},
        {"Ljava/util/AbstractQueue;", "Ljava/util/AbstractCollection;"},
        {"Ljava/util/ArrayDeque;", "Ljava/util/AbstractCollection;"},
        {"Ljava/util/concurrent/ConcurrentHashMap;",
         "Ljava/util/AbstractMap;"},
        {"Ljava/util/concurrent/ConcurrentLinkedQueue;",
         "Ljava/util/AbstractQueue;"},
        {"Ljava/util/concurrent/CopyOnWriteArrayList;",
         "Ljava/lang/Object;"},
        {"Ljava/lang/Exception;", "Ljava/lang/Throwable;"},
        {"Ljava/lang/RuntimeException;", "Ljava/lang/Exception;"},
        {"Ljava/lang/IllegalArgumentException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/IllegalStateException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/NullPointerException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/UnsupportedOperationException;",
         "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/IndexOutOfBoundsException;",
         "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/NoSuchElementException;",
         "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/Throwable;", "Ljava/lang/Object;"},
        // F-NEW-226 companion: TextPaint IS-A Paint (AOSP android.text).
        {"Landroid/text/TextPaint;", "Landroid/graphics/Paint;"},
    };
    return kTable;
}

// Descriptor form law (FIX-G12-001b): DEX internals (class_to_superclass_
// maps, method dispatch) use SLASH form (Lfoo/bar/Baz;); the UI layer
// (AXML tags → ViewNode.class_desc) uses DOT form (Lfoo.bar.Baz;). Every
// cross-layer descriptor comparison must normalize first — G11's
// constructor hook normalized for the class-index, but the superclass
// classifier compared raw dot-form keys against slash-form map keys and
// every app container fell through to leaf classification.
// ────────────────────────────────────────────────────────────────────────
// F-NEW-224 (user campaign §B) — ONE CANONICAL DESCRIPTOR NORMALIZATION
// LAW. The four spellings below must resolve IDENTICALLY everywhere:
//     Landroidx/foo/Bar;      ← canonical internal DEX descriptor
//     androidx.foo.Bar        ← bare dotted (manifests, reflection names)
//     androidx/foo/Bar        ← bare slashed
//     Landroidx.foo.Bar;      ← L-form dotted (malformed/toolchain drift)
// Every hierarchy/lookup consumer (superclass walk, method/field/ctor
// resolution, shadow lookup, View/LayoutParams/framework detection) must
// compare ONLY the canonical form — no per-caller string surgery.
// Primitives (I, Z, J...), arrays ([I, [Ljava/lang/String;) and already-
// canonical descriptors pass through byte-identically (law: normalization
// is idempotent and never invents a type).
// ────────────────────────────────────────────────────────────────────────
inline std::string normalize_class_desc(const std::string& desc) {
    if (desc.empty()) return desc;
    // Arrays and multi-char non-L forms (e.g. "[I") keep their shape; the
    // ELEMENT descriptor of an array type is normalized recursively below.
    if (desc[0] == '[') {
        std::string elem = desc.substr(1);
        std::string norm_elem = normalize_class_desc(elem);
        return "[" + norm_elem;
    }
    const bool l_form = desc.size() >= 3 && desc.front() == 'L' && desc.back() == ';';
    const std::string body = l_form ? desc.substr(1, desc.size() - 2) : desc;
    if (body.empty()) return desc;
    const bool dotted = body.find('.') != std::string::npos;
    if (!l_form && !dotted && body.find('/') == std::string::npos)
        return desc;  // primitives and other special forms: untouched
    std::string out = body;
    for (auto& c : out)
        if (c == '.') c = '/';
    return l_form || dotted ? "L" + out + ";" : out;
}

// One-hop lookup: the direct framework superclass of `class_desc`, or "".
inline std::string framework_superclass_of(const std::string& class_desc) {
    const auto& t = framework_direct_superclass();
    auto it = t.find(normalize_class_desc(class_desc));
    return it == t.end() ? std::string() : it->second;
}

// ────────────────────────────────────────────────────────────────────────
// F-NEW-236 (fairymahjong F-235 probe face): JDK FRAMEWORK INTERFACE
// HIERARCHY — libcore/AOSP source law. The extends table above carries
// only `extends` edges, so `is_subclass_of` walks ArrayList →
// AbstractList → AbstractCollection → Object and NEVER reaches
// Ljava/util/Collection;: `instanceof Collection/List/Set/Map/Iterable`
// answered FALSE for every framework collection. Live face (fairymahjong
// 88a4cbbe…): Kotlin's compiled toSet() (Ls;.D) branch-tests
// `instance-of Collection` on the 50-tile list → FALSE → the Iterable
// arm built a LinkedHashSet whose Set.size() diverged → the method
// returned kotlin.collections.EmptySet (Lj0;.a) for a 50-element list →
// the BoardShape dedup gate `toSet().size() != tiles.size()` threw the
// game's own IAE "Duplicate tile position" at APP BOUNDARY.
//
// Two libcore tables (source truth, java.util Collections/AbstractX):
//   (a) framework_class_interfaces: DIRECT interfaces each framework
//       class declares (implements clause only — inherited interfaces
//       arrive through the superclass walk + super-interface closure);
//   (b) framework_iface_supers: interface-extends edges of the JDK core
//       interfaces (List/Set/Queue → Collection → Iterable etc.).
// Markers (Cloneable/Serializable/RandomAccess/Comparable/Runnable) have
// no supers; they are membership-only.
// ────────────────────────────────────────────────────────────────────────
inline const std::map<std::string, std::vector<std::string>>&
framework_class_interfaces() {
    static const std::map<std::string, std::vector<std::string>> kTable = {
        // java.util list family (OpenJDK ArrayList/Abstract*.java)
        {"Ljava/util/ArrayList;",
         {"Ljava/util/List;", "Ljava/util/RandomAccess;",
          "Ljava/lang/Cloneable;", "Ljava/io/Serializable;"}},
        {"Ljava/util/AbstractList;", {"Ljava/util/List;"}},
        {"Ljava/util/AbstractCollection;", {"Ljava/util/Collection;"}},
        {"Ljava/util/LinkedList;",
         {"Ljava/util/List;", "Ljava/util/Deque;",
          "Ljava/lang/Cloneable;", "Ljava/io/Serializable;"}},
        {"Ljava/util/AbstractSequentialList;", {"Ljava/util/List;"}},
        {"Ljava/util/Vector;",
         {"Ljava/util/List;", "Ljava/util/RandomAccess;",
          "Ljava/lang/Cloneable;", "Ljava/io/Serializable;"}},
        {"Ljava/util/Stack;", {}},  // Vector's interfaces cover the family
        {"Ljava/util/Arrays$ArrayList;",
         {"Ljava/util/List;", "Ljava/util/RandomAccess;",
          "Ljava/io/Serializable;"}},
        // java.util map family
        {"Ljava/util/HashMap;",
         {"Ljava/util/Map;", "Ljava/lang/Cloneable;",
          "Ljava/io/Serializable;"}},
        {"Ljava/util/AbstractMap;", {"Ljava/util/Map;"}},
        {"Ljava/util/LinkedHashMap;", {}},  // HashMap carries Map
        {"Ljava/util/Hashtable;",
         {"Ljava/util/Map;", "Ljava/io/Serializable;"}},
        {"Ljava/util/TreeMap;",
         {"Ljava/util/NavigableMap;", "Ljava/lang/Cloneable;",
          "Ljava/io/Serializable;"}},
        {"Ljava/util/concurrent/ConcurrentHashMap;",
         {"Ljava/util/concurrent/ConcurrentMap;",
          "Ljava/io/Serializable;"}},
        {"Ljava/util/IdentityHashMap;",
         {"Ljava/util/Map;", "Ljava/lang/Cloneable;",
          "Ljava/io/Serializable;"}},
        {"Ljava/util/EnumMap;", {"Ljava/util/Map;", "Ljava/io/Serializable;",
                                 "Ljava/lang/Cloneable;"}},
        {"Ljava/util/WeakHashMap;", {"Ljava/util/Map;"}},
        // java.util set family
        {"Ljava/util/HashSet;",
         {"Ljava/util/Set;", "Ljava/lang/Cloneable;",
          "Ljava/io/Serializable;"}},
        {"Ljava/util/AbstractSet;", {"Ljava/util/Set;"}},
        {"Ljava/util/LinkedHashSet;", {}},  // HashSet carries Set
        {"Ljava/util/TreeSet;",
         {"Ljava/util/NavigableSet;", "Ljava/lang/Cloneable;",
          "Ljava/io/Serializable;"}},
        {"Ljava/util/concurrent/CopyOnWriteArraySet;",
         {"Ljava/util/Set;", "Ljava/io/Serializable;"}},
        // queue/deque family
        {"Ljava/util/AbstractQueue;", {"Ljava/util/Queue;"}},
        {"Ljava/util/PriorityQueue;",
         {"Ljava/io/Serializable;"}},
        {"Ljava/util/ArrayDeque;",
         {"Ljava/util/Deque;", "Ljava/lang/Cloneable;",
          "Ljava/io/Serializable;"}},
        {"Ljava/util/concurrent/ConcurrentLinkedQueue;",
         {"Ljava/util/Queue;", "Ljava/io/Serializable;"}},
        // other core classes whose interfaces real apps branch on
        {"Ljava/lang/String;",
         {"Ljava/lang/CharSequence;", "Ljava/io/Serializable;",
          "Ljava/lang/Comparable;"}},
        {"Ljava/lang/StringBuilder;", {"Ljava/lang/CharSequence;"}},
        {"Ljava/lang/Integer;", {"Ljava/lang/Comparable;",
                                 "Ljava/io/Serializable;"}},
        {"Ljava/lang/Long;", {"Ljava/lang/Comparable;",
                              "Ljava/io/Serializable;"}},
        {"Ljava/lang/Boolean;", {"Ljava/lang/Comparable;",
                                 "Ljava/io/Serializable;"}},
        {"Ljava/lang/Byte;", {"Ljava/lang/Comparable;",
                              "Ljava/io/Serializable;"}},
        {"Ljava/lang/Short;", {"Ljava/lang/Comparable;",
                               "Ljava/io/Serializable;"}},
        {"Ljava/lang/Character;", {"Ljava/lang/Comparable;",
                                   "Ljava/io/Serializable;"}},
        {"Ljava/lang/Float;", {"Ljava/lang/Comparable;",
                               "Ljava/io/Serializable;"}},
        {"Ljava/lang/Double;", {"Ljava/lang/Comparable;",
                                "Ljava/io/Serializable;"}},
        {"Ljava/util/Date;", {"Ljava/lang/Comparable;",
                              "Ljava/io/Serializable;",
                              "Ljava/lang/Cloneable;"}},
        // android core (executor/looper surfaces apps branch on)
        {"Ljava/util/concurrent/ThreadPoolExecutor;",
         {"Ljava/util/concurrent/Executor;",
          "Ljava/util/concurrent/ExecutorService;"}},
        {"Ljava/util/concurrent/Executors$DelegatedExecutorService;",
         {"Ljava/util/concurrent/Executor;",
          "Ljava/util/concurrent/ExecutorService;"}},
    };
    return kTable;
}

// Interface-extends edges (OpenJDK headers).
inline const std::map<std::string, std::vector<std::string>>&
framework_iface_supers() {
    static const std::map<std::string, std::vector<std::string>> kTable = {
        {"Ljava/util/Collection;", {"Ljava/lang/Iterable;"}},
        {"Ljava/util/List;", {"Ljava/util/Collection;"}},
        {"Ljava/util/Set;", {"Ljava/util/Collection;"}},
        {"Ljava/util/SortedSet;", {"Ljava/util/Set;"}},
        {"Ljava/util/NavigableSet;", {"Ljava/util/SortedSet;"}},
        {"Ljava/util/Queue;", {"Ljava/util/Collection;"}},
        {"Ljava/util/Deque;", {"Ljava/util/Queue;"}},
        {"Ljava/util/SortedMap;", {"Ljava/util/Map;"}},
        {"Ljava/util/NavigableMap;", {"Ljava/util/SortedMap;"}},
        {"Ljava/util/concurrent/ConcurrentMap;", {"Ljava/util/Map;"}},
        {"Ljava/util/concurrent/ExecutorService;",
         {"Ljava/util/concurrent/Executor;"}},
        {"Ljava/util/ListIterator;", {"Ljava/util/Iterator;"}},
        {"Ljava/lang/Appendable;", {}},
        // markers: membership-only, no supers
        {"Ljava/lang/Iterable;", {}},
        {"Ljava/util/Iterator;", {}},
        {"Ljava/util/Map;", {}},
        {"Ljava/util/Map$Entry;", {}},
        {"Ljava/util/RandomAccess;", {}},
        {"Ljava/lang/CharSequence;", {}},
        {"Ljava/lang/Cloneable;", {}},
        {"Ljava/io/Serializable;", {}},
        {"Ljava/lang/Comparable;", {}},
        {"Ljava/lang/Runnable;", {}},
        {"Ljava/util/Comparator;", {}},
    };
    return kTable;
}

// Transitive interface closure of `cls` through BOTH tables + the
// framework extends table (a superclass's implemented interfaces belong
// to the subclass). BFS, cycle-safe, bounded.
inline void framework_interface_closure(const std::string& class_desc,
                                        std::unordered_set<std::string>& out) {
    const auto& direct = framework_class_interfaces();
    const auto& supers = framework_iface_supers();
    std::vector<std::string> queue;
    std::string cur = normalize_class_desc(class_desc);
    // the class's own extends chain contributes its ancestors' interfaces
    for (int hops = 0; hops < 16 && !cur.empty() &&
                       cur != "Ljava/lang/Object;"; ++hops) {
        auto dit = direct.find(cur);
        if (dit != direct.end())
            for (const auto& i : dit->second)
                if (out.insert(normalize_class_desc(i)).second)
                    queue.push_back(normalize_class_desc(i));
        cur = framework_superclass_of(cur);
    }
    // super-interface closure (interface-extends edges)
    for (size_t qi = 0; qi < queue.size() && qi < 64; ++qi) {
        auto sit = supers.find(queue[qi]);
        if (sit != supers.end())
            for (const auto& s : sit->second)
                if (out.insert(normalize_class_desc(s)).second)
                    queue.push_back(normalize_class_desc(s));
    }
}

// Law: `class_desc` IS-A `iface_desc` through the framework interface
// hierarchy (covers the class itself being an interface, e.g.
// List is-a Collection).
inline bool framework_implements(const std::string& class_desc,
                                 const std::string& iface_desc) {
    std::string want = normalize_class_desc(iface_desc);
    if (want.empty()) return false;
    std::string cur = normalize_class_desc(class_desc);
    if (cur == want) return true;
    if (cur == "Ljava/lang/Object;" || cur.empty()) return false;
    std::unordered_set<std::string> closure;
    framework_interface_closure(cur, closure);
    return closure.count(want) != 0;
}

// Walks the FRAMEWORK table (multi-hop, cycle-safe): true when class_desc
// is-a ancestor_desc through the AOSP hierarchy. App classes whose DEX
// chain is unknown here simply return false — the caller (DEX classifier
// or descriptor fallback) layers its own resolution around this.
inline bool framework_is_subclass(const std::string& class_desc,
                                  const std::string& ancestor_desc) {
    if (ancestor_desc.empty()) return false;
    std::string current = normalize_class_desc(class_desc);
    const std::string want = normalize_class_desc(ancestor_desc);
    for (int hops = 0; hops < 16 && !current.empty(); ++hops) {
        if (current == want) return true;
        if (current == "Ljava/lang/Object;") return false;
        current = framework_superclass_of(current);
    }
    return false;
}

}  // namespace framework
}  // namespace miniandroid

#endif  // MINIANDROID_VIEW_ANCESTRY_H
