#!/usr/bin/env python3
"""Measure actual pinned wrapper with host display reads and automation echoes."""
import argparse,json,subprocess,tempfile
from pathlib import Path
from patch_preview_wrapper import patch
p=argparse.ArgumentParser();p.add_argument('native',type=Path);a=p.parse_args();native=a.native.resolve();build=native/'source/vst/build';up=native/'dependencies/mpc-vst-plugins/wrapper'
params=json.loads((native/'source/vst/params.json').read_text())['params'];first=next(i for i,p in enumerate(params) if p['key'].startswith('previewpx_'));count=sum(p['key'].startswith('previewpx_') for p in params)
code=r'''
#include "wrapper.c"
#include <assert.h>
#include <time.h>
static unsigned revision=1,image_revision=1,gets,pixel_gets,callbacks,pixel_callbacks,updates;
static unsigned max_pixels,max_gets;static unsigned long long worst_ns;
static void*fake_create(const char*p){(void)p;return &revision;}
static void fake_destroy(void*p){(void)p;}
static void fake_midi(void*p,const uint8_t*b,int n){(void)p;(void)b;(void)n;}
static void fake_set(void*p,const char*k,const char*v){(void)p;(void)k;(void)v;}
static int fake_get(void*p,const char*k,char*b,int n){(void)p;gets++;
 if(!strcmp(k,"state"))return 0;
 if(!strcmp(k,"display_rev")){snprintf(b,n,"%u",revision);return 1;}
 if(!strncmp(k,"previewpx_",10)){pixel_gets++;int r,pix;sscanf(k+10,"%d_%d",&r,&pix);snprintf(b,n,"%u",((r-1)*1800+pix+image_revision)&4095);return 1;}
 if(strstr(k,"_on"))return 0;
 snprintf(b,n,"0");return 1;
}
static void fake_render(void*p,int16_t*out,int n){(void)p;memset(out,0,n*4);}
const mpc_engine_t*mpc_engine(void){static const mpc_engine_t api={fake_create,fake_destroy,fake_midi,fake_set,fake_get,fake_render,NULL};return &api;}
int openplugin_preview_snapshot(void*p,unsigned*rev,uint16_t*out,int count,char ids[3][48]){(void)p;if(*rev==image_revision)return 0;*rev=image_revision;for(int row=0;row<3;row++)snprintf(ids[row],48,"plugin-%u-%d",image_revision,row);for(int i=0;i<count;i++)out[i]=(i+image_revision)&4095;return 1;}
static intptr_t host(AEffect*e,int32_t op,int32_t index,intptr_t value,void*ptr,float opt){(void)value;(void)ptr;
 if(op==audioMasterAutomate){callbacks++;if(index>=TEST_FIRST&&index<TEST_FIRST+TEST_COUNT)pixel_callbacks++;e->setParameter(e,index,opt);}
 if(op==audioMasterUpdateDisplay){updates++;for(int i=0;i<NPARAMS;i++){char text[PARAM_TEXT_MAX+32];e->getParameter(e,i);e->dispatcher(e,effGetParamDisplay,i,0,text,0);}}
 return 0;
}
static unsigned long long nanos(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (unsigned long long)t.tv_sec*1000000000ull+t.tv_nsec;}
int main(void){AEffect*e=VSTPluginMain(host);assert(e);float l[128],r[128],*out[]={l,r};unsigned total_pixels=0,total_gets=0;
 for(int b=0;b<7000;b++){if(b%7==0)revision++;if(b<3000&&b%170==0)image_revision++;
  gets=pixel_callbacks=0;unsigned long long t=nanos();e->processReplacing(e,NULL,out,128);t=nanos()-t;
  if(t>worst_ns)worst_ns=t;if(pixel_callbacks>max_pixels)max_pixels=pixel_callbacks;if(gets>max_gets)max_gets=gets;total_pixels+=pixel_callbacks;total_gets+=gets;
 }
#ifdef PREVIEW_COUNT
 assert(pixel_gets==0);assert(max_pixels<=12);assert(max_gets<1000);
 assert(total_pixels>0); /* Unknown IDs receive the bounded online fallback. */
 assert(e->getParameter(e,NPARAMS-3)==1.f);
#else
 assert(pixel_gets>0&&max_pixels>5000);
#endif
 printf("{\"max_pixel_callbacks_per_block\":%u,\"pixel_string_gets\":%u,\"max_engine_gets_per_block\":%u,\"total_engine_gets\":%u,\"total_pixel_callbacks\":%u,\"host_display_updates\":%u,\"worst_wall_us\":%.3f}\n",max_pixels,pixel_gets,max_gets,total_gets,total_pixels,updates,worst_ns/1000.);
 e->dispatcher(e,effClose,0,0,NULL,0);return 0;}
'''
results={}
with tempfile.TemporaryDirectory(prefix='openplugin-wrapper-cpu-') as d:
 d=Path(d)
 for name,source in [('baseline',(up/'vst2_wrap.c').read_text()),('bounded',patch(up/'vst2_wrap.c',first,count))]:
  (d/'wrapper.c').write_text(source);(d/'test.c').write_text(code)
  binary=d/'test';subprocess.run(['cc','-w','-O2','-std=gnu11','-DDISPLAY_REV_NO_UPDATE=1',f'-DTEST_FIRST={first}',f'-DTEST_COUNT={count}','-I'+str(build),'-I'+str(up),str(d/'test.c'),'-lpthread','-ldl','-lm','-o',str(binary)],check=True)
  results[name]=json.loads(subprocess.check_output([binary],text=True))
print(json.dumps(results,indent=2))
