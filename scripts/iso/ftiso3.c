/* S200-T03 harness v3 — char-0 (.notdef) vs real char through the JNI layer. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <stdint.h>
typedef long long jlong_; typedef int jint_;
static void* g_font; static long g_sz;
static void* my_GetDirectBufferAddress(void* env, void* buf) { (void)env; (void)buf; return g_font; }

typedef jlong_ (*init_t)(void*, void*);
typedef jlong_ (*newmem_t)(void*, void*, jlong_, void*, jint_, jint_);
typedef jint_ (*jint3_t)(void*, void*, jlong_, jint_, jint_);
typedef jint_ (*jint2_t)(void*, void*, jlong_, jint_);
typedef jlong_ (*jlongfn)(void*, void*, jlong_);
typedef jlong_ (*jlong2fn)(void*, void*, jlong_, jint_);

int main(void){
  setbuf(stdout,NULL);
  void* h = dlopen("/home/z/my-project/tools/native_host/libgdx-freetype64.so", RTLD_NOW|RTLD_LOCAL|RTLD_DEEPBIND);
  if(!h){printf("dlopen: %s\n",dlerror()); return 1;}
  FILE* f=fopen("/tmp/ftx/assets/fonts/Roboto-Medium.ttf","rb");
  fseek(f,0,SEEK_END); g_sz=ftell(f); fseek(f,0,SEEK_SET);
  g_font=malloc(g_sz); fread(g_font,1,g_sz,f); fclose(f);

  static void* table[300];
  table[230] = (void*)(uintptr_t)my_GetDirectBufferAddress;
  static void* envstruct[2]; envstruct[0] = table;
  void* env = envstruct;

  init_t initF=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_initFreeTypeJni");
  newmem_t newMemFace=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Library_newMemoryFace");
  jint3_t setPx=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Face_setPixelSizes");
  jint3_t loadChar=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Face_loadChar");
  jint2_t getCharIndex=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Face_getCharIndex");
  jlongfn faceGetGlyph=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Face_getGlyph");
  jlongfn slotGetGlyph=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024GlyphSlot_getGlyph");
  jlong2fn toBitmap=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Glyph_toBitmap");
  jlongfn glyphGetBitmap=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Glyph_getBitmap");
  jlongfn bmGetW=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Bitmap_getWidth");
  jlongfn bmGetR=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024Bitmap_getRows");
  jlongfn slotGetMetrics=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024GlyphSlot_getMetrics");
  jlongfn gmGetH=dlsym(h,"Java_com_badlogic_gdx_graphics_g2d_freetype_FreeType_00024GlyphMetrics_getHeight");
  void* token="tok";
  jlong_ lib=initF(env,token); printf("lib=%lld\n",(long long)lib);
  jlong_ face=newMemFace(env,token,lib,g_font,(jint_)g_sz,0); printf("face=%lld\n",(long long)face);
  printf("setPx15=%d setPx120=%d\n",setPx(env,token,face,0,15),setPx(env,token,face,0,120));

  printf("loadChar(0,32)=%d getCharIndex(0)=%d\n",loadChar(env,token,face,0,32),getCharIndex(env,token,face,0));
  jlong_ slot=faceGetGlyph(env,token,face);
  jlong_ m=slotGetMetrics(env,token,slot);
  printf("  notdef h=%d\n",gmGetH(env,token,m));
  jlong_ copy=slotGetGlyph(env,token,slot);
  jlong_ bg=toBitmap(env,token,copy,0);
  jlong_ bm=glyphGetBitmap(env,token,bg);
  printf("  notdef bitmap W=%d R=%d\n",(jint_)bmGetW(env,token,bm),(jint_)bmGetR(env,token,bm));

  printf("loadChar(65,32)=%d getCharIndex(65)=%d\n",loadChar(env,token,face,65,32),getCharIndex(env,token,face,65));
  slot=faceGetGlyph(env,token,face);
  m=slotGetMetrics(env,token,slot);
  printf("  A h=%d\n",gmGetH(env,token,m));
  copy=slotGetGlyph(env,token,slot);
  bg=toBitmap(env,token,copy,0);
  bm=glyphGetBitmap(env,token,bg);
  printf("  A bitmap W=%d R=%d\n",(jint_)bmGetW(env,token,bm),(jint_)bmGetR(env,token,bm));
  return 0;
}
