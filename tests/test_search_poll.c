/* Offline regression for filtered catalog polling on the audio thread. */
static unsigned scans;
#define MANAGER_VIEW_SCAN() (++scans)
#include "../native/manager.c"
#include <assert.h>
int main(void) {
    mgr_t *m = calloc(1, sizeof *m); assert(m);
    pthread_mutex_init(&m->mu, NULL);
    m->dev = calloc(1, sizeof *m->dev); assert(m->dev);
    strcpy(m->pkg[0].id,"pulytek"); strcpy(m->pkg[3].id,"dexed-dx7");
    m->npkg=6;m->loaded=1;
    char image[32];mgr_get_param(m,"r1_preview",image,sizeof image);assert(atoi(image)==preview_frame("pulytek"));
    mgr_set_param(m,"page_next","1");mgr_get_param(m,"r1_preview",image,sizeof image);assert(atoi(image)==preview_frame("dexed-dx7"));
    mgr_set_param(m,"page_prev","1");mgr_get_param(m,"r1_preview",image,sizeof image);assert(atoi(image)==preview_frame("pulytek"));
    m->page=0;m->rev++;
    m->searching = 1; m->loaded = 1; m->npkg = MAXPKG;
    for (int i=0; i<MAXPKG; i++) {
        snprintf(m->pkg[i].name, sizeof m->pkg[i].name, "Catalog plugin %d", i);
        strcpy(m->pkg[i].summary, "Long catalog description with synthesizer and effect metadata");
    }
    strcpy(m->pkg[511].id,"airwindows-air3");
    strcpy(m->query_draft, "plugin 511");
    mgr_set_param(m, "source_scan", "1");
    char b[192];
    mgr_get_param(m,"r1_preview",image,sizeof image);assert(atoi(image)==preview_frame("airwindows-air3"));
    m->view_valid=0;scans=0;
    assert(mgr_get_param(m, "display_rev", b, sizeof b)); assert(scans==0);
    const char *keys[]={"card1_1", "card1_1_on", "card2_1", "summary", "r1_state", "empty", "page_txt", "display_rev"};
    unsigned rev=m->rev;
    for (int round=0; round<10000; round++)
        for (unsigned k=0; k<sizeof keys/sizeof keys[0]; k++) mgr_get_param(m,keys[k],b,sizeof b);
    assert(scans==1 && m->rev==rev); /* idle polls neither rescan nor redraw */
    mgr_get_param(m,"card1_1",b,sizeof b); assert(!strcmp(b,"Catalog plugin 511"));
    mgr_set_param(m,"source_clear","1"); scans=0;
    mgr_get_param(m,"card1_1",b,sizeof b); assert(!strcmp(b,"Catalog plugin 0") && scans==1);
    mgr_get_param(m,"card1_1",b,sizeof b); assert(scans==1);
    /* Catalog refresh/state changes invalidate cached matches. */
    strcpy(m->pkg[0].name,"Updated plugin"); m->rev++;
    mgr_get_param(m,"card1_1",b,sizeof b); assert(!strcmp(b,"Updated plugin") && scans==2);
    pthread_mutex_destroy(&m->mu); free(m->dev); free(m);
    puts("Filtered catalog: 80,000 idle reads, one scan, no revision churn; clear and refresh invalidate correctly");
    return 0;
}
