/** Lightweight, flushed startup diagnostics for the 3DS test build. */
#ifndef N3DS_BOOTLOG_H
#define N3DS_BOOTLOG_H
#ifdef N3DS
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <unistd.h>

static inline void N3DSBootLog(bool reset, const char *format, ...)
{
	FILE *f = fopen("sdmc:/3ds/openttd-revival-r1/boot.log", reset ? "w" : "a");
	if (f == NULL) f = fopen("sdmc:/openttd-revival-r1-boot.log", reset ? "w" : "a");
	if (f == NULL) return;
	va_list args;
	va_start(args, format);
	vfprintf(f, format, args);
	va_end(args);
	fputc('\n', f);
	fclose(f);
}

static inline void N3DSPrepareStartup(int &argc, char **&argv)
{
	N3DSBootLog(true, "OpenTTD revival r1b startup: main entered; argc=%d", argc);
	static char fallback_path[] = "sdmc:/3ds/openttd-revival-r1/openttd-revival-r1.3dsx";
	static char *fallback_argv[] = {fallback_path, NULL};
	if (argc < 1 || argv == NULL || argv[0] == NULL || argv[0][0] == '\0') {
		N3DSBootLog(false, "Launcher supplied no executable path; using test-folder fallback");
		argc = 1;
		argv = fallback_argv;
	}
	N3DSBootLog(false, "Executable: %s", argv[0]);
	char path[1024];
	if (getcwd(path, sizeof(path)) != NULL) N3DSBootLog(false, "Initial directory: %s", path);
	snprintf(path, sizeof(path), "%s", argv[0]);
	char *slash = strrchr(path, '/');
	if (slash != NULL) {
		*slash = '\0';
		N3DSBootLog(false, "Executable-directory chdir(%s): %d", path, chdir(path));
	}
	if (access("lang/english.lng", R_OK) != 0 || access("data/opengfx.obg", R_OK) != 0) {
		N3DSBootLog(false, "Trying known test-folder directory: %d", chdir("sdmc:/3ds/openttd-revival-r1"));
	}
	if (getcwd(path, sizeof(path)) != NULL) N3DSBootLog(false, "Asset directory: %s", path);
	N3DSBootLog(false, "Asset checks: english.lng=%d; opengfx.obg=%d", access("lang/english.lng", R_OK), access("data/opengfx.obg", R_OK));
}
#else
static inline void N3DSBootLog(bool, const char *, ...) {}
#endif
#endif
