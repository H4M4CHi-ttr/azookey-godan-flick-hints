#!/usr/bin/env python3
"""Check Custard JSON structure, geometry, tab links, and bundled contents."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTIONS = {'left', 'top', 'right', 'bottom'}
SYSTEM_TABS = {
    'user_japanese', 'user_english', 'flick_japanese', 'flick_english',
    'flick_numbersymbols', 'qwerty_japanese', 'qwerty_english', 'qwerty_numbers',
    'qwerty_symbols', 'last_tab', 'clipboard_history_tab', 'emoji_tab',
}
SYSTEM_KEYS = {
    'change_keyboard', 'enter', 'flick_abc_tab', 'flick_hira_tab',
    'flick_kogaki', 'flick_star123_tab', 'qwerty_shift',
}
SINGLES = [
    'godan-gboard-like.json', 'qwerty-gboard-like.json',
    'numbers-gboard-like.json', 'symbols-gboard-like.json',
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_label(label):
    kind = label.get('type')
    if kind in ('main_and_directions', 'main_and_sub'):
        require(isinstance(label.get('main'), str), 'Missing main label')
        if kind == 'main_and_sub':
            require(isinstance(label.get('sub'), str), 'Missing sub label')
        else:
            directions = label.get('directions')
            require(isinstance(directions, dict), 'Missing directional labels')
            require(set(directions) <= DIRECTIONS, 'Unknown label direction')
            require(all(isinstance(v, str) for v in directions.values()), 'Invalid hint')
    else:
        value = label.get('text', label.get('system_image'))
        require(kind in (None, 'text', 'system_image') and isinstance(value, str), 'Invalid label')


def check_actions(actions, identifiers, edges):
    require(isinstance(actions, list), 'Actions must be an array')
    for action in actions:
        kind = action.get('type')
        if kind in ('input', 'direct_input'):
            require(isinstance(action.get('text'), str), 'Missing input text')
        elif kind in ('delete', 'move_cursor'):
            require(type(action.get('count')) is int, 'Movement/deletion count must be an integer')
        elif kind == 'replace_last_characters':
            table = action.get('table')
            require(isinstance(table, dict) and all(isinstance(v, str) for v in table.values()),
                    'Invalid replacement table')
        elif kind == 'smart_move_cursor':
            require(action.get('direction') in ('forward', 'backward'), 'Invalid scan direction')
            targets = action.get('targets')
            require(isinstance(targets, list) and all(isinstance(t, str) and len(t) == 1 for t in targets),
                    'Scan targets must be individual characters')
        elif kind == 'move_tab':
            target = action.get('identifier')
            tab_type = action.get('tab_type')
            require(tab_type in ('custom', 'system'), 'Unknown tab type')
            require(target in (identifiers if tab_type == 'custom' else SYSTEM_TABS),
                    f'Unresolved tab target: {target}')
            if tab_type == 'custom':
                edges.add(target)
        else:
            require(kind in {'complete', 'dismiss_keyboard', 'paste', 'smart_delete_default',
                             'toggle_cursor_bar', 'toggle_tab_bar'}, f'Unsupported action: {kind}')


def check_longpress(data, identifiers, edges):
    require(data.get('duration', 'normal') in ('normal', 'light'), 'Unknown longpress duration')
    for name in ('start', 'repeat'):
        check_actions(data.get(name), identifiers, edges)


def check_tab(tab, identifiers):
    require(tab['language'] in {'ja_JP', 'en_US', 'el_GR', 'none', 'undefined'}, 'Unknown language')
    require(tab['input_style'] in {'direct', 'roman2kana'}, 'Unknown input style')
    require(tab['metadata']['custard_version'] in {'1.0', '1.1', '1.2'}, 'Unknown Custard version')
    require(isinstance(tab['metadata']['display_name'], str), 'Missing display name')
    interface = tab['interface']
    require(interface['key_style'] in {'tenkey_style', 'pc_style'}, 'Unknown key style')
    layout = interface['key_layout']
    require(layout['type'] == 'grid_fit', 'This checker expects grid_fit layouts')
    width, height = layout['row_count'], layout['column_count']
    require(type(width) is int and type(height) is int and width > 0 and height > 0, 'Invalid grid size')
    positions, edges = [], set()
    for item in interface['keys']:
        require(item['specifier_type'] == 'grid_fit', 'Unexpected position specifier')
        p = item['specifier']
        x, y, w, h = (p[n] for n in ('x', 'y', 'width', 'height'))
        require(all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, y, w, h)),
                'Invalid coordinates')
        require(w > 0 and h > 0 and x >= 0 and y >= 0 and x + w <= width and y + h <= height,
                f'Key outside grid: {p}')
        for px, py, pw, ph in positions:
            require(not (x < px + pw and px < x + w and y < py + ph and py < y + h),
                    f'Overlapping key: {p}')
        positions.append((x, y, w, h))
        key = item['key']
        if item['key_type'] == 'system':
            require(key['type'] in SYSTEM_KEYS, f'Unknown system key: {key["type"]}')
            require(set(key) == {'type'}, 'System keys cannot carry custom variations')
            continue
        require(item['key_type'] == 'custom', 'Unknown key type')
        check_label(key['design']['label'])
        require(key['design']['color'] in {'normal', 'special', 'selected', 'unimportant'}, 'Unknown color')
        check_actions(key['press_actions'], identifiers, edges)
        check_longpress(key['longpress_actions'], identifiers, edges)
        seen = set()
        for variation in key['variations']:
            require(variation['type'] == 'flick_variation', 'Unexpected variation type')
            direction = variation['direction']
            require(direction in DIRECTIONS and direction not in seen, 'Invalid or duplicate flick direction')
            seen.add(direction)
            vkey = variation['key']
            check_label(vkey['design']['label'])
            check_actions(vkey['press_actions'], identifiers, edges)
            check_longpress(vkey['longpress_actions'], identifiers, edges)
    return edges


def main():
    tabs = {p.name: json.loads(p.read_text()) for p in ROOT.glob('*.json') if p.name != 'gboard-like-pair.json'}
    identifiers = {tab['identifier'] for tab in tabs.values()}
    require(len(identifiers) == len(tabs), 'Duplicate standalone tab identifier')
    graph = {}
    for path, tab in tabs.items():
        try:
            graph[tab['identifier']] = check_tab(tab, identifiers)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f'{path}: {error}') from error
    bundle = json.loads((ROOT / 'gboard-like-pair.json').read_text())
    require(bundle == [tabs[name] for name in SINGLES], 'Bundle differs from standalone tabs')
    bundle_ids = {t['identifier'] for t in bundle}
    for start in bundle_ids:
        reached, pending = set(), [start]
        while pending:
            current = pending.pop()
            if current in reached:
                continue
            reached.add(current)
            pending.extend(graph[current] - reached)
        require(bundle_ids <= reached, f'Cannot reach every bundled tab from {start}')
    numbers = tabs['numbers-gboard-like.json']
    for y, expected in [(0, list('1234567890')),
                        (1, ['-', '/', ':', ';', '(', ')', '$', '&', '@', '"'])]:
        row = sorted((k for k in numbers['interface']['keys'] if k['specifier']['y'] == y),
                     key=lambda k: k['specifier']['x'])
        require([k['key']['press_actions'] for k in row] ==
                [[{'type': 'input', 'text': t}] for t in expected], 'Reference row differs')
    print(f'OK: {len(tabs)} standalone tabs, 4-tab bundle, geometry, actions, and tab links')


if __name__ == '__main__':
    main()
