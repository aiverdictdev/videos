# 006: Why Your Claude Code Limit Dies So Fast

Video: https://youtu.be/8qJZtH6WxU8

`split_usage.py` reads only the usage metadata Claude Code stores locally in `~/.claude/projects` (token counts, model,
timestamp, whether a request came from a subagent) and prices it at Anthropic's API list rates. It sends nothing
anywhere and prints no project names unless you pass `--projects`.

It is the same script as in `001-ai-coding-costs`, plus a `--bytype` flag that splits your bill by what you were paying
for: fresh input, output (the answers, thinking included), cache writes (saving the conversation) and cache reads
(re-reading it). It also prints what your cache reads would have cost at the full input price, which is what prompt
caching saved you.

```bash
python3 split_usage.py                       # last 30 days
python3 split_usage.py --bytype              # + split by token type and model
python3 split_usage.py --since 2026-10-01 --until 2026-11-06 --bytype   # the window used in the video
```

My numbers in the video (Oct 1 to Nov 6, 2026, 24 active days): 6,566,676,358 tokens, $3,045.89 at list prices.
Cache reads were 94.7% of the tokens; cache writes were the biggest share of the cost (38.2%); the answers were 1.2% of
the tokens and 26.4% of the cost; subagents cost more than my own sessions ($1,636 vs $1,410). Without caching, the
same work would have cost about $24,284.

Prices are in the `PRICES` table at the top of the script (checked 2026-11-13). Update them if Anthropic changes its
pricing. If you're on a Pro or Max plan you don't pay these amounts; they show what your usage would cost on the API,
which is the same meter your plan's limits are based on.
