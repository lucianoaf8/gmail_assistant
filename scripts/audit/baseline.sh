#!/usr/bin/env bash
#
# Captures baseline measurements and writes JSON atomically.
# Fixed: uses find -prune for proper exclusion.
#
set -euo pipefail

OUTPUT_DIR="${1:-docs/audit}"

# Ensure we're in repo root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "Error: Not in a git repository" >&2
    exit 1
}
cd "$REPO_ROOT"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Timestamp and commit
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
FILE_TIMESTAMP="$(date +"%Y%m%d-%H%M")"
COMMIT_SHA="$(git rev-parse HEAD)"

# Fixed: Use -prune for proper exclusion (doesn't traverse excluded dirs)
get_max_folder_depth() {
    find . \( \
        -name .git -o \
        -name __pycache__ -o \
        -name node_modules -o \
        -name backups -o \
        -name .venv -o \
        -name venv -o \
        -name .pytest_cache -o \
        -name .mypy_cache -o \
        -name .ruff_cache -o \
        -name htmlcov -o \
        -name dist -o \
        -name build -o \
        -name '*.egg-info' \
    \) -prune -o -type d -print 2>/dev/null | \
        awk -F/ '{print NF-1}' | \
        sort -rn | \
        head -1
}

get_sys_path_insert_count() {
    find . \( \
        -name .git -o \
        -name __pycache__ -o \
        -name .venv -o \
        -name venv \
    \) -prune -o -name "*.py" -print 2>/dev/null | \
        xargs grep -l 'sys\.path\.\(insert\|append\)' 2>/dev/null | \
        wc -l | \
        tr -d '[:space:]'
}

get_config_location_count() {
    local count=0
    for dir in "config/app" "config/analysis" "src/analysis"; do
        [[ -d "$dir" ]] && ((count++)) || true
    done
    echo "$count"
}

get_python_file_count() {
    [[ -d "src" ]] || { echo 0; return; }
    find src \( -name __pycache__ -o -name .venv \) -prune -o \
        -name "*.py" -print 2>/dev/null | wc -l | tr -d '[:space:]'
}

get_test_file_count() {
    [[ -d "tests" ]] || { echo 0; return; }
    find tests \( -name __pycache__ -o -name .pytest_cache \) -prune -o \
        -name "test_*.py" -print 2>/dev/null | wc -l | tr -d '[:space:]'
}

get_entry_point_count() {
    local count=0
    [[ -f "main.py" ]] && ((count++)) || true
    [[ -f "src/cli/main.py" ]] && ((count++)) || true
    echo "$count"
}

get_hidden_docs_count() {
    [[ -d "docs/claude-docs" ]] || { echo 0; return; }
    find docs/claude-docs -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l | tr -d '[:space:]'
}

# Collect measurements
echo "Collecting measurements..."

MAX_DEPTH=$(get_max_folder_depth)
SYS_PATH_COUNT=$(get_sys_path_insert_count)
CONFIG_LOCS=$(get_config_location_count)
PY_FILES=$(get_python_file_count)
TEST_FILES=$(get_test_file_count)
ENTRY_POINTS=$(get_entry_point_count)
HIDDEN_DOCS=$(get_hidden_docs_count)

# Build JSON atomically
OUTPUT_FILE="$OUTPUT_DIR/${FILE_TIMESTAMP}_baseline.json"
TEMP_FILE="$(mktemp)"

trap 'rm -f "$TEMP_FILE"' EXIT

cat > "$TEMP_FILE" << EOF
{
  "schema_version": "1.0",
  "timestamp": "$TIMESTAMP",
  "commit_sha": "$COMMIT_SHA",
  "repo_root": "$REPO_ROOT",
  "measurements": {
    "max_folder_depth": $MAX_DEPTH,
    "sys_path_inserts": $SYS_PATH_COUNT,
    "config_locations": $CONFIG_LOCS,
    "python_source_files": $PY_FILES,
    "test_files": $TEST_FILES,
    "entry_points": $ENTRY_POINTS,
    "hidden_docs": $HIDDEN_DOCS
  },
  "targets": {
    "max_folder_depth": 3,
    "sys_path_inserts": 0,
    "config_locations": 1,
    "entry_points": 1,
    "hidden_docs": 0
  }
}
EOF

# Validate JSON before moving
python3 -c "import json; json.load(open('$TEMP_FILE'))" || {
    echo "Error: Generated invalid JSON" >&2
    exit 1
}

mv "$TEMP_FILE" "$OUTPUT_FILE"
trap - EXIT

echo "Baseline written to: $OUTPUT_FILE"
echo ""
echo "Measurements vs Targets:"

check_metric() {
    local name="$1" value="$2" target="$3"
    if [[ "$value" -le "$target" ]]; then
        echo "  [PASS] $name: $value (target: $target)"
    else
        echo "  [FAIL] $name: $value (target: $target)"
    fi
}

check_metric "max_folder_depth" "$MAX_DEPTH" 3
check_metric "sys_path_inserts" "$SYS_PATH_COUNT" 0
check_metric "config_locations" "$CONFIG_LOCS" 1
echo "  [INFO] python_source_files: $PY_FILES"
echo "  [INFO] test_files: $TEST_FILES"
check_metric "entry_points" "$ENTRY_POINTS" 1
check_metric "hidden_docs" "$HIDDEN_DOCS" 0

exit 0
