// Filesystem operations run outside MPC; original plugin folders are never deleted.
#define main skin_registration_main
#include "skin_locations.cpp"
#undef main
#include "third_party/picojson/picojson.h"
#include <filesystem>
#include <map>
#include <set>
#include <sstream>
#include <functional>
#include <algorithm>
#include <mntent.h>
#include <sys/statvfs.h>
namespace fs = std::filesystem;

static std::string read_bytes(const fs::path &p) {
    std::ifstream f(p, std::ios::binary);
    require(f.good(), "Cannot read file");
    std::string s((std::istreambuf_iterator<char>(f)), {});
    require(!f.bad(), "File read failed"); return s;
}
static std::string field(const picojson::value &v, const char *key) {
    if (!v.is<picojson::object>() || !v.contains(key) || !v.get(key).is<std::string>()) return "";
    return v.get(key).get<std::string>();
}
struct Owned { std::string id, uid, name, binary; fs::path folder; };
static std::vector<Owned> owned(XMLDocument &doc, const char *state, size_t &skipped) {
    std::map<std::string,std::string> records;
    std::ifstream input(state); require(input.good(), "Manager installation history is missing; ownership cannot be proved");
    std::string id, version;
    while (input >> id >> version) records[id] = version;
    std::vector<Owned> result; std::set<std::string> ids, folders;
    auto *props = doc.RootElement(); require(props && !strcmp(props->Name(), "PROPERTIES"), "Invalid settings root");
    XMLElement *list = nullptr;
    for(auto *v=props->FirstChildElement("VALUE");v;v=v->NextSiblingElement("VALUE"))
        if(v->Attribute("name","pluginList-arm")) { require(!list,"Duplicate plugin lists"); list=v; }
    require(list && list->FirstChildElement("KNOWNPLUGINS"), "Plugin list is missing");
    for(auto *p=list->FirstChildElement("KNOWNPLUGINS")->FirstChildElement("PLUGIN");p;p=p->NextSiblingElement("PLUGIN")) {
        const char *file=p->Attribute("file"), *uid=p->Attribute("uid");
        if(!file || !uid || !p->Attribute("format","VST")) { ++skipped; continue; }
        fs::path binary(file), folder=binary.parent_path();
        if (!binary.is_absolute() || folder.parent_path().filename()!="Synths" ||
            folder.filename().string().find(" - VST - ")==std::string::npos ||
            folder.string().find("/usr/")==0 || !fs::is_regular_file(binary) ||
            fs::is_symlink(folder) || fs::is_symlink(binary) ||
            !fs::is_regular_file(folder/"mpc-plugin.json") || fs::is_symlink(folder/"mpc-plugin.json") || fs::file_size(folder/"mpc-plugin.json") > (1u<<20)) { ++skipped; continue; }
        picojson::value manifest;
        std::string error=picojson::parse(manifest,read_bytes(folder/"mpc-plugin.json"));
        std::string mid=field(manifest,"id"), kind=field(manifest,"kind");
        if(!error.empty() || mid.empty() || mid.size()>64 || mid.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789-")!=std::string::npos || !records.count(mid) || records[mid]!=field(manifest,"version") ||
           mid=="openplugin-manager" || mid=="plugin-manager" ||
           (kind!="instrument" && kind!="effect") || field(manifest,"layout")!="portable" ||
           field(manifest,"uid")!=uid || field(manifest,"so")!=binary.filename() ||
           field(manifest,"skin")!=folder.filename()) { ++skipped; continue; }
        require(ids.insert(mid).second && folders.insert(canonical(folder.c_str())).second,"Ambiguous managed plugin copies");
        result.push_back({mid,uid,p->Attribute("name")?p->Attribute("name"):mid,file,folder});
    }
    return result;
}
static void load_settings(XMLDocument &doc, const char *path) {
    require(fs::is_regular_file(path) && !fs::is_symlink(path),"Settings must be a regular file");
    require(doc.LoadFile(path)==XML_SUCCESS,"Invalid settings XML");
}
static bool scanned(XMLDocument &doc, const fs::path &root) {
    auto *props=doc.RootElement();
    for(auto *v=props->FirstChildElement("VALUE");v;v=v->NextSiblingElement("VALUE")) {
        if(!v->Attribute("name","SynthContentLocations")) continue;
        auto *list=v->FirstChildElement("SynthContentLocations"); if(!list) continue;
        for(auto *p=list->FirstChildElement("Location");p;p=p->NextSiblingElement("Location"))
            if(p->GetText() && canonical(p->GetText())==canonical(root.c_str())) return true;
    }
    return false;
}
#include "locations_exec.inc"
static unsigned long long destination(const fs::path &root, dev_t *device=nullptr) {
    require(root.is_absolute() && root.filename()=="Synths" && root.string().find('\n')==std::string::npos,
            "Choose a Synths folder on a mounted drive");
    require(root.string().find("/usr/")!=0 && root.string().find("/synths/")!=0,"Factory content cannot be a move destination");
    fs::path at=fs::exists(root)?root:root.parent_path();
    require(fs::is_directory(at),"Destination drive is unavailable");

#ifndef OPENPLUGIN_TEST
    auto mount=volume_mount(at);
    bool internal=mount.path=="/sdcard" || mount.path=="/media/az01-internal-sd" || mount.path=="/data" || mount.path=="/media/az01-internal";
    require(mount.rw && supported_volume(mount) && ((internal&&mount.exec) || external_volume(mount)),
            "Drive is read-only, unavailable or unsupported");
#endif
    struct stat st; require(stat(at.c_str(),&st)==0,"Destination disappeared");
    if(device) *device=st.st_dev;
    struct statvfs v; require(statvfs(at.c_str(),&v)==0 && !(v.f_flag & ST_RDONLY) && access(at.c_str(),W_OK)==0,"Destination is not writable");
    return (unsigned long long)v.f_bavail*v.f_frsize;
}
/* Resolve a downloaded package before confirmation and repeat before install.
 * Its files have not been installed yet; links force an Internal destination. */
