#!/usr/bin/env python3
"""Extract TextAttributesKey external names from the downloaded reference files.

An "attribute key" is a direct child <option name="X"> of an <attributes> block.
Nested <option name="FOREGROUND">/BACKGROUND/EFFECT_* live inside <value> blocks
and are FONT_ATTRIBUTE keys, not TextAttributesKey external names, so they are
tracked separately (deep variant) rather than mixed into the primary output.
"""
import glob
import hashlib
import json
import os
import re
import urllib.request

REF = os.path.dirname(os.path.abspath(__file__))

# Permissive: real external names contain dots and lowercase segments
# (APACHE_CONFIG.ARG_LEXEM, CSS.ATTRIBUTE_NAME, com.plan9.KEYWORD, org.toml.KEY).
NAME_RE = re.compile(r'<option\s+name="([^"]+)"')
STRICT_RE = re.compile(r'^[A-Z0-9_]+$')
TAG_RE = re.compile(r'<option\b[^>]*?(/?)>|</option>')
# everforest includes are ERB-templated: value="<%= ${bg1} %>" embeds a bare ">"
# inside an attribute value, which breaks naive tag scanning. Blank the templates
# out first (their contents never carry an attribute key name).
ERB_RE = re.compile(r'<%.*?%>', re.S)


def blocks(text):
    text = ERB_RE.sub('ERB', text)
    return re.findall(r'<attributes>(.*?)</attributes>', text, re.S)


def extract(region):
    """Return (direct_children, all_nested_option_names) within one attributes region."""
    direct, nested = [], []
    depth = 0
    for m in TAG_RE.finditer(region):
        if m.group(0) == '</option>':
            depth = max(0, depth - 1)
            continue
        nm = NAME_RE.search(m.group(0))
        if nm:
            name = nm.group(1)
            nested.append(name)
            if depth == 0:
                direct.append(name)
        if m.group(1) != '/':  # not self-closing
            depth += 1
    return direct, nested


def collect(path):
    text = open(path, encoding="utf-8").read()
    d, n = [], []
    for b in blocks(text):
        dd, nn = extract(b)
        d += dd
        n += nn
    return d, n, len(blocks(text))


# ---------- integrity check against the GitHub API blob SHAs ----------
EXPECTED = {
    "everforest/src/pallete_light_soft.env": "61f497a46b41750c7a31e1caf21758f5f68afc85",
    "everforest/src/theme.xml": "63d79539b78cd1dea4181bda804d92eaf95ea383",
    "github/GitHub 3.icls": "47b98894cf1cffc4ac7980562159db58716a5611",
}


def blob_sha1(path):
    d = open(path, "rb").read()
    return hashlib.sha1(b"blob %d\0" % len(d) + d).hexdigest()


print("=== integrity (git blob sha1) ===")
for rel, exp in EXPECTED.items():
    got = blob_sha1(os.path.join(REF, rel))
    print("%-45s %s %s" % (rel, "MATCH " if got == exp else "MISMATCH", got))

# ---------- extraction ----------
icls_path = os.path.join(REF, "github", "GitHub 3.icls")
icls_direct, icls_nested, icls_blocks = collect(icls_path)

ef_files = sorted(glob.glob(os.path.join(REF, "everforest", "src", "includes", "*.xml")))
ef_files.append(os.path.join(REF, "everforest", "src", "theme.xml"))
ef_direct, ef_nested, ef_info = [], [], []
for f in ef_files:
    d, n, nb = collect(f)
    ef_direct += d
    ef_nested += n
    ef_info.append((os.path.relpath(f, REF), nb, len(set(d)), len(d)))

union = sorted(set(icls_direct) | set(ef_direct))
icls_names = sorted(set(icls_direct))


def dump(path, names):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(names) + ("\n" if names else ""))
    return len(names)


n1 = dump(os.path.join(REF, "icls_attribute_names.txt"), icls_names)
n2 = dump(os.path.join(REF, "all_reference_attribute_names.txt"), union)

# supplementary: nested-inclusive (adds FONT_ATTRIBUTE keys) for transparency
dump(os.path.join(REF, "icls_attribute_names_deep.txt"), sorted(set(icls_nested)))
dump(
    os.path.join(REF, "all_reference_attribute_names_deep.txt"),
    sorted(set(icls_nested) | set(ef_nested)),
)

print("\n=== extraction summary ===")
print("icls <attributes> blocks: %d, direct attribute keys: %d distinct / %d total, all nested option names: %d distinct"
      % (icls_blocks, len(icls_names), len(icls_direct), len(set(icls_nested))))
print("icls strict [A-Z0-9_]+ full-match keys: %d (permissive adds %d dotted/lowercase keys)"
      % (sum(1 for x in icls_names if STRICT_RE.match(x)),
         sum(1 for x in icls_names if not STRICT_RE.match(x))))
print("\neverforest per-file (path, attributes blocks, distinct direct keys, total direct):")
for rel, nb, nd, nd2 in ef_info:
    print("  %-40s blocks=%d distinct=%d total=%d" % (rel, nb, nd, nd2))
print("\neverforest direct keys total (with dups) %d, distinct %d"
      % (len(ef_direct), len(set(ef_direct))))
print("icls_attribute_names.txt                 lines=%d" % n1)
print("all_reference_attribute_names.txt        lines=%d" % n2)
print("overlap (in both icls and everforest):   %d" % len(set(icls_names) & set(ef_direct)))
print("everforest-only keys:                    %d" % len(set(ef_direct) - set(icls_names)))

# ---------- icls structure facts ----------
icls_text = open(icls_path, encoding="utf-8").read()
cm = re.search(r'<colors>(.*?)</colors>', icls_text, re.S)
colors_opts = re.findall(r'<option\s+name="([^"]*)"', cm.group(1)) if cm else []
print("\n=== GitHub 3.icls structure ===")
print("<attributes> blocks: %d" % len(re.findall(r'<attributes>', icls_text)))
print("<colors> blocks: %d" % len(re.findall(r'<colors>', icls_text)))
print("<colors> <option> entries: %d -> %s" % (len(colors_opts), colors_opts))
print("schema tag: %s" % re.search(r'<scheme[^>]*>', icls_text).group(0))

# ---------- theme.xml skeleton ----------
print("\n=== everforest/src/theme.xml first 15 lines ===")
for i, line in enumerate(open(os.path.join(REF, "everforest", "src", "theme.xml"), encoding="utf-8").read().splitlines()[:15], 1):
    print("%3d| %s" % (i, line))
