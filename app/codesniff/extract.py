"""Method extraction and feature computation for Java source.

* Methods with a body are found with lizard (1.17.13).
* Declarations without a body (interface / abstract methods, which matter for Long Parameter List) are invisible
  to lizard; a small lexer-based fallback finds them at class-body level.
* cc: lizard counts `&&` and `||` as decision points, DesigniteJava (the paper's metric) does not. CodeSniff
  reports both `cc_lizard` and the DesigniteJava-compatible `cc` = lizard cc minus the number of `&&`/`||`
  operators outside strings and comments (floored at 1). On DACOS method snippets this raises exact agreement
  with the stored DesigniteJava value from 0.50 to 0.77 (see app/models/lizard_agreement.json).
* pc: counted from the declaration's parameter list (top-level commas, generics-aware).
* loc: lizard NLOC (non-blank, non-comment lines); for bodiless declarations, non-blank lines after stripping
  comments.
* statements, max_nesting, method_calls, comment_ratio, mean_identifier_length: src/features.py `compute`,
  unchanged, exactly as in the paper.
"""
import dataclasses
import re

import lizard

from .resources import paper_features

TYPE_DECL = re.compile(r"\b(class|interface|enum|record)\s+[A-Za-z_$][\w$]*")
WRAPPER = "class __CodeSniffSnippet__ {"
KEYWORDS_BEFORE_CALL = {"return", "new", "throw", "else", "case", "assert", "yield"}
BODILESS = re.compile(
    r"(?:(?<=[;{}\n])|^)[ \t]*(?P<head>[A-Za-z_$@<][\w$<>\[\]?.,@ \t]*?)[ \t\n]+(?P<name>[A-Za-z_$][\w$]*)[ \t\n]*\("
    r"(?P<params>[^;{}()]*(?:\([^;{}()]*\)[^;{}()]*)*)\)[ \t\n]*(?:throws[ \t\n]+[\w$.,<> \t\n]+)?;", re.M)


@dataclasses.dataclass
class Method:
    file: str
    name: str
    start_line: int
    end_line: int
    has_body: bool
    code: str
    cc_lizard: int
    cc: int
    pc: int
    loc: int
    statements: int
    max_nesting: int
    method_calls: int
    comment_ratio: float
    mean_identifier_length: float

    def as_dict(self):
        return dataclasses.asdict(self)


def count_params(param_text):
    """Number of parameters in a Java parameter list (text between the parentheses, comments removed)."""
    depth, parts, cur = 0, [], ""
    for ch in param_text:
        if ch in "<([":
            depth += 1
        elif ch in ">)]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return sum(1 for p in parts if p.strip())


def _signature_params(stripped_method, name=None):
    """Parameter-list text of the declaration of `name` (else the first parenthesis) in a stripped method text."""
    m = re.search(r"\b" + re.escape(name) + r"\s*\(", stripped_method) if name else None
    i = (m.end() - 1) if m else stripped_method.find("(")
    if i < 0:
        return ""
    depth = 0
    for j in range(i, len(stripped_method)):
        c = stripped_method[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return stripped_method[i + 1:j]
    return stripped_method[i + 1:]


def _features(code):
    f = paper_features()
    statements, max_nesting, comment_ratio, calls, mean_id = f.compute(code, False)
    stripped = f.strip(code)[0]
    return stripped, dict(statements=int(statements), max_nesting=int(max_nesting), method_calls=int(calls),
                          comment_ratio=float(comment_ratio), mean_identifier_length=float(mean_id))


def _wrap(text):
    stripped = paper_features().strip(text)[0]
    if TYPE_DECL.search(stripped):
        return text, 0
    return WRAPPER + "\n" + text + "\n}", 1


def extract_methods(text, filename="Snippet.java"):
    """All methods (with and without body) in a Java compilation unit or a bare method snippet."""
    src, offset = _wrap(text)
    lines = src.split("\n")
    info = lizard.analyze_file.analyze_source_code(filename if filename.endswith(".java") else filename + ".java", src)
    out, covered = [], set()
    for fn in info.function_list:
        s, e = fn.start_line, fn.end_line
        code = "\n".join(lines[s - 1:e])
        covered.update(range(s, e + 1))
        stripped, feats = _features(code)
        andor = len(re.findall(r"&&|\|\|", stripped))
        name = fn.name.split("::")[-1]
        out.append(Method(file=filename, name=name, start_line=s - offset, end_line=e - offset,
                          has_body=True, code=code, cc_lizard=int(fn.cyclomatic_complexity),
                          cc=max(1, int(fn.cyclomatic_complexity) - andor),
                          pc=count_params(_signature_params(stripped, name)), loc=int(fn.nloc), **feats))
    # bodiless declarations outside lizard functions
    stripped_src = paper_features().strip(src)[0]
    masked = "\n".join(l if (k + 1) not in covered else " " * len(l) for k, l in enumerate(stripped_src.split("\n")))
    for m in BODILESS.finditer(masked):
        head = m.group("head").split()
        if not head or head[-1] in KEYWORDS_BEFORE_CALL or m.group("name") in KEYWORDS_BEFORE_CALL:
            continue
        if any(t in KEYWORDS_BEFORE_CALL for t in head) or "=" in m.group("head"):
            continue
        s = masked.count("\n", 0, m.start("head")) + 1
        e = masked.count("\n", 0, m.end()) + 1
        code = "\n".join(lines[s - 1:e])
        _, feats = _features(code)
        loc = sum(1 for l in masked.split("\n")[s - 1:e] if l.strip())
        out.append(Method(file=filename, name=m.group("name"), start_line=s - offset, end_line=e - offset,
                          has_body=False, code=code, cc_lizard=1, cc=1, pc=count_params(m.group("params")),
                          loc=loc, **feats))
    return sorted(out, key=lambda m: m.start_line)