static fs::path install_target(fs::path requested,const fs::path &package) {
    require(fs::is_directory(package)&&!fs::is_symlink(package),"Downloaded package is missing");
    bool links=false;
    for(auto &e:fs::recursive_directory_iterator(package)) {
        if(e.is_symlink())links=true;
        else require(e.is_directory()||e.is_regular_file(),"Package contains unsupported special files");
    }
    // Portable releases also restore links recorded in MODES after extraction.
    fs::path modes=package/"MODES";
    if(fs::is_regular_file(modes)&&!fs::is_symlink(modes)) {
        require(fs::file_size(modes)<(16u<<20),"Package mode manifest is too large");
        std::istringstream input(read_bytes(modes));std::string line;
        while(std::getline(input,line))if(line.compare(0,2,"l\t")==0)links=true;
    }
    if(links) {
#ifdef OPENPLUGIN_TEST
        require(getenv("OPENPLUGIN_TEST_INTERNAL"),"Internal test destination missing");fs::path internal=getenv("OPENPLUGIN_TEST_INTERNAL");destination(internal);return internal;
#else
        for(auto root:{"/sdcard/Synths","/media/az01-internal-sd/Synths"})try{destination(root);return root;}catch(const std::exception &){}
        throw std::runtime_error("This package needs symbolic links, but Internal storage is unavailable");
#endif
    }
#ifndef OPENPLUGIN_TEST
    if(requested.string().find(volume_base.string()+"/")==0) {
        auto id=requested.parent_path().filename().string();require(volume_id_valid(id)&&requested==volume_base/id/"Synths","Invalid plugin view path");
        FILE *f=setmntent("/proc/mounts","r");require(f,"Cannot inspect drives");std::vector<VolumeMount> mounts;
        while(auto *m=getmntent(f)){VolumeMount v{m->mnt_dir,m->mnt_fsname,m->mnt_type,hasmntopt(m,"rw")!=nullptr,hasmntopt(m,"noexec")==nullptr};if(external_volume(v))mounts.push_back(v);}endmntent(f);
        fs::path physical;
        for(auto &m:mounts){std::string found;try{found=volume_id(m);}catch(const std::exception &){continue;}if(found==id){require(physical.empty(),"Ambiguous mounted drive");physical=fs::path(m.path)/"Synths";}}
        require(!physical.empty(),"Selected plugin drive is disconnected");requested=physical;
    }
#endif
    destination(requested);auto target=volume_target(requested);prepare_volume(requested,target);return target;
}
#include "locations_report.inc"
static bool same_file(const fs::path &a,const fs::path &b) {
    if(fs::file_size(a)!=fs::file_size(b)) return false;
    std::ifstream x(a,std::ios::binary), y(b,std::ios::binary); char bx[65536],by[65536];
    while(x && y) { report.snapshot(); x.read(bx,sizeof bx);y.read(by,sizeof by);if(x.gcount()!=y.gcount() || memcmp(bx,by,x.gcount()))return false; }
    return !x.bad() && !y.bad();
}
static void preset_paths(const fs::path &file, const std::string &source, const std::string &target, bool write) {
    XMLDocument preset; require(preset.LoadFile(file.c_str())==XML_SUCCESS,"Preset XML cannot be safely relocated");
    bool changed=false;
    auto replace=[&](const char *v)->std::string {
        std::string value=v?v:"";
        if(value.find(source)==std::string::npos)return value;
        require(value==source || value.compare(0,source.size()+1,source+"/")==0,"Preset contains an unsupported embedded path");
        changed=true;return target+value.substr(source.size());
    };
    std::function<void(XMLNode*)> visit=[&](XMLNode *node) {
        if(auto *element=node->ToElement()) {
            std::vector<std::pair<std::string,std::string>> attributes;
            for(auto *a=element->FirstAttribute();a;a=a->Next())attributes.push_back({a->Name(),replace(a->Value())});
            for(auto &a:attributes)element->SetAttribute(a.first.c_str(),a.second.c_str());
        } else if(auto *text=node->ToText())text->SetValue(replace(text->Value()).c_str());
        for(auto *child=node->FirstChild();child;child=child->NextSibling())visit(child);
    };
    visit(&preset);
    if(write && changed)require(preset.SaveFile(file.c_str())==XML_SUCCESS,"Could not update copied preset paths");
}
struct UnsupportedMove:std::runtime_error {using std::runtime_error::runtime_error;};
static void movable_require(bool ok,const char *message){if(!ok)throw UnsupportedMove(message);}
static unsigned long long check_tree(const Owned &p, const fs::path &target, bool inspect_contents=true) {
    unsigned long long size=0;
    const std::string source=p.folder.string();
    for(const auto &e:fs::recursive_directory_iterator(p.folder)) {
        report.file=e.path().lexically_relative(p.folder).string();report.files++;report.snapshot();
        auto status=e.symlink_status();
        if(fs::is_symlink(status)) {
            auto link=fs::read_symlink(e.path());
            auto resolved=(e.path().parent_path()/link).lexically_normal().string();
            movable_require(!link.is_absolute() && resolved.compare(0,source.size()+1,source+"/")==0,"Plugin has an external symbolic link; move blocked");
        } else if(fs::is_regular_file(status)) {
            size+=e.file_size();
            if(!inspect_contents)continue;
            if(e.path().extension()==".xpl") { preset_paths(e.path(),source,target.string(),false); continue; }
            // Preserve external resources; reject an embedded reference to the old plugin folder.
            // This conservative first version avoids silently breaking package-specific paths.
            std::ifstream f(e.path(),std::ios::binary); require(f.good(),"Plugin file is unreadable");
            char bytes[65536]; std::string tail;
            while(f) { f.read(bytes,sizeof bytes);tail.append(bytes,f.gcount());report.checked+=f.gcount();report.snapshot();
                movable_require(tail.find(source)==std::string::npos,"Plugin contains absolute references to its current folder; move blocked");
                if(tail.size()>source.size())tail.erase(0,tail.size()-source.size()); }
            require(!f.bad(),"Plugin read failed");
        } else movable_require(fs::is_directory(status),"Plugin has unsupported special files");
    }
    return size;
}
static void verify_tree(const fs::path &source,const fs::path &target) {
    for(const auto &e:fs::recursive_directory_iterator(source)) {
        auto relative=e.path().lexically_relative(source); auto copy=target/relative;
        report.file=relative.string();report.files++;report.snapshot();
        if(e.is_symlink()) require(fs::is_symlink(copy) && fs::read_symlink(e.path())==fs::read_symlink(copy),"Symbolic link verification failed");
        else if(e.is_regular_file()) require(fs::is_regular_file(copy) && !fs::is_symlink(copy) && same_file(e.path(),copy),"Copied file verification failed");
        else require(fs::is_directory(copy),"Copied directory missing");
    }
}
static void sync_tree(const fs::path &path) {
    // Flush the completed package together, including files, permissions and
    // directory entries. Per-file flushes make small-file packages painfully slow.
    int fd=open(path.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW);
    require(fd>=0,"Cannot sync copied package");
    report.step("Saving copied files to drive",report.plugin);
    int result=syncfs(fd);close(fd);
    require(result==0,"Cannot sync copied package; source retained");
}
static void save_atomic(XMLDocument &doc,const fs::path &settings,const fs::path &backup) {
    require(system("pidof MPC >/dev/null 2>&1")==256,"MPC restarted during the operation; settings unchanged");
    XMLPrinter out;doc.Print(&out);XMLDocument check;require(check.Parse(out.CStr())==XML_SUCCESS,"Generated settings invalid");
    struct stat st;require(stat(settings.c_str(),&st)==0,"Settings disappeared");
    int fd=open(backup.c_str(),O_CREAT|O_EXCL|O_WRONLY,0600);require(fd>=0,"Cannot create recovery backup");
    std::string original=read_bytes(settings);
    try {write_all(fd,original.data(),original.size());}catch(...){close(fd);throw;}close(fd);
    std::string temp=settings.string()+".move-XXXXXX";std::vector<char> name(temp.begin(),temp.end());name.push_back(0);
    fd=mkstemp(name.data());require(fd>=0,"Cannot stage settings");
    try {require(fchown(fd,st.st_uid,st.st_gid)==0 && fchmod(fd,st.st_mode&0777)==0,"Cannot preserve settings metadata");write_all(fd,out.CStr(),out.CStrSize()-1);}
    catch(...){close(fd);unlink(name.data());throw;}close(fd);
    require(rename(name.data(),settings.c_str())==0,"Cannot commit settings");
    fd=open(settings.parent_path().c_str(),O_RDONLY|O_DIRECTORY);require(fd>=0,"Cannot sync settings directory");
    int result=fsync(fd);close(fd);require(result==0,"Settings committed but directory sync failed; use recovery backup");
}
static void add_root(XMLDocument &doc,const fs::path &root) {
    if(scanned(doc,root))return;
    XMLElement *value=nullptr;
    for(auto *v=doc.RootElement()->FirstChildElement("VALUE");v;v=v->NextSiblingElement("VALUE"))
        if(v->Attribute("name","SynthContentLocations")){require(!value,"Duplicate content settings");value=v;}
    if(!value){value=doc.NewElement("VALUE");value->SetAttribute("name","SynthContentLocations");doc.RootElement()->InsertEndChild(value);}
    auto *list=value->FirstChildElement("SynthContentLocations");
    if(!list){require(!value->FirstChildElement()&&!value->GetText()&&!value->Attribute("val"),"Unsupported content settings");list=doc.NewElement("SynthContentLocations");value->InsertEndChild(list);}
    auto *location=doc.NewElement("Location");location->SetText(root.c_str());list->InsertEndChild(location);
}
static void select_install_target(XMLDocument &doc,const fs::path &target) {
    XMLElement *value=nullptr;
    for(auto *v=doc.RootElement()->FirstChildElement("VALUE");v;v=v->NextSiblingElement("VALUE"))
        if(v->Attribute("name","OpenPlugin.InstallTarget")){require(!value,"Duplicate manager install preference");value=v;}
    if(!value){value=doc.NewElement("VALUE");value->SetAttribute("name","OpenPlugin.InstallTarget");doc.RootElement()->InsertEndChild(value);}
    value->SetAttribute("val",target.c_str());
}
#include "locations_return.inc"
#include "locations_drives.inc"

