# LawCodex — Nauru (`nr`)

Legislation of the Republic of Nauru (Naoero) as plain Markdown, from **RONLAW**, the official
online legal database of the Republic of Nauru (<https://ronlaw.gov.nr>), maintained for the
Nauru Department of Justice and Border Control.

Part of [LawCodex](https://github.com/LawCodex): the legislation of every country as Markdown in git.

Retrieved: **2026-10-13**.

## Contents

| Category | Directory | Files | Notes |
|---|---|---:|---|
| Constitution | `constitution/` | 1 | Constitution of Naoero 1968, consolidated (Service 6, to the Constitution (Amendment) (No 2) Act 2026) |
| Acts | `acts/<year>/` | 444 | everything RONLAW files under category *acts* |
| Subsidiary legislation | `subsidiary/<year>/` | 445 | everything RONLAW files under category *laws* (regulations, orders, rules, notices) |
| **Total** | | **890** | |

RONLAW's *acts* collection mixes two kinds of documents, recorded in the `consolidation:` front
matter field:

- **consolidated reprints** from the *Laws of the Republic of Naoero* (`Service 4/5/6` or
  "consolidated reprint") — the current in-force text with a *Table of Amendments* and inline
  amendment notes such as `[subs (1) am Act 21 of 2026 s 5, opn 12 May 2026]`
  (acts: 218, subsidiary: 269);
- **texts as published** (`none (text as published)`) — mostly amending Acts, appropriation Acts
  and recent regulations not (yet) consolidated (acts: 226, subsidiary: 176). Their `status` is
  `unknown`.

## What is NOT covered

- Bills, gazettes, court decisions (also on RONLAW).
- *General Customs Duties (Mode of Collection) Regulations 1997* — no extractable text.
- Layout: the text is the per-page text that RONLAW extracts from each official PDF (served by its
  public search API); page headers/footers (`Service N`, page ids, running titles), tables of
  contents and the *Table of Provisions* are removed. Tables (incl. the tables of amendments) and
  forms are flattened to text. Headings: `## PART …`, `### DIVISION …`, `#### <section> <heading>`
  (constitution: `#### Article N …`), detected heuristically.

## Structure

```
constitution/constitution-of-naoero-1968.md
acts/<year>/<slug>.md          acts/2016/crimes-act-2016.md
subsidiary/<year>/<slug>.md
```

`identifier` is RONLAW's document id; `source` is the RONLAW PDF-viewer link and `source_file` the
document path on RONLAW. `year` is the year RONLAW files the document under.

## Sources and licence

- Official source: RONLAW (<https://ronlaw.gov.nr>), search API `https://ronlaw.gov.nr/api/pdf/search`
  (the same API the RONLAW web application uses). One request per category and year, sequential.
  No robots.txt is published and no terms of use restricting automated access were found
  (footer: "Copyright 2023 — Ronlaw. All rights reserved.").
- The texts are official legislation of the Republic of Nauru, reproduced verbatim (text only) as
  public legal information. This is not an official version; consult RONLAW for authoritative texts.

## Regenerate

```sh
python3 scripts/nr_fetch.py   ../_raw/nr      # API dumps per category/year (cached)
python3 scripts/nr_convert.py ../_raw/nr .
```
