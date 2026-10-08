/* Offline tests: no network, no worker thread, no device or service changes. */
#define SOURCE_CACHE "source-cache.json"
#define SOURCE_DIR "."
#include "../native/manager.c"
#include <assert.h>
int main(void) {
    char repo[160];
    assert(source_repo("https://github.com/WorldLinkStudio/mpcsample",repo,sizeof repo));
    assert(!strcmp(repo,"WorldLinkStudio/mpcsample"));
    assert(source_repo("owner/repo.git/",repo,sizeof repo));
    assert(!strcmp(repo,"owner/repo"));
    assert(!source_repo("https://evil.test/owner/repo",repo,sizeof repo));
    assert(!source_repo("owner/repo/releases",repo,sizeof repo));
    assert(!source_repo("../repo",repo,sizeof repo));
    source_release release={0};
    assert(jobject("{\"assets\":[{\"name\":\"Desktop.dmg\"},{\"name\":\"synth-mpc-armv7.zip\",\"digest\":\"sha256:abc\"}]}",source_release_field,&release));
    assert(release.n==1 && !strcmp(release.assets[0].name,"synth-mpc-armv7.zip"));
    pkg_t imported={0};
    strcpy(imported.id,"synth");strcpy(imported.name,"Synth");strcpy(imported.kind,"instrument");
    strcpy(imported.latest,"1.0");strcpy(imported.url,"https://github.com/owner/repo/releases/download/v1/synth-mpc-armv7.zip");
    memset(imported.sha,'a',64);assert(source_pkg_valid(&imported));
    strcpy(imported.url,"file:///etc/passwd");assert(!source_pkg_valid(&imported));
    mgr_t *model=calloc(1,sizeof *model); assert(model);
    pthread_mutex_init(&model->mu,NULL);
    model->searching=1;model->npkg=2;
    strcpy(model->pkg[0].name,"Dream Synth");strcpy(model->pkg[0].author,"Community");strcpy(model->pkg[0].url,"https://example.test/a.zip");
    strcpy(model->pkg[1].name,"Room Reverb");strcpy(model->pkg[1].url,"https://example.test/b.zip");
    int matches[MAXPKG]; assert(visible(model,matches)==2);
    strcpy(model->query,"SYNTH");assert(visible(model,matches)==1 && matches[0]==0);
    strcpy(model->query,"community");assert(visible(model,matches)==1);
    strcpy(model->query,"no-such-sound");assert(visible(model,matches)==0);
    mgr_set_param(model,"source_clear","1");assert(!model->query[0]);
    mgr_set_param(model,"source_key_0","1");assert(!strcmp(model->query,"a"));
    mgr_set_param(model,"source_key_0","0");assert(!strcmp(model->query,"a"));
    mgr_set_param(model,"source_back","1");assert(!model->query[0]);
    mgr_set_param(model,"source_search","1");assert(!model->searching);
    mgr_set_param(model,"source_clear","1");assert(!strcmp(model->source_url,"https://github.com/"));
    model->busy=J_SCAN;mgr_set_param(model,"source_key_0","1");assert(!strcmp(model->source_url,"https://github.com/"));
    char oldcwd[4096];assert(getcwd(oldcwd,sizeof oldcwd));
    char temp[]="./openplugin-cache-test-XXXXXX";assert(mkdtemp(temp));assert(!chdir(temp));
    model->npkg=1;model->pkg[0]=imported;
    strcpy(model->pkg[0].url,"https://github.com/owner/repo/releases/download/v1/synth-mpc-armv7.zip");
    strcpy(model->pkg[0].style,"community source");strcpy(model->pkg[0].name,"Dream \"Synth\"");
    assert(source_save(model));
    pkg_t *roundtrip=calloc(MAXPKG,sizeof *roundtrip);assert(roundtrip);int count=0;
    source_merge(roundtrip,&count);assert(count==1);
    assert(!strcmp(roundtrip[0].name,"Dream \"Synth\"") && !strcmp(roundtrip[0].sha,model->pkg[0].sha));
    source_merge(roundtrip,&count);assert(count==1); /* no duplicate imports */
    free(roundtrip);assert(!unlink(SOURCE_CACHE));assert(!chdir(oldcwd));assert(!rmdir(temp));
    pthread_mutex_destroy(&model->mu);free(model);
    char *catalog = calloc(1, 20000);
    strcpy(catalog, "{\"schema\":1,\"plugins\":[");
    for (int i = 0; i < 100; i++) {
        char entry[150];
        snprintf(entry, sizeof entry, "%s{\"id\":\"plugin-%d\",\"name\":\"Plugin %d\",\"kind\":\"instrument\"}", i ? "," : "", i, i);
        strcat(catalog, entry);
    }
    strcat(catalog, "]}");
    pkg_t *pkgs = calloc(MAXPKG, sizeof *pkgs);
    list_t list = {pkgs, 0};
    assert(jobject(catalog, top_member, &list));
    assert(list.n == 100); /* regression: upstream silently stopped at 64 */
    assert(!sha_ok("'$(touch /tmp/openplugin-should-not-exist)'", "/tmp/missing"));
    sink_t sink = {0};
    assert(on_data("x", 1, (16u << 20) + 1, &sink) == 0);
    int16_t audio[256];
    memset(audio, 0xff, sizeof audio);
    mgr_render(NULL, audio, 128);
    for (int i = 0; i < 256; i++) assert(audio[i] == 0);
    pkg_t p = {0};
    strcpy(p.installed, "1.0.0"); strcpy(p.latest, "1.1.0"); strcpy(p.url, "https://example.test/a.zip");
    assert(has_update(&p));
    strcpy(p.latest, "1.0.0"); assert(!has_update(&p));
    free(pkgs); free(catalog);
    puts("native offline tests: PASS");
    return 0;
}
