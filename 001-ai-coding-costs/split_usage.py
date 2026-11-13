"""Price your local Claude Code usage at API list rates, split into main sessions vs subagents.

Reads only usage metadata (tokens, model, timestamp, isSidechain) from ~/.claude/projects;
never sends anything anywhere.

Usage:
  python3 split_usage.py [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--projects]

Defaults to the last 30 days (local time). The AiVerdict video used
  python3 split_usage.py --since 2026-10-01 --until 2026-11-06

Per-project totals are printed only with --projects, because project folder names can be
private (keep it off when sharing your screen).

Prices: USD per million tokens, Anthropic API list prices (checked 2026-11-07; Sonnet 5.5 cache
reads were cut from $0.20 to $0.10 on 2026-10-08).
Cache writes: 1.25x input for the 5-minute TTL, 2x input for the 1-hour TTL; cache reads as
listed per model (Anthropic prompt-caching docs). Update PRICES if prices change.
"""
import argparse, collections, glob, json, os
from datetime import date, datetime, timedelta

ROOT = os.path.expanduser("~/.claude/projects")

# model: (input, output, cache write 5m, cache write 1h, cache read)
PRICES = {
    "claude-opus-5-5": (4.00, 20.00, 5.00, 8.00, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 4.00, 0.10),
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.20, 0.01),
    "claude-fable-5-1": (10.00, 50.00, 12.50, 20.00, 0.25),
}


def main():
    ap = argparse.ArgumentParser()
    today = date.today()
    ap.add_argument("--since", default=(today - timedelta(days=29)).isoformat(), help="first day included")
    ap.add_argument("--until", default=today.isoformat(), help="last day included")
    ap.add_argument("--projects", action="store_true", help="also print per-project totals")
    ap.add_argument("--bytype", action="store_true", help="also split tokens and cost by token type and model (video 006)")
    args = ap.parse_args()

    # One API response is logged as several lines (one per content block); keep the line
    # with the final (largest) output count per (message id, request id).
    best = {}
    unknown_models = collections.Counter()

    for path in glob.glob(os.path.join(ROOT, "*", "**", "*.jsonl"), recursive=True):
        project = os.path.relpath(path, ROOT).split(os.sep)[0]
        is_sub_file = f"{os.sep}subagents{os.sep}" in path
        with open(path, errors="ignore") as fh:
            for line in fh:
                if '"usage"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if o.get("type") != "assistant":
                    continue
                m = o.get("message") or {}
                u = m.get("usage")
                ts = o.get("timestamp")
                if not u or not ts:
                    continue
                d = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d")
                if d < args.since or d > args.until:
                    continue
                model = m.get("model", "?")
                p = PRICES.get(model)
                if not p:
                    unknown_models[model] += 1
                    continue
                cc = u.get("cache_creation") or {}
                w5 = cc.get("ephemeral_5m_input_tokens")
                w1 = cc.get("ephemeral_1h_input_tokens")
                if w5 is None and w1 is None:
                    w5, w1 = u.get("cache_creation_input_tokens", 0), 0
                w5, w1 = w5 or 0, w1 or 0
                inp, out = u.get("input_tokens", 0), u.get("output_tokens", 0)
                cr = u.get("cache_read_input_tokens", 0)
                cost = (inp * p[0] + out * p[1] + w5 * p[2] + w1 * p[3] + cr * p[4]) / 1e6
                # Cost of each token type on its own (video 006 reads the bill line by line).
                parts = dict(input=inp * p[0] / 1e6, output=out * p[1] / 1e6,
                             cache_write=(w5 * p[2] + w1 * p[3]) / 1e6, cache_read=cr * p[4] / 1e6)
                kind = "sub" if (is_sub_file or o.get("isSidechain")) else "main"
                key = (m.get("id"), o.get("requestId"))
                prev = best.get(key)
                if prev is None or out > prev["out"]:
                    best[key] = dict(out=out, day=d, kind=kind, project=project, cost=cost,
                                     inp=inp, cw=w5 + w1, cr=cr, model=model, parts=parts)

    day = collections.defaultdict(collections.Counter)
    proj = collections.defaultdict(collections.Counter)
    tok = collections.defaultdict(collections.Counter)
    for r in best.values():
        day[r["day"]][r["kind"]] += r["cost"]
        proj[r["project"]][r["kind"]] += r["cost"]
        t = tok[r["kind"]]
        t["input"] += r["inp"]; t["output"] += r["out"]; t["cache_write"] += r["cw"]
        t["cache_read"] += r["cr"]; t["requests"] += 1

    tot = collections.Counter()
    for d in sorted(day):
        tot.update(day[d])
        print(f"{d}  main ${day[d]['main']:8.2f}  sub ${day[d]['sub']:8.2f}")
    print(f"TOTAL main ${tot['main']:.2f}  sub ${tot['sub']:.2f}  all ${tot['main'] + tot['sub']:.2f}")
    print("active days:", len(day))
    for kind in ("main", "sub"):
        t = tok[kind]
        allt = t["input"] + t["output"] + t["cache_write"] + t["cache_read"]
        print(kind, {k: f"{v:,}" for k, v in t.items()},
              f"cache-read share {t['cache_read'] / max(allt, 1) * 100:.1f}%")
    if args.bytype:
        # Tokens and cost per token type, overall and per model, plus what cache reads would have cost
        # at the full input price (the saving prompt caching makes).
        types = ("input", "output", "cache_write", "cache_read")
        bym = collections.defaultdict(lambda: (collections.Counter(), collections.Counter()))
        allt, allc = collections.Counter(), collections.Counter()
        for r in best.values():
            t, c = bym[r["model"]]
            for k, field in zip(types, ("inp", "out", "cw", "cr")):
                t[k] += r[field]; allt[k] += r[field]
                c[k] += r["parts"][k]; allc[k] += r["parts"][k]
        def show(label, t, c):
            tt, tc = sum(t[k] for k in types), sum(c[k] for k in types)
            print(f"  {label}: {tt:,} tokens, ${tc:,.2f}")
            for k in types:
                print(f"    {k:12s} {t[k]:>15,}  {t[k]/max(tt,1)*100:6.2f}% of tokens   "
                      f"${c[k]:10,.2f}  {c[k]/max(tc,1)*100:6.2f}% of cost")
        print("by token type (all models):")
        show("all", allt, allc)
        for model in sorted(bym, key=lambda m: -sum(bym[m][1].values())):
            t, c = bym[model]
            show(model, t, c)
            full = t["cache_read"] * PRICES[model][0] / 1e6
            print(f"    cache reads at full input price: ${full:,.2f} instead of ${c['cache_read']:,.2f} "
                  f"(saved ${full - c['cache_read']:,.2f})")
    if args.projects:
        print("per project (top):")
        for pth, c in sorted(proj.items(), key=lambda x: -(x[1]["main"] + x[1]["sub"]))[:6]:
            print(f"  {pth[-45:]:45s} main ${c['main']:8.2f} sub ${c['sub']:8.2f}")
    if unknown_models:
        print("unknown models skipped:", dict(unknown_models))


if __name__ == "__main__":
    main()
