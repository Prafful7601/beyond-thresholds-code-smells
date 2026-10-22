"""Prompt 4 Part 1 / plan.md §7.1: why same-snippet agreement exceeds cross-snippet agreement (primary).

Populations: entities with exactly 2 usable annotations (CM primary, LPL primary, LPL R5).
1.1 matched near-duplicate groups, 1.2 exact-duplicate groups, 1.3 annotation-id gap, 1.4 tool design, 1.5 paragraph.
"""
import os
import sys
import time
import zipfile

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403,E402
from human_ceiling import m_from_counts  # noqa: E402
from step3_e import keys  # noqa: E402

N_DESIG = 2000
POPS = [("CM", "CM", "primary"), ("LPL", "LPL", "primary"), ("LPL R5", "LPL", "R5")]
MIN_GROUPS = 20
TAGMAN = "SMART-Dal/Tagman @ 40f3aa67bc16d780c6a0e1da63995b7d92789ddc (2023-01-19)"


def population(L, smell, variant):
    A, E = variant_annotations(L, variant)
    A, E = A[A.smell == smell], E[E.smell == smell]
    E = attach_metrics(E[E.n == 2]).reset_index(drop=True)
    ids = A[A.entity.isin(E.entity)].groupby("entity").ann_id.agg(["min", "max"])
    E["gap"] = E.entity.map(ids["max"] - ids["min"]).astype(int)
    return E


def same_snippet(y, r_, n_desig=N_DESIG):
    """y: yes-counts (0, 1, 2) of entities with 2 annotations. Returns mean MCC and accuracy over designations."""
    b0, b1, s = int((y == 0).sum()), int((y == 2).sum()), int((y == 1).sum())
    k = r_.binomial(s, 0.5, n_desig)
    m = m_from_counts(np.full(n_desig, b1), np.full(n_desig, b0), s - k, k)
    return float(m["MCC"].mean()), float(m["accuracy"].mean())


def cross_snippet(pa, pb, r_, n_desig=N_DESIG):
    """pa, pb: yes-probabilities of the two entities of each pair (random annotation per entity, random roles)."""
    c11 = pa * pb
    c10 = 0.5 * (pa * (1 - pb) + pb * (1 - pa))
    c00 = (1 - pa) * (1 - pb)
    T = pd.DataFrame({"t": list(zip(np.minimum(pa, pb), np.maximum(pa, pb))), "c11": c11, "c10": c10, "c00": c00})
    tot = np.zeros((n_desig, 4))
    for _, g in T.groupby("t"):
        pr = np.array([g.c11.iloc[0], g.c10.iloc[0], g.c10.iloc[0], g.c00.iloc[0]])
        tot += r_.multinomial(len(g), pr / pr.sum(), size=n_desig)
    m = m_from_counts(tot[:, 0], tot[:, 3], tot[:, 1], tot[:, 2])
    return float(m["MCC"].mean()), float(m["accuracy"].mean())


def groups_of(E, key):
    gs = [g for _, g in E.groupby(["project", key]) if len(g) >= 2]
    out = []
    for g in gs:
        y = g.y.values.astype(int)
        p = y / 2.0
        ia, ib = np.triu_indices(len(g), 1)
        out.append({"y": y, "pa": p[ia], "pb": p[ib]})
    return out


