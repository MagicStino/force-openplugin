/* Device-side previews: network and decoding run only on the manager worker. */
#define STB_IMAGE_STATIC
#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_PNG
#define STBI_ONLY_JPEG
#define STBI_ONLY_GIF
#define STBI_ONLY_BMP
#include "third_party/stb/stb_image.h"
#define STB_IMAGE_WRITE_STATIC
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "third_party/stb/stb_image_write.h"
#ifndef PREVIEW_DIR
#define PREVIEW_DIR "/data/openplugin/previews"
#endif
#ifndef BUNDLED_PREVIEW_DIR
#define BUNDLED_PREVIEW_DIR "/usr/share/openplugin/bundled-previews"
#endif
#define PREVIEW_W 180
#define PREVIEW_H 90
static int visible(const mgr_t *, int *);
static int preview_id_ok(const char *id) {
    return *id && strlen(id)<48 && strspn(id,"abcdefghijklmnopqrstuvwxyz0123456789-_")==strlen(id);
}
static int preview_fetch(mgr_t *m,const char *url,sink_t *s) {
    if(strncmp(url,"https://",8) || strlen(url)>1023 || !curl_load()) return 0;
    CURL *c=cu.init();if(!c)return 0;
    prog_t g={m,NULL,0,-1};
    cu.setopt(c,CU_URL,url);cu.setopt(c,CU_FOLLOWLOCATION,1L);
    cu.setopt(c,181,2L);cu.setopt(c,182,2L);
    cu.setopt(c,CU_FAILONERROR,1L);cu.setopt(c,CU_CONNECTTIMEOUT,5L);
    cu.setopt(c,13,12L); /* CURLOPT_TIMEOUT: image fetch must not delay other jobs indefinitely. */
    cu.setopt(c,CU_USERAGENT,"OpenPlugin-preview/0.8");
    if(is_file("/etc/ssl/certs/ca-certificates.crt"))cu.setopt(c,CU_CAINFO,"/etc/ssl/certs/ca-certificates.crt");
    cu.setopt(c,CU_WRITEFUNCTION,on_data);cu.setopt(c,CU_WRITEDATA,s);
    cu.setopt(c,CU_NOPROGRESS,0L);cu.setopt(c,CU_XFERINFOFUNCTION,on_progress);cu.setopt(c,CU_XFERINFODATA,&g);
    int rc=cu.perform(c);cu.cleanup(c);
    return !rc && s->len && s->len<=4*1024*1024;
}
static unsigned char *preview_decode(const unsigned char *data,size_t len) {
    int w,h,n;
    if(len>4*1024*1024 || !stbi_info_from_memory(data,(int)len,&w,&h,&n) ||
       w<=0 || h<=0 || w>8192 || h>8192 || (uint64_t)w*h>16000000) return NULL;
    unsigned char *src=stbi_load_from_memory(data,(int)len,&w,&h,&n,4);if(!src)return NULL;
    unsigned char *dst=malloc(PREVIEW_W*PREVIEW_H*4);if(!dst){stbi_image_free(src);return NULL;}
    for(int i=0;i<PREVIEW_W*PREVIEW_H;i++){dst[i*4]=19;dst[i*4+1]=22;dst[i*4+2]=27;dst[i*4+3]=255;}
    double scale=fmin((double)PREVIEW_W/w,(double)PREVIEW_H/h);
    int tw=(int)(w*scale+0.5),th=(int)(h*scale+0.5);if(tw<1)tw=1;if(th<1)th=1;
    int ox=(PREVIEW_W-tw)/2,oy=(PREVIEW_H-th)/2;
    for(int y=0;y<th;y++)for(int x=0;x<tw;x++) {
        double fx=fmax(0,(x+0.5)/scale-0.5),fy=fmax(0,(y+0.5)/scale-0.5);
        int x0=(int)fx,y0=(int)fy,x1=x0+1<w?x0+1:x0,y1=y0+1<h?y0+1:y0;
        if(x0>=w)x0=x1=w-1;if(y0>=h)y0=y1=h-1;
        double dx=fx-x0,dy=fy-y0;unsigned char rgba[4];
        for(int c=0;c<4;c++)rgba[c]=(unsigned char)((1-dy)*((1-dx)*src[(y0*w+x0)*4+c]+dx*src[(y0*w+x1)*4+c])+dy*((1-dx)*src[(y1*w+x0)*4+c]+dx*src[(y1*w+x1)*4+c])+0.5);
        unsigned char *p=dst+((y+oy)*PREVIEW_W+x+ox)*4;
        for(int c=0;c<3;c++)p[c]=(rgba[c]*rgba[3]+p[c]*(255-rgba[3])+127)/255;
    }
    stbi_image_free(src);return dst;
}
static unsigned char *preview_read(const char *file) {
    FILE *f=fopen(file,"rb");if(!f)return NULL;
    unsigned char *data=malloc(4*1024*1024+1);if(!data){fclose(f);return NULL;}
    size_t len=fread(data,1,4*1024*1024+1,f);fclose(f);
    unsigned char *rgba=preview_decode(data,len);free(data);return rgba;
}
static int preview_save(const char *path,const unsigned char *rgba) {
    char tmp[768];snprintf(tmp,sizeof tmp,"%s.new",path);
    int fd=open(tmp,O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW,0600);if(fd<0)return 0;
    int len=0;unsigned char *png=stbi_write_png_to_mem(rgba,PREVIEW_W*4,PREVIEW_W,PREVIEW_H,4,&len);
    size_t off=0;if(png)while(off<(size_t)len){ssize_t k=write(fd,png+off,len-off);if(k<=0)break;off+=k;}
    int ok=png && off==(size_t)len && !fsync(fd);free(png);if(close(fd))ok=0;
    if(ok && !rename(tmp,path))return 1;unlink(tmp);return 0;
}
static void preview_request_locked(mgr_t *m) {
    if(!m->preview_enabled)return;
    m->preview_generation++;m->preview_pending=1;
    if(!m->busy && !m->job){m->job=J_PREVIEW;m->preview_pending=0;pthread_cond_signal(&m->cv);}
}
static void preview_refresh(mgr_t *m) {
    pkg_t rows[ROWS];memset(rows,0,sizeof rows);int online;unsigned generation;
    pthread_mutex_lock(&m->mu);
    int idx[MAXPKG],n=visible(m,idx);generation=m->preview_generation;online=m->online;m->preview_pending=0;
    for(int r=0;r<ROWS;r++){int k=m->page*ROWS+r;if(k<n)rows[r]=m->pkg[idx[k]];}
    pthread_mutex_unlock(&m->mu);
    char parent[768];snprintf(parent,sizeof parent,"%s",PREVIEW_DIR);
    char *slash=strrchr(parent,'/');if(slash){*slash=0;mkdir(parent,0755);}
    mkdir(PREVIEW_DIR,0755);
    unsigned char *pictures[ROWS]={0};
    for(int r=0;r<ROWS;r++) {
        char file[768];pkg_t *p=&rows[r];
        if(preview_id_ok(p->id)) {
            snprintf(file,sizeof file,PREVIEW_DIR "/%s.png",p->id);
            if(online && p->screenshot[0]) {
                sink_t s={0};if(preview_fetch(m,p->screenshot,&s))pictures[r]=preview_decode((unsigned char*)s.buf,s.len);free(s.buf);
                if(pictures[r])preview_save(file,pictures[r]);
            }
            if(!pictures[r])pictures[r]=preview_read(file);
            if(!pictures[r]){snprintf(file,sizeof file,BUNDLED_PREVIEW_DIR "/%s.png",p->id);pictures[r]=preview_read(file);}
        }
        if(!pictures[r])pictures[r]=preview_read(BUNDLED_PREVIEW_DIR "/fallback.png");
    }
    /* Decode and encode outside the mutex used by host parameter reads. */
    int staged[ROWS]={0};
    for(int r=0;r<ROWS;r++)if(pictures[r]) {
        char file[768],stage[768];snprintf(file,sizeof file,PREVIEW_DIR "/row%d.png",r+1);
        snprintf(stage,sizeof stage,PREVIEW_DIR "/row%d.stage.png",r+1);
        unsigned char *old=preview_read(file);
        int same=old && !memcmp(old,pictures[r],PREVIEW_W*PREVIEW_H*4);free(old);
        if(!same)staged[r]=preview_save(stage,pictures[r]);
    }
    pthread_mutex_lock(&m->mu);
    int changed=0;
    for(int r=0;r<ROWS;r++)if(staged[r]) {
        char file[768],stage[768];snprintf(file,sizeof file,PREVIEW_DIR "/row%d.png",r+1);
        snprintf(stage,sizeof stage,PREVIEW_DIR "/row%d.stage.png",r+1);
        if(generation==m->preview_generation && !rename(stage,file))changed=1;
        else unlink(stage);
    }
    if(changed)m->rev++;
    pthread_mutex_unlock(&m->mu);
    for(int r=0;r<ROWS;r++)free(pictures[r]);
}
