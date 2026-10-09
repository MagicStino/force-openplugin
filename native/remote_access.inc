/* Credentials remain local and are exposed only on the requested touchscreen page. */
#include <ifaddrs.h>
#include <arpa/inet.h>
#include <sys/socket.h>
static int remote_running(void) {int fd=socket(AF_INET,SOCK_STREAM,0);if(fd<0)return 0;struct sockaddr_in a={0};a.sin_family=AF_INET;a.sin_port=htons(22);a.sin_addr.s_addr=htonl(INADDR_LOOPBACK);int ok=connect(fd,(struct sockaddr*)&a,sizeof a)==0;close(fd);return ok;}
static void do_remote(mgr_t *m,int job) {
#ifdef __arm__
    char *argv[]={"/bin/sh","/usr/share/openplugin/remote-access.sh",job==J_REMOTE_ENABLE?"enable":"disable",NULL};
    int error=run(argv);
    say(m,error?ERR:OK,error?"SSH change failed; inspect the service locally.":job==J_REMOTE_ENABLE?"SSH enabled. See Remote Access for your password.":"SSH disabled; stays disabled after reboot.");
#else
    say(m,WARN,"Remote access controls require Force/MPC hardware.");
#endif
}
static void remote_field(mgr_t *m,const char *key,char *b,int n) {
    snprintf(b,n,"0");
    if(!strcmp(key,"remote_status")) {
        snprintf(b,n,"%s",access("/usr/share/openplugin/remote-sshd_config",R_OK)?"Not available in this image":remote_running()?"Running - SSH / SFTP port 22":access("/data/openplugin/ssh/disabled",F_OK)==0?"Disabled (saved across reboots)":"Stopped - tap Enable SSH to retry");
    } else if(!strcmp(key,"remote_password")) {
        snprintf(b,n,"Username: root    Password: mpc    Port: 22");
    } else if(!strcmp(key,"remote_ip")) {
        snprintf(b,n,"No IPv4 network address");struct ifaddrs *all=NULL;
        if(getifaddrs(&all)==0){int used=0;for(struct ifaddrs *a=all;a;a=a->ifa_next){if(!a->ifa_addr||a->ifa_addr->sa_family!=AF_INET||!strcmp(a->ifa_name,"lo"))continue;char ip[INET_ADDRSTRLEN];if(inet_ntop(AF_INET,&((struct sockaddr_in*)a->ifa_addr)->sin_addr,ip,sizeof ip)){int written=snprintf(b+used,n-used,"%s%s",used?" | ":"",ip);if(written<0||written>=n-used)break;used+=written;}}freeifaddrs(all);}
    } else if(!strcmp(key,"remote_storage")) {
        snprintf(b,n,"SFTP: browse /media for internal storage, SD and USB mounts");
    }
}
