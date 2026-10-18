#!/usr/bin/env python3
"""Scan a unified diff for hidden or suspicious Unicode characters.

By default only ADDED lines are checked (what a PR would introduce).

Usage:
    gh pr diff 190 | python scan_diff_hidden_chars.py
    git diff master...FETCH_HEAD | python scan_diff_hidden_chars.py
    python scan_diff_hidden_chars.py changes.diff --non-ascii --keywords

Exit code: 0 = nothing found, 1 = findings, 2 = usage/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass

# Explicit ranges/sets that are almost never legitimate in source code.
BIDI_CONTROLS = {
    0x061C, 0x200E, 0x200F,
    *range(0x202A, 0x202F),  # LRE RLE PDF LRO RLO
    *range(0x2066, 0x206A),  # LRI RLI FSI PDI
}
ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}
OTHER_INVISIBLE = {
    0x00AD,  # soft hyphen
    0x034F,  # combining grapheme joiner
    0x180E,  # mongolian vowel separator
    0x2061, 0x2062, 0x2063, 0x2064,  # invisible math operators
}
VARIATION_SELECTORS = set(range(0xFE00, 0xFE10)) | set(range(0xE0100, 0xE01F0))
TAG_CHARS = set(range(0xE0000, 0xE0080))  # used for "ASCII smuggling"

KEYWORDS = re.compile(
    r"\b(base64|b64decode|exec|eval|compile|__import__|subprocess|os\.system|"
    r"urllib|requests\.(get|post)|socket|pickle|marshal|zlib\.decompress|"
    r"codecs\.decode|fromhex|chr\()",
    re.IGNORECASE,
)

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass
class Finding:
    path: str
    line: int
    col: int
    kind: str
    detail: str


def classify(ch: str, flag_non_ascii: bool) -> tuple[str, str] | None:
    cp = ord(ch)
    if 0xDC80 <= cp <= 0xDCFF:
        return "invalid-utf8", f"byte 0x{cp - 0xDC00:02X}"
    if cp in BIDI_CONTROLS:
        return "bidi-control", unicodedata.name(ch, "?")
    if cp in TAG_CHARS:
        return "tag-char", f"U+{cp:04X} (can hide ASCII text)"
    if cp in ZERO_WIDTH:
        return "zero-width", unicodedata.name(ch, "?")
    if cp in OTHER_INVISIBLE:
        return "invisible", unicodedata.name(ch, "?")
    if cp in VARIATION_SELECTORS:
        return "variation-selector", f"U+{cp:04X}"
    cat = unicodedata.category(ch)
    if cat == "Cc" and ch not in "\t\n\r":
        return "control", f"U+{cp:04X}"
    if cat == "Cf":
        return "format-char", unicodedata.name(ch, f"U+{cp:04X}")
    if cat in ("Zs", "Zl", "Zp") and ch != " ":
        return "odd-space", unicodedata.name(ch, f"U+{cp:04X}")
    if flag_non_ascii and cp > 0x7F:
        return "non-ascii", f"{unicodedata.name(ch, '?')} (looks like '{ch}')"
    return None


def scan(diff_text: str, check_all: bool, non_ascii: bool, keywords: bool):
    findings: list[Finding] = []
    path = "<unknown>"
    new_line = 0
    in_hunk = False

    for raw in diff_text.split("\n"):
        line = raw[:-1] if raw.endswith("\r") else raw

        if line.startswith("+++ "):
            target = line[4:].split("\t")[0]
            path = target[2:] if target.startswith("b/") else target
            in_hunk = False
            continue
        if line.startswith("--- ") or line.startswith("diff --git"):
            in_hunk = False
            continue

        m = HUNK_RE.match(line)
        if m:
            new_line = int(m.group(1))
            in_hunk = True
            continue
        if not in_hunk or not line:
            continue

        marker, body = line[0], line[1:]
        if marker == "\\":  # "\ No newline at end of file"
            continue

        is_added = marker == "+"
        if is_added or (check_all and marker in " -"):
            for col, ch in enumerate(body, start=1):
                hit = classify(ch, non_ascii)
                if hit:
                    findings.append(Finding(path, new_line, col, *hit))
            if keywords and is_added and KEYWORDS.search(body):
                findings.append(
                    Finding(path, new_line, 1, "keyword", body.strip()[:100])
                )

        if marker in "+ ":
            new_line += 1

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("diff", nargs="?", help="diff file (default: stdin)")
    ap.add_argument("--all-lines", action="store_true",
                    help="also scan context and removed lines")
    ap.add_argument("--non-ascii", action="store_true",
                    help="also flag every non-ASCII character (homoglyph check)")
    ap.add_argument("--keywords", action="store_true",
                    help="also flag risky keywords on added lines (exec, eval, base64...)")
    args = ap.parse_args()

    try:
        if args.diff:
            with open(args.diff, "rb") as f:
                data = f.read()
        else:
            data = sys.stdin.buffer.read()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    text = data.decode("utf-8", errors="surrogateescape")
    findings = scan(text, args.all_lines, args.non_ascii, args.keywords)

    if not findings:
        print("No hidden or suspicious characters found.")
        return 0

    for f in findings:
        print(f"{f.path}:{f.line}:{f.col}  [{f.kind}]  {f.detail}")
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
