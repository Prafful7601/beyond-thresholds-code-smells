"""Line-level diff and changed-method detection for one Java file (before -> after).

A method is "changed" if its line range intersects an added or modified hunk (after side) or a deleted hunk
(before side). Methods are paired across versions by name when the name is unique on both sides (a signature
change is then a modification), otherwise by (name, parameter count, occurrence) among overloads.
"""
import difflib

from .extract import extract_methods


def line_changes(old_text, new_text):
    """(lines added or modified in new, lines deleted or modified in old), both 1-based."""
    old, new = old_text.splitlines(), new_text.splitlines()
    added, removed = set(), set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag in ("replace", "insert"):
            added.update(range(j1 + 1, j2 + 1))
        if tag in ("replace", "delete"):
            removed.update(range(i1 + 1, i2 + 1))
    return added, removed


def _pair(before_methods, after_methods):
    """Match methods across versions: by name when the name is unique on both sides (so a signature change is a
    modification), otherwise by (name, parameter count, occurrence) among overloads."""
    from collections import defaultdict
    bn, an = defaultdict(list), defaultdict(list)
    for m in before_methods:
        bn[m.name].append(m)
    for m in after_methods:
        an[m.name].append(m)
    pairs, only_before, only_after = [], [], []
    for name in sorted(set(bn) | set(an)):
        bs, as_ = bn.get(name, []), an.get(name, [])
        if len(bs) == 1 and len(as_) == 1:
            pairs.append((bs[0], as_[0]))
            continue
        bk, ak = {}, {}
        for group, target in ((bs, bk), (as_, ak)):
            seen = {}
            for m in group:
                seen[m.pc] = seen.get(m.pc, 0) + 1
                target[(m.pc, seen[m.pc])] = m
        for k in ak:
            if k in bk:
                pairs.append((bk[k], ak[k]))
            else:
                only_after.append(ak[k])
        only_before += [bk[k] for k in bk if k not in ak]
    return pairs, only_before, only_after


def changed_methods(old_text, new_text, filename):
    """List of {key, change_type (added|modified|deleted), before, after, changed_lines}."""
    added, removed = line_changes(old_text or "", new_text or "")
    pairs, only_before, only_after = _pair(extract_methods(old_text, filename) if old_text else [],
                                           extract_methods(new_text, filename) if new_text else [])
    out = []
    for b, m in pairs:
        span = set(range(m.start_line, m.end_line + 1))
        touched = sorted(span & added)
        if touched or (set(range(b.start_line, b.end_line + 1)) & removed):
            out.append({"key": (m.name, m.start_line), "change_type": "modified", "before": b, "after": m,
                        "changed_lines": touched})
    for m in only_after:
        span = set(range(m.start_line, m.end_line + 1))
        out.append({"key": (m.name, m.start_line), "change_type": "added", "before": None, "after": m,
                    "changed_lines": sorted(span & added) or sorted(span)})
    for b in only_before:
        out.append({"key": (b.name, b.start_line), "change_type": "deleted", "before": b, "after": None,
                    "changed_lines": []})
    return out
