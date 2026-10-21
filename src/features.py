"""Secondary features computed from snippet source text (plan §1.6).

Usage: python -I src/features.py
Reads files.zip for every DACOS-annotated snippet and every granularity-consistent DACOSX entry.
Writes data/features/features.csv.gz (one row per path) and results/logs/features.log.

Definitions (computed on text with comments, string, text-block and char literals removed):
  statements    = number of ';' outside for(...) headers
                  + number of if / for / while / do / switch / try keywords
  max_nesting   = methods: maximum '{' depth inside the method body (body itself = depth 0)
                  classes: maximum '{' depth minus 2 (class body and method body), floored at 0
  comment_ratio = lines containing any part of a // or /* */ comment / non-blank lines
  method_calls  = occurrences of `identifier (` that are not declarations, keywords or annotations
                  (a match whose closing paren is followed by `{` or `throws` is a declaration),
                  plus generic constructor calls `new T<...>(`. A match is a declaration when the
                  previous token is a non-keyword identifier, a primitive type, '>' or ']'.
"""
import os
import re
import sys
import time
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FEAT_DIR, LOG, ZIP, load_tables  # noqa: E402

KEYWORDS = set("""abstract assert boolean break byte case catch char class const continue default do double else enum
extends final finally float for goto if implements import instanceof int interface long native new package private
protected public return short static strictfp super switch synchronized this throw throws transient try void volatile
while var yield record sealed permits true false null""".split())
PRIMITIVE = set("boolean byte char double float int long short void var".split())
CONTROL = {"if", "for", "while", "do", "switch", "try"}


def strip(src):
    """Return (code with comments/literals blanked, set of line indexes containing comments)."""
    out = []
    comment_lines = set()
    i, n, line = 0, len(src), 0
    while i < n:
        c = src[i]
        if c == "\n":
            out.append(c)
            line += 1
            i += 1
        elif src.startswith("//", i):
            comment_lines.add(line)
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            seg = src[i:j]
            for k in range(seg.count("\n") + 1):
                comment_lines.add(line + k)
            out.append("".join(ch if ch == "\n" else " " for ch in seg))
            line += seg.count("\n")
            i = j
        elif src.startswith('"""', i):
            j = src.find('"""', i + 3)
            j = n if j < 0 else j + 3
            seg = src[i:j]
            out.append('""' + "".join(ch if ch == "\n" else " " for ch in seg[2:]))
            line += seg.count("\n")
            i = j
        elif c in ('"', "'"):
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(c + " " * (j - i - 2) + c if j - i >= 2 else c)
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out), comment_lines


TOKEN = re.compile(r"[A-Za-z_$][\w$]*|\S")


def compute(src, is_class):
    code, clines = strip(src)
    lines = src.split("\n")
    nonblank = sum(1 for ln in lines if ln.strip())
    comment_ratio = len([k for k in clines if k < len(lines) and lines[k].strip()]) / nonblank if nonblank else 0.0

    toks = TOKEN.findall(code)
    # statements
    semis, ctrl, depth, maxd, i = 0, 0, 0, 0, 0
    in_for, for_paren = False, 0
    for idx, t in enumerate(toks):
        if t in CONTROL:
            ctrl += 1
            if t == "for":
                in_for, for_paren = True, 0
        elif t == "(" and in_for:
            for_paren += 1
        elif t == ")" and in_for:
            for_paren -= 1
            if for_paren == 0:
                in_for = False
        elif t == ";":
            if not (in_for and for_paren > 0):
                semis += 1
        elif t == "{":
            depth += 1
            maxd = max(maxd, depth)
        elif t == "}":
            depth -= 1
    statements = semis + ctrl
    max_nesting = max(maxd - (2 if is_class else 1), 0)

    # method calls
    calls = 0
    for idx, t in enumerate(toks):
        if idx + 1 < len(toks) and toks[idx + 1] == "(" and re.match(r"[A-Za-z_$]", t):
            if t in KEYWORDS and t != "this" and t != "super":
                continue
            prev = toks[idx - 1] if idx > 0 else ""
            if prev == "@":
                continue
            if prev in (">", "]") or prev in PRIMITIVE or (re.match(r"[A-Za-z_$]", prev) and prev not in KEYWORDS):
                continue  # declaration
            # constructor / method declaration: matching ')' followed by '{' or 'throws'
            j, d = idx + 1, 0
            while j < len(toks):
                if toks[j] == "(":
                    d += 1
                elif toks[j] == ")":
                    d -= 1
                    if d == 0:
                        break
                j += 1
            if j + 1 < len(toks) and toks[j + 1] in ("{", "throws"):
                continue
            calls += 1
    calls += len(re.findall(r"\bnew\s+[\w$.]+\s*<", code))
    idents = [t for t in toks if re.match(r"[A-Za-z_$]", t) and t not in KEYWORDS]
    mean_id_len = float(np.mean([len(t) for t in idents])) if idents else np.nan
    return statements, max_nesting, comment_ratio, calls, mean_id_len


