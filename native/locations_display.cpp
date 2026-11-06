/* Standalone progress display while MPC is stopped. Only the known Force
 * portrait framebuffer is supported; unsupported hardware is left untouched. */
#include <linux/fb.h>
#include <linux/input.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
#include <chrono>
#include "third_party/picojson/picojson.h"
#include "progress_font.h"
static volatile sig_atomic_t running=1;
static void stop(int){running=0;}
static std::vector<unsigned> canvas(1280*800);
static void pixel(int x,int y,unsigned c){if(x>=0&&x<1280&&y>=0&&y<800)canvas[y*1280+x]=c;}
static void rect(int x,int y,int w,int h,unsigned c){for(int yy=y;yy<y+h;yy++)for(int xx=x;xx<x+w;xx++)pixel(xx,yy,c);}
static int text(int x,int y,const std::string &s,unsigned color=0xe9edff,int max_lines=1){
    int start=x,line=1;
    for(unsigned char ch:s){if(ch<32||ch>126)ch='?';int g=ch-32;if(x+40>1235){if(line++>=max_lines)break;x=start;y+=48;}
        for(int yy=0;yy<48;yy++)for(int xx=0;xx<40;xx++)if(glyph_pixels[g][yy*40+xx]>100)pixel(x+xx,y+yy,color);
        x+=glyph_advance[g];
    }return y+48;
}
static std::string value(const picojson::value &v,const char *key){return v.is<picojson::object>()&&v.contains(key)&&v.get(key).is<std::string>()?v.get(key).get<std::string>():"";}
static double number(const picojson::value &v,const char *key){return v.is<picojson::object>()&&v.contains(key)&&v.get(key).is<double>()?v.get(key).get<double>():0;}
int main(int argc,char **argv){
    if(argc!=2 || system("pidof MPC >/dev/null 2>&1")!=256)return 2;
    int fd=open("/dev/fb0",O_RDWR);if(fd<0)return 3;
    fb_var_screeninfo v{};fb_fix_screeninfo f{};
    if(ioctl(fd,FBIOGET_VSCREENINFO,&v)||ioctl(fd,FBIOGET_FSCREENINFO,&f)||v.xres!=800||v.yres!=1280||v.bits_per_pixel!=32||v.red.offset!=16||v.green.offset!=8||v.blue.offset!=0||f.line_length<3200||f.smem_len<f.line_length*1280){close(fd);return 4;}
    auto *mem=(unsigned char*)mmap(nullptr,f.smem_len,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);if(mem==MAP_FAILED){close(fd);return 5;}
    signal(SIGTERM,stop);signal(SIGINT,stop);
    v.xoffset=0;v.yoffset=0;v.activate=FB_ACTIVATE_NOW;
    int touch=open("/dev/input/event0",O_RDONLY|O_NONBLOCK);
    bool first=true;auto started=std::chrono::steady_clock::now();
    while(running){
        picojson::value state;std::ifstream file(argv[1]);std::string input;
        if(file){char bytes[4097]={0};file.read(bytes,4096);input.assign(bytes,file.gcount());picojson::parse(state,input);}
        std::fill(canvas.begin(),canvas.end(),0x0c0c0d);text(48,35,"PLUGIN STORAGE");
        std::string status=value(state,"state"),phase=value(state,"phase");bool failed=status=="failed";
        text(48,110,failed?"Operation stopped - "+value(state,"code"):status=="done"?"Operation complete":phase.empty()?"Preparing operation...":phase,failed?0xffbb77:0x72e6cc);
        std::string plugin=value(state,"plugin");if(!plugin.empty())text(48,180,plugin);
        char count[100];snprintf(count,sizeof count,"Plugin %.0f of %.0f",number(state,"plugin_index"),number(state,"plugin_count"));
        if(number(state,"plugin_count")>0)text(48,245,count);
        double done=number(state,"bytes_done"),total=number(state,"bytes_total");
        if(total>0){snprintf(count,sizeof count,"Copied %.1f of %.1f MB",done/1048576,total/1048576);text(48,305,count);rect(48,370,1180,20,0x222838);rect(48,370,(int)(1180*(done>total?1:done/total)),20,0x72e6cc);}
        if(!failed && status!="done") {
            auto seconds=std::chrono::duration_cast<std::chrono::seconds>(std::chrono::steady_clock::now()-started).count();
            snprintf(count,sizeof count,"Elapsed %lld sec | %.0f files checked",(long long)seconds,number(state,"files_checked"));
            text(48,430,count);text(48,490,value(state,"file"),0xe9edff,2);
        }
        if(failed || status=="done")text(48,430,value(state,"message"),0xe9edff,3);
        if(failed){text(48,605,"Verified copies preserved; recovery is available.");text(48,660,"Photograph this screen. Tap to return.");}
        else text(48,660,"Please keep the Force and drive powered on.");
        for(int y=0;y<800;y++)for(int x=0;x<1280;x++)((unsigned*)(mem+(1279-x)*f.line_length))[y]=canvas[y*1280+x];
        if(first){if(ioctl(fd,FBIOPAN_DISPLAY,&v)){munmap(mem,f.smem_len);close(fd);return 6;}first=false;}
        if(touch>=0){struct input_event e;while(read(touch,&e,sizeof e)==sizeof e)if(failed && e.type==EV_KEY && e.code==BTN_TOUCH && e.value==0)running=0;}
        usleep(250000);
    }
    if(touch>=0)close(touch);munmap(mem,f.smem_len);close(fd);return 0;
}
