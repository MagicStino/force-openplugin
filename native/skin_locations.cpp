// Register content roots after a manager installation batch, before MPC restarts.
// No dependency on Python or device XML utilities. TinyXML2 is linked statically.
#include "third_party/tinyxml2/tinyxml2.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <stdexcept>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <fcntl.h>
using namespace tinyxml2;

static void require(bool ok, const char *message) {
    if (!ok) throw std::runtime_error(message);
}
static std::string canonical(const char *path) {
    char *resolved = realpath(path, nullptr);
    if (resolved) { std::string result(resolved); free(resolved); return result; }
    std::string result(path);
    while (result.size() > 1 && result.back() == '/') result.pop_back();
    return result;
}
static void write_all(int fd, const char *data, size_t size) {
    while (size) {
        ssize_t n = write(fd, data, size);
        if (n < 0 && errno == EINTR) continue;
        require(n > 0, "Could not write settings copy");
        data += n; size -= n;
    }
    require(fsync(fd) == 0, "Could not sync settings copy");
}
int main(int argc, char **argv) {
    int lock = -1, fd = -1, parent = -1;
    std::string temporary;
    try {
        require(argc == 3, "Usage: skin-locations MPC.settings successful-roots.txt");
        // This helper never stops/restarts MPC itself. The detached manager job owns that lifecycle.
        int running = system("pidof MPC >/dev/null 2>&1");
        require(running == 256, "MPC is running or its state could not be checked");
        std::ifstream roots_file(argv[2]);
        require(roots_file.good(), "Cannot read installed content roots");
        std::vector<std::string> roots;
        std::string root;
        while (std::getline(roots_file, root)) {
            if (root.empty()) continue;
            struct stat st;
            require(root[0] == '/' && root.find('\r') == std::string::npos,
                    "Invalid content root");
            require(stat(root.c_str(), &st) == 0 && S_ISDIR(st.st_mode), "Installed content root is unavailable");
            bool duplicate = false;
            for (const auto &previous : roots) if (canonical(previous.c_str()) == canonical(root.c_str())) duplicate = true;
            if (!duplicate) roots.push_back(root);
        }
        require(!roots_file.bad(), "Failed reading installed content roots");
        if (roots.empty()) return 0; // Add-ins/removals alone do not touch skin settings.
        std::string settings(argv[1]);
        std::string lockpath = settings + ".openplugin-lock";
        lock = open(lockpath.c_str(), O_CREAT | O_RDWR | O_NOFOLLOW, 0600);
        require(lock >= 0 && flock(lock, LOCK_EX | LOCK_NB) == 0, "Settings are busy");
        struct stat original;
        require(lstat(settings.c_str(), &original) == 0 && S_ISREG(original.st_mode), "Settings must be a regular file");
        XMLDocument doc;
        require(doc.LoadFile(settings.c_str()) == XML_SUCCESS, "Settings XML is invalid; unchanged");
        XMLElement *properties = doc.RootElement();
        require(properties && !strcmp(properties->Name(), "PROPERTIES"), "Unexpected settings root; unchanged");
        XMLElement *value = nullptr;
        for (auto *v = properties->FirstChildElement("VALUE"); v; v = v->NextSiblingElement("VALUE")) {
            if (v->Attribute("name", "SynthContentLocations")) {
                require(!value, "Duplicate content location settings; unchanged");
                value = v;
            }
        }
        if (!value) {
            value = doc.NewElement("VALUE"); value->SetAttribute("name", "SynthContentLocations");
            properties->InsertEndChild(value);
        }
        auto *locations = value->FirstChildElement("SynthContentLocations");
        require(!locations || !locations->NextSiblingElement("SynthContentLocations"), "Duplicate content location lists; unchanged");
        if (!locations) {
            require(!value->FirstChildElement() && !value->GetText() && !value->Attribute("val"),
                    "Unsupported content location setting; unchanged");
            locations = doc.NewElement("SynthContentLocations"); value->InsertEndChild(locations);
        }
        size_t added = 0;
        for (const auto &wanted : roots) {
            bool found = false;
            for (auto *v = locations->FirstChildElement("Location"); v; v = v->NextSiblingElement("Location")) {
                if (v->GetText() && canonical(v->GetText()) == canonical(wanted.c_str())) found = true;
            }
            if (!found) {
                auto *v = doc.NewElement("Location"); v->SetText(wanted.c_str()); locations->InsertEndChild(v); ++added;
            }
        }
        if (!added) { puts("Skin search locations already registered; settings unchanged."); close(lock); return 0; }
        XMLPrinter printer; doc.Print(&printer);
        XMLDocument validation;
        require(validation.Parse(printer.CStr()) == XML_SUCCESS, "Generated settings XML is invalid");
        std::ifstream input(settings, std::ios::binary);
        require(input.good(), "Cannot back up settings");
        std::string bytes((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
        require(!input.bad(), "Cannot read settings backup");
        std::string backup = settings + ".bak-skins-XXXXXX";
        std::vector<char> backup_name(backup.begin(), backup.end()); backup_name.push_back(0);
        fd = mkstemp(backup_name.data()); require(fd >= 0, "Cannot create settings backup");
        require(fchown(fd, original.st_uid, original.st_gid) == 0 && fchmod(fd, original.st_mode & 0777) == 0, "Cannot preserve backup metadata");
        write_all(fd, bytes.data(), bytes.size()); close(fd); fd = -1;
        temporary = settings + ".new-skins-XXXXXX";
        std::vector<char> temp_name(temporary.begin(), temporary.end()); temp_name.push_back(0);
        fd = mkstemp(temp_name.data()); require(fd >= 0, "Cannot stage updated settings");
        temporary = temp_name.data();
        require(fchown(fd, original.st_uid, original.st_gid) == 0 && fchmod(fd, original.st_mode & 0777) == 0, "Cannot preserve settings metadata");
        write_all(fd, printer.CStr(), printer.CStrSize() - 1); close(fd); fd = -1;
        parent = open(settings.substr(0, settings.find_last_of('/')).c_str(), O_RDONLY | O_DIRECTORY);
        require(parent >= 0, "Cannot open settings directory");
        require(rename(temporary.c_str(), settings.c_str()) == 0, "Cannot replace settings");
        temporary.clear();
        require(fsync(parent) == 0, "Settings updated but directory sync failed; backup retained");
        printf("Registered %zu skin search location(s). Backup: %s\n", added, backup_name.data());
        close(parent); close(lock); return 0;
    } catch (const std::exception &error) {
        if (fd >= 0) close(fd);
        if (!temporary.empty()) unlink(temporary.c_str());
        if (parent >= 0) close(parent);
        if (lock >= 0) close(lock);
        fprintf(stderr, "Skin search registration failed: %s\n", error.what());
        return 1;
    }
}
