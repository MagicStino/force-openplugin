/* Offline preview codec/cache regression: no network, no device directories. */
#define PREVIEW_DIR "/tmp/openplugin-preview-fixture/cache"
#define BUNDLED_PREVIEW_DIR "/tmp/openplugin-preview-fixture/baked"
#include "../native/manager.c"
#include <assert.h>
int main(void) {
 assert(preview_id_ok("pulytek"));assert(!preview_id_ok("../bad"));
 assert(!preview_decode((const unsigned char*)"bad",3));
 unsigned char rgba[PREVIEW_W*PREVIEW_H*4];memset(rgba,255,sizeof rgba);
 mkdir("/tmp/openplugin-preview-fixture",0700);mkdir(PREVIEW_DIR,0700);mkdir(BUNDLED_PREVIEW_DIR,0700);
 assert(preview_save(BUNDLED_PREVIEW_DIR "/fallback.png",rgba));
 unsigned char *read=preview_read(BUNDLED_PREVIEW_DIR "/fallback.png");assert(read && !memcmp(read,rgba,sizeof rgba));free(read);
 mgr_t *m=calloc(1,sizeof *m);assert(m);pthread_mutex_init(&m->mu,NULL);
 m->npkg=1;strcpy(m->pkg[0].id,"pulytek");m->loaded=1;
 preview_refresh(m);assert(m->rev==1);
 preview_refresh(m);assert(m->rev==1); /* identical pixels cause no display churn */
 read=preview_read(PREVIEW_DIR "/row1.png");assert(read && !memcmp(read,rgba,sizeof rgba));free(read);
 pthread_mutex_destroy(&m->mu);free(m);
 unlink(PREVIEW_DIR "/row1.png");unlink(PREVIEW_DIR "/row2.png");unlink(PREVIEW_DIR "/row3.png");unlink(BUNDLED_PREVIEW_DIR "/fallback.png");
 rmdir(PREVIEW_DIR);rmdir(BUNDLED_PREVIEW_DIR);rmdir("/tmp/openplugin-preview-fixture");
 return 0;
}
