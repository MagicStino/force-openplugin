/* Storage discovery stays off the audio/UI polling thread. */
#include <mntent.h>
static void post(mgr_t *m, int job);
static int locations_helper(char *out,size_t n) {
    if(!skin_helper_path(out,n))return 0;
    char *slash=strrchr(out,'/');
    if(!slash || (size_t)(slash-out)+sizeof("/locations-tool")>n)return 0;
    strcpy(slash,"/locations-tool");return safe(out)&&access(out,X_OK)==0;
}
static void storage_text(const char *path,const char *label,char *out,size_t n) {
    struct statvfs s;
    if(!path[0]||statvfs(path,&s))snprintf(out,n,"%s: unavailable",label);
    else snprintf(out,n,"%s: %.1f GB free",label,(double)s.f_bavail*s.f_frsize/1e9);
}
static int same_directory(const char *a,const char *b) {
    struct stat x,y;return !strcmp(a,b) || (!stat(a,&x)&&!stat(b,&y)&&x.st_dev==y.st_dev&&x.st_ino==y.st_ino);
}
static void locations_label(const char *root,char *label,size_t n) {
    if(!strncmp(root,"/sdcard/",8)||!strncmp(root,"/media/az01-internal-sd/",24))snprintf(label,n,"Internal content");
    else if(!strncmp(root,"/media/az01-internal/",21))snprintf(label,n,"Internal system storage");
    else {char parent[256];snprintf(parent,sizeof parent,"%s",root);char *slash=strrchr(parent,'/');if(slash)*slash=0;slash=strrchr(parent,'/');snprintf(label,n,"%s",slash?slash+1:parent);}
}
static int locations_command(const char *,const char *,const device_t *,const char *,const char *);
static int locations_command(const char *helper,const char *mode,const device_t *d,const char *target,const char *progress_path) {
    if(!safe(helper)||!safe(d->settings)||!safe(d->state)||(target&&!safe(target)))return -1;
    char command[2400];
    if(!strcmp(mode,"plan-return")||!strcmp(mode,"return"))snprintf(command,sizeof command,"'%s' '%s' '%s' '%s' '" WORK "/return-plan.xml' > '" WORK "/locations-result' 2>&1",helper,mode,d->settings,d->state);
    else if(target)snprintf(command,sizeof command,"'%s' '%s' '%s' '%s' '%s' '" WORK "/move-plan.xml' > '" WORK "/locations-result' 2>&1",helper,mode,d->settings,d->state,target);
    else snprintf(command,sizeof command,"'%s' '%s' '%s' '%s' > '" WORK "/locations-result' 2>&1",helper,mode,d->settings,d->state);
    if(progress_path){
        if(!safe(progress_path))return -1;
        char wrapped[3100];snprintf(wrapped,sizeof wrapped,"OPENPLUGIN_PROGRESS_FILE='%s' %s",progress_path,command);return sh(wrapped);
    }
    return sh(command);
}
/* Poll snapshots on the worker only. Host parameter getters read memory. */
typedef struct {
    const char *helper,*mode,*target,*progress_path;const device_t *device;
    pthread_mutex_t mutex;int done,result;
} locations_task_t;
static void *locations_command_thread(void *arg) {
    locations_task_t *task=arg;
    int result=locations_command(task->helper,task->mode,task->device,task->target,task->progress_path);
    pthread_mutex_lock(&task->mutex);task->result=result;task->done=1;pthread_mutex_unlock(&task->mutex);return NULL;
}
typedef struct {char phase[100],plugin[100],file[120];double index,count,files;} locations_progress_t;
static const char *locations_progress_field(const char *key,const char *value,void *ctx) {
    locations_progress_t *p=ctx;
    if(!strcmp(key,"phase"))return jstr(value,p->phase,sizeof p->phase);
    if(!strcmp(key,"plugin"))return jstr(value,p->plugin,sizeof p->plugin);
    if(!strcmp(key,"file"))return jstr(value,p->file,sizeof p->file);
    if(!strcmp(key,"plugin_index"))p->index=strtod(value,NULL);
    if(!strcmp(key,"plugin_count"))p->count=strtod(value,NULL);
    if(!strcmp(key,"files_checked"))p->files=strtod(value,NULL);
    return NULL;
}
static int locations_command_progress(mgr_t *m,const char *helper,const char *mode,const device_t *d,const char *target) {
    char path[512];snprintf(path,sizeof path,WORK "/locations-progress-%ld-%p.json",(long)getpid(),(void*)m);
    unlink(path); /* Never display a previous operation's snapshot. */
    locations_task_t task={.helper=helper,.mode=mode,.target=target,.device=d,.progress_path=path};
    pthread_mutex_init(&task.mutex,NULL);pthread_t thread;
    struct timespec start,now;clock_gettime(CLOCK_MONOTONIC,&start);
    if(pthread_create(&thread,NULL,locations_command_thread,&task)){pthread_mutex_destroy(&task.mutex);return -1;}
    for(;;) {
        locations_progress_t p={0};char *json=slurp(path,4096);
        if(json){jobject(json,locations_progress_field,&p);free(json);}
        clock_gettime(CLOCK_MONOTONIC,&now);
        pthread_mutex_lock(&m->mu);
        snprintf(m->locations_progress,sizeof m->locations_progress,"%.28s%s%.30s | %ld sec",p.phase[0]?p.phase:"Checking storage",p.plugin[0]?": ":"",p.plugin,(long)(now.tv_sec-start.tv_sec));
        if(p.count>0)snprintf(m->locations_progress_detail,sizeof m->locations_progress_detail,"Plugin %.0f/%.0f | %.0f files | %.50s",p.index,p.count,p.files,strlen(p.file)>50?p.file+strlen(p.file)-50:p.file);
        else snprintf(m->locations_progress_detail,sizeof m->locations_progress_detail,"%s",p.file[0]?p.file:"Checking available drives and managed plugins...");
        m->rev++;pthread_mutex_unlock(&m->mu);
        pthread_mutex_lock(&task.mutex);int done=task.done;pthread_mutex_unlock(&task.mutex);
        if(done)break;
        usleep(500000);
    }
    pthread_join(thread,NULL);pthread_mutex_destroy(&task.mutex);unlink(path);
    pthread_mutex_lock(&m->mu);m->locations_progress[0]=m->locations_progress_detail[0]=0;pthread_mutex_unlock(&m->mu);
    return task.result;
}
typedef struct {mgr_t *m;int row;} storage_parse_t;
static const char *storage_row_field(const char *key,const char *value,void *ctx) {
    storage_parse_t *p=ctx;mgr_t *m=p->m;int i=p->row;
    if(!strcmp(key,"root"))return jstr(value,m->locations_roots[i],sizeof m->locations_roots[i]);
    if(!strcmp(key,"label"))return jstr(value,m->storage_labels[i],sizeof m->storage_labels[i]);
    if(!strcmp(key,"space"))return jstr(value,m->storage_space[i],sizeof m->storage_space[i]);
    if(!strcmp(key,"status"))return jstr(value,m->locations_info[i],sizeof m->locations_info[i]);
    if(!strcmp(key,"ready"))m->storage_viable[i]=!strncmp(value,"true",4);
    if(!strcmp(key,"main"))m->storage_main[i]=!strncmp(value,"true",4);
    return NULL;
}
static const char *storage_snapshot_field(const char *key,const char *value,void *ctx) {
    mgr_t *m=ctx;
    if(!strcmp(key,"warning"))return jstr(value,m->storage_warning,sizeof m->storage_warning);
    if(!strcmp(key,"tip"))return jstr(value,m->storage_tip,sizeof m->storage_tip);
    if(strcmp(key,"drives")||*value!='[')return NULL;
    const char *p=ws(value+1);
    while(*p && *p!=']') {if(m->locations_n>=24)return NULL;storage_parse_t row={m,m->locations_n++};p=jobject(p,storage_row_field,&row);if(!p)return NULL;p=ws(p);if(*p==',')p=ws(p+1);else break;}
    return *p==']'?p+1:NULL;
}
static void locations_scan(mgr_t *m) {
    device_t *d=calloc(1,sizeof *d);mgr_t *snapshot=calloc(1,sizeof *snapshot);
    if(!d||!snapshot){free(d);free(snapshot);return;}
    probe_device(d);char helper[1024];
    unlink(WORK "/locations-result");
    int ok=strcmp(d->problem,"Multiple settings profiles") && locations_helper(helper,sizeof helper) && locations_command_progress(m,helper,"drives",d,NULL)==0;
    char *report=slurp(WORK "/locations-result",32768);
    if(!ok||!report||!jobject(report,storage_snapshot_field,snapshot)){memset(snapshot->storage_viable,0,sizeof snapshot->storage_viable);snprintf(snapshot->storage_warning,sizeof snapshot->storage_warning,"Storage check failed. Refresh drives or view the debug log.");}
    char internal_why[320];
    storage_text(is_dir("/sdcard")&&!bad_fs("/sdcard",internal_why,sizeof internal_why)?"/sdcard":"/media/az01-internal","Internal",snapshot->storage_internal,sizeof snapshot->storage_internal);
    const char *label=strrchr(d->preferred,'/');label=label&&label[1]?label+1:"Preferred drive";
    if(d->preferred[0])storage_text(d->preferred,label,snapshot->storage_preferred,sizeof snapshot->storage_preferred);
    else snprintf(snapshot->storage_preferred,sizeof snapshot->storage_preferred,"No download drive selected");
    int repair=strcmp(d->problem,"Multiple settings profiles") && locations_helper(helper,sizeof helper) && locations_command_progress(m,helper,"check-repair",d,NULL)==0;
    char *skins=slurp(WORK "/locations-result",190);
    pthread_mutex_lock(&m->mu);
    m->storage_checked=1;
    m->locations_return_available=0;m->locations_repair_available=repair;
    m->locations_n=snapshot->locations_n;m->locations_selected=0;m->locations_ready=0;m->storage_page=0;m->locations_skin_check=0;
    memcpy(m->locations_roots,snapshot->locations_roots,sizeof m->locations_roots);
    memcpy(m->locations_info,snapshot->locations_info,sizeof m->locations_info);
    memcpy(m->storage_labels,snapshot->storage_labels,sizeof m->storage_labels);
    memcpy(m->storage_space,snapshot->storage_space,sizeof m->storage_space);
    memcpy(m->storage_viable,snapshot->storage_viable,sizeof m->storage_viable);
    memcpy(m->storage_main,snapshot->storage_main,sizeof m->storage_main);
    snprintf(m->storage_warning,sizeof m->storage_warning,"%s",snapshot->storage_warning);
    snprintf(m->storage_tip,sizeof m->storage_tip,"%s",snapshot->storage_tip[0]?snapshot->storage_tip:skins?skins:"");
    snprintf(m->storage_internal,sizeof m->storage_internal,"%s",snapshot->storage_internal);
    snprintf(m->storage_preferred,sizeof m->storage_preferred,"%s",snapshot->storage_preferred);
    snprintf(m->locations_summary,sizeof m->locations_summary,"%s",skins?skins:"");
    snprintf(m->locations_status,sizeof m->locations_status,"Choose Move here beside a drive. Checks run before confirmation.");
    m->rev++;pthread_mutex_unlock(&m->mu);free(skins);free(report);free(d);free(snapshot);
}
static void locations_load_log(mgr_t *m) {
    device_t *d=calloc(1,sizeof *d);if(!d)return;probe_device(d);
    char path[512];snprintf(path,sizeof path,"%s/.pluginmgr-locations-debug.log",d->base);free(d);
    char *text=slurp(path,8193);char lines[48][192]={{0}};int count=0;
    if(text){char *save=NULL;for(char *line=strtok_r(text,"\n",&save);line;line=strtok_r(NULL,"\n",&save)) {
        if(count==48){memmove(lines,lines+1,47*sizeof lines[0]);count--;}
        snprintf(lines[count++],sizeof lines[0],"%s",line);
    }free(text);}
    pthread_mutex_lock(&m->mu);memcpy(m->locations_log_lines,lines,sizeof lines);
    m->locations_log_count=count;m->locations_log_page=count?count-1:0;m->locations_ready=3;m->rev++;pthread_mutex_unlock(&m->mu);
}
static void locations_job(mgr_t *m,int job) {
    if(job==J_LOC_LOG){locations_load_log(m);return;}
    if(job==J_LOC_SCAN){locations_scan(m);return;}
    char helper[1024],target[256];device_t *d=calloc(1,sizeof *d);if(!d)return;probe_device(d);
    pthread_mutex_lock(&m->mu);int selected=m->locations_selected;
    snprintf(target,sizeof target,"%s",selected<m->locations_n?m->locations_roots[selected]:"");pthread_mutex_unlock(&m->mu);
    const char *error=NULL;
    if(!locations_helper(helper,sizeof helper))error="Install the complete manager package; locations helper missing.";
    else if(!d->settings[0]||!safe(d->settings)||!safe(d->state)||!safe(d->base))error="Cannot safely identify settings.";
    else if(!strcmp(d->problem,"Multiple settings profiles"))error="Multiple settings profiles: resolve the active profile first.";
    else if(job!=J_LOC_REPAIR && job!=J_LOC_REPAIR_CHECK && job!=J_LOC_RETURN_CHECK && job!=J_LOC_RETURN && !target[0])error="Select a destination.";
    if(error){pthread_mutex_lock(&m->mu);snprintf(m->locations_status,sizeof m->locations_status,"%s",error);m->locations_ready=5;m->rev++;pthread_mutex_unlock(&m->mu);free(d);return;}
    if(job==J_LOC_PLAN || job==J_LOC_REPAIR_CHECK || job==J_LOC_RETURN_CHECK) {
        int result=locations_command_progress(m,helper,job==J_LOC_PLAN?"plan":job==J_LOC_RETURN_CHECK?"plan-return":"check-repair",d,job==J_LOC_PLAN?target:NULL);
        char *report=slurp(WORK "/locations-result",190);
        pthread_mutex_lock(&m->mu);m->locations_ready=result?5:job==J_LOC_PLAN?1:job==J_LOC_RETURN_CHECK?4:2;
        snprintf(m->locations_status,sizeof m->locations_status,"%s",report?report:"Move check failed; see diagnostic log.");m->rev++;pthread_mutex_unlock(&m->mu);free(report);free(d);return;
    }
    // Confirmation happens on the touchscreen before this detached operation is prepared.
    FILE *f=fopen(WORK "/apply.sh","w");
    if(!f){free(d);say(m,ERR,"Cannot prepare locations operation");return;}
    fprintf(f,"#!/bin/sh\nexec > '%s/.pluginmgr-locations-result' 2>&1\nset -e\ndisplay_pid=\"\"\nfinish() { rc=$?; trap - EXIT; if [ -n \"$display_pid\" ]; then if [ \"$rc\" -ne 0 ] && grep -q '\"state\":\"failed\"' \"$progress_file\"; then wait \"$display_pid\" || :; else kill \"$display_pid\" 2>/dev/null || :; wait \"$display_pid\" 2>/dev/null || :; fi; fi; systemctl start acvs || exit 1; exit \"$rc\"; }\ntrap finish EXIT\nsystemctl stop acvs\ni=0; while pidof MPC >/dev/null && [ $i -lt 30 ]; do sleep 1; i=$((i+1)); done\nif pidof MPC >/dev/null; then echo 'MPC did not stop; nothing moved'; exit 1; fi\n",d->base);
    char display[1024];snprintf(display,sizeof display,"%s",helper);char *slash=strrchr(display,'/');if(slash)strcpy(slash,"/locations-display");
    fprintf(f,"progress_file='%s/.pluginmgr-locations-progress.json'\nrm -f \"$progress_file\"\nif [ -x '%s' ]; then '%s' '%s/.pluginmgr-locations-progress.json' & display_pid=$!; fi\n",d->base,display,display,d->base);
    if(job==J_LOC_REPAIR)fprintf(f,"'%s' repair '%s' '%s'\n",helper,d->settings,d->state);
    else if(job==J_LOC_RETURN)fprintf(f,"'%s' return '%s' '%s' '" WORK "/return-plan.xml'\n",helper,d->settings,d->state);
    else fprintf(f,"'%s' move '%s' '%s' '%s' '" WORK "/move-plan.xml'\n",helper,d->settings,d->state,target);
    fprintf(f,"rm -f \"$0\"\nexit 0\n");fclose(f);free(d);
    pthread_mutex_lock(&m->mu);m->locations_running=1;pthread_mutex_unlock(&m->mu);
    do_launch(m);
    pthread_mutex_lock(&m->mu);if(m->status_kind==ERR)m->locations_running=0;pthread_mutex_unlock(&m->mu);
}
static void locations_action(mgr_t *m,const char *key) {
    if(m->busy||m->job)return;
    if(!strcmp(key,"locations_log")){post(m,J_LOC_LOG);return;}
    if(m->locations_ready==3){
        if(!strcmp(key,"locations_cancel"))m->locations_ready=0;
        else if(!strcmp(key,"locations_log_next") && m->locations_log_page+1<m->locations_log_count)m->locations_log_page++;
        else if(!strcmp(key,"locations_log_prev") && m->locations_log_page>0)m->locations_log_page--;
        return;
    }
    if(!strcmp(key,"storage_prev")&&m->storage_page>0){m->storage_page--;return;}
    if(!strcmp(key,"storage_next")&&(m->storage_page+1)*3<m->locations_n){m->storage_page++;return;}
    int queued=0;for(int i=0;i<m->npkg;i++)if(m->pkg[i].queued)queued++;
    if(queued){snprintf(m->locations_status,sizeof m->locations_status,"Finish or clear queued changes in Catalog before moving plugins.");return;}
    if(!strncmp(key,"storage_move_",13)){
        int row=atoi(key+13)-1,index=m->storage_page*3+row;
        if(row>=0&&row<3&&index<m->locations_n&&m->storage_viable[index]){m->locations_selected=index;m->locations_skin_check=0;m->locations_ready=0;post(m,J_LOC_PLAN);}
    }
    else if(!strcmp(key,"locations_scan")){m->locations_ready=0;post(m,J_LOC_SCAN);}
    else if(!strcmp(key,"locations_prev")||!strcmp(key,"locations_next")){
        if(m->locations_n)m->locations_selected=(m->locations_selected+m->locations_n+(!strcmp(key,"locations_next")?1:-1))%m->locations_n;
        m->locations_ready=0;snprintf(m->locations_status,sizeof m->locations_status,"Selected destination shown above. Move plugins checks it before confirmation.");
    } else if(!strcmp(key,"locations_plan")&&m->locations_n){m->locations_ready=0;post(m,J_LOC_PLAN);}
    else if(!strcmp(key,"locations_confirm")&&(m->locations_ready==1||m->locations_ready==2||m->locations_ready==4)){int mode=m->locations_ready;m->locations_ready=0;post(m,mode==1?J_LOC_MOVE:mode==4?J_LOC_RETURN:J_LOC_REPAIR);}
    else if(!strcmp(key,"locations_return")&&m->locations_return_available){m->locations_ready=0;post(m,J_LOC_RETURN_CHECK);}
    else if(!strcmp(key,"locations_repair")){m->locations_skin_check=1;m->locations_ready=0;post(m,J_LOC_REPAIR_CHECK);}
    else if(!strcmp(key,"locations_cancel")){m->locations_ready=0;snprintf(m->locations_status,sizeof m->locations_status,"Cancelled. No files or preferences changed.");}
}
static void locations_field(mgr_t *m,const char *key,char *b,int n) {
    int i=m->locations_selected;
    int scanning=m->storage_pending||m->job==J_LOC_SCAN||m->busy==J_LOC_SCAN;
    int calculating=!m->locations_ready&&(m->job==J_LOC_PLAN||m->busy==J_LOC_PLAN||m->job==J_LOC_RETURN_CHECK||m->busy==J_LOC_RETURN_CHECK||m->job==J_LOC_REPAIR_CHECK||m->busy==J_LOC_REPAIR_CHECK);
    int idle=!scanning&&!m->locations_ready&&!m->locations_running&&!m->busy&&!m->job;
    int queued=0;for(int k=0;k<m->npkg;k++)if(m->pkg[k].queued)queued++;
    if(queued)idle=0;
    int row=0;
    if(sscanf(key,"storage_row%d",&row)==1&&row>=1&&row<=3) {
        int index=m->storage_page*3+row-1;const char *suffix=strchr(key+8,'_');suffix=suffix?suffix+1:"";
        int visible=!m->locations_ready&&index<m->locations_n;
        if(!strcmp(suffix,"visible"))snprintf(b,n,"%d",visible);
        else if(!strcmp(suffix,"busy"))snprintf(b,n,"%d",visible&&calculating&&index==i);
        else if(!strcmp(suffix,"move"))snprintf(b,n,"%d",visible&&m->storage_viable[index]?(idle?1:queued?2:0):0);
        else if(!visible)b[0]=0;
        else if(!strcmp(suffix,"label"))snprintf(b,n,"%s",m->storage_labels[index]);
        else if(!strcmp(suffix,"space"))snprintf(b,n,"%s",m->storage_space[index]);
        else snprintf(b,n,"%s",calculating&&index==i?"Checking plugin files and available space...":m->locations_info[index]);
    }
    else if(!strcmp(key,"storage_warning")&&(scanning||calculating)&&m->locations_progress[0])snprintf(b,n,"%s",m->locations_progress);
    else if(!strcmp(key,"storage_tip")&&(scanning||calculating)&&m->locations_progress_detail[0])snprintf(b,n,"%s",m->locations_progress_detail);
    else if(!strcmp(key,"storage_warning")&&scanning)snprintf(b,n,"Checking drives...");
    else if(!strcmp(key,"storage_tip")&&scanning)snprintf(b,n,"Checking available space, plugin locations and skins. Please wait.");
    else if(!strcmp(key,"storage_warning")&&calculating)snprintf(b,n,"Calculating move to %s...",m->storage_labels[i]);
    else if(!strcmp(key,"storage_tip")&&calculating)snprintf(b,n,"Please wait. You can review the result before moving anything.");
    else if(!strcmp(key,"storage_warning")&&queued&&!m->storage_warning[0])snprintf(b,n,"Finish pending plugin changes first.");
    else if(!strcmp(key,"storage_tip")&&queued)snprintf(b,n,"Go to Catalog to finish the install/update and restart when asked.");
    else if(!strcmp(key,"storage_warning"))snprintf(b,n,"%s",m->storage_warning[0]?m->storage_warning:"Move only plugins installed with this manager.");
    else if(!strcmp(key,"storage_tip"))snprintf(b,n,"%s",m->storage_tip);
    else if(!strcmp(key,"storage_list"))snprintf(b,n,"%d",!m->locations_ready);
    else if(!strcmp(key,"storage_details"))snprintf(b,n,"%d",m->locations_ready!=0);
    else if(!strcmp(key,"storage_has_prev"))snprintf(b,n,"%d",idle&&m->storage_page>0);
    else if(!strcmp(key,"storage_has_next"))snprintf(b,n,"%d",idle&&(m->storage_page+1)*3<m->locations_n);
    else if(!strcmp(key,"storage_internal"))snprintf(b,n,"%s",m->storage_internal[0]?m->storage_internal:"Internal: checking...");
    else if(!strcmp(key,"storage_preferred"))snprintf(b,n,"%s",m->storage_preferred[0]?m->storage_preferred:"Preferred: checking...");
    else if(!strcmp(key,"locations_drive") && m->locations_ready==3)snprintf(b,n,"Critical event %d of %d",m->locations_log_count?m->locations_log_page+1:0,m->locations_log_count);
    else if(!strcmp(key,"locations_info") && m->locations_ready==3)snprintf(b,n,"Photograph this screen for support");
    else if(!strcmp(key,"locations_drive")&&m->locations_skin_check)snprintf(b,n,"Plugin skin check");
    else if(!strcmp(key,"locations_info")&&m->locations_skin_check)snprintf(b,n,"Missing skin files require reinstalling the affected plugin.");
    else if(!strcmp(key,"locations_drive")&&m->locations_return_available)snprintf(b,n,"Plugins moved; return to Internal is available");
    else if(!strcmp(key,"locations_drive")){char label[128];locations_label(m->locations_n?m->locations_roots[i]:"",label,sizeof label);snprintf(b,n,"%s%s",m->locations_n?"Move plugins to: ":"",m->locations_n?label:"No available move destination");}
    else if(!strcmp(key,"locations_info"))snprintf(b,n,"%s",m->locations_return_available?"Internal copies will be checked before switching back":m->locations_n?m->locations_info[i]:"Your plugins stay in their current locations");
    else if(!strcmp(key,"locations_summary"))snprintf(b,n,"%s",m->locations_summary);
    else if(!strcmp(key,"locations_status") && m->locations_ready==3)snprintf(b,n,"%s",m->locations_log_count?m->locations_log_lines[m->locations_log_page]:"No critical events recorded.");
    else if(!strcmp(key,"locations_status"))snprintf(b,n,"%s",m->locations_running?"Applying changes and restarting the application...":m->busy>=J_LOC_SCAN?"Checking storage and managed plugins...":m->locations_status);
    else if(!strcmp(key,"locations_ready"))snprintf(b,n,"%d",m->locations_ready);
    else if(!strcmp(key,"locations_can_move"))snprintf(b,n,"%d",idle&&m->locations_n>0&&!m->locations_return_available);
    else if(!strcmp(key,"locations_can_choose"))snprintf(b,n,"%d",idle&&m->locations_n>1&&!m->locations_return_available);
    else if(!strcmp(key,"locations_can_return"))snprintf(b,n,"%d",idle&&m->locations_return_available);
    else if(!strcmp(key,"locations_can_repair"))snprintf(b,n,"%d",idle);
    else if(!strcmp(key,"locations_can_log"))snprintf(b,n,"%d",idle);
    else if(!strcmp(key,"locations_log_older"))snprintf(b,n,"%d",m->locations_ready==3 && m->locations_log_page>0);
    else if(!strcmp(key,"locations_log_newer"))snprintf(b,n,"%d",m->locations_ready==3 && m->locations_log_page+1<m->locations_log_count);
    else if(!strcmp(key,"locations_idle"))snprintf(b,n,"%d",idle);
    else if(!strcmp(key,"locations_status1")||!strcmp(key,"locations_status2")||!strcmp(key,"locations_status3")) {
        char full[192];locations_field(m,"locations_status",full,sizeof full);
        const char *start=full;int line=key[strlen(key)-1]-'1';
        for(int part=0;part<=line;part++) {
            size_t cut=strlen(start);if(cut>64){cut=64;while(cut>0&&start[cut]!=' ')cut--;if(!cut)cut=64;}
            if(part==line){snprintf(b,n,"%.*s",(int)cut,start);break;}
            start+=cut;while(*start==' ')start++;
        }
    }
    else snprintf(b,n,"0");
}
