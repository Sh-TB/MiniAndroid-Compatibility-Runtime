#include "/home/z/my-project/miniandroid/src/jni/native_dep.h"
#include <cstdio>
int main(int argc, char** argv) {
    std::vector<std::string> out; std::string why;
    bool ok = miniandroid::jni::list_dt_needed(argv[1], out, why);
    printf("ok=%d rows=%zu why=%s\n", (int)ok, out.size(), why.c_str());
    for (auto& s : out) printf("  NEEDED %s\n", s.c_str());
    return 0;
}
