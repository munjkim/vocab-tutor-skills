---
name: vocabulary-quiz-generator
description: Build a printable A4 vocabulary test paper and matching answer key (HTML + PDF) from a Day Markdown file produced by vocabulary-photo-to-md. Use when the user asks to make a vocabulary quiz, word test, or worksheet for a Day, or to turn Day46.md into a test paper and answer sheet. Asks whether to add review words the student got wrong on earlier Days, then generates both documents from one shared quiz definition so they always correspond. Korean triggers 한국어 트리거: 단어 시험지 만들어줘, Day 46 시험지, 영어 단어 시험지와 정답지, 단어 테스트 출제, 시험지 PDF로 뽑아줘, 이전 오답 포함해서 시험지.
---

# Vocabulary Quiz Generator

Turn a Day Markdown file into a printable test paper and answer key.

The test paper and the answer key are rendered from **one shared quiz object**,
so their question order, direction, chosen sense and example sentences always
match. Never generate the two documents independently.

The documents are Korean study material; only these instructions are in English.

## Before generating: ask about review words

Vocabulary review is cumulative, so **always ask the user this before running
the generator** (unless they already said in their request):

> 이전 Day에서 틀린 단어를 복습 문항으로 추가할까요?

- If **no**, generate from the current Day only.
- If **yes**, ask which words. Accept them in whatever form the user gives —
  a plain list, a Day number plus the words, or a mix. For each word you need
  the **headword, part of speech, and Korean meaning**; example sentences are
  not needed.
  - If the user names words from a Day whose Markdown file is available
    (`Day45.md` and similar), read the meanings from that file instead of
    asking the user to retype them. Only ask about words you cannot find.
  - Write what you collected to `wrong_words.md` beside the Day file, one
    per line:
    `- force: 명사 - 힘 / 동사 - 강요하다`
  - Show the user the list you assembled before generating.

Review words are **added to**, never substituted for, the current Day's words.
They appear after the main block, numbered continuously and marked with `*`.

## Generating

One command does everything — quiz data, both HTML documents, and both PDFs.
The generator finds Chrome or Chromium itself and renders the PDFs from the
print CSS.

```bash
SKILL=~/.claude/skills/vocabulary-quiz-generator/scripts

python3 $SKILL/generate_quiz.py Day46.md
#    with review words:    --wrong wrong_words.md
#    to reproduce a paper: --seed 4821
#    HTML only, no PDF:    --no-pdf

python3 $SKILL/verify_quiz.py Day46.md
```

The two **PDFs land next to the Day Markdown** — those are the files the tutor
actually uses. The intermediates (`-quiz.json`, both `.html`) go into a `build/`
subfolder so the working folder stays clean:

```
Day46.md
Day46-test.pdf
Day46-answer.pdf
build/
  Day46-quiz.json     shared quiz definition
  Day46-test.html
  Day46-answer.html
```

The Day number and output filenames come from the input filename, so a new Day
needs no other change. `--outdir` moves the whole set elsewhere.

## After generating: look at the result

`verify_quiz.py` checks structure, not appearance. **Always also render the PDFs
to images and look at them** before reporting done:

```bash
sips -s format png --resampleWidth 1000 Day46-test.pdf --out /tmp/t.png
```

Read the image and confirm: nothing is cut off at the page edge, no text
overlaps, Korean renders correctly, the writing cells are roomy enough to write
in, and no answer is visible on the test paper.

## What the generator does

- **20 words, each once.** Order shuffled; exactly half ask for the English
  word and half for the Korean meaning.
- **Korean-to-English questions** show the **meaning only — never the part of
  speech**. When a word has several parts of speech, one group is chosen at
  random and only that group's meanings are shown. Any `(= tool)` or
  `(↔ weakness)` cross-reference is stripped from the question, so a blank
  asking for an English word never has English sitting next to it.
- **English-to-Korean questions** show the headword alone. The answer key lists
  **every meaning** from the Markdown, sense groups separated by ` / `, with the
  cross-references kept.
- **4 cloze examples**, preferring sentences where the headword appears in an
  inflected form (`framed`, `spotted`, `ran across`). Fragments that are not
  full sentences (`a bicycle frame`, `cotton fields`) are never used. The blank
  is sized to the answer, and the printed Korean translation sits on the right.
- **Seed.** Randomly chosen unless `--seed` is given, and printed to the
  terminal rather than onto the page. Passing the same seed reproduces the paper
  exactly — use it when fixing a mistake so the rest does not reshuffle, and
  tell the user the seed so they can ask for the same paper again. Adding or
  removing review words never changes the main 20 questions or the examples.

## Layout

A4 portrait, one page for a normal Day. Words go in a two-up table: number,
English cell, Korean cell — the empty cell is where the student writes, which
matches the tutor's existing paper format. Examples follow below the table.
Answers are marked with bold and an underline so they survive black-and-white
printing. Both documents carry a `___월 ___일` date field in the top-right
corner, and the test paper adds a large boxed score field (`___ / 24`) sized to
be written in. There is no name field, no seed on the page, and no footer.

If content ever overflows, let it run to a second page rather than shrinking
the type — handwriting room matters more than fitting one page.

## Reporting

Tell the user the output paths and the verification result. Give them the seed
too, noting that `--seed <n>` reproduces the same paper — it is not printed on
the documents.
