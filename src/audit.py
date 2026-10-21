"""Phase 0 audit of the DACOS SQLite conversions.

Usage: python -I src/audit.py <paper3_dir>
Writes results/logs/audit.txt (and prints it).
"""
import collections
import os
import sqlite3
import sys
import zipfile

import numpy as np
import pandas as pd

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 200)

ROOT = sys.argv[1]
MAIN = os.path.join(ROOT, "data/db/dacos_main.sqlite")
EXT = os.path.join(ROOT, "data/db/dacos_ext.sqlite")
ZIP = os.path.join(ROOT, "data/raw/files.zip")
OUT = os.path.join(ROOT, "results/logs/audit.txt")

lines = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)


def h(t):
    p("")
    p("=" * 100)
    p(t)
    p("=" * 100)


def q(con, sql):
    return pd.read_sql_query(sql, con)


main = sqlite3.connect(MAIN)
ext = sqlite3.connect(EXT)

# ---------------------------------------------------------------- schemas
h("1. SCHEMAS AND ROW COUNTS")
for name, con in (("DACOSMain", main), ("DACOSExtended", ext)):
    for (t,) in con.execute("select name from sqlite_master where type='table' order by name"):
        n = con.execute('select count(*) from "%s"' % t).fetchone()[0]
        cols = con.execute('pragma table_info("%s")' % t).fetchall()
        p("%s.%s  rows=%d" % (name, t, n))
        for c in cols:
            p("    %-22s %s" % (c[1], c[2]))

h("1b. Are the tables shared between the two dumps identical?")
for t in ("sample", "method_metrics", "class_metrics"):
    a = q(main, 'select * from "%s" order by id' % t)
    b = q(ext, 'select * from "%s" order by id' % t)
    p("%-15s identical=%s" % (t, a.equals(b)))

# ---------------------------------------------------------------- load
ann = q(main, "select * from annotation")
smp = q(main, "select * from sample")
mm = q(main, "select * from method_metrics")
cm = q(main, "select * from class_metrics")
for c in ("cc", "loc", "pc"):
    mm[c] = pd.to_numeric(mm[c], errors="coerce")
for c in ("dit", "fanin", "fanout", "lcom", "loc", "nc", "nof", "nom", "nopf", "nopm", "wmc"):
    cm[c] = pd.to_numeric(cm[c], errors="coerce")

h("2. VALUE DOMAINS")
p("annotation flag columns value counts:")
for c in ("iscm", "isim", "islp", "isma", "is_smell"):
    p("   ", c, dict(ann[c].value_counts().sort_index()))
p("sample.smells value counts (all samples):", dict(smp["smells"].value_counts()))
p("sample.has_smell x is_class:")
p(pd.crosstab(smp.has_smell, smp.is_class).to_string())
p("annotation.sample_id null:", int(ann.sample_id.isna().sum()),
  " orphan (not in sample):", int((~ann.sample_id.isin(smp.id)).sum()))
p("duplicate annotation ids:", int(ann.id.duplicated().sum()))
p("non-numeric metric values: method", int(mm[["cc", "loc", "pc"]].isna().sum().sum()),
  " class", int(cm[["lcom", "nom", "nof", "wmc", "loc"]].isna().sum().sum()))

# designite_id join check
p("")
p("designite_id -> metrics join (all samples):")
for ic, tab in ((0, mm), (1, cm)):
    s = smp[smp.is_class == ic]
    p("   is_class=%d: samples=%d, designite_id found in %s_metrics=%d" %
      (ic, len(s), "method" if ic == 0 else "class", int(s.designite_id.isin(tab.id).sum())))


def name_ok(row):
    # path: /codesplit_java_<kind>/<proj>/<proj>/<package>/<Type>[/<method>].code
    parts = row.path_to_file.strip("/").split("/")
    return parts


chk = smp.merge(mm, left_on="designite_id", right_on="id", suffixes=("", "_m"))
chk = chk[chk.is_class == 0]
parts = chk.path_to_file.str.strip("/").str.split("/")
chk["p_pkg"] = parts.str[3]
chk["p_type"] = parts.str[4]
chk["p_meth"] = parts.str[5].str.replace(r"\.code$", "", regex=True)
ok = (chk.p_pkg == chk.package_name) & (chk.p_type == chk.type_name) & (chk.p_meth == chk.method_name)
p("   method samples whose path (package/type/method) matches joined method_metrics row: %d / %d" % (ok.sum(), len(ok)))
chk = smp.merge(cm, left_on="designite_id", right_on="id", suffixes=("", "_c"))
chk = chk[chk.is_class == 1]
parts = chk.path_to_file.str.strip("/").str.split("/")
ok = (parts.str[3] == chk.package_name) & (parts.str[4].str.replace(r"\.code$", "", regex=True) == chk.type_name)
p("   class samples whose path (package/type) matches joined class_metrics row: %d / %d" % (ok.sum(), len(ok)))

