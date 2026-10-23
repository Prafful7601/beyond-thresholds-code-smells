"""Feature extraction on hand-written Java with known cc and pc."""
import pytest

from codesniff.extract import count_params, extract_methods


def one(code, name=None):
    ms = extract_methods(code)
    if name:
        ms = [m for m in ms if m.name == name]
    assert len(ms) == 1, [m.name for m in ms]
    return ms[0]


@pytest.mark.parametrize("body, cc", [
    ("return a;", 1),
    ("if (a > 0) { return 1; } return 0;", 2),
    ("if (a > 0 && b > 0) { return 1; } return 0;", 2),          # && is not a decision (DesigniteJava convention)
    ("if (a > 0 || b > 0) { return 1; } return 0;", 2),
    ("for (int i = 0; i < a; i++) { b++; } while (b > 0) { b--; } return b;", 3),
    ("return a > b ? a : b;", 2),
    ("switch (a) { case 1: return 1; case 2: return 2; default: return 0; }", 3),
    ("try { return a / b; } catch (ArithmeticException e) { return 0; }", 2),
])
def test_cc_designite_compatible(body, cc):
    m = one(f"int f(int a, int b) {{ {body} }}")
    assert m.cc == cc
    assert m.cc_lizard >= m.cc


def test_cc_raw_lizard_counts_boolean_operators():
    m = one("int f(int a, int b) { if (a > 0 && b > 0 || a < -1) { return 1; } return 0; }")
    assert m.cc == 2 and m.cc_lizard == 4


@pytest.mark.parametrize("sig, pc", [
    ("void f()", 0),
    ("void f(int a)", 1),
    ("void f(int a, String b, double c)", 3),
    ("void f(Map<String, List<Integer>> m, int x)", 2),
    ("void f(int... values)", 1),
    ("void f(final @Nonnull String a, int[] b)", 2),
    ("<T extends Comparable<T>> T max(List<T> xs, Comparator<? super T> c)", 2),
])
def test_pc(sig, pc):
    m = one(sig + " { }")
    assert m.pc == pc


def test_count_params_direct():
    assert count_params("") == 0
    assert count_params("Map<String, Integer> m, Function<A, B> f, int x") == 3


def test_bodiless_declarations_found():
    code = """public interface Repo<T> {
  List<T> find(String a, Map<String, List<Integer>> b, int... c);
  <R> R map(Function<T, R> f, R fallback) throws java.io.IOException;
  default int size() { return 0; }
}"""
    ms = {m.name: m for m in extract_methods(code, "Repo.java")}
    assert set(ms) == {"find", "map", "size"}
    assert ms["find"].pc == 3 and not ms["find"].has_body
    assert ms["map"].pc == 2 and not ms["map"].has_body
    assert ms["size"].has_body


def test_calls_and_fields_are_not_declarations():
    code = """abstract class A {
  int x = compute(1, 2);
  List<String> xs = new ArrayList<>(10);
  abstract void run(int a);
  void g() { foo(1, 2); return; }
}"""
    names = sorted(m.name for m in extract_methods(code))
    assert names == ["g", "run"]


def test_bare_snippet_line_numbers_and_features():
    code = "public int f(int a) {\n  // comment\n  if (a > 1) {\n    return helper(a);\n  }\n  return a;\n}"
    m = one(code)
    assert (m.start_line, m.end_line) == (1, 7)
    assert m.cc == 2 and m.pc == 1
    assert m.method_calls == 1 and m.max_nesting == 1 and m.comment_ratio > 0


def test_enum_constructor_pc_uses_declaration_not_constants():
    m = one("class C { enum E { A(1, 2), B(3); E(int x) { } } }", "E")
    assert m.pc == 1


def test_sample_project_known_values():
    import os
    from conftest import SAMPLE
    path = os.path.join(SAMPLE, "src/main/java/demo/OrderService.java")
    ms = {m.name: m for m in extract_methods(open(path).read(), "OrderService.java")}
    assert (ms["count"].cc, ms["count"].pc) == (1, 1)
    assert (ms["discount"].cc, ms["discount"].pc) == (6, 2)
    assert ms["label"].pc == 5
    assert ms["grade"].cc == 16
