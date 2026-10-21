#!/usr/bin/env bash
# Regenerate every table, figure and results/results.md from scratch.
# Usage: bash run_all.sh   (from paper3/)
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
PY="$ROOT/.venv/bin/python"
LOGS="$ROOT/results/logs"
mkdir -p "$LOGS" data/raw data/db results/tables results/figures results/fragments

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
cp src/s6_deviations.md results/fragments/s6_deviations.md
step build_report     "$PY" -I src/build_report.py
echo "done: results/results.md"
