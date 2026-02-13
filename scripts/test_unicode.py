#!/usr/bin/env python3
import sys
import unicodedata

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)


def clean_text(text):
    """Clean non-ASCII characters from text."""
    # Handle known mojibake patterns FIRST
    for pattern in [
        chr(0xe2) + chr(0x20ac) + chr(0x201c),  # em-dash
        chr(0xe2) + chr(0x20ac) + chr(0x201d),
        chr(0xe2) + chr(0x20ac) + chr(0x2122),
        chr(0xe2) + chr(0x20ac) + chr(0x153),
    ]:
        text = text.replace(pattern, '-')

    # Try to fix double-encoded UTF-8
    try:
        fixed = text.encode('latin-1').decode('utf-8')
        text = fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        result = []
        i = 0
        while i < len(text):
            try:
                chunk = text[i:i + 4].encode('latin-1').decode('utf-8')
                result.append(chunk[0])
                consumed = len(chunk[0].encode('utf-8'))
                i += consumed
            except (UnicodeDecodeError, UnicodeEncodeError):
                result.append(text[i])
                i += 1
        text = ''.join(result)

    # Strip accents
    nfkd = unicodedata.normalize('NFKD', text)
    cleaned = ''.join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = cleaned.encode('ascii', 'ignore').decode('ascii')
    # Clean up double spaces
    while '  ' in cleaned:
        cleaned = cleaned.replace('  ', ' ')
    return cleaned.strip()


tests = [
    ('Paradise Caf\u00c3\u00a9', 'Paradise Cafe'),
    ('D\u00c3\u0089J\u00c3\u0080 VU', 'DEJA VU'),
    ('DESIR\u00c3\u0089E', 'DESIREE'),
    ('Fr\u00c3\u00a8re Jacques', 'Frere Jacques'),
    ('Another Brick In The Wall \u00e2\u20ac\u201c Part 2', 'Another Brick In The Wall - Part 2'),
    ('W\u00c3\u00bcRM', 'WuRM'),
    ('Ti Guarder\u00c3\u00b2 Nel Cuore', 'Ti Guardero Nel Cuore'),
]

all_pass = True
for text, expected in tests:
    result = clean_text(text)
    status = 'OK' if result == expected else 'FAIL'
    if status == 'FAIL':
        all_pass = False
    print(f'  [{status}] "{text}" -> "{result}" (expected: "{expected}")')

print(f'\nAll pass: {all_pass}')
