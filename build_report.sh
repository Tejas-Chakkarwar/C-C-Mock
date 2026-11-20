#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "report build failed: Python executable not found: $PYTHON_BIN" >&2
    exit 1
fi
for tool in pdfinfo pdftotext pdftoppm; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "report build failed: required PDF tool is missing: $tool" >&2
        exit 1
    fi
done

"$PYTHON_BIN" "$ROOT_DIR/scripts/build_report.py"
"$PYTHON_BIN" "$ROOT_DIR/scripts/verify_report.py" --pdf "$ROOT_DIR/report/report.pdf"
