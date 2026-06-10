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
    m = TITLE_RE.search(entry_body)
    if not m:
        return ''
    i = m.end() - 1
    opener = entry_body[i]
    closer = '}' if opener == '{' else '"'
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
                    return entry_body[start:i]
            i += 1
        return entry_body[start:i]
    else:
        i += 1
        start = i
        while i < len(entry_body) and entry_body[i] != closer:
            i += 1
        return entry_body[start:i]


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


def entry_sort_key(bib_key):
    """Sort key: (year, prefix_lower).

    The trailing 4 digits of `bib_key` are treated as the year; if missing,
    the entry sinks to the bottom (year = 9999) and is ordered by the full
    lowercased key.
    """
    m = re.search(r'(\d{4})$', bib_key)
    if m:
        year = int(m.group(1))
        prefix = bib_key[:m.start()].lower()
    else:
        year = 9999
        prefix = bib_key.lower()
    return (year, prefix)


def sort_entries_in_text(text):
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
    for idx, (_etype, key, _body, start, end) in enumerate(entries):
        chunk_start = entries[idx - 1][4] if idx > 0 else entries[0][3]
        chunks.append((entry_sort_key(key), text[chunk_start:end]))
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
            sorted_text = sort_entries_in_text(text)
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

    return 0


if __name__ == '__main__':
    sys.exit(main())
