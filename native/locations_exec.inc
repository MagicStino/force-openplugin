/* A UUID-bound executable view of a dedicated manager folder. Never remount the
 * user's drive. Only this view gets exec; nosuid/nodev remain enforced. */
#include <sys/mount.h>
#include <sys/mman.h>
#include <thread>
static const fs::path volume_base="/run/openplugin-volumes";
static const fs::path volume_config="/data/openplugin/locations/volumes";
struct VolumeMount {std::string path,device,type;bool rw=false,exec=false;};
static VolumeMount volume_mount(const fs::path &path) {
    auto name=canonical(path.c_str());VolumeMount found;
    FILE *f=setmntent("/proc/mounts","r");require(f,"Cannot read drive mounts");
    while(auto *m=getmntent(f)) {std::string at=m->mnt_dir;
        if(name.compare(0,at.size(),at)||(at!="/"&&name.size()>at.size()&&name[at.size()]!='/')||at.size()<found.path.size())continue;
        found={at,m->mnt_fsname,m->mnt_type,hasmntopt(m,"rw")!=nullptr,hasmntopt(m,"noexec")==nullptr};
    }endmntent(f);return found;
}
static bool volume_id_valid(const std::string &id) {return !id.empty()&&id.size()<=64&&id.find_first_not_of("0123456789abcdefABCDEF-")==std::string::npos;}
static std::string volume_id(const VolumeMount &m) {
    struct stat device;require(stat(m.device.c_str(),&device)==0&&S_ISBLK(device.st_mode),"Drive identity unavailable");
    std::string id;
    require(fs::is_directory("/dev/disk/by-uuid"),"Drive UUIDs unavailable");
    for(auto &e:fs::directory_iterator("/dev/disk/by-uuid")){struct stat other;
        if(stat(e.path().c_str(),&other)==0&&S_ISBLK(other.st_mode)&&other.st_rdev==device.st_rdev){require(id.empty(),"Ambiguous drive UUID");id=e.path().filename();}}
    require(volume_id_valid(id),"Drive needs a stable UUID before moving plugins");return id;
}
static bool external_volume(const VolumeMount &m) {
    // Force mounts user drives directly under /media. Nested bind mounts are
    // application/content views, never independent storage destinations.
    return fs::path(m.path).parent_path()=="/media"&&m.path!="/media/az01-internal"&&m.path!="/media/az01-internal-sd"&&m.path!="/media/acvs-synths";
}
static bool supported_volume(const VolumeMount &m) {
    return m.type=="ext4"||m.type=="ext3"||m.type=="f2fs"||m.type=="btrfs"||m.type=="exfat"||m.type=="vfat";
}
static bool startup_hook_available() {
    // The image includes this hook; /run is used only for reversible development tests.
    for(auto base:{"/etc/systemd/system/acvs.service.d","/usr/lib/systemd/system/acvs.service.d","/run/systemd/system/acvs.service.d"}) {
        fs::path p=fs::path(base)/"25-openplugin-volumes.conf";
        if(fs::is_regular_file(p)&&read_bytes(p).find("/data/openplugin/locations/locations-tool restore-volumes")!=std::string::npos)return true;
    }return false;
}
static fs::path volume_target(const fs::path &requested) {
#ifdef OPENPLUGIN_TEST
    return requested;
#else
    require(requested.string().find(volume_base.string()+"/")!=0,"Select the physical drive as the destination");
    fs::path at=fs::exists(requested)?requested:requested.parent_path();auto m=volume_mount(at);
    if(!external_volume(m))return requested;
    require(m.rw&&supported_volume(m),"Drive is read-only or has an unsupported filesystem");
    require(requested==fs::path(m.path)/"Synths","Choose the drive's Synths destination");
    require(startup_hook_available(),"SSD startup support is missing; install the updated manager image");
    return volume_base/volume_id(m)/"Synths";
#endif
}
static void safe_directory(const fs::path &path) {
    fs::path part;
    for(const auto &component:path){part/=component;require(!fs::is_symlink(part),"Unsafe symbolic link in manager storage path");if(!fs::exists(part))fs::create_directory(part);require(fs::is_directory(part),"Manager storage path is not a directory");}
}
static void ensure_volume(const VolumeMount &m,const std::string &id) {
    require(external_volume(m)&&m.rw&&supported_volume(m)&&volume_id(m)==id,"Drive identity changed");
    fs::path source=fs::path(m.path)/".openplugin"/"Synths",view=volume_base/id/"Synths";
    safe_directory(source);safe_directory(view);
    auto current=volume_mount(view);
    if(current.path==view) {
        struct stat a,b;require(stat(source.c_str(),&a)==0&&stat(view.c_str(),&b)==0&&a.st_dev==b.st_dev&&a.st_ino==b.st_ino&&current.exec&&current.rw,"Existing plugin view does not match the selected drive");return;
    }
    require(fs::is_empty(view),"Plugin view contains unexpected files");
    require(mount(source.c_str(),view.c_str(),nullptr,MS_BIND,nullptr)==0,"Cannot create executable plugin view");
    // Preserve the Force drive protection against following symbolic links.
    if(mount(nullptr,view.c_str(),nullptr,MS_REMOUNT|MS_BIND|MS_NOSUID|MS_NODEV|256 /* MS_NOSYMFOLLOW */,nullptr)!=0){umount(view.c_str());throw std::runtime_error("Cannot enable execution for the plugin folder");}
    auto check=volume_mount(view);if(!check.exec||!check.rw){umount(view.c_str());throw std::runtime_error("Executable plugin view verification failed");}
}
static void probe_execution(const fs::path &folder) {
    std::string name=(folder/".openplugin-exec-check-XXXXXX").string();std::vector<char> path(name.begin(),name.end());path.push_back(0);
    int fd=mkstemp(path.data());require(fd>=0,"Cannot test plugin execution on this drive");
    try{char page[4096]={0};write_all(fd,page,sizeof page);void *memory=mmap(nullptr,sizeof page,PROT_READ|PROT_EXEC,MAP_PRIVATE,fd,0);
        bool allowed=memory!=MAP_FAILED;if(allowed)munmap(memory,sizeof page);close(fd);fd=-1;unlink(path.data());require(allowed,"Drive cannot load executable plugin code");
    }catch(...){if(fd>=0)close(fd);unlink(path.data());throw;}
}
static void prepare_volume(const fs::path &requested,const fs::path &effective) {
    if(requested==effective)return;
    auto m=volume_mount(requested.parent_path());auto id=volume_id(m);
    require(effective==volume_base/id/"Synths","Drive changed since confirmation");
    require(startup_hook_available(),"Persistent plugin startup support is missing");
    safe_directory(volume_config);
    // The persistent helper remains on Internal, independent of plugin updates.
    auto helper=volume_config.parent_path()/"locations-tool";
    fs::path temporary=helper.string()+".new-"+std::to_string(getpid());
    fs::copy_file("/proc/self/exe",temporary,fs::copy_options::none);fs::permissions(temporary,fs::perms::owner_all);
    int helperfd=open(temporary.c_str(),O_RDONLY|O_NOFOLLOW);require(helperfd>=0,"Cannot sync startup helper");int synced=fsync(helperfd);close(helperfd);require(synced==0,"Cannot sync startup helper");fs::rename(temporary,helper);
    ensure_volume(m,id);probe_execution(effective);
    auto names=volume_config.parent_path()/"names";safe_directory(names);
    auto label=fs::path(m.path).filename().string();require(label.find('\n')==std::string::npos,"Unsupported drive label");
    fs::path label_file=names/id;int label_fd=open(label_file.c_str(),O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW,0600);require(label_fd>=0,"Cannot save drive label");try{write_all(label_fd,label.data(),label.size());}catch(...){close(label_fd);throw;}close(label_fd);
    fs::path record=volume_config/id;
    if(fs::exists(record))require(!fs::is_symlink(record)&&read_bytes(record)==id+"\n","Invalid saved drive identity");
    else {int fd=open(record.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);require(fd>=0,"Cannot persist drive identity");std::string content=id+"\n";try{write_all(fd,content.data(),content.size());}catch(...){close(fd);throw;}close(fd);}
    for(auto dir:{volume_config,volume_config.parent_path()}){int fd=open(dir.c_str(),O_RDONLY|O_DIRECTORY);require(fd>=0,"Cannot sync startup configuration");int synced=fsync(fd);close(fd);require(synced==0,"Cannot sync startup configuration");}
}
static int restore_volumes() {
    if(!fs::exists(volume_config))return 0;
    require(!fs::is_symlink(volume_config),"Unsafe saved volume directory");
    std::set<std::string> pending,errors;
    for(auto &e:fs::directory_iterator(volume_config)) {std::string id=e.path().filename();require(volume_id_valid(id)&&e.is_regular_file()&&!e.is_symlink()&&read_bytes(e.path())==id+"\n","Invalid saved drive identity");pending.insert(id);}
    // Bounded wait for Force's drive scanner. Missing drives never cause writes
    // into an empty mountpoint or an endless app startup delay.
    for(int attempt=0;attempt<20&&!pending.empty();attempt++) {
        FILE *f=setmntent("/proc/mounts","r");require(f,"Cannot inspect mounted drives");std::vector<VolumeMount> mounts;
        while(auto *m=getmntent(f)){VolumeMount v{m->mnt_dir,m->mnt_fsname,m->mnt_type,hasmntopt(m,"rw")!=nullptr,hasmntopt(m,"noexec")==nullptr};if(external_volume(v))mounts.push_back(v);}endmntent(f);
        for(auto &m:mounts){try{auto id=volume_id(m);if(pending.count(id)){ensure_volume(m,id);pending.erase(id);}}catch(const std::exception &e){if(errors.insert(e.what()).second)fprintf(stderr,"OpenPlugin volume: %s\n",e.what());}}
        if(!pending.empty())std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }
    for(auto &id:pending)fprintf(stderr,"OpenPlugin: drive %s unavailable; connect it and restart the application.\n",id.c_str());
    return 0;
}