def matched(groups, r_):
    def stat(sel):
        y = np.concatenate([groups[i]["y"] for i in sel])
        pa = np.concatenate([groups[i]["pa"] for i in sel])
        pb = np.concatenate([groups[i]["pb"] for i in sel])
        a = same_snippet(y, r_)
        b = cross_snippet(pa, pb, r_)
        return a, b
    allg = np.arange(len(groups))
    (a_mcc, a_acc), (b_mcc, b_acc) = stat(allg)
    bs = {"a": [], "b": [], "d": [], "a_acc": [], "b_acc": [], "d_acc": []}
    for _ in range(B):
        sel = r_.integers(0, len(groups), len(groups))
        (am, aa), (bm, ba) = stat(sel)
        bs["a"].append(am)
        bs["b"].append(bm)
        bs["d"].append(am - bm)
        bs["a_acc"].append(aa)
        bs["b_acc"].append(ba)
        bs["d_acc"].append(aa - ba)
    ci = {k: boot_ci(v) for k, v in bs.items()}
    return {"groups": len(groups), "entities": int(sum(len(g["y"]) for g in groups)),
            "pairs": int(sum(len(g["pa"]) for g in groups)),
            "same_MCC": a_mcc, "same_lo": ci["a"][0], "same_hi": ci["a"][1],
            "cross_MCC": b_mcc, "cross_lo": ci["b"][0], "cross_hi": ci["b"][1],
            "diff_MCC": a_mcc - b_mcc, "diff_lo": ci["d"][0], "diff_hi": ci["d"][1],
            "same_raw_agreement": a_acc, "cross_raw_agreement": b_acc,
            "diff_raw_agreement": a_acc - b_acc, "diff_raw_lo": ci["d_acc"][0], "diff_raw_hi": ci["d_acc"][1]}


def raw_only(groups):
    y = np.concatenate([g["y"] for g in groups]) if groups else np.array([])
    pa = np.concatenate([g["pa"] for g in groups]) if groups else np.array([])
    pb = np.concatenate([g["pb"] for g in groups]) if groups else np.array([])
    same = float(np.mean(y != 1)) if len(y) else np.nan                      # P(two annotations agree)
    cross = float(np.mean(pa * pb + (1 - pa) * (1 - pb))) if len(pa) else np.nan
    return {"groups": len(groups), "entities": int(len(y)), "pairs": int(len(pa)),
            "same_raw_agreement": same, "cross_raw_agreement": cross,
            "diff_raw_agreement": same - cross if len(y) else np.nan}


