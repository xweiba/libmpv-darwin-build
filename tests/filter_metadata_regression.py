#!/usr/bin/env python3
"""Compile the actual command.c function against a minimal metadata harness.

Usage: python3 tests/filter_metadata_regression.py /path/to/patched/mpv
The harness deliberately rejects NULL tags, reproducing the iOS crash path
without needing an Apple toolchain. It does not replace device acceptance.
"""

import pathlib
import subprocess
import sys
import tempfile


source = (pathlib.Path(sys.argv[1]) / "player/command.c").read_text()
start = source.index("static int mp_property_filter_metadata(")
end = source.index("\nstatic int ", start + 1)
function = source[start:end]
prelude = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define M_PROPERTY_KEY_ACTION 1
#define M_PROPERTY_GET_TYPE 2
#define M_PROPERTY_GET 3
#define M_PROPERTY_UNAVAILABLE -1
#define M_PROPERTY_ERROR -2
#define M_PROPERTY_NOT_IMPLEMENTED -3
#define MP_FILTER_COMMAND_GET_META 1
typedef struct { char *start; int len; } bstr;
#define BSTR_P(b) (b).len, (b).start
struct mp_tags { int unused; };
struct mp_output_chain { int unused; };
struct chain_owner { struct mp_output_chain *filter; };
typedef struct { struct chain_owner *vo_chain, *ao_chain; } MPContext;
struct m_property { char *priv; };
struct m_property_action_arg { char *key; int action; void *arg; };
struct mp_filter_command { int type; struct mp_tags **res; };
static struct mp_tags tags;
static int available = 1, fetches;
static void m_property_split_path(char *path, bstr *key, char **rem) {
    char *slash = strchr(path, '/');
    key->start = path; key->len = slash ? (int)(slash - path) : (int)strlen(path);
    *rem = slash ? slash + 1 : path + strlen(path);
}
static char *mp_tprintf(int size, const char *fmt, int len, char *key) {
    (void)size; (void)fmt; (void)len; return key;
}
static void mp_output_chain_command(struct mp_output_chain *chain,
                                    char *key, struct mp_filter_command *cmd) {
    (void)chain; (void)key; ++fetches;
    *cmd->res = available ? &tags : NULL;
}
static int tag_property(int action, void *arg, struct mp_tags *metadata) {
    (void)arg;
    // Root GET_TYPE needs no values; nested key lookup always needs tags.
    assert(action == M_PROPERTY_GET_TYPE || metadata != NULL);
    return 0;
}
static void talloc_free(void *ptr) { (void)ptr; }
'''
main = r'''
int main(void) {
    struct mp_output_chain output;
    struct chain_owner owner = { &output };
    MPContext ctx = { &owner, &owner };
    struct m_property prop = { "af" };
    struct m_property_action_arg ka = { "ppviz/lavfi.astats.3.RMS_level", M_PROPERTY_GET_TYPE, NULL };
    assert(mp_property_filter_metadata(&ctx, &prop, M_PROPERTY_KEY_ACTION, &ka) == 0);
    assert(fetches == 1);
    ka.action = M_PROPERTY_GET;
    assert(mp_property_filter_metadata(&ctx, &prop, M_PROPERTY_KEY_ACTION, &ka) == 0);
    available = 0;
    assert(mp_property_filter_metadata(&ctx, &prop, M_PROPERTY_KEY_ACTION, &ka) == M_PROPERTY_ERROR);
    ka.key = "ppviz"; ka.action = M_PROPERTY_GET_TYPE;
    int before = fetches;
    assert(mp_property_filter_metadata(&ctx, &prop, M_PROPERTY_KEY_ACTION, &ka) == 0);
    assert(fetches == before);
    ctx.ao_chain = NULL;
    assert(mp_property_filter_metadata(&ctx, &prop, M_PROPERTY_KEY_ACTION, &ka) == M_PROPERTY_UNAVAILABLE);
    puts("nested type/value, absent metadata, root type and absent chain passed");
}
'''
with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    (root / "regression.c").write_text(prelude + function + main)
    subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror",
                    str(root / "regression.c"), "-o", str(root / "regression")], check=True)
    subprocess.run([str(root / "regression")], check=True)
