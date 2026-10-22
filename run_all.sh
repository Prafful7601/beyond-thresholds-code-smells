#!/usr/bin/env bash
# Regenerate every table, figure and results/results.md from scratch.
# Usage: bash run_all.sh   (from paper3/)
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
PY="$ROOT/.venv/bin/python"
LOGS="$ROOT/results/logs"
# xgboost needs an OpenMP runtime; reuse the libomp bundled with scikit-learn (no system install needed)
export DYLD_LIBRARY_PATH="$ROOT/.venv/lib/python3.9/site-packages/sklearn/.dylibs${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
mkdir -p "$LOGS" data/raw data/db data/cache results/tables results/figures results/fragments results/error_analysis

if [ ! -x "$PY" ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt
fi

# 1. data (Zenodo record 7570428), checksum-verified
declare -a FILES=("DACOSMain.sql:30fe42bd366da825908e86d901702b79"
                  "DACOSExtended.sql:081b9725362b34a78e18de303aa35fb2"
                  "files.zip:d38d4a2526123c66f6b30e871e50cd4c"
                  "contributors.txt:453d08349206d1d99822f2e23e72f9f6")
for entry in "${FILES[@]}"; do
  f="${entry%%:*}"; sum="${entry##*:}"
  if [ ! -f "data/raw/$f" ]; then
    curl -sL -o "data/raw/$f" "https://zenodo.org/api/records/7570428/files/$f/content"
  fi
  got=$( (md5 -q "data/raw/$f" 2>/dev/null) || md5sum "data/raw/$f" | cut -d' ' -f1)
  [ "$got" = "$sum" ] || { echo "MD5 mismatch for $f: $got != $sum"; exit 1; }
done

# 1b. external C# dataset (Zenodo record 10475432, Prokić et al. 2024), checksum-verified; used for the B0 audit only
mkdir -p data/external/csharp
declare -a XFILES=("DataSet_Data_Class.xlsx:7e6446de483b4166202ccae1f2d76311"
                   "DataSet_Feature_Envy.xlsx:94e29c01288472a5232b34a02be46262"
                   "DataSet_Refused_Bequest.xlsx:11330c613e921003450f3c62d384d57f"
                   "Data_Class_Heuristics.xlsx:c719dbcbecedb10908fdfa508e718c8c"
                   "Feature_Envy_Heuristics.xlsx:0f8cf3d1b3df28f8ec2c1a4e4622c48a"
                   "Refused_Bequest_Heuristics.xlsx:ef740b048a1a2a76df3ef2c5cef3185f")
for entry in "${XFILES[@]}"; do
  f="${entry%%:*}"; sum="${entry##*:}"
  if [ ! -f "data/external/csharp/$f" ]; then
    curl -sL -o "data/external/csharp/$f" "https://zenodo.org/api/records/10475432/files/$f/content"
  fi
  got=$( (md5 -q "data/external/csharp/$f" 2>/dev/null) || md5sum "data/external/csharp/$f" | cut -d' ' -f1)
  [ "$got" = "$sum" ] || { echo "MD5 mismatch for $f: $got != $sum"; exit 1; }
done

: > "$LOGS/runtime.tsv"
step () {
  local name="$1"; shift
  local t0=$(date +%s)
  echo ">> $name"
  "$@" > "$LOGS/$name.log" 2>&1 || { echo "step $name failed, see $LOGS/$name.log"; tail -20 "$LOGS/$name.log"; exit 1; }
  echo -e "$name\t$(( $(date +%s) - t0 ))" >> "$LOGS/runtime.tsv"
}

step convert_main     "$PY" -I src/convert_sql.py data/raw/DACOSMain.sql data/db/dacos_main.sqlite
step convert_extended "$PY" -I src/convert_sql.py data/raw/DACOSExtended.sql data/db/dacos_ext.sqlite
step audit            "$PY" -I src/audit.py "$ROOT"
step features         "$PY" -I src/features.py
step dataset_audit    "$PY" -I src/dataset_audit.py
step rq1              "$PY" -I src/rq1.py
step rq2              "$PY" -I src/rq2.py
step rq4              "$PY" -I src/rq4.py
step rq3              "$PY" -I src/rq3.py
step rq5              "$PY" -I src/rq5.py
step robustness       "$PY" -I src/robustness.py
step run_anatomy      "$PY" -I src/run_anatomy.py
step step3_A_B        "$PY" -I src/step3_ab.py
step step3_C          "$PY" -I src/step3_c.py
step step3_E          "$PY" -I src/step3_e.py
step step3_D          "$PY" -I src/step3_d.py
step step3_F_H        "$PY" -I src/step3_fh.py
step step3_G_I_J      "$PY" -I src/step3_gij.py
step step3_R5         "$PY" -I src/step3_r5.py
step human_ceiling    "$PY" -I src/human_ceiling.py
step extras           "$PY" -I src/extras.py
step range_restrict   "$PY" -I src/range_restriction.py
step external_B0      "$PY" -I src/external_audit.py
step agreement        "$PY" -I src/agreement_anatomy.py
step external_B1      "$PY" -I src/external_b1.py
cp src/s6_deviations.md results/fragments/s6_deviations.md
step build_report     "$PY" -I src/build_report.py
step paper_figures    "$PY" -I src/paper_figures.py
echo "done: results/results.md"