def gap_analysis(E, label, metric, r_):
    rows = []
    E = E.copy()
    E["unanimous_i"] = E.unanimous.astype(int)
    E["quintile"] = pd.qcut(E.gap.rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    for q, g in E.groupby("quintile", observed=True):
        y = g.y.values.astype(int)
        u = g.unanimous_i.values
        mm, _ = same_snippet(y, r_)
        bu, bm = [], []
        for _ in range(B):
            i = r_.integers(0, len(g), len(g))
            bu.append(u[i].mean())
            bm.append(same_snippet(y[i], r_, 200)[0])
        rows.append({"population": label, "quintile": int(q), "gap_min": int(g.gap.min()), "gap_max": int(g.gap.max()),
                     "entities": len(g), "share_unanimous": float(u.mean()), "share_lo": boot_ci(bu)[0],
                     "share_hi": boot_ci(bu)[1], "same_MCC": mm, "MCC_lo": boot_ci(bm)[0], "MCC_hi": boot_ci(bm)[1]})
    X = sm.add_constant(pd.DataFrame({"log_gap": np.log(E.gap.astype(float)), "metric": E[metric].astype(float)}))
    fit = sm.Logit(E.unanimous_i.values, X).fit(disp=0, maxiter=200)
    ci = fit.conf_int().loc["log_gap"]
    separated = (not np.isfinite(ci).all()) or float(fit.bse["log_gap"]) > 5
    logit = {"population": label, "entities": len(E),
             "OR_per_log_gap": np.nan if separated else float(np.exp(fit.params["log_gap"])),
             "OR_lo": np.nan if separated else float(np.exp(ci[0])), "OR_hi": np.nan if separated else float(np.exp(ci[1])),
             "p": np.nan if separated else float(fit.pvalues["log_gap"]),
             "OR_metric_per_unit": np.nan if separated else float(np.exp(fit.params["metric"])),
             "p_metric": np.nan if separated else float(fit.pvalues["metric"]),
             "note": "not estimable: quasi-complete separation (robust SE > 5)" if separated else ""}
    dist = {"population": label, "entities": len(E), "min": int(E.gap.min()), "q1": float(E.gap.quantile(.25)),
            "median": float(E.gap.median()), "q3": float(E.gap.quantile(.75)), "max": int(E.gap.max()),
            "share_gap_le_10": float((E.gap <= 10).mean()), "share_gap_le_100": float((E.gap <= 100).mean())}
    return rows, logit, dist


TOOL = [
    {"question": "(a) Does serving prevent one user from annotating the same sample twice?",
     "finding": "Yes for the same `sample` row. Once a user has any annotation, candidate samples are filtered by `id NOT IN (<sample ids this user annotated>)`. "
                "The filter does not apply across different `sample` rows of the same code entity, such as the 332 MA classes imported twice (§1.3).",
     "reference": "src/main/java/com/smartlab/tagman/service/AnnotationService.java:99-120, 131-133"},
    {"question": "(b) What does the annotator see?",
     "finding": "Only the contents of the snippet's own file (`sample.path_to_file`, the CodeSplit method or class file), read line by line. "
                "It is shown in a code block titled with the file path. The surrounding class or source file is not shown.",
     "reference": "src/main/java/com/smartlab/tagman/web/AnnotationController.java:107-118; src/main/resources/templates/indexNonAdmin.html:438-439; "
                  "src/main/java/com/smartlab/tagman/util/TagmanUtil.java:53-58"},
    {"question": "(c) How are samples assigned and ordered?",
     "finding": "Each request picks methods with probability 0.7 and classes with 0.3 (`random.nextInt(10) < 7`). "
                "It first queries samples with `has_smell = true` and `sample_constraints = 1` (already annotated once), then falls back to `sample_constraints < 2`. "
                "Both queries use `LIMIT 10` with no `ORDER BY`, and the tool picks uniformly at random among the ≤ 10 rows returned. "
                "Without `ORDER BY`, the rows returned follow the database's storage order, so serving tends to follow sample-id order. "
                "Preferring samples with one annotation tends to bring a sample's second annotation soon after its first. "
                "The counter `sample_constraints` is incremented on submit. Each user is capped at `MaxUserAnnotations` = 2500.",
     "reference": "AnnotationService.java:76-79, 92-93, 117-120, 131-133, 142-143; util/Constants.java:41, 51"},
]


def main():
    t0 = time.time()
    L = annotation_long()
    z = zipfile.ZipFile(ZIP)
    m_rows, e_rows, q_rows, lg_rows, d_rows = [], [], [], [], []
    p3 = pd.read_csv(os.path.join(TAB, "human_ceiling_neardup.csv")).set_index("smell")
    for label, smell, variant in POPS:
        E = population(L, smell, variant)
        names = set(z.namelist())
        kk = [keys(z.read(p.lstrip("/")).decode("utf-8", "replace")) if p.lstrip("/") in names else (None, None)
              for p in E.path]   # snippets missing from files.zip get no duplicate key (excluded from groups)
        E["exact_key"], E["near_key"] = [a for a, _ in kk], [b for _, b in kk]
        r_ = rng()
        res = matched(groups_of(E, "near_key"), r_)
        m_rows.append({"population": label, "key": "near-duplicate", **res,
                       "prompt3_cross_MCC_all_entities": float(p3.loc[label].MCC)})
        eg = groups_of(E, "exact_key")
        if len(eg) >= MIN_GROUPS:
            e_rows.append({"population": label, "key": "exact duplicate", "reported_as": "CI (≥ 20 groups)", **matched(eg, r_)})
        else:
            e_rows.append({"population": label, "key": "exact duplicate", "reported_as": f"counts and raw agreement only (< {MIN_GROUPS} groups)",
                           **raw_only(eg)})
        rows, lg, dist = gap_analysis(E, label, PRIMARY[smell], r_)
        q_rows += [{**r, "set": "primary" if variant == "primary" else "R5"} for r in rows]
        lg_rows.append({**lg, "set": "primary" if variant == "primary" else "R5"})
        d_rows.append({**dist, "set": "primary" if variant == "primary" else "R5"})
        if variant == "primary":
            E4 = population(L, smell, "R4")
            rows4, lg4, dist4 = gap_analysis(E4, label, PRIMARY[smell], r_)
            q_rows += [{**r, "set": "R4"} for r in rows4]
            lg_rows.append({**lg4, "set": "R4"})
            d_rows.append({**dist4, "set": "R4"})
        print(label, f"{time.time() - t0:.0f}s", flush=True)
    M = pd.DataFrame(m_rows)
    X = pd.DataFrame(e_rows)
    Q = pd.DataFrame(q_rows)
    G = pd.DataFrame(lg_rows)
    Dd = pd.DataFrame(d_rows)
    for df, n, kind in ((M, "agreement_matched_neardup", "primary"), (X, "agreement_exact_dup", "primary"),
                        (Q, "agreement_gap_quintiles", "primary (R4 rows: robustness)"),
                        (G, "agreement_gap_logit", "primary (R4 rows: robustness)"),
                        (Dd, "agreement_gap_distribution", "primary (R4 rows: robustness)")):
        df["analysis"] = kind
        df.to_csv(os.path.join(TAB, n + ".csv"), index=False)
    pd.DataFrame(TOOL).to_csv(os.path.join(TAB, "agreement_tool_design.csv"), index=False)

    # ---------------- 1.5 paragraph from the pre-registered rules (plan §7.1)
    sent = []
    gap_excl = [r for r in M.itertuples() if r.diff_lo > 0]
    sent.append(f"In the matched comparison, same-snippet MCC exceeds cross-snippet MCC on the same entities for "
                f"{len(gap_excl)} of {len(M)} populations (CI of the difference excluding 0). "
                + ("This shows that the gap is not an artefact of comparing different populations. It does not discriminate between the two explanations."
                   if gap_excl else "The gap is therefore not established on matched entities."))
    ex_txt = []
    for r in X.itertuples():
        if r.reported_as.startswith("CI"):
            ex_txt.append(f"{r.population}: same − cross MCC {r.diff_MCC:.3f} [{r.diff_lo:.3f}, {r.diff_hi:.3f}]")
        else:
            ex_txt.append(f"{r.population}: {r.groups} groups, raw agreement {r.same_raw_agreement:.3f} same-snippet versus {r.cross_raw_agreement:.3f} cross-snippet")
    lower = [r for r in X.itertuples() if (r.reported_as.startswith("CI") and r.diff_lo > 0) or
             (not r.reported_as.startswith("CI") and np.isfinite(r.diff_raw_agreement) and r.diff_raw_agreement > 0)]
    sent.append(f"For exact duplicates, which share names and text ({'; '.join(ex_txt)}), cross-snippet agreement is below same-snippet agreement in "
                f"{len(lower)} of {len(X)} populations. Where it is lower, this is inconsistent with the view that information inside the snippet text "
                "explains the gap; context outside the snippet and collection effects remain possible."
                + (" Where only counts are available, this rests on small numbers." if any(not r.reported_as.startswith("CI") for r in X.itertuples()) else ""))
    prim = G[G.set != "R4"]
    neg = [r for r in prim.itertuples() if np.isfinite(r.OR_hi) and r.OR_hi < 1]
    pos = [r for r in prim.itertuples() if np.isfinite(r.OR_lo) and r.OR_lo > 1]
    sent.append("The annotation-id gap shows an OR per unit log(gap) below 1 with a CI excluding 1 for "
                f"{', '.join(r.population for r in neg) or 'no population'}. "
                + ("That is consistent with collection or session effects. " if neg else "")
                + (f"The OR is above 1 with a CI excluding 1 for {', '.join(r.population for r in pos)}, meaning agreement rises with the gap. "
                   if pos else "")
                + "A null result here is not evidence against collection effects.")
    sent.append("The public tool source shows annotators only the snippet's own file, which is inconsistent with an explanation based on context outside the snippet, "
                "unless the deployed version differed. It prevents the same user from annotating the same sample row twice, so a same-annotator explanation "
                "is possible only through duplicated sample rows or multiple accounts. Neither can be checked, because the data have no annotator ids.")
    para = " ".join(sent)

    mm = M.copy()
    mm["same-snippet MCC [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(mm.same_MCC, mm.same_lo, mm.same_hi)]
    mm["cross-snippet MCC [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(mm.cross_MCC, mm.cross_lo, mm.cross_hi)]
    mm["difference [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(mm.diff_MCC, mm.diff_lo, mm.diff_hi)]
    mm["Prompt 3 cross-snippet MCC"] = mm.prompt3_cross_MCC_all_entities.round(3)
    mm = mm[["population", "groups", "entities", "pairs", "same-snippet MCC [95% CI]", "cross-snippet MCC [95% CI]",
             "difference [95% CI]", "Prompt 3 cross-snippet MCC"]]
    xx = X.copy()
    for c in xx.columns:
        if xx[c].dtype.kind == "f":
            xx[c] = xx[c].round(3)
    xx = xx.drop(columns=["analysis"]).astype(object).where(xx.drop(columns=["analysis"]).notna(), "–")
    qq = Q.copy()
    qq["gap range"] = qq.gap_min.astype(str) + "–" + qq.gap_max.astype(str)
    qq["share unanimous [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(qq.share_unanimous, qq.share_lo, qq.share_hi)]
    qq["same-snippet MCC [95% CI]"] = [fmt_ci(a, b, c) for a, b, c in zip(qq.same_MCC, qq.MCC_lo, qq.MCC_hi)]
    qq = qq[["population", "set", "quintile", "gap range", "entities", "share unanimous [95% CI]", "same-snippet MCC [95% CI]"]]
    gg = G.copy()
    gg["OR per unit log(gap) [95% CI]"] = [fmt_ci(a, b, c) if np.isfinite(a) else "n/a" for a, b, c in zip(gg.OR_per_log_gap, gg.OR_lo, gg.OR_hi)]
    gg["p"] = [fmt_p(v) for v in gg.p]
    gg["OR per unit metric (p)"] = [f"{a:.3f} ({fmt_p(b)})" if np.isfinite(a) else "n/a" for a, b in zip(gg.OR_metric_per_unit, gg.p_metric)]
    gg = gg[["population", "set", "entities", "OR per unit log(gap) [95% CI]", "p", "OR per unit metric (p)", "note"]]
    dd = Dd.copy()
    for c in ("q1", "median", "q3", "share_gap_le_10", "share_gap_le_100"):
        dd[c] = dd[c].round(3)
    dd = dd.drop(columns=["analysis"])
    txt = f"""**Analysis type: primary** (R4 rows of 1.3 are robustness). plan.md §7.1.

**Population.** Primary-set entities with exactly 2 usable annotations (R5 set for "LPL R5"). Entities whose snippet file is missing from `files.zip` (§1.8) get no duplicate key and are excluded from 1.1–1.2, but are kept in 1.3. Groups are entities of the same project with the same near-duplicate key (identifiers → ID, literals → LIT) or the same exact key (comments removed, whitespace collapsed, names kept), with at least 2 entities.

**1.1 Matched comparison on near-duplicate groups**
- (a) Same-snippet MCC: one annotation versus the other, random roles, {N_DESIG} designations.
- (b) Cross-snippet MCC: for every entity pair within a group, one random annotation per entity, random roles, {N_DESIG} draws.
- CIs: bootstrap over groups (B = {B}); the difference is paired.
- The Prompt 3 cross-snippet number (§6, last column) used every primary-set entity with ≥ 2 usable annotations, drawing each entity's annotation with probability y/n. (b) uses the same construction restricted to entities with exactly 2 usable annotations, so both sides here are computed on identical entities.

{md_table(mm)}

**1.2 Exact duplicates**

{md_table(xx)}

**1.3 Annotation-id gap** (|id₁ − id₂| per entity; R4 = run annotations removed first)

{md_table(dd)}

{md_table(qq)}

Logistic regression of unanimous on log(gap) and the raw primary metric:

{md_table(gg)}

**1.4 Tool design** (public source {TAGMAN}; the deployed version may differ)

{md_table(pd.DataFrame(TOOL))}

**1.5 Interpretation (rules fixed in plan.md §7.1)**

{para}

Tables: `tables/agreement_matched_neardup.csv`, `agreement_exact_dup.csv`, `agreement_gap_distribution.csv`, `agreement_gap_quintiles.csv`, `agreement_gap_logit.csv`, `agreement_tool_design.csv`. Runtime {time.time() - t0:.0f}s.
"""
    write_frag("agreement_anatomy", txt)
    print(txt)


if __name__ == "__main__":
    main()
