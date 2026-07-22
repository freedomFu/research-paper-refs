#!/usr/bin/env python3
"""Apply conservative, repeatable normalizations to source BibTeX files."""
import argparse
import pathlib
import re

import merge_bib


MONTHS = {
    'jan': 'jan', 'january': 'jan', 'feb': 'feb', 'february': 'feb',
    'mar': 'mar', 'march': 'mar', 'apr': 'apr', 'april': 'apr',
    'may': 'may', 'jun': 'jun', 'june': 'jun', 'jul': 'jul', 'july': 'jul',
    'aug': 'aug', 'august': 'aug', 'sep': 'sep', 'sept': 'sep',
    'september': 'sep', 'oct': 'oct', 'october': 'oct', 'nov': 'nov',
    'november': 'nov', 'dec': 'dec', 'december': 'dec',
}


def add_missing_conference_years(text):
    """Add year fields from four-digit cite-key suffixes when unambiguous."""
    replacements = []
    for etype, key, body, start, end in merge_bib.iter_entries(text):
        if etype.lower() != 'inproceedings' or merge_bib.extract_field(body, 'year'):
            continue
        match = re.search(r'(\d{4})$', key)
        if not match:
            continue
        base = body[:-1].rstrip()
        separator = '\n' if base.endswith(',') else ',\n'
        replacements.append((start, end, f'{base}{separator}year = {{{match.group(1)}}}\n}}'))
    for start, end, replacement in reversed(replacements):
        text = text[:start] + replacement + text[end:]
    return text, len(replacements)


def normalize_months(text):
    """Convert legacy braced month names to portable BibTeX month macros."""
    text = re.sub(r'(?im)^(\s*)monthh(\s*=)', r'\1month\2', text)
    pattern = re.compile(r'(?im)^(\s*month\s*=\s*)\{([A-Za-z]+)\.?\}(\s*,?\s*)$')

    def replace(match):
        month = MONTHS.get(match.group(2).lower())
        if not month:
            return match.group(0)
        return f'{match.group(1)}{month}{match.group(3)}'

    return pattern.sub(replace, text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', default='refs')
    parser.add_argument('--write', action='store_true', help='Rewrite changed files.')
    args = parser.parse_args()

    changed = 0
    years_added = 0
    for path in sorted(pathlib.Path(args.directory).glob('*-local.bib')):
        original = path.read_text(encoding='utf-8')
        normalized, count = add_missing_conference_years(original)
        normalized = normalize_months(normalized)
        if normalized != original:
            changed += 1
            years_added += count
            print(f'{path}: changed (conference years added: {count})')
            if args.write:
                path.write_text(normalized, encoding='utf-8')
    action = 'Updated' if args.write else 'Would update'
    print(f'{action} {changed} file(s); conference years added: {years_added}.')


if __name__ == '__main__':
    main()
