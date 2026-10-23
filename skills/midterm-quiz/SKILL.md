---
name: midterm-quiz
description: Build a printable A4 midterm vocabulary test paper and matching answer key (HTML + PDF) that covers a range of Days — five by default — from the Day Markdown files already in the folder. Same layout and question counts as a single-Day paper (20 words, 4 example sentences), with the words spread evenly across the Days. Use when the user asks for a midterm, a cumulative test, or a test spanning several Days. Korean triggers 한국어 트리거: 중간 테스트 만들어줘, 중간고사 시험지, Day 46부터 50까지 시험지, 5개 Day 누적 시험, 여러 Day 합쳐서 시험지.
---

# Midterm Quiz

Turn several Day Markdown files into one test paper and answer key. It uses the
`quiz-generator` script and paper format unchanged. Only the word selection
differs.

The documents are Korean study material; only these instructions are in English.

## Pick the range

- If the user names a range (`Day 46~50`, `46부터 52까지`), use it as given.
- Otherwise use the **five most recent** `DayNN.md` files in the folder and say
  which Days you picked in the same message as the re-sit question below, if
  there is one.

Every Day in the range must have its Markdown file. If one is missing, stop and
tell the user which Day is missing — do not quietly skip it.

## Is this a re-sit?

If `DayAA-BB-midterm-test.pdf` already exists for that range, ask:

> 이 범위는 이미 중간 테스트를 만들었습니다. 재시험인가요?

If **yes**, pass `--retest`, as in `quiz-generator`: the generator picks a new
seed, the paper gets new words and directions, and the files are numbered
`Day46-50-midterm-2-test.pdf`.

Do not ask about review words — the midterm already is the review.

## Generating

Pass every Day file in the range. The generator sorts them by Day number.

```bash
SKILL=~/.claude/skills/quiz-generator/scripts

python3 $SKILL/generate_quiz.py Day{46..50}.md
#    a re-sit of this range: --retest
#    to reproduce a paper:  --seed 4821

python3 $SKILL/verify_quiz.py Day46.md '' Day46-50-midterm
```

The generator prints the exact verify command, including the attempt number
after a `--retest`.

It draws **20 words**, spread as evenly as the range allows (four per Day for
five Days). If a headword appears in more than one Day, it is asked at most
once. The cloze sentences are 4 of the chosen words' examples, and the
question rules, direction split, layout and seed behaviour are the same as in
`quiz-generator`.

The paper is titled `단어 시험지 Day 46-50 Review` (`단어 정답지 …` on the
answer key).

Output, next to the Day files:

```
Day46-50-midterm-test.pdf
Day46-50-midterm-answer.pdf
build/Day46-50-midterm-quiz.json   lists the Day files it drew from
```

## After generating

Render the test paper to an image and look at it, exactly as `quiz-generator`
describes, before reporting done.

## Reporting

Tell the user the range, the two PDF paths, the verification result, and the
seed (`--seed <n>` reproduces the same paper).
