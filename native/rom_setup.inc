/* JV-880 content setup: external archive, never bundled in firmware. */
static const char *rom_names[5]={"jv880_rom1.bin","jv880_rom2.bin","jv880_waverom1.bin","jv880_waverom2.bin","jv880_nvram.bin"};
static const long rom_sizes[5]={32768,262144,2097152,2097152,32768};
#define ROM_ARCHIVE_SHA "f29a3d59bce0e46696d6b618fe8c2d40d2db92459a8e7c2ca114f196cfde7cf4"
static int rom_regular(const char *p,long size) {struct stat st;return !lstat(p,&st)&&S_ISREG(st.st_mode)&&st.st_size==size;}
static void rom_message(mgr_t *m,const char *s) {pthread_mutex_lock(&m->mu);snprintf(m->rom_status,sizeof m->rom_status,"%s",s);say_locked(m,OK,"JV-880: %s",s);pthread_mutex_unlock(&m->mu);}
static int rom_folder(const device_t *d,char *out,size_t n) {
    for(int i=0;i<d->nent;i++) if(!strcasecmp(d->ent[i].uid,"4a563838") || !strcasecmp(d->ent[i].name,"JV-880")) {
        char folder[512];snprintf(folder,sizeof folder,"%s",d->ent[i].file);
        char *slash=strrchr(folder,'/');if(!slash)return 0;*slash=0;
        /* Require the portable package; never write to an arbitrary registration. */
        if(!strstr(folder,"/sd88me - VST - JV-880"))return 0;
        char meta[600];snprintf(meta,sizeof meta,"%s/plugin-meta.xml",folder);
        if(!is_file(meta))return 0;
        snprintf(out,n,"%s/jv880-roms/roms",folder);return 1;
    }return 0;
}
static int rom_check(mgr_t *m,const char *folder) {
    int good=0;pthread_mutex_lock(&m->mu);
    for(int i=0;i<5;i++) {char p[768];snprintf(p,sizeof p,"%s/%s",folder,rom_names[i]);
        int ok=rom_regular(p,rom_sizes[i]);good+=ok;
        snprintf(m->rom_files[i],sizeof m->rom_files[i],"%s: %s",rom_names[i],ok?"Present (size OK)":is_file(p)?"Wrong size / type":"Missing");
    }m->rev++;pthread_mutex_unlock(&m->mu);return good;
}
static int rom_copy_missing(const char *src,const char *dst) {
    int in=open(src,O_RDONLY|O_NOFOLLOW);if(in<0)return 0;
    int out=open(dst,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0644);
    if(out<0){int exists=errno==EEXIST;close(in);return exists;}
    char buf[16384];ssize_t got;int ok=1;
    while((got=read(in,buf,sizeof buf))>0){ssize_t off=0;while(off<got){ssize_t w=write(out,buf+off,got-off);if(w<=0){ok=0;break;}off+=w;}if(!ok)break;}
    if(got<0||fsync(out))ok=0;close(in);if(close(out))ok=0;if(!ok)unlink(dst);return ok;
}
static int rom_mkdir(const char *p) {struct stat st;if(!mkdir(p,0755))return 1;return errno==EEXIST&&!lstat(p,&st)&&S_ISDIR(st.st_mode);}
static int rom_import(mgr_t *m,const char *zip,const char *folder) {
    if(!sha_ok(ROM_ARCHIVE_SHA,zip)){rom_message(m,"Archive fingerprint differs. Nothing imported. See the ROM instructions for your own dump.");return 0;}
    char stage[] = WORK "/roms-XXXXXX";if(!mkdtemp(stage))return 0;
    char *args[]={"unzip","-q","-j",(char*)zip,(char*)rom_names[0],(char*)rom_names[1],(char*)rom_names[2],(char*)rom_names[3],(char*)rom_names[4],"-d",stage,NULL};
    int ok=run(args)==0;
    for(int i=0;i<5;i++){char p[768];snprintf(p,sizeof p,"%s/%s",stage,rom_names[i]);if(!rom_regular(p,rom_sizes[i]))ok=0;}
    char parent[768];snprintf(parent,sizeof parent,"%s",folder);char *sl=strrchr(parent,'/');if(sl)*sl=0;
    if(ok)ok=rom_mkdir(parent)&&rom_mkdir(folder);
    for(int i=0;i<5&&ok;i++){char src[768],dst[768];snprintf(src,sizeof src,"%s/%s",stage,rom_names[i]);snprintf(dst,sizeof dst,"%s/%s",folder,rom_names[i]);ok=rom_copy_missing(src,dst);}
    for(int i=0;i<5;i++){char p[768];snprintf(p,sizeof p,"%s/%s",stage,rom_names[i]);unlink(p);}rmdir(stage);
    int good=rom_check(m,folder);
    rom_message(m,ok&&good==5?"5 files present. Close and reload JV-880. ROM version/audio remain unverified; skin issues are separate.":"Import incomplete. Existing files were preserved. Check missing/wrong-size entries, then retry.");return ok&&good==5;
}
static void do_rom_setup(mgr_t *m,int job) {
    device_t *d=calloc(1,sizeof *d);if(!d)return;probe_device(d);
    char folder[768];int found=rom_folder(d,folder,sizeof folder);free(d);
    if(!found){rom_message(m,"Install JV-880's portable package first, then choose Check files.");return;}
    if(job==J_ROM_CHECK){int n=rom_check(m,folder);char msg[160];snprintf(msg,sizeof msg,"%d/5 required files present (size check). Unload JV-880 before importing. Expansions are optional.",n);rom_message(m,msg);return;}
    if(job==J_ROM_DOWNLOAD){
        struct statvfs sv;if(statvfs(WORK,&sv)||sv.f_bavail*(unsigned long long)sv.f_frsize<200ull*1024*1024){rom_message(m,"Need 200 MiB free temporary space. Use USB import instead.");return;}
        pkg_t p={0};snprintf(p.name,sizeof p.name,"JV ROM archive");snprintf(p.url,sizeof p.url,"https://archive.org/download/jv880_rompack_v1/jv880_rompack_v1.zip");snprintf(p.sha,sizeof p.sha,ROM_ARCHIVE_SHA);
        rom_message(m,"Downloading external archive. Progress appears in the catalog footer; internet required.");
        if(download(m,&p,WORK "/jv880-rompack.zip")){rom_message(m,"Download failed. Check internet and retry, or import the archive from USB.");return;}
        rom_import(m,WORK "/jv880-rompack.zip",folder);unlink(WORK "/jv880-rompack.zip");return;
    }
    /* Only known filenames at mount roots; no recursive scanning or shell interpolation. */
    static const char *roots[]={"/media","/mnt"};
    for(int r=0;r<2;r++){DIR *dir=opendir(roots[r]);struct dirent *e;
        while(dir&&(e=readdir(dir))){if(e->d_name[0]=='.')continue;char zip[768];snprintf(zip,sizeof zip,"%s/%s/jv880_rompack_v1.zip",roots[r],e->d_name);
            struct stat st;if(!lstat(zip,&st)&&S_ISREG(st.st_mode)){closedir(dir);rom_import(m,zip,folder);return;}}
        if(dir)closedir(dir);
    }rom_message(m,"USB archive not found. Put jv880_rompack_v1.zip at the USB/SD drive root, then tap Import USB.");
}
