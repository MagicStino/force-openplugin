/* Journal-backed recovery, including copy-back after verified Internal cleanup. */
#include <sys/syscall.h>
struct ReturnItem {std::string id,uid;fs::path original,current;bool copy_back=false;};
struct ReturnPlan {fs::path journal;std::vector<ReturnItem> items;};
static XMLElement *registration(XMLDocument &doc,const std::string &uid) {
    XMLElement *found=nullptr;
    for(auto *v=doc.RootElement()->FirstChildElement("VALUE");v;v=v->NextSiblingElement("VALUE"))if(v->Attribute("name","pluginList-arm"))
        for(auto *list=v->FirstChildElement("KNOWNPLUGINS");list;list=list->NextSiblingElement("KNOWNPLUGINS"))
            for(auto *p=list->FirstChildElement("PLUGIN");p;p=p->NextSiblingElement("PLUGIN"))if(p->Attribute("uid",uid.c_str())){require(!found,"Duplicate plugin registration; return stopped");found=p;}
    return found;
}
static void regular_record(const fs::path &p) {require(fs::is_regular_file(p)&&!fs::is_symlink(p),"Recovery record is missing or unsafe");}
static bool internal_root(const fs::path &root) {
#ifdef OPENPLUGIN_TEST
    return root.filename()=="Synths"&&root.parent_path().filename()=="internal";
#else
    std::string path=canonical(root.c_str());return path==canonical("/sdcard/Synths")||path==canonical("/media/az01-internal-sd/Synths");
#endif
}
static bool compatibility_link(const fs::path &from,const fs::path &to) {return fs::is_symlink(from)&&fs::read_symlink(from)==to;}
static void exchange_paths(const fs::path &a,const fs::path &b) {
    require(syscall(SYS_renameat2,AT_FDCWD,a.c_str(),AT_FDCWD,b.c_str(),2 /* RENAME_EXCHANGE */)==0,"Cannot safely exchange plugin folder; verified copies kept");
    int fd=open(a.parent_path().c_str(),O_RDONLY|O_DIRECTORY);require(fd>=0,"Cannot sync plugin directory");int rc=fsync(fd);close(fd);require(rc==0,"Cannot sync plugin directory");
}
static std::string normalized_preset(const fs::path &p,const std::string &from,const std::string &to) {
    XMLDocument doc;require(doc.LoadFile(p.c_str())==XML_SUCCESS,"Preset cannot be verified for return");
    auto replace=[&](const char *value){std::string s=value?value:"";size_t at=0;while(!from.empty()&&(at=s.find(from,at))!=std::string::npos){s.replace(at,from.size(),to);at+=to.size();}return s;};
    std::function<void(XMLNode*)> visit=[&](XMLNode *n){if(auto *e=n->ToElement())for(auto *a=e->FirstAttribute();a;a=a->Next())e->SetAttribute(a->Name(),replace(a->Value()).c_str());if(auto *t=n->ToText())t->SetValue(replace(t->Value()).c_str());for(auto *c=n->FirstChild();c;c=c->NextSibling())visit(c);};
    visit(&doc);XMLPrinter out;doc.Print(&out);return out.CStr();
}
static void verify_pair(const fs::path &source,const fs::path &dest,const fs::path &logical_source={}) {
    auto original=logical_source.empty()?source:logical_source;
    require(fs::is_directory(source)&&!fs::is_symlink(source)&&fs::is_directory(dest)&&!fs::is_symlink(dest),"A plugin copy is unavailable");
    std::set<fs::path> paths;
    for(auto &e:fs::recursive_directory_iterator(source)) {
        auto rel=e.path().lexically_relative(source);report.file=rel.string();report.files++;report.snapshot();paths.insert(rel);auto other=dest/rel;
        if(e.is_symlink())require(fs::is_symlink(other)&&fs::read_symlink(e.path())==fs::read_symlink(other),"Plugin links differ; both copies kept");
        else if(e.is_directory())require(fs::is_directory(other)&&!fs::is_symlink(other),"Plugin folders differ; both copies kept");
        else {require(e.is_regular_file()&&fs::is_regular_file(other)&&!fs::is_symlink(other),"Plugin files differ; both copies kept");
            bool same=e.path().extension()==".xpl"?normalized_preset(e.path(),"","")==normalized_preset(other,dest.string(),original.string()):same_file(e.path(),other);
            require(same,"Plugin content differs; both copies kept");}
    }
    for(auto &e:fs::recursive_directory_iterator(dest))require(paths.count(e.path().lexically_relative(dest)),"Additional plugin content exists; both copies kept");
}
static ReturnPlan return_plan(XMLDocument &current,const char *settings,const char *state,const fs::path &journal) {
    fs::path parent=fs::path(settings).parent_path();std::string prefix=fs::path(settings).filename().string()+".move-recovery-";
    require(journal.parent_path()==parent && journal.filename().string().find(prefix)==0 && fs::is_directory(journal)&&!fs::is_symlink(journal),"Invalid recovery journal");
    regular_record(journal/"COMMITTED");regular_record(journal/"plan.xml");regular_record(journal/"MPC.settings.before");
    XMLDocument plan,before,restored;load_settings(before,(journal/"MPC.settings.before").c_str());
    require(plan.LoadFile((journal/"plan.xml").c_str())==XML_SUCCESS,"Cannot read recovery plan");
    auto *root=plan.RootElement();require(root && root->Attribute("target"),"Invalid recovery target");fs::path target=root->Attribute("target");
    current.DeepCopy(&restored);ReturnPlan result{journal,{}};std::set<std::string> seen;
    for(auto *item=root->FirstChildElement("Plugin");item;item=item->NextSiblingElement("Plugin")) {
        require(item->Attribute("id")&&item->Attribute("uid")&&item->Attribute("file"),"Incomplete recovery record");
        ReturnItem r{item->Attribute("id"),item->Attribute("uid"),item->Attribute("file"),{},false};
        require(seen.insert(r.uid).second,"Duplicate recovery plugin");
        require(r.original.is_absolute() && internal_root(r.original.parent_path().parent_path()),"Original plugin location is not Internal content");
        destination(r.original.parent_path().parent_path());
        auto *old=registration(before,r.uid);require(old&&old->Attribute("file",r.original.c_str()),"Original registration does not match recovery record");
        r.current=target/r.original.parent_path().filename()/r.original.filename();
        auto *now=registration(current,r.uid);require(now && now->Attribute("format","VST") && (now->Attribute("file",r.current.c_str())||now->Attribute("file",r.original.c_str())),"Plugin locations changed since this move; return stopped");
        auto source=r.original.parent_path();
        r.copy_back=compatibility_link(source,r.current.parent_path()) || (!fs::exists(source)&&!fs::is_symlink(source));
        if(!r.copy_back)require(fs::is_directory(source)&&!fs::is_symlink(source),"Internal path was replaced; return stopped");
        registration(restored,r.uid)->SetAttribute("file",r.original.c_str());result.items.push_back(r);
    }
    require(!result.items.empty(),"Recovery record has no plugins");
    size_t skipped=0;auto originals=owned(restored,state,skipped);auto moved=owned(current,state,skipped);
    for(auto &r:result.items) {
        if(!r.copy_back)require(std::any_of(originals.begin(),originals.end(),[&](const Owned &o){return o.id==r.id&&o.uid==r.uid&&o.binary==r.original;}),"Internal copy is updated or no longer manager-owned");
        require(std::any_of(moved.begin(),moved.end(),[&](const Owned &o){return o.id==r.id&&o.uid==r.uid;}),"Current copy is missing, updated or no longer manager-owned");
    }
    return result;
}
static fs::path latest_return(XMLDocument &doc,const char *settings,const char *state) {
    fs::path latest;fs::file_time_type newest=fs::file_time_type::min();
    std::string prefix=fs::path(settings).filename().string()+".move-recovery-";
    for(auto &e:fs::directory_iterator(fs::path(settings).parent_path())) {
        if(e.is_symlink()||!e.is_directory()||e.path().filename().string().find(prefix)!=0||!fs::exists(e.path()/"COMMITTED")||fs::exists(e.path()/"RETURNED"))continue;
        auto time=fs::last_write_time(e.path()/"COMMITTED");if(time>newest){newest=time;latest=e.path();}
    }
    if(latest.empty())return {};
    auto plan=return_plan(doc,settings,state,latest);
    bool changed=false;for(auto &r:plan.items)if(registration(doc,r.uid)->Attribute("file",r.current.c_str()))changed=true;
    return changed?latest:fs::path{};
}
static void verify_return(const ReturnPlan &plan) {
    report.count=plan.items.size();report.index=0;unsigned long long required=0;fs::path internal;
    for(auto &r:plan.items) {
        auto source=r.original.parent_path(),dest=r.current.parent_path();report.index++;report.step("Verifying",source.filename());
        if(r.copy_back){Owned p{r.id,r.uid,source.filename(),r.current.string(),dest};required+=check_tree(p,source);internal=source.parent_path();}
        else verify_pair(source,dest);
    }
    if(required){auto free=destination(internal);require(free>required+(64ull<<20),"Not enough Internal space to copy plugins back safely");}
    report.total=required;
}
static void reclaim_internal(const std::vector<Owned> &plugins,const fs::path &target,const fs::path &journal) {
    if(internal_root(target))return;
    // All copies are verified again before deleting any Internal data.
    for(auto &p:plugins)verify_pair(p.folder,target/p.folder.filename());
    report.count=plugins.size();report.index=0;
    for(auto &p:plugins){report.index++;
        if(!internal_root(p.folder.parent_path())){
#ifdef OPENPLUGIN_TEST
            auto alias=p.folder.parent_path().parent_path().parent_path()/"internal"/"Synths"/p.folder.filename();
#else
            auto alias=fs::path("/sdcard/Synths")/p.folder.filename();
#endif
            if(compatibility_link(alias,p.folder)){
                auto replacement=alias.parent_path()/(".openplugin-link-"+std::to_string(getpid())+"-"+p.id);
                require(!fs::exists(replacement)&&!fs::is_symlink(replacement),"Previous link update needs recovery");
                fs::create_symlink(target/p.folder.filename(),replacement);
                try{exchange_paths(alias,replacement);}catch(...){fs::remove(replacement);throw;}
                require(compatibility_link(replacement,p.folder),"Previous link changed; preserved for recovery");fs::remove(replacement);
            }
            continue;
        }
        report.step("Freeing Internal space",p.name);
        fs::path dest=target/p.folder.filename(),retired=p.folder.parent_path()/(".openplugin-retired-"+journal.filename().string()+"-"+p.id);
        require(!fs::exists(retired)&&!fs::is_symlink(retired),"Previous cleanup needs recovery; no files deleted");
        fs::create_symlink(dest,retired);
        try{exchange_paths(p.folder,retired);}catch(...){if(fs::is_symlink(retired))fs::remove(retired);throw;}
        require(compatibility_link(p.folder,dest),"Compatibility link verification failed; old copy retained");
        verify_pair(retired,dest,p.folder);
        fs::remove_all(retired);report.originals_retained=false;
    }
    LocationReport::replace(journal/"RECLAIMED","Internal copies verified and removed; compatibility links retained.\n");
}
static bool reusable_copy(const Owned &p,const fs::path &target,const char *settings,bool verify) {
    auto dest=target/p.folder.filename();if(!fs::is_directory(dest)||fs::is_symlink(dest))return false;
    std::string prefix=fs::path(settings).filename().string()+".move-recovery-";
    for(auto &e:fs::directory_iterator(fs::path(settings).parent_path())) {
        if(e.is_symlink()||!e.is_directory()||e.path().filename().string().find(prefix)!=0||!fs::is_regular_file(e.path()/"plan.xml")||fs::is_symlink(e.path()/"plan.xml"))continue;
        XMLDocument plan;if(plan.LoadFile((e.path()/"plan.xml").c_str())!=XML_SUCCESS)continue;auto *root=plan.RootElement();if(!root||!root->Attribute("target",target.c_str()))continue;
        for(auto *item=root->FirstChildElement("Plugin");item;item=item->NextSiblingElement("Plugin"))if(item->Attribute("id",p.id.c_str())&&item->Attribute("uid",p.uid.c_str())&&item->Attribute("file",p.binary.c_str())){if(verify)verify_pair(p.folder,dest);return true;}
    }return false;
}
static void return_operation(XMLDocument &doc,const char *settings,const char *state,const char *review,bool apply) {
    fs::path journal;
    if(apply){regular_record(review);XMLDocument selected;require(selected.LoadFile(review)==XML_SUCCESS && selected.RootElement() && selected.RootElement()->Attribute("journal"),"Return confirmation is missing");journal=selected.RootElement()->Attribute("journal");}
    else journal=latest_return(doc,settings,state);
    require(!journal.empty(),"No completed move can safely return to Internal");
    auto plan=return_plan(doc,settings,state,journal);verify_return(plan);
    if(!apply){XMLDocument selected;auto *root=selected.NewElement("Return");selected.InsertEndChild(root);root->SetAttribute("journal",journal.c_str());require(selected.SaveFile(review)==XML_SUCCESS,"Cannot save return confirmation");
        report.finish("Return checks passed; waiting for confirmation");printf("Return %zu plugins to Internal. Copy back and verify where needed. Save your project before restarting.\n",plan.items.size());return;}
    report.index=0;
    for(auto &r:plan.items){report.index++;if(!r.copy_back)continue;
        auto source=r.current.parent_path(),dest=r.original.parent_path();
        auto stage=dest.parent_path()/(".openplugin-return-"+std::to_string(getpid())+"-"+r.id);
        report.step("Copying back",dest.filename());copy_reported(source,stage);verify_tree(source,stage);
        for(auto &e:fs::recursive_directory_iterator(stage))if(e.is_regular_file()&&!e.is_symlink()&&e.path().extension()==".xpl")preset_paths(e.path(),source.string(),dest.string(),true);
        sync_tree(stage);
        if(compatibility_link(dest,source)){exchange_paths(dest,stage);require(fs::is_symlink(stage),"Return staging changed");fs::remove(stage);}
        else {require(!fs::exists(dest)&&!fs::is_symlink(dest),"Internal path changed during return");fs::rename(stage,dest);}
    }
    XMLDocument fresh;load_settings(fresh,settings);plan=return_plan(fresh,settings,state,journal);verify_return(plan);
    bool changed=false;
    for(auto &r:plan.items){auto *p=registration(fresh,r.uid);if(!p->Attribute("file",r.original.c_str())){p->SetAttribute("file",r.original.c_str());changed=true;}if(!scanned(fresh,r.original.parent_path().parent_path())){add_root(fresh,r.original.parent_path().parent_path());changed=true;}}
    if(changed){select_install_target(fresh,plan.items.front().original.parent_path().parent_path());report.step("Updating plugin locations");save_atomic(fresh,settings,journal/("MPC.settings.before-return-"+std::to_string(time(nullptr))+"-"+std::to_string(getpid())));}
    LocationReport::replace(journal/"RETURNED","Internal registrations restored; verified drive copies retained for reuse.\n");
    report.finish("Plugins returned to Internal. Other preferences preserved.");printf("Returned %zu plugins to Internal. Verified drive copies retained for reuse.\n",plan.items.size());
}
