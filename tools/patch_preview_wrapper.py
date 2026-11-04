"""Manager-only wrapper: cache image values and bound audio-thread UI traffic."""
from pathlib import Path

def patch(source, first, count):
 s=Path(source).read_text()
 def replace(old,new):
  nonlocal s
  if s.count(old)!=1:raise ValueError('Pinned wrapper anchor changed: '+old[:70])
  s=s.replace(old,new,1)
 replace('typedef struct {\n    AEffect fx;',f'''#define PREVIEW_FIRST {first}
#define PREVIEW_COUNT {count}
#define PREVIEW_END (PREVIEW_FIRST+PREVIEW_COUNT)
#define PREVIEW_READY_FIRST (NPARAMS-3)
#define PREVIEW_NEXT_CONTROL(i) ((i)+1==PREVIEW_FIRST?PREVIEW_END:(i)+1)
#define PREVIEW_SCAN_BUDGET 64
#define PREVIEW_SEND_BUDGET 24
#define PREVIEW_PIXEL_VISIBLE(p) (((p)%2)==0 && (((p)/60)%2)==0)
extern int openplugin_preview_snapshot(void*,unsigned*,uint16_t*,int,char[3][48]);
typedef struct {{
    uint16_t preview_target[PREVIEW_COUNT],preview_current[PREVIEW_COUNT];
    char preview_ids[3][48],preview_target_ids[3][48];
    unsigned char preview_ready[3];
    unsigned preview_revision;
    int preview_cursor,preview_pending,preview_poll;
    AEffect fx;''')
 replace('    if (i < 0 || i >= NPARAMS) return 0;\n    if (popup_is(i))', '''    if (i < 0 || i >= NPARAMS) return 0;
    if(i>=PREVIEW_READY_FIRST)return __atomic_load_n(&w->preview_ready[i-PREVIEW_READY_FIRST],__ATOMIC_RELAXED);
    if(i>=PREVIEW_FIRST&&i<PREVIEW_END)return __atomic_load_n(&w->preview_current[i-PREVIEW_FIRST],__ATOMIC_RELAXED)/4095.f;
    if (popup_is(i))''')
 # Display-only automation echoes must not enter either engine or wrapper UI state.
 replace('static void setParameter(AEffect *e, int32_t i, float n) {','''static void setParameter(AEffect *e, int32_t i, float n) {
    if((i>=PREVIEW_FIRST&&i<PREVIEW_END)||i>=PREVIEW_READY_FIRST)return;''')
 replace('    case effGetParamDisplay: {', '''    case effGetParamDisplay: {
        if(idx>=PREVIEW_FIRST&&idx<PREVIEW_END){snprintf(p,24,"%u",(unsigned)__atomic_load_n(&w->preview_current[idx-PREVIEW_FIRST],__ATOMIC_RELAXED));return 1;}
        if(idx>=PREVIEW_READY_FIRST&&idx<NPARAMS){snprintf(p,24,"%u",(unsigned)__atomic_load_n(&w->preview_ready[idx-PREVIEW_READY_FIRST],__ATOMIC_RELAXED));return 1;}''')
 a=s.index('static void housekeeping(');b=s.index('\n#ifdef PLUG_EFFECT',a)
 h=s[a:b].replace('i < NPARAMS','i < PREVIEW_READY_FIRST').replace('i++)','i = PREVIEW_NEXT_CONTROL(i))')
 s=s[:a]+h+s[b:]
 replace('    w->master = master;','''    w->preview_revision=~0u;
    for(int p=0;p<PREVIEW_COUNT;p++)w->preview_current[p]=w->preview_target[p]=0x111;
    w->master = master;''')
 s=s.replace("static void housekeeping(AEffect *e, int32_t n) {", '/* Online-only fallback. Fixed callback budget, cached getters, no I/O on audio thread. */\nstatic void preview_step(wrap_t *w) {\n    if(openplugin_preview_snapshot(w->dsp,&w->preview_revision,w->preview_target,PREVIEW_COUNT,w->preview_target_ids)) {\n        w->preview_cursor=0;w->preview_pending=1;\n        for(int row=0;row<3;row++) {\n            if(w->preview_ready[row]) {__atomic_store_n(&w->preview_ready[row],0,__ATOMIC_RELAXED);w->master(&w->fx,audioMasterAutomate,PREVIEW_READY_FIRST+row,0,0,0);}\n        }\n    }\n    int sent=0,scanned=0;\n    while(w->preview_pending && w->preview_cursor<PREVIEW_COUNT && sent<12 && scanned<128) {\n        int p=w->preview_cursor++,row=p/1800;scanned++;\n        if(!w->preview_target_ids[row][0] || !PREVIEW_PIXEL_VISIBLE(p))continue;\n        unsigned v=w->preview_target[p];\n        if(v!=w->preview_current[p]) {\n            __atomic_store_n(&w->preview_current[p],v,__ATOMIC_RELAXED);\n            w->master(&w->fx,audioMasterAutomate,PREVIEW_FIRST+p,0,0,v/4095.f);sent++;\n        }\n    }\n    if(w->preview_pending && w->preview_cursor>=PREVIEW_COUNT) {\n        w->preview_pending=0;\n        for(int row=0;row<3;row++)if(w->preview_target_ids[row][0]) {\n            __atomic_store_n(&w->preview_ready[row],1,__ATOMIC_RELAXED);\n            w->master(&w->fx,audioMasterAutomate,PREVIEW_READY_FIRST+row,0,0,1);\n        }\n    }\n}\n'+"static void housekeeping(AEffect *e, int32_t n) {",1)
 s=s.replace("static void housekeeping(AEffect *e, int32_t n) {\n    wrap_t *w = e->object;", "static void housekeeping(AEffect *e, int32_t n) {\n    wrap_t *w = e->object;\n    preview_step(w);",1)
 return s
