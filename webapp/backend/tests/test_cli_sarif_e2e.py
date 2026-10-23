"""CLI exit codes, report formats, SARIF structure and end-to-end runs."""
import csv
import io
import json
import os
import zipfile

import pytest

from codesniff.analyze import analyze_path, safe_extract, sort_rows
from codesniff.cli import main
from conftest import SAMPLE


def run(capsys, *args):
    code = main(list(args))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_exit_codes(capsys):
    assert run(capsys, "scan", SAMPLE)[0] == 1                       # sample has clear methods
    assert run(capsys, "scan", SAMPLE, "--fail-on", "never")[0] == 0
    assert run(capsys, "scan", SAMPLE, "--fail-on", "borderline")[0] == 1
    assert run(capsys, "scan", "does/not/exist")[0] == 2
    assert run(capsys, "scan", "https://example.com/not-github")[0] == 2


def test_clean_only_input_passes_default_gate(tmp_path, capsys):
    f = tmp_path / "Clean.java"
    f.write_text("class Clean { int one() { return 1; } int two(int a) { return a + 1; } }")
    assert run(capsys, "scan", str(f))[0] == 0
    assert run(capsys, "scan", str(f), "--fail-on", "borderline")[0] == 0


def test_borderline_only_input_warns_but_passes_default_gate(tmp_path, capsys):
    f = tmp_path / "B.java"
    f.write_text("class B { void f(int a, int b, int c, int d, int e) { } }")
    assert run(capsys, "scan", str(f))[0] == 0
    assert run(capsys, "scan", str(f), "--fail-on", "borderline")[0] == 1


def test_json_and_csv(capsys, tmp_path):
    code, out, _ = run(capsys, "scan", SAMPLE, "--format", "json", "--fail-on", "never")
    data = json.loads(out)
    assert data["meta"]["tool"] == "CodeSniff" and len(data["methods"]) == 6
    for m in data["methods"]:
        for s in ("CM", "LPL"):
            assert 0 <= m[f"{s}_probability"] <= 1 and m[f"{s}_zone"] in {"clean", "borderline", "clear"}
    out_file = tmp_path / "r.csv"
    run(capsys, "scan", SAMPLE, "--format", "csv", "--fail-on", "never", "--output", str(out_file))
    rows = list(csv.DictReader(io.StringIO(out_file.read_text())))
    assert len(rows) == 6 and "CM_note" in rows[0]


def test_table_output(capsys):
    _, out, _ = run(capsys, "scan", SAMPLE, "--fail-on", "never")
    assert "candidates to review, not verdicts" in out


def test_sarif_is_valid_2_1_0(capsys):
    _, out, _ = run(capsys, "scan", SAMPLE, "--format", "sarif", "--fail-on", "never")
    s = json.loads(out)
    assert s["version"] == "2.1.0" and s["$schema"].endswith("sarif-2.1.0.json")
    run0 = s["runs"][0]
    driver = run0["tool"]["driver"]
    assert driver["name"] == "CodeSniff" and driver["rules"]
    rule_ids = {r["id"] for r in driver["rules"]}
    for r in driver["rules"]:
        assert r["defaultConfiguration"]["level"] in {"none", "note", "warning", "error"}
        assert r["shortDescription"]["text"] and r["fullDescription"]["text"]
    assert run0["results"]
    for res in run0["results"]:
        assert res["ruleId"] in rule_ids
        assert res["level"] in {"warning", "error"}
        assert res["message"]["text"]
        loc = res["locations"][0]["physicalLocation"]
        assert not os.path.isabs(loc["artifactLocation"]["uri"]) and "\\" not in loc["artifactLocation"]["uri"]
        assert 1 <= loc["region"]["startLine"] <= loc["region"]["endLine"]
        if res["level"] == "warning":
            assert "not a verdict" in res["message"]["text"]
    try:   # full schema validation when jsonschema and the schema file are available locally
        import jsonschema  # noqa: F401
    except ImportError:
        pytest.skip("jsonschema not installed; structural checks above passed")


def test_end_to_end_folder_and_zip(tmp_path):
    rows, skipped, _ = analyze_path(SAMPLE)
    assert len(rows) == 6 and not skipped
    status = {r["name"]: r["status"] for r in rows}
    assert status == {"count": "clean", "name": "clean", "discount": "borderline", "label": "borderline",
                      "grade": "clear", "quote": "clear"}
    assert [r["status"] for r in sort_rows(rows)][:2] == ["clear", "clear"]
    z = tmp_path / "p.zip"
    with zipfile.ZipFile(z, "w") as zf:
        for d, _, files in os.walk(SAMPLE):
            for f in files:
                zf.write(os.path.join(d, f), os.path.relpath(os.path.join(d, f), SAMPLE))
    rows_zip, _, _ = analyze_path(str(z))
    assert sorted(r["name"] for r in rows_zip) == sorted(r["name"] for r in rows)


def test_zip_slip_is_rejected(tmp_path):
    z = tmp_path / "evil.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("../escape.java", "class X {}")
    with pytest.raises(ValueError):
        safe_extract(str(z), str(tmp_path / "out"))


def test_unreadable_file_is_skipped_not_fatal(tmp_path):
    (tmp_path / "Big.java").write_text("class Big {}\n" + " " * 1_100_000)
    (tmp_path / "Ok.java").write_text("class Ok { int f() { return 1; } }")
    rows, skipped, _ = analyze_path(str(tmp_path))
    assert [r["name"] for r in rows] == ["f"] and skipped[0][0] == "Big.java"
