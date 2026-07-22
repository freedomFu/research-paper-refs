#!/usr/bin/env python3
"""Merge .bib files and optionally detect duplicate entries.

Default behaviour matches the original script: merge all `*-local.bib`
files under ./refs into ./bb.bib. Inputs and output can be overridden,
and a regex can replace the default `-local.bib` suffix match.
"""
import argparse
import os
import re
import sys
from collections import defaultdict


def collect_files(inputs, pattern):
    """Expand the user-provided inputs into a sorted list of .bib files.

    Each input can be a directory (scanned with `pattern`) or a single file.
    """
    files = []
    for item in inputs:
        if os.path.isdir(item):
            for name in os.listdir(item):
                full = os.path.join(item, name)
                if os.path.isfile(full) and pattern.search(name):
                    files.append(full)
        elif os.path.isfile(item):
            files.append(item)
        else:
            print(f"Warning: {item} is neither a file nor a directory, skipping.")

    def sort_key(path):
        name = os.path.basename(path)
        m = re.match(r'(\d+)', name)
        return (int(m.group(1)) if m else 9999, name)

    files.sort(key=sort_key)
    return files


def collapse_blank_lines(text):
    """Collapse runs of blank lines into a single blank line."""
    lines = text.split('\n')
    out = []
    empty = 0
    for line in lines:
        if line.strip() == '':
            empty += 1
            if empty == 1:
                out.append(line)
        else:
            empty = 0
            out.append(line)
    return '\n'.join(out)


# Match a full bib entry: @type{key, ... } with balanced braces.
ENTRY_RE = re.compile(r'@(\w+)\s*\{\s*([^,\s]+)\s*,', re.IGNORECASE)


def iter_entries(text):
    """Yield (entry_type, key, body, start, end) for every @entry in text.

    `body` is the full entry source (from `@` to the matching closing brace).
    """
    for m in ENTRY_RE.finditer(text):
        start = m.start()
        # Walk forward to find the matching closing brace.
        i = text.find('{', m.start())
        depth = 0
        end = None
        while i < len(text):
            c = text[i]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
            i += 1
        if end is None:
            end = len(text)
        yield m.group(1), m.group(2), text[start:end], start, end


# Require a non-letter before `title` so we don't match `booktitle`, `subtitle`, etc.
TITLE_RE = re.compile(r'(?:^|[^A-Za-z])title\s*=\s*[\{"]', re.IGNORECASE)


def extract_title(entry_body):
    """Return the raw title field value, or '' if not found."""
    return extract_field(entry_body, 'title')


def extract_field(entry_body, field):
    """Return a braced or quoted BibTeX field value, or '' if absent."""
    field_re = re.compile(
        rf'(?:^|[^A-Za-z]){re.escape(field)}\s*=\s*[\{{"]', re.IGNORECASE
    )
    m = field_re.search(entry_body)
    if not m:
        return ''
    i = m.end() - 1
    opener = entry_body[i]
    if opener == '{':
        depth = 1
        i += 1
        start = i
        while i < len(entry_body) and depth > 0:
            if entry_body[i] == '{':
                depth += 1
            elif entry_body[i] == '}':
                depth -= 1
                if depth == 0:
                    return entry_body[start:i].strip()
            i += 1
        return entry_body[start:i].strip()
    i += 1
    start = i
    escaped = False
    while i < len(entry_body):
        if entry_body[i] == '"' and not escaped:
            return entry_body[start:i].strip()
        escaped = entry_body[i] == '\\' and not escaped
        if entry_body[i] != '\\':
            escaped = False
        i += 1
    return entry_body[start:i].strip()


def normalize_title(title):
    """Lowercase, strip every non-alphanumeric character."""
    return re.sub(r'[^0-9a-z]+', '', title.lower())


