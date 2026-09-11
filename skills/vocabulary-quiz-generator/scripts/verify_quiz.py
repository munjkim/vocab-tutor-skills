#!/usr/bin/env python3
"""Check a generated quiz against its source Markdown. Exits non-zero on failure."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_quiz import (parse_markdown, fmt_senses, fmt_prompt, BOLD_RE,
                           strip_bold, BUILD_DIR)

checks = []


def check(name, ok, detail=""):
    checks.append((ok, name, detail))


def main(src_md, outdir=None, stem=None):
    outdir = Path(outdir) if outdir else Path(src_md).resolve().parent
    stem = stem or Path(src_md).stem
    title, entries = parse_markdown(src_md)
    build = outdir / BUILD_DIR
    quiz = json.loads((build / f"{stem}-quiz.json").read_text(encoding="utf-8"))
    test_html = (build / f"{stem}-test.html").read_text(encoding="utf-8")
    ans_html = (build / f"{stem}-answer.html").read_text(encoding="utf-8")

    src_heads = [e["headword"] for e in entries]
    main_words = [w for w in quiz["words"] if not w["extra"]]
    quiz_heads = [w["headword"] for w in main_words]

    check("표제어가 모두 출제됨", sorted(src_heads) == sorted(quiz_heads),
          f"원본 {len(src_heads)} / 출제 {len(quiz_heads)}")
    check("중복 출제 없음", len(quiz_heads) == len(set(quiz_heads)))
    n_en = sum(1 for w in main_words if w["direction"] == "en")
    check("영어 답 / 한국어 답 절반씩", abs(n_en - (len(main_words) - n_en)) <= 1,
          f"영어 {n_en} / 한국어 {len(main_words) - n_en}")

    by_head = {e["headword"]: e for e in entries}
    ok_pos, bad = True, []
    for w in main_words:
        if w["direction"] != "en":
            continue
        senses = by_head[w["headword"]]["senses"]
        chosen = w["prompt_sense"]
        if chosen not in senses:
            ok_pos, _ = False, bad.append(f"{w['headword']}: 원본에 없는 뜻")
        elif len({s["pos"] for s in senses}) > 1:
            shown = fmt_prompt(chosen)
            for s in senses:
                if s is not chosen and s["pos"] != chosen["pos"] and s["meaning"] in shown:
                    ok_pos, _ = False, bad.append(f"{w['headword']}: 다른 품사 뜻 노출")
    check("복수 품사 선택 규칙 준수", ok_pos, "; ".join(bad))

    t_nums = re.findall(r'<td class="num">(\d+)', test_html)
    a_nums = re.findall(r'<td class="num">(\d+)', ans_html)
    check("시험지·정답지 문항 순서 동일", t_nums == a_nums and len(t_nums) == len(quiz["words"]))

    check("예문 4개", len(quiz["examples"]) == 4, str(len(quiz["examples"])))
    src_ex = {strip_bold(ex["en_md"]): ex for e in entries for ex in e["examples"]}
    ok_sent = all(e["en"][0].isupper() and e["en"][-1] in ".?!" for e in quiz["examples"])
    check("예문이 모두 온전한 문장", ok_sent)
    check("예문 빈칸이 정확한 활용형을 대체",
          all(BOLD_RE.search(e["en_md"]).group(1) == e["answer"] for e in quiz["examples"]))
    check("예문 한국어 번역이 원본과 일치",
          all(src_ex[e["en"]]["ko"] == e["ko"] for e in quiz["examples"]))

    table_test = test_html.split('<section class="examples">')[0]
    leaked = [w["headword"] for w in quiz["words"] if w["direction"] == "en"
              and re.search(r"\b%s\b" % re.escape(w["headword"]), table_test, re.I)]
    check("시험지에 정답 노출 없음", not leaked, ", ".join(leaked))
    blanks_ok = all(e["answer"] not in
                    test_html.split('<section class="examples">')[1].split(e["ko"])[0]
                    for e in quiz["examples"])
    check("예문 정답이 시험지에 노출되지 않음", blanks_ok)

    ok_ans = True
    for w in quiz["words"]:
        expect = w["headword"] if w["direction"] == "en" else fmt_senses(w["senses"])
        if expect not in ans_html:
            ok_ans = False
    check("정답지 정답이 원본 데이터와 일치", ok_ans)

    for pdf in (f"{stem}-test.pdf", f"{stem}-answer.pdf"):
        p = outdir / pdf
        if p.exists():
            data = p.read_bytes()
            pages = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
            check(f"{pdf} 생성됨 ({pages}쪽)", pages >= 1)

    width = max(len(n) for _, n, _ in checks)
    for ok, name, detail in checks:
        print(f"  {'✓' if ok else '✗'} {name.ljust(width)}  {detail}")
    failed = sum(1 for ok, _, _ in checks if not ok)
    print(f"\n  {len(checks) - failed}/{len(checks)} 통과")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
