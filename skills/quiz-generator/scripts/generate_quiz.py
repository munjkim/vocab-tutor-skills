#!/usr/bin/env python3
"""Build a printable vocabulary quiz (test paper + answer key) from a Day Markdown file.

The test paper and the answer key are rendered from one shared quiz-data object,
so they always agree on order, direction, chosen sense and example sentences.
"""
import argparse
import html
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

POS_WORDS = ("명사", "동사", "형용사", "부사", "전치사", "대명사", "접속사", "감탄사", "관사")
POS_RE = re.compile(r"^(%s)\s*-\s*(.+)$" % "|".join(POS_WORDS))
ENTRY_RE = re.compile(r"^###\s+(\d+)\.\s+(.+?):\s*(.+)$")
PLAIN_RE = re.compile(r"^-\s+(.+?):\s*(.+)$")
EXAMPLE_RE = re.compile(r"^-\s+(.*\S)\s+\((.+)\)\s*$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
BUILD_DIR = "build"
CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


def previous_attempts(builddir, stem):
    """Seeds already used for this Day, and the highest attempt number on disk."""
    used, highest = set(), 0
    pattern = re.compile(re.escape(stem) + r"(?:-(\d+))?-quiz\.json")
    for f in sorted(builddir.glob(f"{stem}*-quiz.json")):
        m = pattern.fullmatch(f.name)
        if not m:
            continue                      # a different Day that shares the prefix
        try:
            used.add(json.loads(f.read_text(encoding="utf-8")).get("seed"))
        except (ValueError, OSError):
            continue
        highest = max(highest, int(m.group(1) or 1))
    used.discard(None)
    return used, highest


def find_chrome():
    for path in CHROME_PATHS:
        if Path(path).exists():
            return path
    for name in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return None


# ---------------------------------------------------------------- parsing

def parse_senses(rest):
    senses = []
    for part in rest.split(" / "):
        part = part.strip()
        m = POS_RE.match(part)
        if m:
            senses.append({"pos": m.group(1), "meaning": m.group(2).strip()})
        else:
            senses.append({"pos": None, "meaning": part})
    return senses


def strip_bold(s):
    return BOLD_RE.sub(r"\1", s)


def is_sentence(text):
    t = strip_bold(text).strip()
    return bool(t) and t[0].isupper() and t[-1] in ".?!"


def parse_markdown(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    title = None
    entries = []
    current = None
    for line in lines:
        if title is None and line.startswith("# "):
            title = line[2:].strip()
            continue
        m = ENTRY_RE.match(line)
        if m:
            current = {
                "number": int(m.group(1)),
                "headword": m.group(2).strip(),
                "senses": parse_senses(m.group(3).strip()),
                "examples": [],
            }
            entries.append(current)
            continue
        if current is None or not line.startswith("- "):
            continue
        if line.startswith("- 관련어:") or line.startswith("- 참고:"):
            continue
        m = EXAMPLE_RE.match(line)
        if m:
            en, ko = m.group(1).strip(), m.group(2).strip()
            bold = BOLD_RE.search(en)
            current["examples"].append({
                "en_md": en,
                "en": strip_bold(en),
                "ko": ko,
                "target": bold.group(1) if bold else None,
                "sentence": is_sentence(en),
            })
    if title is None:
        title = Path(path).stem
    return title, entries


def parse_wrong_words(path):
    """Extra entries from a previous Day. Accepts the same `### n. word: pos - 뜻`
    form as a Day file, or a plain `- word: pos - 뜻` list."""
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            m = ENTRY_RE.match(line)
            if not m:
                continue
            head, rest = m.group(2).strip(), m.group(3).strip()
        else:
            m = PLAIN_RE.match(line.strip())
            if not m:
                continue
            head, rest = m.group(1).strip(), m.group(2).strip()
        out.append({"number": None, "headword": head,
                    "senses": parse_senses(rest), "examples": [], "extra": True})
    return out


# ---------------------------------------------------------------- quiz build

def build_quiz(title, entries, extras, seed, n_examples=4):
    rng = random.Random(seed)
    items = [dict(e, extra=e.get("extra", False)) for e in entries]
    extras = [dict(e, extra=True) for e in extras]

    order = items[:]
    rng.shuffle(order)
    half = len(order) // 2
    directions = ["en"] * half + ["ko"] * (len(order) - half)
    rng.shuffle(directions)

    words = []
    for entry, direction in zip(order, directions):
        sense = rng.choice(entry["senses"]) if direction == "en" else None
        words.append({
            "headword": entry["headword"],
            "direction": direction,
            "prompt_sense": sense,
            "senses": entry["senses"],
            "extra": entry["extra"],
        })

    pool = [(e, ex) for e in entries for ex in e["examples"]
            if ex["sentence"] and ex["target"]]
    inflected = [p for p in pool
                 if p[1]["target"].lower() != p[0]["headword"].lower()]
    plain = [p for p in pool if p not in inflected]
    rng.shuffle(inflected)
    rng.shuffle(plain)
    chosen = (inflected + plain)[:n_examples]

    examples = [{
        "headword": e["headword"],
        "en_md": ex["en_md"],
        "en": ex["en"],
        "ko": ex["ko"],
        "answer": ex["target"],
        "inflected": ex["target"].lower() != e["headword"].lower(),
    } for e, ex in chosen]

    # Review words are drawn last and appended after the main block, so adding or
    # removing them never changes the main questions or the example sentences.
    for entry in extras:
        direction = rng.choice(["en", "ko"])
        words.append({
            "headword": entry["headword"],
            "direction": direction,
            "prompt_sense": rng.choice(entry["senses"]) if direction == "en" else None,
            "senses": entry["senses"],
            "extra": True,
        })

    return {"title": title, "seed": seed, "words": words, "examples": examples}


# ---------------------------------------------------------------- rendering

CROSSREF_RE = re.compile(r"\s*\((?:=|↔)[^)]*\)")


def fmt_senses(senses):
    """Answer-key form: every meaning, sense groups kept apart by ' / '."""
    return " / ".join(s["meaning"] for s in senses)


def fmt_prompt(sense):
    """Test-paper form: one sense group, with any (= ...) / (↔ ...) stripped so
    the question does not show English next to a blank asking for English."""
    return CROSSREF_RE.sub("", sense["meaning"]).strip()


def blank_html(en_md, answer, reveal):
    if reveal:
        return BOLD_RE.sub(
            lambda m: f'<span class="filled">{html.escape(m.group(1))}</span>', en_md, count=1)
    width = max(5.0, len(answer) * 0.85)
    return BOLD_RE.sub(
        lambda m: f'<span class="blank" style="width:{width:.1f}em"></span>', en_md, count=1)


CSS = """
@page { size: A4 portrait; margin: 14mm 13mm 12mm 13mm; }
* { box-sizing: border-box; }
body { margin: 0; font-family: "Apple SD Gothic Neo", "Noto Sans KR", -apple-system,
       "Helvetica Neue", sans-serif; color: #000; font-size: 10.2pt; line-height: 1.45; }
header { display: flex; align-items: center; justify-content: space-between;
         border-bottom: 2px solid #000; padding-bottom: 9px; margin-bottom: 11px; }
h1 { font-size: 14pt; margin: 0; letter-spacing: -0.2px; }
h1 .day { font-weight: 400; margin-left: 6px; }
.meta { font-size: 9.5pt; text-align: right; white-space: nowrap; }
.date { margin-right: 14px; }
.date u { display: inline-block; width: 2.6em; border-bottom: 1px solid #000;
          text-decoration: none; }
.score { display: inline-block; min-width: 108px; text-align: center;
         font-size: 16pt; font-weight: 600; border: 1.5px solid #000;
         border-radius: 3px; padding: 9px 10px 8px; }
.score .of { font-size: 12pt; font-weight: 400; color: #333; margin-left: 2px; }
h2 { font-size: 10.5pt; margin: 0 0 6px; padding: 3px 7px; background: #f0f0f0;
     border-left: 3px solid #000; }
h2 .hint { font-weight: 400; font-size: 8.6pt; color: #444; margin-left: 6px; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; }
td { border: 1px solid #999; padding: 5px 6px; vertical-align: middle; height: 30px;
     word-break: keep-all; overflow-wrap: anywhere; }
/* the test paper spreads out to fill the page and leave room for handwriting */
body.test td { height: 48px; }
body.test ol.ex li { padding: 13px 8px; }
td.num { width: 5%; text-align: center; font-size: 8.4pt; color: #555;
         background: #fafafa; padding: 5px 2px; }
td.en { width: 18.5%; font-size: 10.4pt; }
td.ko { width: 26.5%; font-size: 9.5pt; }
td.fill { background: #fcfcfc; }
.extra-tag { font-weight: 700; margin-left: 1px; }
td.num { white-space: nowrap; }
p.note { margin: 5px 2px 0; font-size: 8pt; color: #444; }
section.examples { margin-top: 13px; break-inside: avoid; }
ol.ex { margin: 0; padding-left: 0; list-style: none; counter-reset: ex; }
ol.ex li { counter-increment: ex; border: 1px solid #999; border-top: none;
           padding: 7px 8px; display: flex; align-items: baseline; gap: 8px; }
ol.ex li:first-child { border-top: 1px solid #999; }
ol.ex li::before { content: counter(ex) "."; font-size: 8.8pt; color: #555;
                   min-width: 1.1em; }
.ex-en { flex: 1 1 58%; font-size: 10.4pt; }
.ex-ko { flex: 0 0 36%; font-size: 8.8pt; color: #333; text-align: right;
         word-break: keep-all; }
.blank { display: inline-block; border-bottom: 1px solid #000; height: 1.05em;
         vertical-align: -2px; }
.filled { font-weight: 700; border-bottom: 1.5px solid #000; padding: 0 2px; }
.answer { font-weight: 700; }
.answer-ko { font-weight: 700; }
"""


def render(quiz, answer_key):
    kind = "정답지" if answer_key else "시험지"
    body_cls = "answer" if answer_key else "test"
    total = len(quiz["words"]) + len(quiz["examples"])
    rows = []
    words = quiz["words"]
    n_rows = (len(words) + 1) // 2
    for r in range(n_rows):
        cells = []
        for c in (r, r + n_rows):
            if c >= len(words):
                cells.append('<td class="num"></td><td class="en"></td><td class="ko"></td>')
                continue
            w = words[c]
            tag = '<span class="extra-tag">*</span>' if w["extra"] else ""
            if w["direction"] == "en":
                en = (f'<span class="answer">{html.escape(w["headword"])}</span>'
                      if answer_key else "")
                ko = html.escape(fmt_prompt(w["prompt_sense"]))
                en_cls, ko_cls = "en fill", "ko"
            else:
                en = html.escape(w["headword"])
                ko = (f'<span class="answer-ko">{html.escape(fmt_senses(w["senses"]))}</span>'
                      if answer_key else "")
                en_cls, ko_cls = "en", "ko fill"
            cells.append(f'<td class="num">{c + 1}{tag}</td>'
                         f'<td class="{en_cls}">{en}</td><td class="{ko_cls}">{ko}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")

    ex_items = []
    for ex in quiz["examples"]:
        ex_items.append(
            f'<li><span class="ex-en">{blank_html(ex["en_md"], ex["answer"], answer_key)}</span>'
            f'<span class="ex-ko">{html.escape(ex["ko"])}</span></li>')

    note = ('<p class="note">* 이전 Day 복습 단어</p>'
            if any(w["extra"] for w in words) else "")
    date_field = '<span class="date"><u></u> 월 <u></u> 일</span>'
    score_field = "" if answer_key else f'<span class="score"><span class="of">/ {total}</span></span>'
    hint_w = "빈칸에 알맞은 영어 단어 또는 우리말 뜻을 쓰세요."
    hint_e = "밑줄에 알맞은 단어를 알맞은 형태로 쓰세요."
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>{html.escape(quiz['title'])} 단어 {kind}</title>
<style>{CSS}</style></head><body class="{body_cls}">
<header>
  <h1>단어 {kind}<span class="day">{html.escape(quiz['title'])}</span></h1>
  <div class="meta">{date_field}{score_field}</div>
</header>
<h2>1. 단어<span class="hint">{hint_w}</span></h2>
<table>{''.join(rows)}</table>{note}
<section class="examples">
  <h2>2. 예문<span class="hint">{hint_e}</span></h2>
  <ol class="ex">{''.join(ex_items)}</ol>
</section>
</body></html>"""


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description="Vocabulary quiz generator")
    ap.add_argument("input", help="Day Markdown file (e.g. Day46.md)")
    ap.add_argument("--wrong", help="Markdown file of review words from earlier Days")
    ap.add_argument("--seed", type=int, help="Random seed (default: random 4-digit)")
    ap.add_argument("--outdir", help="Output directory (default: next to the input file)")
    ap.add_argument("--examples", type=int, default=4, help="Number of cloze examples")
    ap.add_argument("--no-pdf", action="store_true", help="Write HTML only, skip PDF rendering")
    ap.add_argument("--retest", action="store_true",
                    help="Re-sit of a Day already tested: pick a seed none of the "
                         "earlier papers used and number the files by attempt")
    args = ap.parse_args()

    title, entries = parse_markdown(args.input)
    extras = parse_wrong_words(args.wrong) if args.wrong else []

    stem = Path(args.input).stem
    outdir = Path(args.outdir) if args.outdir else Path(args.input).resolve().parent
    builddir = outdir / BUILD_DIR
    builddir.mkdir(parents=True, exist_ok=True)

    used, highest = previous_attempts(builddir, stem)
    if args.retest:
        attempt = highest + 1
        if not used:
            print("  주의: 이 Day의 이전 시험지가 없어 1회차로 만듭니다.")
            attempt = 1
    else:
        attempt = 1
    suffix = "" if attempt == 1 else f"-{attempt}"

    if args.seed is not None:
        seed = args.seed
    else:
        # A retest must not repeat a paper the student has already sat.
        seed = random.randint(1000, 9999)
        while args.retest and seed in used:
            seed = random.randint(1000, 9999)

    quiz = build_quiz(title, entries, extras, seed, args.examples)

    out = stem + suffix
    html = {}
    (builddir / f"{out}-quiz.json").write_text(
        json.dumps(quiz, ensure_ascii=False, indent=2), encoding="utf-8")
    for kind, is_answer in (("test", False), ("answer", True)):
        html[kind] = builddir / f"{out}-{kind}.html"
        html[kind].write_text(render(quiz, is_answer), encoding="utf-8")

    n_en = sum(1 for w in quiz["words"] if w["direction"] == "en")
    print(f"{title}  {attempt}회차  seed={seed}"
          + (f"  (이전 시드 {sorted(used)} 회피)" if args.retest and used else ""))
    print(f"  words    {len(quiz['words'])}  (영어 답 {n_en} / 한국어 답 {len(quiz['words']) - n_en})")
    print(f"  examples {len(quiz['examples'])}  "
          f"(활용형 {sum(1 for e in quiz['examples'] if e['inflected'])})")
    print(f"  build    {builddir}/")
    print(f"  verify   python3 verify_quiz.py {args.input} '' {out}")

    if args.no_pdf:
        return
    chrome = find_chrome()
    if not chrome:
        print("  PDF      건너뜀 (Chrome 또는 Chromium을 찾지 못함)")
        return
    for kind, src in html.items():
        pdf = outdir / f"{out}-{kind}.pdf"
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", src.resolve().as_uri()],
                       check=True, capture_output=True)
        print(f"  {kind:<8} {pdf}")


if __name__ == "__main__":
    main()
