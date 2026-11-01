"""Align every org table in a file by raw characters, and report lines over the width limit.

Usage: python orgTableAlign.py FILE [--width 105] [--check]

- Pads each column to its widest raw cell (org shows =/~ markers by default, so they count).
- Leaves alone what is inside dblocks (generated) and #+begin_example / #+begin_src blocks
  (whose lines may start with | as ascii art).
- Rules (|---+---|) are rebuilt to the new widths.
- --check: change nothing; exit 1 if a table is misaligned or a line is over the width.
Prints every line over the width (tables included) after aligning.
"""
import pathlib
import re
import sys


def _isRow(line: str) -> bool:
    return line.lstrip().startswith("|")


def _cells(line: str) -> list[str]:
    body = line.strip()
    return [c.strip() for c in body[1:-1].split("|")] if body.endswith("|") else \
        [c.strip() for c in body[1:].split("|")]


def _alignTable(rows: list[str]) -> list[str]:
    indent = rows[0][:len(rows[0]) - len(rows[0].lstrip())]
    parsed = [None if re.fullmatch(r"\|[-+|]+\|?", r.strip()) else _cells(r) for r in rows]
    ncols = max(len(c) for c in parsed if c is not None)
    widths = [0] * ncols
    for cells in parsed:
        if cells is None:
            continue
        for i, c in enumerate(cells):
            widths[i] = max(widths[i], len(c))
    out = []
    for cells in parsed:
        if cells is None:
            out.append(indent + "|" + "+".join("-" * (w + 2) for w in widths) + "|")
        else:
            cells = cells + [""] * (ncols - len(cells))
            out.append(indent + "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |")
    return out


def align(text: str) -> str:
    lines = text.split("\n")
    out, i, inDblock = [], 0, False
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        low = s.lower()
        if s.startswith("#+BEGIN:") or s.startswith("####+BEGIN:") or low.startswith("#+begin_"):
            inDblock = True
        elif s.startswith("#+END:") or s.startswith("####+END:") or s == "#+END" or low.startswith("#+end_"):
            inDblock = False
        if _isRow(line) and not inDblock:
            j = i
            while j < len(lines) and _isRow(lines[j]):
                j += 1
            out.extend(_alignTable(lines[i:j]))
            i = j
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def main() -> int:
    args = sys.argv[1:]
    width = 105
    if "--width" in args:
        width = int(args[args.index("--width") + 1])
    check = "--check" in args
    path = pathlib.Path(args[0])
    text = path.read_text()
    aligned = align(text)
    if check:
        bad = aligned != text
    else:
        path.write_text(aligned)
        bad = False
    over = [(n, len(l)) for n, l in enumerate(aligned.split("\n"), 1) if len(l) > width]
    inDblock, report = False, []
    for n, l in enumerate(aligned.split("\n"), 1):
        s = l.strip()
        if s.startswith("#+BEGIN:") or s.startswith("####+BEGIN:"):
            inDblock = True
        elif s.startswith("#+END:") or s.startswith("####+END:"):
            inDblock = False
        if len(l) > width and not inDblock:
            report.append(f"{n:5d} {len(l):4d} {l[:70]}")
    for r in report:
        print(r)
    print(f"{path}: {'misaligned tables; ' if bad else ''}{len(report)} lines over {width} (dblocks excluded)")
    return 1 if (bad or report) else 0


if __name__ == "__main__":
    sys.exit(main())
