"""Changed-method detection on fixture commits, and the commit analysis built on it."""
import os

from codesniff.diff import changed_methods, line_changes
from codesniff.service import analyze_files
from conftest import APP

C1 = os.path.join(APP, "tests", "data", "commits", "c1")
BEFORE = open(os.path.join(C1, "before.java")).read()
AFTER = open(os.path.join(C1, "after.java")).read()


def test_line_changes():
    added, removed = line_changes("a\nb\nc\n", "a\nB\nc\nd\n")
    assert added == {2, 4} and removed == {2}


def test_changed_methods_fixture():
    ch = {c["after"].name if c["after"] else c["before"].name: c for c in changed_methods(BEFORE, AFTER, "Pricing.java")}
    assert set(ch) == {"tax", "discount", "legacy"}          # base and label are untouched
    assert ch["tax"]["change_type"] == "modified" and (ch["tax"]["before"].pc, ch["tax"]["after"].pc) == (1, 5)
    assert (ch["tax"]["before"].cc, ch["tax"]["after"].cc) == (1, 4)
    assert ch["discount"]["change_type"] == "added" and ch["discount"]["after"].cc == 5
    assert ch["legacy"]["change_type"] == "deleted" and ch["legacy"]["after"] is None
    assert ch["tax"]["changed_lines"][0] == ch["tax"]["after"].start_line


def test_added_and_deleted_files():
    assert {c["change_type"] for c in changed_methods("", AFTER, "P.java")} == {"added"}
    assert {c["change_type"] for c in changed_methods(BEFORE, "", "P.java")} == {"deleted"}
    assert changed_methods(BEFORE, BEFORE, "P.java") == []


def test_overloads_are_matched_by_parameter_count():
    old = "class A { int f(int a) { return a; } int f(int a, int b) { return a + b; } }"
    new = "class A { int f(int a) { return a; } int f(int a, int b) { if (a > b) { return a; } return a + b; } }"
    old = old.replace("{ return a; }", "{\n return a;\n }").replace("{ return a + b; }", "{\n return a + b;\n }")
    new = new.replace("{ return a; }", "{\n return a;\n }").replace("{ if", "{\n if").replace("return a + b; }", "return a + b;\n }")
    ch = changed_methods(old, new, "A.java")
    assert [(c["change_type"], c["after"].pc) for c in ch] == [("modified", 2)]


def test_analyze_files_statuses_and_points():
    ms = {m["name"]: m for m in analyze_files([("src/Pricing.java", BEFORE, AFTER)])}
    assert ms["tax"]["smells"]["LPL"]["status"] == "introduced" and ms["tax"]["smells"]["LPL"]["zone"] == "borderline"
    assert ms["discount"]["smells"]["CM"]["status"] == "introduced"
    assert ms["legacy"]["points"] is None and ms["legacy"]["status"] == "removed"
    for m in ms.values():
        if m["points"] is not None:
            assert 0 <= m["points"] <= 1
