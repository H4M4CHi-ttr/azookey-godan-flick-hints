#!/usr/bin/env python3
"""Synchronize GODAN's direct-composition tables with the pinned kana reference."""

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODAN_FILES = (
    'godan-gboard-like.json', 'godan-flick-hints.json', 'godan-android-width.json',
)


def letter_routes(tab):
    routes = {}
    for item in tab['interface']['keys']:
        if item['key_type'] != 'custom':
            continue
        key = item['key']
        label = key['design']['label']
        main = label.get('main', label.get('text', ''))
        if len(main) == 1 and main.isascii() and main.isalpha():
            routes[main.lower()] = key
        for variation in key['variations']:
            node = variation['key']
            text = node['design']['label'].get('text', '')
            if len(text) == 1 and text.isascii() and text.isalpha():
                routes[text.lower()] = node
    return routes


def replacement_table(node):
    return next(a['table'] for a in node['press_actions']
                if a['type'] == 'replace_last_characters')


def input_text(node):
    return next(a['text'] for a in node['press_actions'] if a['type'] == 'input')


def synchronize(tab, syllables):
    """Modify only replacement tables, leaving geometry and all gestures intact."""
    routes = letter_routes(tab)
    for vowel in 'aiueo':
        key = routes[vowel]
        variations = {v['direction']: v['key'] for v in key['variations']}
        for node, suffix in [(key, ''), (variations['left'], 'っ'),
                             (variations['top'], 'ん')]:
            table = replacement_table(node)
            inserted = input_text(node)
            for roman, kana in syllables.items():
                if roman.endswith(vowel) and len(roman) > 1:
                    table[roman[:-1] + inserted] = kana + suffix
            # An inherited typo changed wya into unrelated りゃ.
            if vowel == 'a':
                table.pop('wy' + inserted, None)

        right = variations['right']
        table, inserted = replacement_table(right), input_text(right)
        # Explicit multi-consonant prefixes use the corresponding kana syllable;
        # retain the existing single-consonant GODAN shorthand (kゃ -> きゃ etc.).
        for roman, kana in syllables.items():
            if roman.endswith(vowel) and len(roman) >= 3:
                table[roman[:-1] + inserted] = kana
        table['c' + inserted] = syllables['cy' + vowel]
        if vowel == 'o':
            table['w' + inserted] = 'うぉ'  # wょ was incorrectly うぅ.

    replacement_table(routes['n'])['xn'] = 'ん'
    replacement_table(routes['h'])['tch'] = 'っch'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail on stale tables without writing')
    parser.add_argument('--root', type=Path, default=ROOT, help='repository root')
    args = parser.parse_args()
    root = args.root
    reference = json.loads((root / 'data/romaji-kana.json').read_text(encoding='utf-8'))
    syllables = {**reference['syllables'], **reference['legacy_aliases']}
    updated, changed = {}, []
    for name in GODAN_FILES:
        original = json.loads((root / name).read_text(encoding='utf-8'))
        tab = copy.deepcopy(original)
        synchronize(tab, syllables)
        updated[name] = tab
        if tab != original:
            changed.append(name)

    bundle_path = 'gboard-like-pair.json'
    bundle = json.loads((root / bundle_path).read_text(encoding='utf-8'))
    godan = updated[GODAN_FILES[0]]
    assert sum(tab['identifier'] == godan['identifier'] for tab in bundle) == 1
    expected_bundle = [godan if tab['identifier'] == godan['identifier'] else tab
                       for tab in bundle]
    updated[bundle_path] = expected_bundle
    if expected_bundle != bundle:
        changed.append(bundle_path)
    if args.check:
        if changed:
            print('Stale romanization tables: ' + ', '.join(changed))
            raise SystemExit(1)
        print(f'OK: {len(reference['syllables'])} reference syllables + {len(reference['legacy_aliases'])} inherited aliases synchronized across 3 GODAN layouts and bundle')
        return
    for name in changed:
        (root / name).write_text(
            json.dumps(updated[name], ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
    print('Updated: ' + ', '.join(changed) if changed else 'No romanization changes needed')


if __name__ == '__main__':
    main()
