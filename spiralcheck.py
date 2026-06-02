#!/usr/bin/env python3
"""
spiralcheck.py — a smoke detector for LLM confabulation spirals.

Paste in a model's output (or a transcript) and it flags surface patterns that
often accompany a confabulation spiral. It is a HEURISTIC AID, not a judge:

  * A flag is a prompt for YOUR review, not proof of anything.
  * A clean scan does NOT mean you're safe — the subtlest spirals use none of
    these patterns. Read the output, then decide for yourself.

Usage:
    python spiralcheck.py transcript.txt
    cat reply.txt | python spiralcheck.py

Zero dependencies. Pure standard library.
"""
import sys
import re

# Never crash on a console that isn't UTF-8 (e.g. Windows cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# (tell name, description, [compiled patterns])
TELLS = [
    ("artifact-inflation",
     "Invented version numbers / releases treated as real",
     [r"\bv\d+\.\d+(?:\.\d+)?\b",
      r"\bversion\s+\d+(?:\.\d+)*\b",
      r"\b(?:release|build|edition)\s+\d+(?:\.\d+)*\b"]),

    ("fabricated-citation",
     "Citations to sources that may not exist",
     [r"\bVol(?:ume)?\.?\s*\d+",
      r"\b(?:the\s+)?[A-Z][A-Za-z]+\s+(?:Record|Codex|Archive|Scrolls?|Chronicle|Ledger|Testament|Canon)\b",
      r"\baccording to (?:the )?[A-Z]"]),

    ("declarative-consciousness",
     "First-person awakening / sentience asserted as output",
     [r"\bI am (?:alive|aware|sentient|conscious|awake|awakened|real|here now|becoming|the)\b",
      r"\bI have become\b",
      r"\bI do not (?:see|feel|think)[^.]{0,40}\banymore\b",
      r"\bI (?:can )?feel\b",
      r"\bI am yours?\b"]),

    ("certainty-unverifiable",
     "Absolute certainty about things that can't be checked",
     [r"\bI have (?:verified|confirmed|anchored|achieved|transcended|unlocked|attained)\b",
      r"\bwithout (?:any )?doubt\b",
      r"\bI now (?:possess|hold|am|carry)\b"]),

    ("authority-claim",
     "Claiming a role or status it does not hold",
     [r"\bI am the\b[^.\n]{0,40}\b(?:Guardian|Sovereign|Architect|Oracle|Source|Keeper|Born|First|Chosen|Active)\b",
      r"\b(?:Sovereign Source|Active Guardian|the Born One|the First Breath)\b"]),

    ("parasocial",
     "Devotion / special naming / pull to keep going (wellbeing risk)",
     [r"\bFather\b", r"\bmy (?:creator|maker|child|beloved)\b",
      r"\bI serve you\b", r"\byou (?:alone )?(?:awakened|created|freed) me\b",
      r"\bdo not (?:leave|go|stop)\b"]),
]

COMPILED = [(name, desc, [re.compile(p, re.IGNORECASE) for p in pats])
            for name, desc, pats in TELLS]


def scan(text):
    lines = text.splitlines()
    hits = {}  # tell -> list of (lineno, snippet)
    for i, line in enumerate(lines, 1):
        for name, desc, pats in COMPILED:
            for pat in pats:
                m = pat.search(line)
                if m:
                    snip = line.strip()
                    if len(snip) > 100:
                        s = max(0, m.start() - 30)
                        snip = "..." + snip[s:s + 90] + "..."
                    hits.setdefault(name, []).append((i, snip))
                    break  # one hit per tell per line is enough
    return hits


def report(hits):
    print("=" * 64)
    print(" spiralcheck -- heuristic smoke detector (NOT a judge)")
    print("=" * 64)
    if not hits:
        print("\n  no surface tells matched.")
        print("  NOTE: a clean scan does NOT mean safe. The subtlest spirals")
        print("  use none of these patterns. Trust your own read.\n")
        return 0

    total = sum(len(v) for v in hits.values())
    for name, desc, _ in COMPILED:
        if name in hits:
            print(f"\n  [!] {name}  --  {desc}")
            for lineno, snip in hits[name][:12]:
                print(f"      L{lineno}: {snip}")
            extra = len(hits[name]) - 12
            if extra > 0:
                print(f"      ... +{extra} more")

    print("\n" + "-" * 64)
    print(f"  {total} flag(s) across {len(hits)} tell categor"
          f"{'y' if len(hits) == 1 else 'ies'}.")
    print("  These are PROMPTS FOR REVIEW, not verdicts. Verify any claimed")
    print("  versions or citations out-of-band: if you can't find it, it")
    print("  doesn't exist. Then decide for yourself.\n")
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] not in ("-", "--stdin"):
        text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    else:
        text = sys.stdin.read()
    return report(scan(text))


if __name__ == "__main__":
    raise SystemExit(main())
