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
static size_t preview_on_data(char *p,size_t sz,size_t count,void *ud) {
    sink_t *s=ud;
    if(sz && count>SIZE_MAX/sz)return 0;
    size_t bytes=sz*count;
    if(bytes>4u*1024*1024 || s->len>4u*1024*1024-bytes)return 0;
    return on_data(p,sz,count,ud);
}
typedef struct {mgr_t *m;unsigned generation;} preview_progress_t;
static int preview_progress(void *ud,long long total,long long now,long long ut,long long un) {
    (void)total;(void)now;(void)ut;(void)un;
    preview_progress_t *g=ud;
    pthread_mutex_lock(&g->m->mu);
    int stop=g->m->quit || g->generation!=g->m->preview_generation || g->m->job;
    pthread_mutex_unlock(&g->m->mu);return stop;
}
#ifndef PREVIEW_FETCH_TEST
static int preview_fetch(mgr_t *m,const char *url,sink_t *s) {
    if(strncmp(url,"https://",8) || strlen(url)>1023 || !curl_load()) return 0;
    CURL *c=cu.init();if(!c)return 0;
    pthread_mutex_lock(&m->mu);preview_progress_t g={m,m->preview_generation};pthread_mutex_unlock(&m->mu);
    cu.setopt(c,CU_URL,url);cu.setopt(c,CU_FOLLOWLOCATION,1L);
    cu.setopt(c,181,2L);cu.setopt(c,182,2L);
    cu.setopt(c,CU_FAILONERROR,1L);cu.setopt(c,CU_CONNECTTIMEOUT,5L);
    cu.setopt(c,13,12L); /* CURLOPT_TIMEOUT: image fetch must not delay other jobs indefinitely. */
    cu.setopt(c,CU_USERAGENT,"OpenPlugin-preview/0.8");
    if(is_file("/etc/ssl/certs/ca-certificates.crt"))cu.setopt(c,CU_CAINFO,"/etc/ssl/certs/ca-certificates.crt");
    cu.setopt(c,CU_WRITEFUNCTION,preview_on_data);cu.setopt(c,CU_WRITEDATA,s);
    cu.setopt(c,CU_NOPROGRESS,0L);cu.setopt(c,CU_XFERINFOFUNCTION,preview_progress);cu.setopt(c,CU_XFERINFODATA,&g);
    int rc=cu.perform(c);cu.cleanup(c);
    return !rc && s->len && s->len<=4*1024*1024;
}
#else
static int preview_fetch(mgr_t *m,const char *url,sink_t *s) {return PREVIEW_FETCH_TEST(m,url,s);}
#endif
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
/* RGB444 values drive immutable native Image/FilmStrip palette cells. The host
 * may cache every PNG for its lifetime: only numeric values change at runtime. */
static void preview_quantize(const unsigned char *rgba,uint16_t *pixels) {
    for(int y=0;y<PREVIEW_LINES;y++)for(int x=0;x<PREVIEW_COLS;x++) {
        unsigned sums[3]={0};
        for(int dy=0;dy<3;dy++)for(int dx=0;dx<3;dx++) {
            const unsigned char *p=rgba+((y*3+dy)*PREVIEW_W+x*3+dx)*4;
            for(int c=0;c<3;c++)sums[c]+=p[c];
        }
        unsigned rr=(sums[0]+76)/153,gg=(sums[1]+76)/153,bb=(sums[2]+76)/153;
        pixels[y*PREVIEW_COLS+x]=(rr<<8)|(gg<<4)|bb;
    }
}
static int preview_current(mgr_t *m,unsigned generation) {
    pthread_mutex_lock(&m->mu);
    int ok=!m->quit && generation==m->preview_generation;
    pthread_mutex_unlock(&m->mu);return ok;
}
static void preview_publish(mgr_t *m,unsigned generation,int row,const char *id,const unsigned char *rgba) {
    uint16_t pixels[PREVIEW_PIXELS];
    if(rgba)preview_quantize(rgba,pixels);
    else for(int i=0;i<PREVIEW_PIXELS;i++)pixels[i]=0x111;
    pthread_mutex_lock(&m->mu);
    if(generation==m->preview_generation && !m->quit &&
       (strcmp(m->preview_row_id[row],id) || memcmp(m->preview_pixels[row],pixels,sizeof pixels))) {
        memcpy(m->preview_pixels[row],pixels,sizeof pixels);
        snprintf(m->preview_row_id[row],sizeof m->preview_row_id[row],"%s",id);
        m->rev++;
    }
    pthread_mutex_unlock(&m->mu);
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
    /* Populate every visible row locally before waiting for any network request. */
    for(int r=0;r<ROWS;r++) {
        if(!preview_current(m,generation))return;
        char file[768];unsigned char *rgba=NULL;pkg_t *p=&rows[r];
        if(preview_id_ok(p->id)) {
            snprintf(file,sizeof file,PREVIEW_DIR "/%s.png",p->id);rgba=preview_read(file);
            if(!rgba){snprintf(file,sizeof file,BUNDLED_PREVIEW_DIR "/%s.png",p->id);rgba=preview_read(file);}
        }
        if(!rgba)rgba=preview_read(BUNDLED_PREVIEW_DIR "/fallback.png");
        preview_publish(m,generation,r,p->id,rgba);free(rgba);
    }
    for(int r=0;r<ROWS;r++) {
        pkg_t *p=&rows[r];
        if(!preview_current(m,generation))return;
        if(!online || !preview_id_ok(p->id) || !p->screenshot[0] || p->preview_checked)continue;
        sink_t s={0};unsigned char *rgba=NULL;
        if(preview_fetch(m,p->screenshot,&s))rgba=preview_decode((unsigned char*)s.buf,s.len);
        free(s.buf);
        if(rgba) {
            char file[768];snprintf(file,sizeof file,PREVIEW_DIR "/%s.png",p->id);
            preview_save(file,rgba); /* failure to persist must not prevent display */
            preview_publish(m,generation,r,p->id,rgba);free(rgba);
        }
        pthread_mutex_lock(&m->mu);
        if(generation==m->preview_generation)for(int i=0;i<m->npkg;i++)
            if(!strcmp(m->pkg[i].id,p->id) && !strcmp(m->pkg[i].screenshot,p->screenshot))m->pkg[i].preview_checked=1;
        pthread_mutex_unlock(&m->mu);
    }
}
