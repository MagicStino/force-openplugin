/* Progress is a replaced snapshot, never a per-file log. Critical history is
 * bounded to 8 KiB and contains no credentials or command output. */
#include <chrono>
struct LocationReport {
    fs::path log, progress;
    std::string operation, phase="Checking", plugin, file;
    unsigned long long done=0,total=0,files=0,checked=0;
    size_t index=0,count=0;
    std::chrono::steady_clock::time_point last{};
    bool active=false,originals_retained=true;
    static std::string clean(std::string s,size_t limit=180) {
        for(char &c:s)if((unsigned char)c<32 || c==127)c=' ';
        if(s.size()>limit)s=s.substr(0,limit-3)+"...";
        return s;
    }
    static void replace(const fs::path &path,const std::string &data) {
        std::string tmp=path.string()+".tmp-XXXXXX";std::vector<char> name(tmp.begin(),tmp.end());name.push_back(0);
        int fd=mkstemp(name.data());require(fd>=0,"Cannot save operation report");
        try {write_all(fd,data.data(),data.size());}catch(...){close(fd);unlink(name.data());throw;}
        close(fd);if(rename(name.data(),path.c_str())){unlink(name.data());throw std::runtime_error("Cannot commit operation report");}
    }
    void event(const std::string &message) {
        if(!active)return;
        std::string prior;
        if(fs::exists(log)) {require(fs::is_regular_file(log)&&!fs::is_symlink(log),"Unsafe diagnostic log");
            std::ifstream f(log,std::ios::binary);f.seekg(0,std::ios::end);auto n=f.tellg();if(n>8192)f.seekg(n-std::streamoff(8192));else f.seekg(0);
            prior.assign(std::istreambuf_iterator<char>(f),{});
        }
        char stamp[32];time_t now=time(nullptr);struct tm utc;gmtime_r(&now,&utc);strftime(stamp,sizeof stamp,"%Y-%m-%d %H:%M:%SZ",&utc);
        std::string line=std::string(stamp)+" "+operation+" "+clean(message,130)+"\n";
        prior+=line;
        while(prior.size()>8192){auto pos=prior.find('\n');if(pos==std::string::npos){prior=line;break;}prior.erase(0,pos+1);}
        replace(log,prior);
    }
    std::string code() const {return (phase=="Copying"||phase=="Copying back")?"LOC-COPY":phase=="Freeing Internal space"?"LOC-CLEANUP":phase=="Verifying"?"LOC-VERIFY":phase=="Updating plugin locations"?"LOC-SAVE":phase=="Repairing skin locations"?"LOC-SKIN":"LOC-CHECK";}
    void snapshot(const char *state="running",const std::string &message="",bool force=false) {
        if(!active)return;
        auto now=std::chrono::steady_clock::now();
        if(!force && now-last<std::chrono::milliseconds(500))return;
        last=now;picojson::object obj;
        obj["code"]=picojson::value(std::string(state)=="failed"?code():"");obj["operation"]=picojson::value(operation);obj["phase"]=picojson::value(phase);
        obj["plugin"]=picojson::value(clean(plugin,64));obj["state"]=picojson::value(std::string(state));
        obj["message"]=picojson::value(clean(message));obj["bytes_done"]=picojson::value(double(done));
        obj["bytes_total"]=picojson::value(double(total));obj["plugin_index"]=picojson::value(double(index));obj["plugin_count"]=picojson::value(double(count));
        obj["file"]=picojson::value(clean(file,100));obj["files_checked"]=picojson::value(double(files));obj["bytes_checked"]=picojson::value(double(checked));
        obj["original_files_retained"]=picojson::value(originals_retained);
        replace(progress,picojson::value(obj).serialize()+"\n");
    }
    void begin(const char *state,const std::string &mode) {
        fs::path base=fs::path(state).parent_path();log=base/".pluginmgr-locations-debug.log";progress=base/".pluginmgr-locations-progress.json";
        if(const char *path=getenv("OPENPLUGIN_PROGRESS_FILE")){require(path[0]=='/',"Invalid progress path");progress=path;}
        operation=mode+"-"+std::to_string(time(nullptr))+"-"+std::to_string(getpid());active=true;
        if(mode!="drives"&&mode!="check-repair")event("START "+mode);
        snapshot("running","",true);
    }
    void step(const std::string &next,const std::string &name="") {phase=next;plugin=name;file.clear();snapshot("running","",true);}
    void finish(const std::string &message) {event("DONE "+message);snapshot("done",message,true);}
    void fail(const std::string &message) noexcept {
        try {event("ERROR "+code()+" "+phase+" "+clean(plugin,40)+": "+message);snapshot("failed",message,true);}catch(...) {}
    }
};
static LocationReport report;
static void copy_reported(const fs::path &source,const fs::path &target) {
    require(!fs::exists(target),"Staging folder already exists");fs::create_directory(target);
    for(const auto &e:fs::recursive_directory_iterator(source)) {
        report.file=e.path().lexically_relative(source).string();report.snapshot();
        auto out=target/e.path().lexically_relative(source);auto status=e.symlink_status();
        if(fs::is_symlink(status)){fs::copy_symlink(e.path(),out);continue;}
        if(fs::is_directory(status)){fs::create_directory(out);continue;}
        require(fs::is_regular_file(status),"Unsupported file in plugin package");
        std::ifstream input(e.path(),std::ios::binary);require(input.good(),"Cannot read plugin file");
        int fd=open(out.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);require(fd>=0,"Cannot create copied plugin file");
        try {char bytes[65536];while(input){input.read(bytes,sizeof bytes);auto n=input.gcount();if(n){size_t left=(size_t)n;const char *at=bytes;while(left){ssize_t written=write(fd,at,left);if(written<0 && errno==EINTR)continue;require(written>0,"Cannot write copied plugin file");at+=written;left-=written;}report.done+=n;report.snapshot();}}
            require(!input.bad(),"Cannot read plugin file");require(fchmod(fd,(mode_t)status.permissions()&0777)==0,"Cannot preserve plugin permissions");
        }catch(...){close(fd);throw;}close(fd);
    }
    for(const auto &e:fs::recursive_directory_iterator(source))if(e.is_directory()&&!e.is_symlink())fs::permissions(target/e.path().lexically_relative(source),e.status().permissions());
    fs::permissions(target,fs::status(source).permissions());
}
