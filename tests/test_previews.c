/* Bundled artwork selection and title bounds; no runtime image fetch. */
#include "../native/manager.c"
#include <assert.h>
int main(void) {
 assert(preview_frame("unlisted-plugin-id")==1);
 for(unsigned i=0;i<sizeof preview_ids/sizeof *preview_ids;i++)assert(preview_frame(preview_ids[i])==(int)i+2);
 char out[192];catalog_title("JV-880",out,sizeof out);assert(!strcmp(out,"JV-880"));
 catalog_title("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",out,sizeof out);
 assert(strstr(out,"..."));assert(strlen(out)<48);
 catalog_title("音音音音音音音音音音音音音音音音音音音音音音音音音音音音",out,sizeof out);
 assert(strstr(out,"..."));assert((strlen(out)-3)%3==0);
 char small[5];catalog_title("Long title",small,sizeof small);assert(small[4]==0);
 description_line("Short description.",0,out,sizeof out);assert(!strcmp(out,"Short description."));
 char long_text[400];memset(long_text,'W',sizeof long_text-1);long_text[399]=0;
 description_line(long_text,1,out,sizeof out);assert(strstr(out,"..."));assert(strlen(out)<40);
 description_line("音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音音",1,out,sizeof out);
 assert(strstr(out,"..."));assert((strlen(out)-3)%3==0);
 puts("Bundled thumbnail fallback and bounded UTF-8 titles passed");return 0;
}
