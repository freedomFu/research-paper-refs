# A Library for Research Paper Refs

A personal library of BibTeX references for academic writing.

## Naming Convention

Each entry follows the pattern: **`Author + Topic/Venue + Year`**

## Repository Layout

- `bb.bib` — aggregated bibliography (generated from the files under `refs/`).
- `refs/` — source `.bib` files, organized by entry type and topic:
  - `0x-*-example.bib` — examples for each entry type (journal, conference, url).
  - `1x-journal-*.bib` — journal articles, grouped by topic
    (authentication, HCI, web, other).
  - `2x-conference-*.bib` — conference papers, grouped by the same topics.
  - `3x-url-*.bib` — web resources (authentication, HCI, web, general).
  - `41-techreport-*.bib` — technical reports.
  - `5x-degree-*.bib` — theses (doctoral / master's).
- `scripts/merge_bib.py` — utility to merge all files in `refs/` into `bb.bib`.

## Editing Rules

- Entries inside `refs/` are **kept complete** — do **not** trim `pages`, do **not**
  shorten URLs, and do **not** abbreviate venue names.
- Any trimming or shortening (e.g., dropping `pages`, replacing a long URL with a
  short link) should only be done in the per-paper working copy of the bibliography
  for a specific manuscript, never in this library.

## Usage

Add or update entries in the appropriate file under `refs/`, then regenerate the
combined bibliography:

```bash
python scripts/merge_bib.py
```

Cite `bb.bib` from your LaTeX project, or copy individual entries as needed.

Happy Researching!