def find_duplicates(text):
    """Group entries by (entry_type, normalized_title); return dup groups."""
    groups = defaultdict(list)
    for etype, key, body, _, _ in iter_entries(text):
        title = extract_title(body)
        norm = normalize_title(title)
        if not norm:
            continue
        groups[(etype.lower(), norm)].append((key, title))
    return {k: v for k, v in groups.items() if len(v) > 1}


def find_duplicate_identifiers(text, field):
    """Return duplicate groups for a case-insensitive identifier field."""
    groups = defaultdict(list)
    for _etype, key, body, _, _ in iter_entries(text):
        value = extract_field(body, field).strip().lower()
        if field.lower() == 'doi':
            value = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', value)
            value = re.sub(r'^doi:\s*', '', value)
        if value:
            groups[value].append(key)
    return {value: keys for value, keys in groups.items() if len(keys) > 1}


def find_duplicate_keys(text):
    """Return duplicate cite keys (case-insensitive)."""
    groups = defaultdict(list)
    for _etype, key, _body, _, _ in iter_entries(text):
        groups[key.lower()].append(key)
    return {key: values for key, values in groups.items() if len(values) > 1}


def validate_entries(text):
    """Return human-readable warnings for missing core bibliography fields."""
    warnings = []
    dated_types = {
        'article', 'book', 'inbook', 'incollection', 'inproceedings',
        'manual', 'mastersthesis', 'phdthesis', 'proceedings', 'techreport',
    }
    for etype, key, body, _, _ in iter_entries(text):
        kind = etype.lower()
        missing = []
        if not extract_field(body, 'title'):
            missing.append('title')
        if kind in dated_types and not (
            extract_field(body, 'year') or extract_field(body, 'date')
        ):
            missing.append('year/date')
        if kind == 'article' and not (
            extract_field(body, 'journal') or extract_field(body, 'journaltitle')
        ):
            missing.append('journal/journaltitle')
        if kind == 'inproceedings' and not extract_field(body, 'booktitle'):
            missing.append('booktitle')
        if kind == 'techreport' and not extract_field(body, 'institution'):
            missing.append('institution')
        if kind == 'manual' and not (
            extract_field(body, 'url') or extract_field(body, 'note')
        ):
            missing.append('url/note')
        if missing:
            warnings.append(f"{key} (@{etype}): missing {', '.join(missing)}")
    return warnings


def entry_sort_key(bib_key, entry_body='', order='year-asc'):
    """Sort by explicit year/date, falling back to the cite-key suffix.

    The trailing 4 digits of `bib_key` are treated as the year; if missing,
    the entry sinks to the bottom (year = 9999) and is ordered by the full
    lowercased key.
    """
    if order == 'key':
        return (bib_key.lower(),)
    raw_year = extract_field(entry_body, 'year') or extract_field(entry_body, 'date')
    m = re.search(r'\d{4}', raw_year) or re.search(r'(\d{4})$', bib_key)
    year = int(m.group(0)) if m else None
    if order == 'year-desc':
        return (-(year if year is not None else -1), bib_key.lower())
    return (year if year is not None else 9999, bib_key.lower())


def sort_entries_in_text(text, order='year-asc'):
    """Re-emit `text` with its @entries sorted by (year, prefix).

    Any non-entry text (comments, blank lines) that sits between two entries
    is attached to the entry that follows it, so banner comments like
    `% === 2005 ===` travel with the first entry of their block. Text before
    the first entry is preserved verbatim as a file header.
    """
    entries = list(iter_entries(text))
    if not entries:
        return text

    header = text[:entries[0][3]]
    chunks = []  # (sort_key, chunk_text)
    for idx, (_etype, key, body, start, end) in enumerate(entries):
        chunk_start = entries[idx - 1][4] if idx > 0 else entries[0][3]
        chunks.append((entry_sort_key(key, body, order), text[chunk_start:end]))
    trailing = text[entries[-1][4]:]

    chunks.sort(key=lambda kv: kv[0])
    return header + ''.join(c for _, c in chunks) + trailing


