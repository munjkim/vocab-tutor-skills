---
name: vocabulary-photo-to-quiz
description: Go from photos of an English vocabulary workbook straight to a printable test paper and answer key in one pass — extract the Day's words to Markdown, then generate the quiz PDFs. Use when the user attaches workbook photos and asks for a test paper, worksheet, or quiz without asking for the Markdown separately. Runs vocabulary-photo-to-md and then vocabulary-quiz-generator, stopping only if the extraction looks unreliable. Korean triggers 한국어 트리거: 사진으로 시험지 만들어줘, 교재 사진 주면 시험지까지, 사진에서 시험지 뽑아줘, Day 46 사진으로 단어 시험지, 한 번에 시험지까지 만들어줘.
---

# Workbook Photos → Test Paper

Run the whole pipeline in one pass: photos → `DayNN.md` → `DayNN-test.pdf` and
`DayNN-answer.pdf`.

Use this when the user wants the test paper and did not ask to see the Markdown
as a separate deliverable. If they only want the word list, use
`vocabulary-photo-to-md` alone.

Ask the one question in step 1, then run to the end without stopping. The only
other interruption allowed is the checkpoint in step 3, and only when it trips.

## Steps

### 1. Ask about review words

Before touching the photos, ask:

> 이전 Day에서 틀린 단어를 복습 문항으로 추가할까요?

If **no**, or if the user already settled it in their request, carry on.

If **yes**, collect the words the way `vocabulary-quiz-generator` describes —
take them in whatever form the user gives, read meanings from an earlier Day's
Markdown when that file is available, and only ask about words you cannot find.
Write them to `wrong_words.md` and pass `--wrong wrong_words.md` in step 4.

Ask this once, here. Do not raise it again later in the run.

### 2. Extract

Invoke the **`vocabulary-photo-to-md`** skill and follow it exactly. Do not
re-derive the extraction rules here — that skill owns them. It writes
`DayNN.md` to the working directory.

### 3. Checkpoint

Before generating anything, check the Markdown you just wrote:

- Does it contain `[판독 불가]` anywhere?
- Is the headword count something other than 20?
- Did the photos cover more than one Day?

If **any** of these is true, stop and show the user what you found before going
on. A misread word becomes a wrong question on a paper a student will sit, and
reprinting costs more than one question now.

If none of them is true, continue without asking.

### 4. Generate

```bash
SKILL=~/.claude/skills/vocabulary-quiz-generator/scripts

python3 $SKILL/generate_quiz.py Day46.md
python3 $SKILL/verify_quiz.py  Day46.md
```

Add `--wrong wrong_words.md` if step 1 produced any. See the
`vocabulary-quiz-generator` skill for the full set of flags.

This flow always produces a Day's first paper, so `--retest` never applies here.
If the user wants a re-sit of a Day they already tested, they do not need new
photos — send them to `vocabulary-quiz-generator` with the existing Markdown.

### 5. Look at it

Render the test paper and read it as an image before reporting done:

```bash
sips -s format png --resampleWidth 1000 Day46-test.pdf --out /tmp/t.png
```

Confirm nothing is cut off, no text overlaps, Korean renders, and no answer is
visible on the test paper.

### 6. Report

Give the user, in this order:

1. The Day and the number of words extracted
2. The two PDF paths
3. The verification result
4. Anything you had to judge — a word partly hidden by highlighter that you
   restored from context, a synonym/antonym marker you read by meaning

Keep it short. The user asked for a test paper, not a transcript of the run.

## If multiple Days are photographed

Extract each Day to its own Markdown file, then generate a separate test paper
and answer key per Day. Never mix two Days into one paper.
