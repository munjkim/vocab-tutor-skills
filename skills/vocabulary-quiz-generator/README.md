# vocabulary-quiz-generator

A Claude Code skill that turns a Day vocabulary Markdown file into a printable
A4 test paper and matching answer key (HTML + PDF).

Designed to pair with [`vocabulary-photo-to-md`](../vocabulary-photo-to-md),
which produces the Markdown from photos of a workbook.

## Install

Copy the folder into your personal skills directory:

```bash
cp -r vocabulary-quiz-generator ~/.claude/skills/
```

## Use

Ask Claude Code for a quiz — "Day 46 단어 시험지 만들어줘" — and it will ask
whether to include review words from earlier Days, then generate everything.

Or run the scripts directly:

```bash
SKILL=~/.claude/skills/vocabulary-quiz-generator/scripts

python3 $SKILL/generate_quiz.py Day46.md   # HTML + PDF
python3 $SKILL/verify_quiz.py  Day46.md   # automated checks
```

| Flag | Meaning |
| --- | --- |
| `--wrong FILE` | Markdown list of review words to append as extra questions |
| `--seed N` | Reproduce a specific paper (default: random; reported in the terminal, not printed on the page) |
| `--outdir DIR` | Output directory (default: next to the input file) |
| `--examples N` | Number of cloze sentences (default 4) |
| `--no-pdf` | Write HTML only and skip PDF rendering |
| `--retest` | Re-sit of a Day already tested: draws a seed none of the earlier papers used and numbers the files by attempt (`Day46-2-test.pdf`) |

PDFs are rendered from the print CSS with headless Chrome, which the generator
locates on its own. Pass `--no-pdf` to skip that step.

## Input format

The Day Markdown is what `vocabulary-photo-to-md` writes:

```markdown
# Day 46

### 1. fuel: 명사 - 연료

- The car uses a lot of **fuel**. (그 차는 연료를 많이 소모한다.)

### 5. dislike: 동사 - 싫어하다 (= hate) / 명사 - 싫어함, 반감

- I really **dislike** the cold weather. (나는 추운 날씨를 정말 싫어한다.)
```

Review words (`--wrong`) take one word per line, examples not needed:

```markdown
- force: 명사 - 힘 / 동사 - 강요하다
- cut down: 베어 쓰러뜨리다, 줄이다
```

## Output

The PDFs — the files you actually print — land next to the input. Intermediates
go into `build/`.

```
Day46.md              source
Day46-test.pdf        test paper
Day46-answer.pdf      answer key
build/
  Day46-quiz.json     shared quiz definition (source of both documents)
  Day46-test.html
  Day46-answer.html
```

## Requirements

Python 3 (standard library only) and Chrome or Chromium for PDF output.
