# 001: What AI coding really costs per month

`split_usage.py` prices your local [Claude Code](https://code.claude.com) usage at Anthropic's API list
prices and splits it into **your own sessions** vs **subagents**.

- Reads only usage metadata (token counts, model, timestamp, subagent flag) from `~/.claude/projects`.
- Never sends anything anywhere. Standard library only, Python 3.9+.
- Prints project names only if you pass `--projects` (keep it off when sharing your screen).

## Run it

```bash
python3 split_usage.py                      # last 30 days
python3 split_usage.py --since 2026-10-01 --until 2026-11-06
```

Output: cost per day (main / sub), totals, active days, and token counts with the cache-read share.

The video used the second command. My result: `TOTAL main $1409.82  sub $1704.09  all $3113.91`, 24 active
days, which is about $2,500 a month. [ccusage](https://github.com/ccusage/ccusage) landed within 0.3% of it.

## How it counts

- One API response is logged as several lines; the script keeps one per (message id, request id), the one
  with the final output count, so nothing is counted twice.
- A request counts as a subagent if it's in a `subagents/` log or marked `isSidechain`.
- Prices (USD per million tokens) are in `PRICES` at the top of the file: input, output, cache write
  (5-minute and 1-hour TTL) and cache read, per model. Models not in the table are skipped and listed at
  the end. Update the table if prices change or you use other models.

The "cost" is what your usage would cost at API list prices. On a Pro/Max/Ultra plan you pay the flat fee.

## License

MIT
