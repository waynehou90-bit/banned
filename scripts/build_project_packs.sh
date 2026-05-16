#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${BHA_DB_PATH:-db/bha.sqlite}"
INCLUDE_TXT="${INCLUDE_TXT:-0}"
PACKS="${PACKS:-}"

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python scripts/sync_source.py --branch json --target data/raw
python scripts/init_db.py --db "$DB_PATH"
python scripts/ingest_json.py --input data/raw/json --db "$DB_PATH"

if [[ "$INCLUDE_TXT" == "1" ]]; then
  python scripts/sync_source.py --branch txt --target data/raw
  python scripts/ingest_text.py --input data/raw/txt --db "$DB_PATH"
fi

if [[ -n "$PACKS" ]]; then
  # shellcheck disable=SC2086
  python scripts/export_default_packs.py --db "$DB_PATH" --only $PACKS
else
  python scripts/export_default_packs.py --db "$DB_PATH"
fi

echo ""
echo "Done. Review project_sources/, then run:"
echo "  git add project_sources && git commit -m 'Add default BHA Project source packs' && git push"