# ---------------------------------------------------------------- annotations
h("3. ANNOTATIONS: flag pattern by the sample's smells field")
a = ann.merge(smp, left_on="sample_id", right_on="id", suffixes=("", "_s"))
a["smells"] = a["smells"].fillna("")
p(a.groupby(["is_class", "smells", "iscm", "isim", "islp", "isma", "is_smell"]).size().rename("n").reset_index().to_string(index=False))

p("")
p("Discordance between the per-smell checkbox and is_smell, by annotation-id bin of 1000:")
a["bin"] = (a.id // 1000) * 1000
a["cm_disc"] = a.smells.str.contains("1") & (a.iscm != a.is_smell)
a["lp_disc"] = (a.smells == "2") & (a.islp != a.is_smell)
a["ma_disc"] = (a.smells == "3") & (a.isma != a.is_smell)
a["lp_on_cm_only"] = (a.smells == "1") & (a.islp == 1)
p(a.groupby(["bin"]).agg(n=("id", "size"), cm_disc=("cm_disc", "sum"), lp_disc=("lp_disc", "sum"),
                         ma_disc=("ma_disc", "sum"), lp_ticked_on_CM_only=("lp_on_cm_only", "sum"),
                         empty_smells=("smells", lambda s: (s == "").sum())).to_string())

h("4. COUNTS PER SMELL (smell assigned from sample.smells: 1=CM, 2=LPL, 3=MA; '' = none recorded)")
per = a.groupby("sample_id").agg(n_ann=("id", "size"), smells=("smells", "first"), is_class=("is_class", "first"),
                                 sc=("sample_constraints", "first"))
p("distinct annotated snippets:", len(per), "  annotations:", len(a))
p("")
p("snippets by smells field:")
p(per.groupby("smells").agg(snippets=("n_ann", "size"), annotations=("n_ann", "sum")).to_string())
p("")
rows = []
for sm, mask in (("CM (smells contains 1)", per.smells.str.contains("1")),
                 ("LPL (smells contains 2)", per.smells.str.contains("2")),
                 ("LPL incl. empty-smells method samples", per.smells.str.contains("2") | (per.smells == "")),
                 ("MA (smells == 3)", per.smells == "3")):
    rows.append((sm, int(mask.sum()), int(per.n_ann[mask].sum())))
p(pd.DataFrame(rows, columns=["smell", "snippets", "annotations"]).to_string(index=False))
p("Paper Table II: CM 2197/4349, LPL 1634/3221, MA 1361/2697, total 5192/10267")

p("")
p("Annotations per snippet distribution:")
p(per.n_ann.value_counts().sort_index().to_string())
p("by smells field:")
p(pd.crosstab(per.smells, per.n_ann).to_string())
p("")
p("sample.sample_constraints (tool's served/annotated counter) vs actual annotation count:")
p(pd.crosstab(per.sc, per.n_ann).to_string())

h("5. ANNOTATOR IDENTITY")
p("annotation columns:", list(ann.columns))
p("No user / annotator / timestamp column exists in the dumped annotation table.")
p("contributors.txt lists 16 names (annotators with >50 samples); paper reports 86 annotators.")

# ---------------------------------------------------------------- metrics of annotated snippets
h("6. STORED METRICS OF ANNOTATED SNIPPETS (DesigniteJava values from the dump)")
am = per.reset_index().merge(smp[["id", "designite_id"]], left_on="sample_id", right_on="id")
amm = am[am.is_class == 0].merge(mm, left_on="designite_id", right_on="id", suffixes=("", "_m"))
amc = am[am.is_class == 1].merge(cm, left_on="designite_id", right_on="id", suffixes=("", "_c"))
p("method snippets joined:", len(amm), " class snippets joined:", len(amc))
for sm in sorted(amm.smells.unique()):
    s = amm[amm.smells == sm]
    p("smells=%-4r n=%4d  cc[min,max]=[%g,%g] cc value counts=%s" % (sm, len(s), s.cc.min(), s.cc.max(),
                                                                   dict(s.cc.value_counts().sort_index())))
    p("                 pc[min,max]=[%g,%g] pc value counts=%s" % (s.pc.min(), s.pc.max(),
                                                                 dict(s.pc.value_counts().sort_index())))
p("MA snippets: lcom[min,max]=[%.3f,%.3f]  quantiles=%s" % (amc.lcom.min(), amc.lcom.max(),
                                                           amc.lcom.quantile([0, .1, .25, .5, .75, .9, 1]).round(3).to_dict()))
p("Paper Table I ranges: CM cc 4-7, LPL pc 3-6, MA LCOM 0.4-0.8")

p("")
p("All (not only annotated) samples flagged in sample.smells, metric ranges:")
allm = smp[smp.is_class == 0].merge(mm, left_on="designite_id", right_on="id", suffixes=("", "_m"))
for sm in ("1", "2", "1,2", ""):
    s = allm[allm.smells == sm]
    p("smells=%-5r n=%6d cc in [%g,%g] pc in [%g,%g]" % (sm, len(s), s.cc.min(), s.cc.max(), s.pc.min(), s.pc.max()))
allc = smp[smp.is_class == 1].merge(cm, left_on="designite_id", right_on="id", suffixes=("", "_c"))
for sm in ("3", ""):
    s = allc[allc.smells == sm]
    p("class smells=%-4r n=%6d lcom in [%g,%g]" % (sm, len(s), s.lcom.min(), s.lcom.max()))

# ---------------------------------------------------------------- DACOSX
h("7. DACOSX (entry table)")
ent = q(ext, "select * from entry")
code = {1: "MA present", 4: "MA absent", 2: "LPL present", 5: "LPL absent", 3: "CM present", 6: "CM absent"}
ent["label"] = ent.smellPresented.map(code)
p(ent.groupby(["smellPresented", "label"]).size().rename("n").to_string())
p("positiveAnnotations/negativeAnnotations value counts:",
  dict(ent.positiveAnnotations.value_counts()), dict(ent.negativeAnnotations.value_counts()))
p("duplicate (sampleId, smellPresented):", int(ent.duplicated(["sampleId", "smellPresented"]).sum()))
p("sampleId found in sample table:", int(ent.sampleId.isin(smp.id).sum()), "/", len(ent))
p("DACOSX sampleIds that are also annotated in DACOS:", int(ent.sampleId.isin(per.index).sum()))
e = ent.merge(smp, left_on="sampleId", right_on="id", how="left", suffixes=("", "_s"))
em = e[e.is_class == 0].merge(mm, left_on="designite_id", right_on="id", suffixes=("", "_m"))
ec = e[e.is_class == 1].merge(cm, left_on="designite_id", right_on="id", suffixes=("", "_c"))
for k in (3, 6, 2, 5):
    s = em[em.smellPresented == k]
    p("%-12s n=%6d  is_class=0  cc in [%g,%g]  pc in [%g,%g]" % (code[k], len(s), s.cc.min(), s.cc.max(), s.pc.min(), s.pc.max()))
for k in (1, 4):
    s = ec[ec.smellPresented == k]
    p("%-12s n=%6d  is_class=1  lcom in [%g,%g]" % (code[k], len(s), s.lcom.min(), s.lcom.max()))
p("Granularity-consistent DACOSX (CM/LPL on methods, MA on classes):")
cons = e[((e.smellPresented.isin([2, 3, 5, 6])) & (e.is_class == 0)) | ((e.smellPresented.isin([1, 4])) & (e.is_class == 1))]
p(cons.groupby("label").size().to_string())
ann_sm = per.smells
for sm, codes, lab in (("CM", (3, 6), lambda x: "1" in x), ("LPL", (2, 5), lambda x: "2" in x or x == ""),
                       ("MA", (1, 4), lambda x: x == "3")):
    ids = set(ann_sm[ann_sm.map(lab)].index)
    c = cons[cons.smellPresented.isin(codes)]
    p("  %s: DACOSX same-smell entries whose snippet is also annotated for %s in DACOS: %d (present %d, absent %d)" % (
        sm, sm, c.sampleId.isin(ids).sum(), (c.sampleId.isin(ids) & (c.smellPresented == codes[0])).sum(),
        (c.sampleId.isin(ids) & (c.smellPresented == codes[1])).sum()))
p("Coverage of method samples by stored cc (CM) / pc (LPL): counts in DACOS band (smells field), DACOSX present, DACOSX absent")
mcons = cons.merge(mm, left_on="designite_id", right_on="id", suffixes=("", "_m")) if False else None
msmp = smp[smp.is_class == 0].merge(mm[["id", "cc", "pc"]], left_on="designite_id", right_on="id", suffixes=("", "_m"))
cmp_ = cons[cons.smellPresented.isin([3, 6])].set_index("sampleId").smellPresented
lpp = cons[cons.smellPresented.isin([2, 5])].set_index("sampleId").smellPresented
msmp["cm_x"] = msmp.id.map(cmp_).map({3: "X_present", 6: "X_absent"}).fillna("-")
msmp["lp_x"] = msmp.id.map(lpp).map({2: "X_present", 5: "X_absent"}).fillna("-")
msmp["cm_band"] = msmp.smells.str.contains("1")
msmp["lp_band"] = msmp.smells.str.contains("2")
msmp["annot"] = msmp.id.isin(per.index)
p(pd.crosstab(msmp.cc.clip(upper=20), [msmp.cm_band, msmp.cm_x]).to_string())
p(pd.crosstab(msmp.pc.clip(upper=16), [msmp.lp_band, msmp.lp_x, msmp.annot]).to_string())
csmp = smp[smp.is_class == 1].merge(cm[["id", "lcom", "nof", "nom"]], left_on="designite_id", right_on="id", suffixes=("", "_c"))
map_ = cons[cons.smellPresented.isin([1, 4])].set_index("sampleId").smellPresented
csmp["ma_x"] = csmp.id.map(map_).map({1: "X_present", 4: "X_absent"}).fillna("-")
csmp["lbin"] = pd.cut(csmp.lcom, [-1.01, -0.5, 0, 0.2, 0.4, 0.401, 0.6, 0.8, 0.807, 1.0])
p(pd.crosstab(csmp.lbin, [csmp.smells, csmp.ma_x]).to_string())
p("class samples with designite_id not found in class_metrics:", int((~smp[smp.is_class == 1].designite_id.isin(cm.id)).sum()))
p("smellPresented x is_class:")
p(pd.crosstab(e.smellPresented, e.is_class).to_string())
p("Paper Table II DacosX: CM 94489, LPL 93442, MA 19674, total 207605")

# ---------------------------------------------------------------- source files
h("8. SOURCE CODE MAPPING (Files.zip)")
z = zipfile.ZipFile(ZIP)
names = set(n for n in z.namelist() if not n.endswith("/"))
p("files in zip:", len(names))
key = smp.path_to_file.str.lstrip("/")
smp["in_zip"] = key.isin(names)
p("all samples with file in zip: %d / %d" % (smp.in_zip.sum(), len(smp)))
p("annotated snippets with file in zip: %d / %d" % (smp[smp.id.isin(per.index)].in_zip.sum(), len(per)))
p("DACOSX samples with file in zip: %d / %d" % (smp[smp.id.isin(ent.sampleId)].in_zip.sum(), ent.sampleId.nunique()))
miss = smp[smp.id.isin(per.index) & ~smp.in_zip].path_to_file.head(5).tolist()
p("examples missing:", miss)
ex = smp[smp.id.isin(per.index) & smp.in_zip].iloc[0]
p("example annotated snippet:", ex.path_to_file)
p(z.read(ex.path_to_file.lstrip("/")).decode("utf-8", "replace")[:600])
import re as _re
cls = smp[smp.id.isin(per.index) & (smp.is_class == 1) & smp.in_zip]
nbody = 0
for path in cls.path_to_file:
    txt = z.read(path.lstrip("/")).decode("utf-8", "replace")
    if _re.search(r"\)\s*(throws [^{]+)?\{\s*\}", txt) and not _re.search(r";\s*\n\s*\}", txt.split("{", 1)[-1]):
        nbody += 1
p("annotated class files in which every method body appears empty (bodies stripped by CodeSplitJava):", nbody, "/", len(cls))
mth = smp[smp.id.isin(per.index) & (smp.is_class == 0) & smp.in_zip].path_to_file.iloc[:3]
for path in mth:
    p("--- method example:", path)
    p(z.read(path.lstrip("/")).decode("utf-8", "replace")[:400])

# ---------------------------------------------------------------- projects
h("9. PROJECT / REPOSITORY IDENTITY")
p("distinct project_name in sample:", smp.project_name.nunique())
p("annotated snippets per project:")
pp = smp[smp.id.isin(per.index)][["id", "project_name"]].merge(per, left_on="id", right_index=True)
p(pd.crosstab(pp.project_name, pp.smells, margins=True).to_string())
p("distinct source files (class file, i.e. package/Type) among annotated snippets:",
  smp[smp.id.isin(per.index)].path_to_file.str.strip("/").str.split("/").str[1:5].str.join("/").nunique())
p("path project == sample.project_name for all samples:",
  bool((smp.path_to_file.str.strip("/").str.split("/").str[1] == smp.project_name).all()))
p("repository table rows (extended dump):", ext.execute("select count(*) from repository").fetchone()[0])
p("smell table rows (both dumps):", main.execute("select count(*) from smell").fetchone()[0],
  ext.execute("select count(*) from smell").fetchone()[0])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write("\n".join(lines) + "\n")

# ---------------------------------------------------------------- duplicates and answer runs
lines_extra = []
h("10. DUPLICATE SAMPLE ROWS (same designite entity imported twice)")
s2 = smp.copy()
s2["annot"] = s2.id.isin(per.index)
dup = s2[s2.annot].groupby(["is_class", "designite_id"]).agg(n_rows=("id", "size"), smells=("smells", "first"))
p("annotated sample rows:", int(s2.annot.sum()), " distinct (is_class, designite_id) entities:", len(dup))
p(dup.groupby(["is_class", "smells", "n_rows"]).size().rename("entities").to_string())
pooled = a.merge(smp[["id", "designite_id"]], left_on="sample_id", right_on="id", suffixes=("", "_d"))
pooled = pooled.groupby(["is_class", "designite_id_d" if "designite_id_d" in pooled else "designite_id"]).size()
p("annotations per entity after pooling duplicate rows:")
p(pooled.value_counts().sort_index().to_string())

h("11. CONSTANT-ANSWER RUNS (annotations ordered by annotation id, within smell)")
a_sorted = a.sort_values("id")
spec = {"CM / iscm": (a_sorted.smells.str.contains("1"), "iscm"),
        "LPL / islp": (a_sorted.smells.str.contains("2") | (a_sorted.smells == ""), "islp"),
        "MA / isma": (a_sorted.smells == "3", "isma"),
        "CM / is_smell": (a_sorted.smells.str.contains("1"), "is_smell"),
        "LPL / is_smell": (a_sorted.smells.str.contains("2") | (a_sorted.smells == ""), "is_smell"),
        "MA / is_smell": (a_sorted.smells == "3", "is_smell")}
for k, (mask, col) in spec.items():
    d = a_sorted[mask][["id", col]].reset_index(drop=True)
    v = d[col].values
    runs, s0 = [], 0
    for i in range(1, len(v) + 1):
        if i == len(v) or v[i] != v[s0]:
            if i - s0 >= 40:
                runs.append((int(d.id[s0]), int(d.id[i - 1]), i - s0, int(v[s0])))
            s0 = i
    covered = sum(r[2] for r in runs)
    p("%-15s n=%5d yes-rate=%.3f  runs>=40 (first_id, last_id, length, value): %s  annotations in runs: %d" %
      (k, len(v), v.mean(), runs, covered))
p("yes-rate by annotation-id bin of 500:")
a_sorted["bin500"] = (a_sorted.id // 500) * 500
rows = []
for b, g in a_sorted.groupby("bin500"):
    cmm, lpm, mam = g.smells.str.contains("1"), g.smells.str.contains("2") | (g.smells == ""), g.smells == "3"
    rows.append((b, len(g), cmm.sum(), g.iscm[cmm].mean(), g.is_smell[cmm].mean(), lpm.sum(), g.islp[lpm].mean(),
                 mam.sum(), g.isma[mam].mean(), g.is_smell[mam].mean()))
p(pd.DataFrame(rows, columns=["bin", "n", "CM_n", "CM_iscm", "CM_is_smell", "LPL_n", "LPL_islp", "MA_n", "MA_isma",
                              "MA_is_smell"]).round(2).to_string(index=False))

open(OUT, "w").write("\n".join(lines) + "\n")
