/* Live display regression: deterministic HTTPS responses, no device paths/network. */
#define PREVIEW_DIR "/tmp/openplugin-preview-fixture/cache"
#define BUNDLED_PREVIEW_DIR "/tmp/openplugin-preview-fixture/baked"
static int fake_fetch(const char *,void *,void *);
#define PREVIEW_FETCH_TEST(m,url,s) fake_fetch(url,m,s)
#include "../native/manager.c"
#include <assert.h>
static int requests,fetch_mode;
static unsigned char *response;
static int response_len;
static int fake_fetch(const char *url,void *inst,void *ud) {
    mgr_t *m=inst;sink_t *s=ud;requests++;
    assert(!strncmp(url,"https://",8));
    if(fetch_mode==0)return 0;
    if(fetch_mode==2)m->preview_generation++; /* obsolete page while downloading */
    if(fetch_mode==3)return preview_on_data("bad",1,3,s)==3;
    return preview_on_data((char*)response,1,response_len,s)==(size_t)response_len;
}
static void solid(unsigned char *rgba,int r,int g,int b) {
    for(int i=0;i<PREVIEW_W*PREVIEW_H;i++){rgba[i*4]=r;rgba[i*4+1]=g;rgba[i*4+2]=b;rgba[i*4+3]=255;}
}
int main(void) {
    assert(preview_id_ok("tinyfreaky"));assert(!preview_id_ok("../bad"));
    assert(!preview_decode((const unsigned char*)"bad",3));
    sink_t limit={0};limit.len=4u*1024*1024;assert(!preview_on_data("x",1,1,&limit));
    assert(!preview_on_data("x",SIZE_MAX,2,&limit));
    unsigned char rgba[PREVIEW_W*PREVIEW_H*4];solid(rgba,255,255,255);
    mkdir("/tmp/openplugin-preview-fixture",0700);mkdir(PREVIEW_DIR,0700);mkdir(BUNDLED_PREVIEW_DIR,0700);
    assert(preview_save(BUNDLED_PREVIEW_DIR "/fallback.png",rgba));
    mgr_t *m=calloc(1,sizeof *m);assert(m);pthread_mutex_init(&m->mu,NULL);pthread_cond_init(&m->cv,NULL);
    m->preview_enabled=1;m->npkg=4;m->loaded=1;
    strcpy(m->pkg[0].id,"tinyfreaky");strcpy(m->pkg[0].screenshot,"https://example.org/tiny.png");
    strcpy(m->pkg[3].id,"new-plugin");strcpy(m->pkg[3].screenshot,"https://example.org/new.png");
    preview_refresh(m);char b[32];mgr_get_param(m,"previewpx_1_0",b,sizeof b);assert(atoi(b)==0xfff);
    unsigned rev=m->rev;preview_refresh(m);assert(m->rev==rev); /* no churn for identical pixels */
    /* New online pixels are displayed and persisted, even for an ID not in the build snapshot. */
    solid(rgba,255,136,51);response=stbi_write_png_to_mem(rgba,PREVIEW_W*4,PREVIEW_W,PREVIEW_H,4,&response_len);
    assert(response);m->online=1;fetch_mode=1;preview_refresh(m);assert(requests==1);
    mgr_get_param(m,"previewpx_1_0",b,sizeof b);assert(atoi(b)==0xf83);
    unsigned char *read=preview_read(PREVIEW_DIR "/tinyfreaky.png");assert(read && !memcmp(read,rgba,sizeof rgba));free(read);
    preview_refresh(m);assert(requests==1); /* page revisits don't redownload this refresh */
    /* A catalog refresh revalidates even an unchanged URL; corrupt images retain last good cache. */
    fetch_mode=3;m->pkg[0].preview_checked=0;preview_refresh(m);assert(requests==2);
    mgr_get_param(m,"previewpx_1_0",b,sizeof b);assert(atoi(b)==0xf83);
    /* Paging never exposes the previous plugin's pixels, even before the worker runs. */
    mgr_set_param(m,"page_next","1");mgr_get_param(m,"previewpx_1_0",b,sizeof b);assert(atoi(b)==0x111);
    m->job=0;fetch_mode=1;preview_refresh(m);mgr_get_param(m,"previewpx_1_0",b,sizeof b);assert(atoi(b)==0xf83);
    /* Old transfers cannot publish on the new page. */
    strcpy(m->preview_row_id[0],"");m->pkg[3].preview_checked=0;fetch_mode=2;
    unsigned gen=m->preview_generation;preview_refresh(m);assert(m->preview_generation==gen+1);
    /* Offline restart reads the persisted thumbnail without making requests. */
    m->online=0;m->page=0;m->rev++;memset(m->preview_pixels,0,sizeof m->preview_pixels);int before=requests;
    preview_refresh(m);mgr_get_param(m,"previewpx_1_0",b,sizeof b);assert(atoi(b)==0xf83 && requests==before);
    /* Preview parameters are display-only and cannot alter the page or pixel buffer. */
    mgr_set_param(m,"previewpx_1_0","0");mgr_get_param(m,"previewpx_1_0",b,sizeof b);assert(atoi(b)==0xf83);
    free(response);pthread_cond_destroy(&m->cv);pthread_mutex_destroy(&m->mu);free(m);
    unlink(PREVIEW_DIR "/tinyfreaky.png");unlink(PREVIEW_DIR "/new-plugin.png");unlink(BUNDLED_PREVIEW_DIR "/fallback.png");
    rmdir(PREVIEW_DIR);rmdir(BUNDLED_PREVIEW_DIR);rmdir("/tmp/openplugin-preview-fixture");
    puts("PASS live online pixels, new IDs, corrupt downloads, page identity, offline cache and bounded transfer");return 0;
}
