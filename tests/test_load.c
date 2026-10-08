/* Loading the built ELF checks its dependencies/exports, without starting MPC or a worker. */
#include <dlfcn.h>
#include <stdio.h>
int main(int argc,char **argv) {
    if (argc!=2) return 2;
    void *handle=dlopen(argv[1],RTLD_NOW);
    if (!handle) {fprintf(stderr,"%s\n",dlerror());return 1;}
    if (!dlsym(handle,"VSTPluginMain")) return 1;
    dlclose(handle);
    puts("ARM shared plugin load/export: PASS");return 0;
}
