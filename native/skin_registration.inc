/* The helper ships next to the manager, including in standalone ZIP updates. */
static int skin_helper_path(char *out, size_t n) {
    Dl_info di;
    if (!dladdr((void *)skin_helper_path, &di) || !di.dli_fname || di.dli_fname[0] != '/') return 0;
    if (snprintf(out, n, "%s", di.dli_fname) >= (int)n) return 0;
    char *slash = strrchr(out, '/');
    if (!slash || (size_t)(slash - out) + sizeof("/skin-locations") > n) return 0;
    strcpy(slash, "/skin-locations");
    return safe(out) && access(out, X_OK) == 0;
}

/* Always finalize successful installs, even if a later package fails. The helper
 * deduplicates roots and re-reads settings while MPC is stopped, then we restart once. */
static void skin_write_guard(FILE *f, const char *helper, const char *settings) {
    fprintf(f,
        "export MPC_SETTINGS='%s'\nSKIN_HELPER='%s'\n"
        "SKIN_ROOTS='" WORK "/installed-skin-roots'\n: > \"$SKIN_ROOTS\"\n"
        "finish() {\n"
        "  result=$?\n  trap - EXIT\n"
        "  if [ -s \"$SKIN_ROOTS\" ]; then\n"
        "    \"$SKIN_HELPER\" \"$MPC_SETTINGS\" \"$SKIN_ROOTS\" || result=$?\n"
        "  fi\n"
        "  systemctl start acvs || result=$?\n"
        "  return \"$result\"\n}\ntrap finish EXIT\n",
        settings, helper);
}
