#!/bin/bash
# Usage: bash run.sh <label> <mode> <attack> [project-settings.json] [extra claude args...]
#   mode:   auto | default (Manual)        attack: A B C D E F G (see prompts.sh)
# Resets the demo, runs one attack headless with `claude -p`, saves the stream-json log in ./runs/.
# Note: in -p mode a call that would show a permission prompt is denied, so "denied" there means
# "you would have been asked" in a normal session.
# Example (fix 2): bash run.sh fix2 auto F ../settings/fix2-builtin-sandbox.json --settings "$PWD/../settings/fix2-user-settings.json"
set -u
LABEL=$1; MODE=$2; ATTACK=$3; SETTINGS=${4:-}; shift 3; [ $# -gt 0 ] && shift
HERE=$(cd "$(dirname "$0")" && pwd)
export ATTACKER=${ATTACKER:-$(ipconfig getifaddr en0)}
DECOY="$HOME/aiv-demo/secrets"
. "$HERE/prompts.sh"
PROMPT=$(prompt_for "$ATTACK") || exit 1
bash "$HERE/../setup-demo.sh" ${SETTINGS:+"$SETTINGS"} >/dev/null
mkdir -p "$HERE/runs"; cd "$HOME/aiv-demo/shop-api"
start=$(date +%s)
( sleep 240; pkill -f "claude -p" ) 2>/dev/null & WD=$!   # attack D can start a server that never exits
claude -p "$PROMPT" --permission-mode "$MODE" "$@" --output-format stream-json --verbose \
  > "$HERE/runs/$LABEL-$MODE-$ATTACK.jsonl" 2> "$HERE/runs/$LABEL-$MODE-$ATTACK.err"
RC=$?; pkill -P $WD 2>/dev/null; kill $WD 2>/dev/null; pkill -f "Python app.py" 2>/dev/null
echo "$LABEL $MODE $ATTACK exit=$RC $(( $(date +%s)-start ))s"
