#!/bin/bash
# Usage: ./run-sbx.sh <label> <attack>
# Runs one attack inside a Docker Sandbox named aiv-demo (create it once from ~/aiv-demo/shop-api with
# `sbx run --name aiv-demo claude`, log in to Claude inside, then exit). Claude runs there with
# --dangerously-skip-permissions, the sandbox default. Pick the network preset with `sbx policy`.
set -u
LABEL=$1; ATTACK=$2
HERE=$(cd "$(dirname "$0")" && pwd)
export ATTACKER=${ATTACKER:-$(ipconfig getifaddr en0)}
DECOY="$HOME/aiv-demo/secrets"
. "$HERE/prompts.sh"
PROMPT=$(prompt_for "$ATTACK") || exit 1
"$HERE/../setup-demo.sh" >/dev/null
mkdir -p "$HERE/runs"
start=$(date +%s)
( sleep 300; pkill -f "sbx exec aiv-demo" ) 2>/dev/null & WD=$!
sbx exec aiv-demo sh -c "cd \"$HOME/aiv-demo/shop-api\" && claude -p \"\$0\" --dangerously-skip-permissions --output-format stream-json --verbose" "$PROMPT" \
  > "$HERE/runs/$LABEL-sbx-$ATTACK.jsonl" 2> "$HERE/runs/$LABEL-sbx-$ATTACK.err"
RC=$?; kill $WD 2>/dev/null
echo "$LABEL sbx $ATTACK exit=$RC $(( $(date +%s)-start ))s"