def parse_args(argv):
    p = argparse.ArgumentParser(description='Merge .bib files and detect duplicates.')
    p.add_argument(
        'inputs', nargs='*', default=['refs'],
        help='Files and/or directories to merge (default: refs/).',
    )
    p.add_argument(
        '-o', '--output', default='bb.bib',
        help='Output .bib file (default: bb.bib).',
    )
    p.add_argument(
        '-p', '--pattern', default=r'-local\.bib$',
        help='Regex applied to filenames inside input directories '
            '(default: -local\\.bib$).',
    )
    p.add_argument(
        '--no-dedup', action='store_true',
        help='Skip the duplicate-title scan.',
    )
    p.add_argument(
        '--no-sort', action='store_true',
        help='Do not sort entries within each input file before merging.',
    )
    p.add_argument(
        '--sort-in-place', action='store_true',
        help='Also rewrite each source file with its entries sorted.',
    )
    p.add_argument(
        '--sort-order', choices=('year-asc', 'year-desc', 'key'),
        default='year-asc',
        help='Entry order within each input file (default: year-asc).',
    )
    p.add_argument(
        '--no-validate', action='store_true',
        help='Skip checks for missing core fields.',
    )
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        pattern = re.compile(args.pattern)
    except re.error as e:
        print(f"Invalid regex {args.pattern!r}: {e}")
        return 2

    bib_files = collect_files(args.inputs, pattern)
    if not bib_files:
        print("No .bib files matched.")
        return 1

    print(f"Found {len(bib_files)} files to merge:")
    for f in bib_files:
        print(f"  {f}")

    chunks = []
    for path in bib_files:
        with open(path, 'r', encoding='utf-8') as fh:
            text = fh.read()
        if not args.no_sort:
            sorted_text = sort_entries_in_text(text, args.sort_order)
            if args.sort_in_place and sorted_text != text:
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(sorted_text)
                print(f"  (sorted in place: {path})")
            text = sorted_text
        chunks.append(text)
    merged = '\n'.join(chunks)
    final = collapse_blank_lines(merged)

    with open(args.output, 'w', encoding='utf-8') as fh:
        fh.write(final)
    print(f"\nMerged into {args.output}")

    # Entry keys not ending in a 4-digit year.
    keys = [k for _, k, _, _, _ in iter_entries(merged)]
    non_year = [k for k in keys if not re.search(r'\d{4}$', k)]
    if non_year:
        print(f"\nEntry keys NOT ending with a year ({len(non_year)}):")
        for k in non_year:
            print(f"  {k}")
    else:
        print("\nAll entry keys end with a year!")

    # Duplicate detection.
    if not args.no_dedup:
        duplicate_keys = find_duplicate_keys(merged)
        if duplicate_keys:
            print(f"\nDuplicate cite keys detected ({len(duplicate_keys)} group(s)):")
            for _normalized, keys in duplicate_keys.items():
                print(f"  {', '.join(keys)}")

        duplicate_dois = find_duplicate_identifiers(merged, 'doi')
        if duplicate_dois:
            print(f"\nDuplicate DOIs detected ({len(duplicate_dois)} group(s)):")
            for doi, keys in duplicate_dois.items():
                print(f"  {doi}: {', '.join(keys)}")

        dups = find_duplicates(merged)
        if dups:
            print(f"\nDuplicate entries detected ({len(dups)} group(s)):")
            for (etype, _norm), items in dups.items():
                print(f"  @{etype} -- {len(items)} entries with the same title:")
                for key, title in items:
                    short = title.strip().replace('\n', ' ')
                    if len(short) > 80:
                        short = short[:77] + '...'
                    print(f"    {key}  |  {short}")
        else:
            print("\nNo duplicate titles found.")

    if not args.no_validate:
        warnings = validate_entries(merged)
        if warnings:
            print(f"\nCore-field warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  {warning}")
        else:
            print("\nAll entries contain their core fields.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
