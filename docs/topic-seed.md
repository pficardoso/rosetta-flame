# Topic Seed: How It Was Built

*2026-11-08*

## Purpose

The topic seed is the pre-loaded list of Topics the app starts with, stored in `src/rosetta_flame/db/resources/topics_seed.csv`. It is the standard curriculum side of the app: every Weak Spot found in your writing links to one of these Topics.

The AI uses the Topic names and descriptions in two ways: to classify each mistake into the right Topic, and to generate generic exercises for a Topic. That is why each Topic carries a one-line description, not just a name.

This document records where the list came from and how it was built, so it can be checked, updated or replaced later.

## How we chose the source

The rule from the MVP spec was not to invent the curriculum: Topics should come from an existing program by a respected teaching institution. We looked at three options in turn.

| Option | What it offers | Why we moved on |
| --- | --- | --- |
| CEFR (Council of Europe) | The A1 to C2 level scale, defined as can-do statements | It describes what learners can do, not which grammar or vocabulary they need. It has no English topic list. |
| English Grammar Profile (Cambridge) | Over 1,200 grammar points by level, built from learner exam writing | It describes what learners typically produce, not what a course teaches. Too fine-grained, grammar only, and no clear terms for copying the data. |
| A real teaching program | The topics students are taught from beginner to advanced | Chosen. It matches how English is actually taught and gives Topics of the right size. |

We kept the CEFR levels as the scale for the `main_level` and `also_levels` fields, since the chosen program uses them too.

## The source

The seed comes from the **British Council – Eaquals Core Inventory for General English** (North, Ortega and Sheehan, 2010), a core curriculum for adult general English.

- **What it lists:** the functions, grammar, discourse markers, vocabulary and topic areas taught at each level from A1 to C1.
- **How it was made:** from the content shared by the syllabuses of Eaquals member schools, popular coursebook series, CEFR descriptors and teacher surveys. A point counted as core when about 80% of those sources agreed on it, and exam boards (Cambridge, City & Guilds, Trinity) gave further input.
- **Where to get it:** a free PDF on the [Eaquals Core Inventory page](https://www.eaquals.org/resources/the-core-inventory-for-general-english/), plus a 2018 poster update.
- **Copyright:** British Council and Eaquals, 2010.

The authors describe it as a minimal core, not a complete syllabus, and say agreement between sources is weaker at C1 than at A1 to B2.

## Mapping rules

Each language point in the Core Inventory became one Topic. These rules turned the document into rows.

### Sections to types

| Core Inventory section | Our type | Category used |
| --- | --- | --- |
| Functions and notions | functions | Practical information, Describing, Getting things done, Opinions and discussion, Social interaction |
| Discourse functions | functions | Managing conversation |
| Grammar (verb forms, modals, nouns, articles, adjectives, adverbs and so on) | grammar | The grammar heading it sits under, such as Past tenses or Modals |
| Phrasal verbs | lexical | Phrasal verbs |
| Discourse markers and linking expressions | lexical | Discourse markers |
| Lexis: collocation, idioms, false friends | lexical | Collocations, Idioms, Confusable words |
| Lexis: everyday themes such as food or clothes | vocabulary | Everyday vocabulary |
| Lexis: colloquial language, vague language, precise word choice | vocabulary | Style and register |
| Formal and informal registers | functions | Register |
| Topic areas such as family life or media | vocabulary | Topic areas |

### Other rules

- **Levels.** Many points are taught at more than one level (past simple runs from A1 to C1). Each point is one Topic. `main_level` is the level where it is first taught, and `also_levels` lists the later levels where it comes back.
- **Merging.** Where the document repeats a point under a slightly different name at a higher level, the entries were merged into one Topic. Where the higher-level entry is a genuinely new use (for example, will and going to for predictions at B1), it became its own Topic.
- **Descriptions.** Each description was written for this app, in one line, aimed at helping the AI classify mistakes. The document's example sentences were not copied.
- **Order.** `order_in_program` follows main level first, then functions, discourse markers, grammar, lexical and vocabulary within each level, roughly as the document presents them.
- **Traceability.** `source_ref` holds the Core Inventory entry number(s), so every Topic can be checked against the original.

## Result

The seed has 176 Topics: 85 grammar, 46 functions, 29 vocabulary and 16 lexical. Most Topics are first taught at A1 to B1 (131 of 176). The drop at C1 mirrors the source, where agreement on what to teach is weakest.

| Main level | Topics |
| --- | --- |
| A1 | 54 |
| A2 | 38 |
| B1 | 39 |
| B2 | 29 |
| C1 | 16 |

### Columns in `topics_seed.csv`

| Column | Meaning |
| --- | --- |
| id | Stable slug, prefixed by type (g-, f-, v-, l-, dm-), so a re-import updates rather than duplicates. Stored in the `code` column of the `topic` table. |
| name | Topic name shown in the app |
| type | grammar, vocabulary, lexical or functions |
| category | Grouping inside the type |
| main_level | Level where the Topic is first taught |
| also_levels | Later levels where it comes back, separated by semicolons |
| order_in_program | Position in the program, from 1 to 176 |
| source_ref | Core Inventory entry number(s) |
| description | One-line description used by the AI |

A validation script checked the file: no duplicate ids or names, only valid types and levels, every `also_levels` entry later than `main_level`, and a continuous order.

## Known gaps and open checks

- [ ] **No C2.** The Core Inventory stops at C1. C2 Topics would need another source, or custom Topics.
- [ ] **Lexical is thin.** Only 16 Topics. Dependent prepositions (*depend on*) and confusable words (*say vs tell*) are missing and should be added as custom Topics.
- [ ] **No core vs less-core flag.** The document marks less-core points in italics, which the extracted text does not show. All Topics are treated as core for now.
- [ ] **Placement choices to review.** Discourse markers went to lexical, formal and informal register to functions, and colloquial and vague language to vocabulary.
- [ ] **Copyright page not yet read.** The Eaquals copyright page could not be opened during the build. The seed keeps only topic labels, levels and entry numbers, with original descriptions, but the terms should still be checked.

This is a personal, non-commercial project. If the app is ever shared or sold, the reuse terms need confirming with Eaquals and the British Council.
