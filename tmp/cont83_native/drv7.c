#include <dlfcn.h>
#include <stdio.h>
int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    void* a = dlopen("/home/z/my-project/miniandroid/build/anchor_libs/libm.so", RTLD_LAZY | RTLD_GLOBAL);
    printf("anchor libm -> %s\n", a ? "ok" : dlerror());
    dlerror();
    void* g = dlopen("/home/z/my-project/tmp/cont83_native/lib/x86_64/libnatprobe.so", RTLD_NOW | RTLD_LOCAL);
    printf("app lib -> %s\n", g ? "ok" : dlerror());
    if (g) {
        int (*f)(int,int,int) = (int(*)(int,int,int))dlsym(g, "Java_com_probe_nat1_NativeProbe_add3");
        printf("add3(2,3,4) = %d\n", f ? f(2,3,4) : -1);
        int (*m)(int) = (int(*)(int))dlsym(g, "Java_com_probe_nat1_NativeProbe_mathCheck");
        printf("mathCheck(9) = %d\n", m ? m(9) : -1);
    }
    return 0;
}
