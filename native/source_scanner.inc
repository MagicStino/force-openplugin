/* GitHub source discovery. Imported files are checksummed; scanning executes no package scripts.
 * Version 1 supports portable armv7 MPC release zips with GitHub SHA-256 asset digests.
 * Ordinary desktop VST source repos are deliberately not treated as installable plugins. */
typedef struct { char name[160], url[512], digest[80]; } source_asset;
typedef struct { source_asset assets[24]; int n; char repo[160]; } source_release;
#ifndef SOURCE_CACHE
#define SOURCE_CACHE "/data/openplugin/sources.json"
#endif
#ifndef SOURCE_DIR
#define SOURCE_DIR "/data/openplugin"
#endif
static int source_pkg_valid(const pkg_t *p) {
    return p->id[0] && strspn(p->id,"abcdefghijklmnopqrstuvwxyz0123456789-")==strlen(p->id) &&
        p->name[0] && safe(p->name) && p->latest[0] && safe(p->latest) &&
        (!strcmp(p->kind,"instrument") || !strcmp(p->kind,"effect")) &&
        !strncmp(p->url,"https://github.com/",19) &&
        strlen(p->sha)==64 && strspn(p->sha,"0123456789abcdefABCDEF")==64;
}
static void source_json_string(FILE *f,const char *s) {
    fputc('"',f);
    for (;*s;s++) {
        unsigned char c=*s;
        if (c=='"' || c=='\\') { fputc('\\',f);fputc(c,f); }
        else if (c<32) fprintf(f,"\\u%04x",c);
        else fputc(c,f);
    }
    fputc('"',f);
}
static int source_save(const mgr_t *m) { /* worker owns catalog writes during this operation */
    mkdir(SOURCE_DIR,0700);
    FILE *f=fopen(SOURCE_CACHE ".new","w");if (!f) return 0;
    fputs("{\"schema\":1,\"plugins\":[",f);int n=0;
    for (int i=0;i<m->npkg;i++) {
        const pkg_t *p=&m->pkg[i];
        if (strcmp(p->style,"community source") || !source_pkg_valid(p)) continue;
        if (n++) fputc(',',f);
        fputs("{\"id\":",f);source_json_string(f,p->id);
        fputs(",\"name\":",f);source_json_string(f,p->name);
        fputs(",\"kind\":",f);source_json_string(f,p->kind);
        fputs(",\"author\":",f);source_json_string(f,p->author);
        fputs(",\"style\":\"community source\",\"latest\":",f);source_json_string(f,p->latest);
        fputs(",\"versions\":[{\"version\":",f);source_json_string(f,p->latest);
        fputs(",\"url\":",f);source_json_string(f,p->url);
        fputs(",\"sha256\":",f);source_json_string(f,p->sha);
        fprintf(f,",\"channel\":\"stable\",\"size\":%lld}]}",p->size);
    }
    fputs("]}\n",f);int ok=!ferror(f);
    if (fflush(f) || fsync(fileno(f))) ok=0;
    if (fclose(f)) ok=0;
    if (!ok || rename(SOURCE_CACHE ".new",SOURCE_CACHE)) {unlink(SOURCE_CACHE ".new");return 0;}
    return 1;
}
static void source_merge(pkg_t *out,int *count) {
    char *json=slurp(SOURCE_CACHE,2<<20);if (!json) return;
    pkg_t *cache=calloc(MAXPKG,sizeof *cache);if (!cache) {free(json);return;}
    list_t l={cache,0};const char *end=jobject(json,top_member,&l);
    if (end && !*ws(end)) for (int i=0;i<l.n && *count<MAXPKG;i++) {
        if (!source_pkg_valid(&cache[i])) continue;
        int exists=0;for (int j=0;j<*count;j++) if (!strcmp(out[j].id,cache[i].id)) exists=1;
        if (!exists) out[(*count)++]=cache[i];
    }
    free(cache);free(json);
}
static const char *source_asset_field(const char *key, const char *value, void *opaque) {
    source_asset *a = opaque;
    if (!strcmp(key,"name")) return jstr(value,a->name,sizeof a->name);
    if (!strcmp(key,"browser_download_url")) return jstr(value,a->url,sizeof a->url);
    if (!strcmp(key,"digest")) return jstr(value,a->digest,sizeof a->digest);
    return NULL;
}
static const char *source_release_field(const char *key,const char *value,void *opaque) {
    source_release *r = opaque;
    if (strcmp(key,"assets") || *value!='[') return NULL;
    const char *p=ws(value+1);
    while (*p && *p!=']') {
        source_asset a={0}; p=jobject(p,source_asset_field,&a); if (!p) return NULL;
        size_t len=strlen(a.name); const char *suffix="-mpc-armv7.zip";
        if (len>=strlen(suffix) && !strcmp(a.name+len-strlen(suffix),suffix) && r->n<24) r->assets[r->n++]=a;
        p=ws(p); if (*p==',') p=ws(p+1); else break;
    }
    return *p==']'?p+1:NULL;
}
typedef struct { pkg_t pkg; char arch[16], layout[24], repo[160]; int schema; } source_manifest;
static const char *source_manifest_field(const char *key,const char *value,void *opaque) {
    source_manifest *m=opaque;
    if (!strcmp(key,"id")) return jstr(value,m->pkg.id,sizeof m->pkg.id);
    if (!strcmp(key,"name")) return jstr(value,m->pkg.name,sizeof m->pkg.name);
    if (!strcmp(key,"version")) return jstr(value,m->pkg.latest,sizeof m->pkg.latest);
    if (!strcmp(key,"kind")) return jstr(value,m->pkg.kind,sizeof m->pkg.kind);
    if (!strcmp(key,"arch")) return jstr(value,m->arch,sizeof m->arch);
    if (!strcmp(key,"layout")) return jstr(value,m->layout,sizeof m->layout);
    if (!strcmp(key,"source_repo")) return jstr(value,m->repo,sizeof m->repo);
    if (!strcmp(key,"schema")) m->schema=atoi(value);
    return NULL;
}
static void source_message(mgr_t *m,const char *text) {
    pthread_mutex_lock(&m->mu); snprintf(m->source_status,sizeof m->source_status,"%s",text);m->rev++;
    pthread_mutex_unlock(&m->mu);
}
static int source_repo(const char *input,char *out,size_t size) {
    const char *p=input;
    if (!strncmp(p,"https://github.com/",19)) p+=19;
    else if (strstr(p,"://")) return 0;
    if (strlen(p)>=size) return 0;
    snprintf(out,size,"%s",p);
    size_t len=strlen(out); while (len && out[len-1]=='/') out[--len]=0;
    if (len>4 && !strcmp(out+len-4,".git")) out[len-=4]=0;
    char *slash=strchr(out,'/');
    if (!slash || slash==out || !slash[1] || strchr(slash+1,'/')) return 0;
    if (strspn(out,"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._/")!=strlen(out)) return 0;
    if (out[0]=='.' || slash[1]=='.') return 0;
    return 1;
}
static void do_scan(mgr_t *m) {
    char url[160],repo[160],api[256],note[160];
    pthread_mutex_lock(&m->mu); snprintf(url,sizeof url,"%s",m->source_url);pthread_mutex_unlock(&m->mu);
    if (!source_repo(url,repo,sizeof repo)) {source_message(m,"Use https://github.com/owner/repository");return;}
    snprintf(api,sizeof api,"https://api.github.com/repos/%s/releases/latest",repo);
    source_message(m,"Finding compatible packages in the latest release...");
    sink_t data={0};source_release release={0};
    if (fetch(m,api,&data) || !data.buf || !jobject(data.buf,source_release_field,&release)) {
        free(data.buf);source_message(m,"Cannot read releases. Check the URL, network or GitHub rate limit.");return;
    }
    free(data.buf);
    if (!release.n) {source_message(m,"No MPC armv7 packages found. Desktop plugins cannot be installed here.");return;}
    int added=0;
    for (int i=0;i<release.n && !m->quit;i++) {
        source_asset *a=&release.assets[i];
        if (strncmp(a->url,"https://github.com/",19) || strncmp(a->digest,"sha256:",7) || strlen(a->digest+7)!=64 || strspn(a->digest+7,"0123456789abcdefABCDEF")!=64) continue;
        pkg_t candidate={0};snprintf(candidate.id,sizeof candidate.id,"source-scan-%d",i);
        snprintf(candidate.name,sizeof candidate.name,"Community package");
        snprintf(candidate.url,sizeof candidate.url,"%s",a->url);snprintf(candidate.sha,sizeof candidate.sha,"%s",a->digest+7);
        char archive[256],cmd[1000];snprintf(archive,sizeof archive,WORK "/source-scan-%d.zip",i);
        if (download(m,&candidate,archive)) continue;
        struct stat st; if (stat(archive,&st) || st.st_size>(256ll<<20)) {unlink(archive);continue;}
        snprintf(cmd,sizeof cmd,"(ulimit -f 512; unzip -p '%s' '*/mpc-plugin.json' > '" WORK "/source-manifest.json')",archive);
        if (sh(cmd)) {unlink(archive);continue;}
        char *text=slurp(WORK "/source-manifest.json",256<<10);source_manifest mf={0};
        const char *end=text?jobject(text,source_manifest_field,&mf):NULL;
        int valid=end && !*ws(end) && mf.schema==1 && !strcmp(mf.arch,"armv7") && !strcmp(mf.layout,"portable") &&
            !strcasecmp(mf.repo,repo) && mf.pkg.id[0] && mf.pkg.name[0] && mf.pkg.latest[0] && safe(mf.pkg.name) && safe(mf.pkg.latest) &&
            strspn(mf.pkg.id,"abcdefghijklmnopqrstuvwxyz0123456789-")==strlen(mf.pkg.id) &&
            (!strcmp(mf.pkg.kind,"instrument") || !strcmp(mf.pkg.kind,"effect"));
        free(text);
        if (valid) {
            snprintf(mf.pkg.url,sizeof mf.pkg.url,"%s",candidate.url);snprintf(mf.pkg.sha,sizeof mf.pkg.sha,"%s",candidate.sha);
            snprintf(mf.pkg.author,sizeof mf.pkg.author,"%.*s",(int)(strchr(repo,'/')-repo),repo);
            snprintf(mf.pkg.channel,sizeof mf.pkg.channel,"stable");snprintf(mf.pkg.style,sizeof mf.pkg.style,"community source");
            mf.pkg.size=st.st_size;
            pthread_mutex_lock(&m->mu);int exists=0;
            for (int j=0;j<m->npkg;j++) if (!strcmp(m->pkg[j].id,mf.pkg.id)) exists=1;
            if (!exists && m->npkg<MAXPKG) {m->pkg[m->npkg++]=mf.pkg;added++;m->loaded=1;m->tab=0;m->kindf=0;m->rev++;}
            pthread_mutex_unlock(&m->mu);
        }
        unlink(archive);
    }
    snprintf(note,sizeof note,added?"Added %d package(s) to Discover. Review the author, then choose Install.":"No new verified portable packages. A GitHub SHA-256 asset digest is required.",added);
    if (added && !source_save(m)) snprintf(note,sizeof note,"Added %d package(s), but could not save sources. Check internal storage.",added);
    source_message(m,note);
}
