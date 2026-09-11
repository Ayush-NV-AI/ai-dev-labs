#!/usr/bin/env bash
# Run the semgrep gate (.semgrep.yml) against every local branch except
# main, writing one JSON report per branch plus a combined summary table
# of findings by rule and by branch.
#
# A branch that cannot be checked out cleanly (dirty working tree
# conflicts, a branch that no longer exists, etc.) is skipped with a
# warning rather than aborting the whole run -- one bad branch must not
# hide the results for every other branch.
#
# Usage: scripts/scan_all_branches.sh [output-dir]
#   output-dir defaults to ./semgrep-reports

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || exit 1

OUT_DIR="${1:-semgrep-reports}"
mkdir -p "$OUT_DIR"

CONFIG=".semgrep.yml"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
SUMMARY_TSV="$OUT_DIR/summary.tsv"
printf 'branch\trule\tcount\n' > "$SUMMARY_TSV"

FAILED_BRANCHES=()

# Every local branch except main.
mapfile -t BRANCHES < <(git branch --format='%(refname:short)' | grep -v '^main$')

for branch in "${BRANCHES[@]}"; do
    echo "== Scanning branch: $branch =="

    if ! git checkout --quiet "$branch" 2>"$OUT_DIR/${branch//\//_}.checkout.err"; then
        echo "  SKIPPED: could not check out '$branch' cleanly (see ${branch//\//_}.checkout.err)"
        FAILED_BRANCHES+=("$branch")
        continue
    fi

    if [ ! -d src ]; then
        echo "  SKIPPED: no src/ directory on '$branch'"
        FAILED_BRANCHES+=("$branch")
        continue
    fi

    json_out="$OUT_DIR/${branch//\//_}.json"
    if ! semgrep --config "$CONFIG" --json --output "$json_out" src/ 2>"$OUT_DIR/${branch//\//_}.semgrep.err"; then
        echo "  WARNING: semgrep exited non-zero on '$branch' (see ${branch//\//_}.semgrep.err); report may be partial"
    fi

    if [ -f "$json_out" ]; then
        python3 - "$branch" "$json_out" "$SUMMARY_TSV" <<'PY'
import json
import sys
from collections import Counter

branch, json_path, summary_path = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
except (OSError, json.JSONDecodeError) as exc:
    print(f"  WARNING: could not parse {json_path}: {exc}")
    sys.exit(0)

counts = Counter(r.get("check_id", "unknown") for r in data.get("results", []))
with open(summary_path, "a", encoding="utf-8") as f:
    if not counts:
        f.write(f"{branch}\t(none)\t0\n")
    for rule, count in sorted(counts.items()):
        f.write(f"{branch}\t{rule}\t{count}\n")
PY
    fi
done

git checkout --quiet "$CURRENT_BRANCH"

echo
echo "== Combined summary (also written to $SUMMARY_TSV) =="
column -t -s "$(printf '\t')" "$SUMMARY_TSV" 2>/dev/null || cat "$SUMMARY_TSV"

if [ "${#FAILED_BRANCHES[@]}" -gt 0 ]; then
    echo
    echo "Branches skipped (did not scan cleanly): ${FAILED_BRANCHES[*]}"
fi

echo
echo "Per-branch JSON reports and any errors are in: $OUT_DIR/"
