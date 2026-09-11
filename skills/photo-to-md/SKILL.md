---
name: photo-to-md
description: Convert photos of an English vocabulary workbook into a structured Markdown study file. Use when the user attaches textbook photos and asks to organize a Day's vocabulary, extract headwords with parts of speech and Korean meanings, collect example sentences with their printed Korean translations, or produce a file such as Day46.md. Extracts only printed content in textbook order and excludes handwriting and grading marks. Applies to Day-based English vocabulary workbooks (워드마스터, 능률 보카, and similar). Korean triggers 한국어 트리거: 영어 단어 교재 사진 정리, Day 46 단어 정리, 사진 속 단어 정리해줘, 단어와 품사 뜻 추출, 예문과 해석 정리, 단어장 사진 마크다운으로, Day46.md로 만들어줘.
---

# Vocabulary Workbook Photo → Markdown

Extract **only the printed content** from photos of an English vocabulary
workbook and write it to a Markdown file in the format defined below.

The instructions are in English, but **the output is Korean study material**:
part-of-speech labels, meanings, translations, and the `관련어` / `참고` labels
are all written in Korean exactly as shown in the examples.

## Read this first

Before doing anything else, **read `examples/example.md` in this skill folder**.
That file is the authoritative reference for the output format. If anything
below appears to disagree with it, **follow the example file**.

## Procedure

1. Look at the photos and find the **printed** Day number. Use the printed
   `DAY 46` marking, not a handwritten date or number.
2. Walk through the headwords in the exact order they are printed and collect:
   - the headword
   - the part of speech
   - the Korean meaning (all of them if there are several)
   - the English example sentences or phrases (all of them)
   - the Korean translation as printed in the textbook
   - related words (marked `+`) and cross-references (marked `참고`)
3. Write the Markdown in the format below.
4. Save the file.

## Extraction rules

- **Transcribe printed content only.** Exclude all handwriting: grading marks,
  circles, triangles, checks, slashes, highlighter and pen annotations, and any
  answers the student wrote in.
- If highlighting or handwriting partially covers text, restore it **only when
  the context makes it certain**.
- **Never invent content you cannot read clearly.** Write `[판독 불가]` in its
  place. If an entire example sentence is illegible, put `[판독 불가]` on that
  example's line.
- **Never write your own translation.** Copy the Korean translation exactly as
  printed, even if it reads awkwardly. Copy the English sentences verbatim too.
- Exclude pronunciation guides, word number tags (`0901` and similar), study
  date fields, checkboxes, practice sections such as CHECK-UP and PREVIEW, and
  tables.
- Photos showing only practice pages (CHECK-UP, PREVIEW, and similar) contain
  nothing to extract. Tell the user if that is all the photos contain.

## Output format

The first line is the Day title as an `#` heading.

```
# Day 46
```

Each headword is a numbered `###` heading, followed by a blank line and then
the example list.

```
### 1. fuel: 명사 - 연료

- The car uses a lot of **fuel**. (그 차는 연료를 많이 소모한다.)
- We're running out of **fuel**. (우리는 연료가 다 떨어져 간다.)

### 2. spread: 동사 - 1. 펼치다, 2. (팔 등을) 벌리다, 3. 퍼지다, 퍼뜨리다

- He **spread** the map on the floor. (그는 바닥에 그 지도를 펼쳤다.)
```

### Headword line

- The shape is `### <number>. <headword>: <품사> - <뜻>`.
  Example: `### 1. liberty: 명사 - 자유`
- **The headword line must be an `###` heading.** If it is written as an
  ordered list item (`1.`), Markdown viewers start a new list at every headword
  and render every number as `1.`. A number inside a heading is plain text, so
  it renders exactly as written in every viewer.
- Number the headwords from 1 in textbook order.
- Do not escape the period as `\.` — the heading already handles this.
- Expand the textbook's abbreviated part of speech into the full Korean word:
  명 → `명사`, 동 → `동사`, 형 → `형용사`, 부 → `부사`, 전 → `전치사`.
- Separate multiple meanings with `1.`, `2.`, `3.` joined by commas.
  Example: `### 11. height: 명사 - 1. 키, 높이, 2. 고도`
- **Never use circled numbers such as `①`, `②`, `③`**, even when the textbook
  prints them that way. Convert them to `1.`, `2.`, `3.`.
- When one word has several parts of speech, separate them with ` / `.
  Example: `### 5. dislike: 동사 - 싫어하다 (= hate) / 명사 - 싫어함, 반감`
- When the textbook marks a **synonym** (`유 hate`), append `(= hate)` to that
  meaning.
- When the textbook marks an **antonym** (`반 weakness`), append `(↔ weakness)`
  to that meaning. Example:
  `### 6. strength: 명사 - 1. (육체적·정신적) 힘, 2. 강점, 장점 (↔ weakness)`
- Synonym and antonym markers are both printed as circled glyphs and can be
  hard to tell apart in a photo. Decide from the semantic relationship between
  the two words (`liberty`–`freedom` is a synonym pair, `strength`–`weakness`
  an antonym pair). If it is still unclear, do not guess — ask the user which
  one it is.
- Omit the part of speech for idioms and phrasal verbs, which the textbook
  prints without one. Example: `### 19. pull up: (차 등이) 멈추다[서다]`

### Examples

- Write English examples as a `-` list. Never as a numbered list.
- Do not indent the list; start it at the beginning of the line.
- Leave one blank line between the headword heading and the example list.
- **Put the Korean translation on the same line as the English example, in
  parentheses at the end.** One space before the opening parenthesis.
  Example: `- The car uses a lot of **fuel**. (그 차는 연료를 많이 소모한다.)`
- Never move the translation to the next line or into its own `-` item.
  One example is always one line.
- Keep the translation's printed period **inside** the parentheses.
- Mark the headword, or the inflected form of it, in `**bold**` within the
  example. Bold inflected forms too: `They **spotted** a shark coming.`
- Phrases that are not full sentences follow the same shape.
  Example: `- a bicycle **frame** (자전거의 뼈대)`

### Related words and cross-references

- Append them as `-` items at the **bottom of that headword's example list**.
- A related word that has a part of speech and meaning:
  `- 관련어: wise: 형용사 - 현명한, 지혜로운`
- A cross-reference that has only a meaning: `- 참고: weight - 무게`

Leave one blank line between headwords.

## Saving the file

- Name the file without spaces: `Day46.md`, `Day47.md`.
- Save to the current working directory unless the user specifies a location.
- If the photos cover several Days, **write a separate file per Day.** Never mix
  two Days into one file.
- After saving, report the file path and the number of headwords extracted.
