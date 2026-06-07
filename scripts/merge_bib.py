
#!/usr/bin/env python3
import os
import re


def main():
    refs_dir = 'refs'
    output_file = 'bb.bib'

    # Find all -local.bib files. Here, I mean DO NOT upload your own references to public repositories ... I don't know why, but I will not do that. ^_^
    bib_files = []
    for filename in os.listdir(refs_dir):
        if filename.endswith('-local.bib'): 
            bib_files.append(filename)

    # Sort by the numeric prefix
    def get_number(filename):
        match = re.match(r'(\d+)', filename)
        return int(match.group(1)) if match else 9999

    bib_files.sort(key=get_number)

    print(f"Found {len(bib_files)} files to merge:")
    for f in bib_files:
        print(f"  {f}")

    # Merge all files
    all_content = []
    for filename in bib_files:
        filepath = os.path.join(refs_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        all_content.append(content)

    merged = '\n'.join(all_content)

    # Remove consecutive empty lines (replace 2+ with 1)
    lines = merged.split('\n')
    processed_lines = []
    empty_count = 0

    for line in lines:
        if line.strip() == '':
            empty_count += 1
            if empty_count == 1:
                processed_lines.append(line)
        else:
            empty_count = 0
            processed_lines.append(line)

    final_content = '\n'.join(processed_lines)

    # Write to bb.bib
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_content)

    print(f"\nMerged into {output_file}")

    # Find entry keys not ending with year
    # Pattern: @xxx{key,
    pattern = r'@\w+\{([^,]+),'
    entries = re.findall(pattern, merged)

    # Check if key ends with 4-digit year
    non_year_keys = []
    year_pattern = r'.*\d{4}$'

    for key in entries:
        if not re.match(year_pattern, key):
            non_year_keys.append(key)

    if non_year_keys:
        print(f"\nEntry keys NOT ending with a year ({len(non_year_keys)}):")
        for key in non_year_keys:
            print(f"  {key}")
    else:
        print("\nAll entry keys end with a year!")


if __name__ == '__main__':
    main()