int main(int argc,char **argv) {
    int lock=-1; std::string transaction;
    try {
        if(argc==2 && std::string(argv[1])=="restore-volumes")return restore_volumes();
        require(argc>=4,"Usage: locations-tool inspect|plan|move|repair settings state [target plan]");
        std::string mode=argv[1];require(mode=="inspect"||mode=="eligible"||mode=="plan"||mode=="move"||mode=="repair"||mode=="check-repair"||mode=="check-return"||mode=="plan-return"||mode=="return"||mode=="install-target"||mode=="drives","Unknown operation");
        bool mutation=mode=="move"||mode=="repair"||mode=="return";
        if(mutation){require(system("pidof MPC >/dev/null 2>&1")==256,"Save your project and stop MPC first");
            std::string name=std::string(argv[2])+".openplugin-lock";lock=open(name.c_str(),O_CREAT|O_RDWR|O_NOFOLLOW,0600);
            require(lock>=0&&flock(lock,LOCK_EX|LOCK_NB)==0,"Settings are busy");}
        if(mutation || mode=="plan" || mode=="plan-return" || mode=="drives" || mode=="check-repair")report.begin(argv[3],mode);
        XMLDocument doc;load_settings(doc,argv[2]);size_t skipped=0;
        if(mode=="check-return"){auto journal=latest_return(doc,argv[2],argv[3]);puts(journal.empty()?"No return to Internal available.":"A completed move has Internal copies available for verification.");return journal.empty()?2:0;}
        if(mode=="plan-return"||mode=="return"){require(argc==5,"Return confirmation path required");return_operation(doc,argv[2],argv[3],argv[4],mode=="return");if(lock>=0)close(lock);return 0;}
        if(mode=="drives"){drive_list(doc,argv[2],argv[3]);return 0;}
        if(mode=="install-target"){require(argc==6,"Install destination and package required");printf("%s\n",install_target(argv[4],argv[5]).c_str());return 0;}
        auto plugins=owned(doc,argv[3],skipped);report.count=plugins.size();
        if(mode=="inspect") {printf("%zu managed VSTs; %zu other or unverified registrations left untouched.\n",plugins.size(),skipped);return 0;}
        if(mode=="repair" || mode=="check-repair") {
            report.step("Repairing skin locations");
            size_t missing=0,absent=0;
            for(auto &p:plugins) {
                report.index++;report.step("Checking skin locations",p.name);
                if(!fs::is_directory(p.folder/"Plugin Skins") || fs::is_empty(p.folder/"Plugin Skins")){++absent;continue;}
                if(!scanned(doc,p.folder.parent_path())){add_root(doc,p.folder.parent_path());++missing;}
            }
            if(mode=="check-repair") {
                if(!missing)printf("No missing skin search locations. %zu plugins have no skin files; reinstall those packages.\n",absent);
                else printf("Repair %zu missing screen locations. Save your project before restarting. %zu plugins need skin files reinstalled.\n",missing,absent);
                return missing?0:2;
            }
            if(missing){std::string backup=std::string(argv[2])+".bak-repair-"+std::to_string(time(nullptr))+"-"+std::to_string(getpid());save_atomic(doc,argv[2],backup);}
            report.finish("Added "+std::to_string(missing)+" skin search locations; "+std::to_string(absent)+" packages missing skin files");
            printf("Added %zu skin search locations. %zu plugins have no skin files; reinstall those packages.\n",missing,absent);close(lock);return 0;
        }
        require(argc==6,"Target and plan file required");fs::path requested=argv[4],target=volume_target(requested);dev_t device;
        auto free=destination(requested,&device);
        std::vector<Owned> moving;unsigned long long bytes=0;size_t staying=0;std::string first_staying;
        for(auto &p:plugins) {
            report.index++;report.step("Checking plugin files",p.name);
            if(canonical(p.folder.parent_path().c_str())==canonical(target.c_str()))continue;
            auto existing=target/p.folder.filename();
            require((!fs::exists(existing)&&!fs::is_symlink(existing)) || (internal_root(target)&&compatibility_link(existing,p.folder)) || reusable_copy(p,target,argv[2],mode!="eligible"),"Destination contains different plugin content; nothing overwritten");
            try {
#ifndef OPENPLUGIN_TEST
                if(requested!=target)for(auto &e:fs::recursive_directory_iterator(p.folder))movable_require(!e.is_symlink(),"Package needs symbolic links; stays in its current location");
#endif
                bytes+=check_tree(p,target/p.folder.filename(),mode!="eligible");
            } catch(const UnsupportedMove &e) {
                ++staying;if(first_staying.empty())first_staying=p.name+": "+e.what();continue;
            } catch(const std::exception &e) {throw std::runtime_error(p.name+": "+e.what());}
            moving.push_back(p);
        }
        require(!moving.empty(),first_staying.empty()?"No verified manager-owned VSTs need moving here":first_staying.c_str());
        require(free>bytes+(64ull<<20),"Not enough free space for a verified copy plus reserve");
        if(mode=="eligible") {printf("%zu managed VSTs can move; %zu incompatible packages stay in place.\n",moving.size(),staying);return 0;}
        report.total=bytes;report.count=moving.size();report.index=moving.size();
        if(mode=="plan") {
            XMLDocument plan;auto *r=plan.NewElement("Move");plan.InsertEndChild(r);r->SetAttribute("requested",requested.c_str());r->SetAttribute("target",target.c_str());r->SetAttribute("device",(uint64_t)device);
            for(auto &p:moving){auto *item=plan.NewElement("Plugin");item->SetAttribute("id",p.id.c_str());item->SetAttribute("uid",p.uid.c_str());item->SetAttribute("file",p.binary.c_str());r->InsertEndChild(item);}
            require(plan.SaveFile(argv[5])==XML_SUCCESS,"Cannot save move plan");
            if(staying)report.event("KEEP "+std::to_string(staying)+" incompatible packages: "+first_staying);
            report.finish("Checks passed; waiting for confirmation");
            printf("Move %zu plugins (%.1f MB); %zu stay in place. Save your project before restarting. Copies verified before freeing Internal space.\n",moving.size(),bytes/1048576.0,staying);return 0;
        }
        XMLDocument plan;require(plan.LoadFile(argv[5])==XML_SUCCESS,"Move plan missing; review the move again");auto *r=plan.RootElement();
        require(r && r->Attribute("requested",requested.c_str()) && r->Attribute("target",target.c_str())&&r->Unsigned64Attribute("device")==(uint64_t)device,"Destination changed; review the move again");
        size_t count=0;for(auto *p=r->FirstChildElement("Plugin");p;p=p->NextSiblingElement("Plugin"),++count)
            require(count<moving.size()&&p->Attribute("id",moving[count].id.c_str())&&p->Attribute("uid",moving[count].uid.c_str())&&p->Attribute("file",moving[count].binary.c_str()),"Plugin registrations changed; review the move again");
        require(count==moving.size(),"Plugin selection changed; review the move again");
        std::string templ=std::string(argv[2])+".move-recovery-XXXXXX";std::vector<char> name(templ.begin(),templ.end());name.push_back(0);
        require(mkdtemp(name.data()),"Cannot create recovery journal");transaction=name.data();
        require(plan.SaveFile((fs::path(transaction)/"plan.xml").c_str())==XML_SUCCESS,"Cannot save recovery plan");
        prepare_volume(requested,target);
        fs::create_directories(target);
        std::vector<fs::path> copied;report.index=0;
        for(auto &p:moving) {
            dev_t current;destination(requested,&current);require(volume_target(requested)==target && current==device,"Destination drive changed");
            auto final=target/p.folder.filename();report.step("Checking existing copy",p.name);
            if(fs::is_directory(final)&&!fs::is_symlink(final)&&reusable_copy(p,target,argv[2],true)) {
                report.index++;report.step("Verifying existing copy",p.name);report.done+=check_tree(p,final,false);copied.push_back(final);continue;
            }
            auto staged=target/(".openplugin-"+fs::path(transaction).filename().string()+"-"+p.id);
            require(!fs::exists(staged),"Staging folder already exists");
            report.index++;report.step("Copying",p.name);
            copy_reported(p.folder,staged);
            report.step("Verifying",p.name);
            verify_tree(p.folder,staged);sync_tree(staged);
            if(internal_root(target)&&compatibility_link(final,p.folder)){exchange_paths(final,staged);require(fs::is_symlink(staged),"Internal link changed");fs::remove(staged);}
            else {require(!fs::exists(final)&&!fs::is_symlink(final),"Destination conflict detected");fs::rename(staged,final);}
            copied.push_back(final);
        }
#ifdef OPENPLUGIN_TEST
        if(getenv("OPENPLUGIN_FAIL_AFTER_COPY"))throw std::runtime_error("Injected failure after copying");
#endif
        // Recheck mounts and every registered binary immediately before committing.
        dev_t current;destination(requested,&current);require(volume_target(requested)==target && current==device,"Destination drive changed before registration");
        for(size_t i=0;i<moving.size();i++){report.index=i+1;report.step("Verifying",moving[i].name);verify_pair(moving[i].folder,copied[i]);}
        for(size_t i=0;i<moving.size();i++) {
            for(const auto &e:fs::recursive_directory_iterator(copied[i]))
                if(!e.is_symlink() && e.is_regular_file() && e.path().extension()==".xpl")
                    preset_paths(e.path(),moving[i].folder.string(),copied[i].string(),true);
            sync_tree(copied[i]);
        }
        report.step("Updating plugin locations");
        auto *props=doc.RootElement();
        for(auto *v=props->FirstChildElement("VALUE");v;v=v->NextSiblingElement("VALUE"))if(v->Attribute("name","pluginList-arm"))
            for(auto *p=v->FirstChildElement("KNOWNPLUGINS")->FirstChildElement("PLUGIN");p;p=p->NextSiblingElement("PLUGIN"))
                for(auto &m:moving)if(p->Attribute("uid",m.uid.c_str())&&p->Attribute("file",m.binary.c_str()))
                    p->SetAttribute("file",(target/m.folder.filename()/fs::path(m.binary).filename()).c_str());
        add_root(doc,target);select_install_target(doc,target);
        save_atomic(doc,argv[2],fs::path(transaction)/"MPC.settings.before");
        report.event("COMMIT plugin registrations updated; original files retained");
        std::ofstream marker(fs::path(transaction)/"COMMITTED");marker<<"Original folders retained. Verify audio, skins and projects before any cleanup.\n";marker.close();
        reclaim_internal(moving,target,transaction);
        report.finish(internal_root(target)?"Plugins moved to Internal; verified drive copies kept for reuse.":"Plugins moved; verified Internal copies removed to free space.");
        printf("Moved %zu VSTs. Internal cleanup verified. Recovery: %s\n",moving.size(),transaction.c_str());close(lock);return 0;
    }catch(const std::exception &e){report.fail(e.what());if(lock>=0)close(lock);fprintf(stderr,"Locations: %s. Verified copies preserved.%s%s\n",e.what(),transaction.empty()?"":" Recovery: ",transaction.c_str());return 1;}
}
