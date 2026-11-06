/* Opt-in worker diagnostics. Never called from the audio callback. */
static double startup_clock(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

static void startup_trace(mgr_t *m, double start, const char *stage) {
    if (access(WORK "/startup-trace.enabled", F_OK)) return;
    struct stat st;
    if (!stat(WORK "/startup-trace.log", &st) && st.st_size > 32768)
        rename(WORK "/startup-trace.log", WORK "/startup-trace.previous.log");
    FILE *f = fopen(WORK "/startup-trace.log", "a");
    if (!f) return;
    double now = startup_clock();
    fprintf(f, "uptime=%.3f pid=%ld instance=%p elapsed=%.3f %s\n",
            now, (long)getpid(), (void *)m, now - start, stage);
    fclose(f);
}
