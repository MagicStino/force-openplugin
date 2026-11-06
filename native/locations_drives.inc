/* One discovery snapshot for all drives, including unavailable remembered ones. */
struct DriveRow {fs::path root,effective;std::string label,space,status,id;size_t count=0;bool ready=false,missing=false,main=false;};
static std::string free_space(const fs::path &root) {
    struct statvfs v{};auto at=fs::exists(root)?root:root.parent_path();
    if(statvfs(at.c_str(),&v))return "Unavailable";
    char out[64];snprintf(out,sizeof out,"%.1f GB free",double(v.f_bavail)*v.f_frsize/1e9);return out;
}
static void drive_list(XMLDocument &doc,const char *settings,const char *state) {
    size_t skipped=0;auto plugins=owned(doc,state,skipped);std::vector<DriveRow> rows;std::set<std::string> seen;
    std::vector<fs::path> roots={"/sdcard/Synths"};
    FILE *f=setmntent("/proc/mounts","r");require(f,"Cannot inspect mounted drives");
    while(auto *m=getmntent(f)){VolumeMount v{m->mnt_dir,m->mnt_fsname,m->mnt_type,hasmntopt(m,"rw")!=nullptr,hasmntopt(m,"noexec")==nullptr};if(external_volume(v))roots.push_back(fs::path(v.path)/"Synths");}endmntent(f);
    for(auto &root:roots){if(rows.size()>=24)break;DriveRow r;r.root=root;r.label=internal_root(root)?"Internal":root.parent_path().filename().string();r.space=free_space(root);
        report.step("Checking drive",r.label);
        try {
            if(!internal_root(root)){r.id=volume_id(volume_mount(root.parent_path()));if(!seen.insert(r.id).second)continue;}
            destination(root);r.effective=volume_target(root);
            if(r.effective!=root){auto m=volume_mount(root.parent_path());ensure_volume(m,r.id);}
            if(!fs::exists(r.effective))safe_directory(r.effective);
            probe_execution(r.effective);r.ready=true;
        }catch(const std::exception &){r.status="Read Only";}
        for(auto &p:plugins)if(canonical(p.folder.parent_path().c_str())==canonical(r.effective.c_str()))r.count++;
        rows.push_back(r);
    }
    std::set<std::string> needed;
    for(auto *v=doc.RootElement()->FirstChildElement("VALUE");v;v=v->NextSiblingElement("VALUE"))if(v->Attribute("name","pluginList-arm"))
        for(auto *list=v->FirstChildElement("KNOWNPLUGINS");list;list=list->NextSiblingElement("KNOWNPLUGINS"))for(auto *p=list->FirstChildElement("PLUGIN");p;p=p->NextSiblingElement("PLUGIN")){
            std::string file=p->Attribute("file")?p->Attribute("file"):"";
            if(file.find(volume_base.string()+"/")!=0)continue;
            auto rest=file.substr(volume_base.string().size()+1);auto id=rest.substr(0,rest.find('/'));if(volume_id_valid(id))needed.insert(id);
        }
    std::string warning,tip;
    for(auto &id:needed){auto it=std::find_if(rows.begin(),rows.end(),[&](const DriveRow &r){return r.id==id;});
        if(it!=rows.end()&&!it->ready){warning="Plugins on '"+it->label+"' are unavailable.";tip=it->status;}
        if(it==rows.end()){
            DriveRow r;r.id=id;r.missing=true;r.label="Disconnected drive";auto name=volume_config.parent_path()/"names"/id;
            if(fs::is_regular_file(name)&&!fs::is_symlink(name)&&fs::file_size(name)<128)r.label=read_bytes(name);
            r.space="Disconnected";r.status="Reconnect this drive to use its plugins";if(rows.size()<24)rows.push_back(r);
            warning="Reconnect '"+r.label+"' to use its plugins.";
            tip="Remove this drive often? Reconnect it, then move plugins elsewhere.";
        }
    }
    size_t maximum=0;for(auto &r:rows)maximum=std::max(maximum,r.count);
    for(auto &r:rows){r.main=r.count>0&&r.count==maximum;
        if(r.main){if(r.ready)r.status="Main plugin location";r.ready=false;}
        if(!warning.empty())r.ready=false;
        if(r.ready){report.count=plugins.size();report.index=0;size_t moving=0;unsigned long long bytes=0;
            try{for(auto &p:plugins){report.index++;report.step("Checking drive contents",p.name);if(canonical(p.folder.parent_path().c_str())==canonical(r.effective.c_str()))continue;
                auto existing=r.effective/p.folder.filename();
                require((!fs::exists(existing)&&!fs::is_symlink(existing))||(internal_root(r.root)&&compatibility_link(existing,p.folder))||reusable_copy(p,r.effective,settings,false),"Different plugin copies already exist here");
                try{if(r.root!=r.effective)for(auto &e:fs::recursive_directory_iterator(p.folder))movable_require(!e.is_symlink(),"Package needs links");bytes+=check_tree(p,existing,false);++moving;}catch(const UnsupportedMove &){}}
                require(moving>0,"No plugins need moving here");require(destination(r.root)>bytes+(64ull<<20),"Not enough free space");
            }catch(const std::exception &e){r.ready=false;r.status=e.what();}
        }
    }
    // Keep usable choices on the first page; still explain unavailable drives.
    std::stable_sort(rows.begin(),rows.end(),[](const DriveRow &a,const DriveRow &b){
        auto rank=[](const DriveRow &r){return internal_root(r.root)?0:(r.ready||r.main)?1:r.missing?3:2;};
        return rank(a)<rank(b);
    });
    picojson::array array;
    for(auto &r:rows){picojson::object item;item["root"]=picojson::value(r.root.string());item["label"]=picojson::value(r.label);item["space"]=picojson::value(r.space);item["status"]=picojson::value(r.status);item["ready"]=picojson::value(r.ready);item["missing"]=picojson::value(r.missing);item["main"]=picojson::value(r.main);array.push_back(picojson::value(item));}
    picojson::object result;result["drives"]=picojson::value(array);result["warning"]=picojson::value(warning);result["tip"]=picojson::value(tip);puts(picojson::value(result).serialize().c_str());
}