def main():
    t0 = time.time()
    ann, smp, mm, cm, ent = load_tables()
    annotated = smp[smp.id.isin(ann.sample_id)]
    e = ent.merge(smp, left_on="sampleId", right_on="id")
    cons = e[(e.smellPresented.isin([2, 3, 5, 6]) & (e.is_class == 0)) | (e.smellPresented.isin([1, 4]) & (e.is_class == 1))]
    need = pd.concat([annotated[["path_to_file", "is_class"]], cons[["path_to_file", "is_class"]]]).drop_duplicates()
    z = zipfile.ZipFile(ZIP)
    names = set(z.namelist())
    rows, missing, failed = [], 0, 0
    for path, is_class in need.itertuples(index=False):
        key = path.lstrip("/")
        if key not in names:
            missing += 1
            continue
        try:
            src = z.read(key).decode("utf-8", "replace")
            rows.append((path, is_class) + compute(src, bool(is_class)))
        except Exception:
            failed += 1
    f = pd.DataFrame(rows, columns=["path", "is_class", "statements", "max_nesting", "comment_ratio", "method_calls",
                                    "mean_identifier_length"])
    f.to_csv(os.path.join(FEAT_DIR, "features.csv.gz"), index=False)
    msg = (f"paths needed: {len(need)}; computed: {len(f)}; missing from zip: {missing}; failed: {failed}; "
           f"runtime {time.time() - t0:.1f}s\n")
    msg += f.describe().round(3).to_string() + "\n"

    # lizard cross-check of cc and parameter count on DACOS method snippets (integrity check only)
    import lizard
    am = annotated[annotated.is_class == 0].merge(mm, left_on="designite_id", right_on="id", suffixes=("", "_m"))
    res = []
    for r in am.itertuples():
        key = r.path_to_file.lstrip("/")
        if key not in names:
            continue
        src = z.read(key).decode("utf-8", "replace")
        info = lizard.analyze_file.analyze_source_code("Snippet.java", "class __W__ {\n" + src + "\n}")
        if info.function_list:
            fn = max(info.function_list, key=lambda x: x.nloc)
            res.append((r.cc, fn.cyclomatic_complexity, r.pc, len(fn.parameters)))
    R = pd.DataFrame(res, columns=["cc_designite", "cc_lizard", "pc_designite", "pc_lizard"])
    msg += (f"\nlizard {lizard.version if hasattr(lizard, 'version') else ''} cross-check on {len(R)} DACOS method snippets:\n"
            f"  cc exact match {np.mean(R.cc_designite == R.cc_lizard):.3f}, Spearman "
            f"{R.cc_designite.corr(R.cc_lizard, method='spearman'):.3f}, median |diff| {np.median(abs(R.cc_designite - R.cc_lizard)):.1f}\n"
            f"  pc exact match {np.mean(R.pc_designite == R.pc_lizard):.3f}, Spearman "
            f"{R.pc_designite.corr(R.pc_lizard, method='spearman'):.3f}\n")
    R.to_csv(os.path.join(LOG, "lizard_crosscheck.csv"), index=False)
    open(os.path.join(LOG, "features.log"), "w").write(msg)
    print(msg)


if __name__ == "__main__":
    main()
