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
  - `4x-techreport-*.bib` — technical reports.
  - `5x-degree-*.bib` — theses (doctoral / master's).
- `scripts/merge_bib.py` — utility to merge all files in `refs/` into `bb.bib`.

## Editing Rules

- Entries inside `refs/` are **kept complete** — do **not** trim `pages`, do **not**
  shorten URLs, and do **not** abbreviate venue names.
- Any trimming or shortening (e.g., dropping `pages`, replacing a long URL with a
  short link) should only be done in the per-paper working copy of the bibliography
  for a specific manuscript, never in this library.
- Conference papers must contain an explicit `year = {YYYY}` field.
- By local convention, web resources remain `@manual` entries with URLs in
  `note = {\url{...}}`.
- Use BibTeX month macros (`jan` through `dec`) instead of mixed month strings.

## Usage

Add or update entries in the appropriate file under `refs/`, then regenerate the
combined bibliography:

```bash
python scripts/merge_bib.py
```

The script also accepts custom inputs, output paths, and a filename regex:

```bash
# Defaults: merge refs/*-local.bib into bb.bib, then scan for duplicates.
python scripts/merge_bib.py

# Custom output file.
python scripts/merge_bib.py -o all-refs.bib

# Multiple inputs (directories and/or individual .bib files).
python scripts/merge_bib.py refs other_dir refs/extra.bib

# Change which filenames are picked up inside a directory (regex on basename).
python scripts/merge_bib.py -p '\.bib$'

# Skip the duplicate-title scan.
python scripts/merge_bib.py --no-dedup

# Sort each input file's entries by (year asc, key-prefix asc) before merging.
# Sorting is on by default; use --no-sort to keep the original order.
python scripts/merge_bib.py --no-sort

# Same sort, but also rewrite the source files in refs/ in place.
python scripts/merge_bib.py --sort-in-place

# Put newest entries first (or use "key" for cite-key ordering).
python scripts/merge_bib.py --sort-order year-desc

# Preview/apply conservative year and month normalization.
python scripts/normalize_bib.py
python scripts/normalize_bib.py --write
```

After merging, the script prints:

- Entry keys that don't end with a 4-digit year (likely naming-convention slips).
- **Duplicate groups** — entries sharing the same `@type` and a normalized
  title (lowercased, all non-alphanumeric characters stripped) are reported so
  you can clean them up by hand. Duplicates are *only flagged*, never deleted
  automatically.
- Duplicate cite keys (case-insensitive), duplicate DOIs, and missing core fields.

**Sorting details.** Entries are ordered by their explicit `year`/`date` field,
falling back to the trailing cite-key year, then by the full lowercased key.
`--sort-order` supports `year-asc`, `year-desc`, and `key`. Any comment or blank
line immediately above an entry travels with that entry, so banner comments
like `% === 2005 ===` stay attached to their first entry. Anything before the
first `@entry` is treated as a file header and left untouched.

Cite `bb.bib` from your LaTeX project, or copy individual entries as needed.

Happy Researching!
