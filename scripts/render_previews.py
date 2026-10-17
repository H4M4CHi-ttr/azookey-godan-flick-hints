#!/usr/bin/env python3
"""Generate all README diagrams from Custard JSON, using only the standard library."""

import hashlib
import json
import math
import unicodedata
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIEWS = ROOT / 'previews'
NAMES = (
    'godan-gboard-like', 'qwerty-gboard-like', 'numbers-gboard-like',
    'symbols-gboard-like', 'godan-flick-hints', 'godan-android-width',
)
SHORT_TABS = {
    'godan_gboard_like': 'GODAN', 'qwerty_gboard_like': '英字',
    'numbers_gboard_like': '数字記号', 'symbols_gboard_like': '追加記号',
    'clipboard_history_tab': '履歴', 'emoji_tab': '絵文字',
    'flick_numbersymbols': '標準の数字記号', 'qwerty_numbers': '標準の数字',
}
SYSTEM_LABELS = {
    'enter': '改行', 'qwerty_shift': 'Shift', 'flick_kogaki': '小゛゜',
    'change_keyboard': '地球儀', 'flick_star123_tab': '☆123',
    'flick_abc_tab': 'ABC', 'flick_hira_tab': 'あいう',
}
ICON_LABELS = {
    'delete.left': '削除', 'arrowtriangle.left.fill': '←',
    'arrowtriangle.right.fill': '→', 'arrow.left.and.right': '⇔',
    'doc.on.clipboard': '貼付', 'list.bullet': 'タブバー',
    'keyboard.chevron.compact.down': '閉じる', 'xmark': '削除',
}
BG, PANEL, KEY = '#101827', '#1b273b', '#34435b'
INK, MUTED, ACCENT, INPUT, HOLD = '#f8fafc', '#c6d2e4', '#7dd3fc', '#fde68a', '#d8b4fe'
WIDTH = 1080


def units(value):
    return sum(1 if unicodedata.east_asian_width(c) in ('W', 'F') else 0.62 for c in value)


def key_label(item):
    key = item['key']
    if item['key_type'] == 'system':
        return SYSTEM_LABELS[key['type']]
    label = key['design']['label']
    if 'system_image' in label:
        return ICON_LABELS[label['system_image']]
    return label.get('main', label.get('text', ''))


def is_letter(item):
    label = key_label(item)
    return len(label) == 1 and label.isascii() and label.isalpha()


def input_label(text):
    return {' ': '半角空白', '　': '全角空白', '\t': 'Tab', '\n': '改行'}.get(text, text)


def action_label(actions, popup=None):
    """Describe the action itself; an icon label alone can be misleading."""
    actions = [a for a in actions if a['type'] not in ('complete', 'replace_last_characters')]
    if not actions:
        return '—'
    action = actions[0]
    kind = action['type']
    if kind == 'direct_input':
        value = action['text']
        if len(value) == 2 and actions[1:] == [{'type': 'move_cursor', 'count': -1}]:
            return value[0] + '│' + value[1] + '\nペアを挿入・内側へ'
        return input_label(value)
    if kind == 'input':
        text = action['text']
        if popup and text not in (' ', '　', '\t', '\n') and len(text) == 1 and text.isascii() and text.isalpha():
            return popup.get('text', text)
        return input_label(text)
    if kind == 'delete':
        return '右1文字削除' if action['count'] < 0 else '左1文字削除'
    if kind == 'smart_delete_default':
        return '句読点まで\n削除'
    if kind == 'move_cursor':
        return '1文字左へ' if action['count'] < 0 else '1文字右へ'
    if kind == 'smart_move_cursor':
        return '前の区切りへ' if action['direction'] == 'backward' else '次の区切りへ'
    if kind == 'move_tab':
        return SHORT_TABS[action['identifier']] + 'を開く'
    return {
        'paste': '貼り付け', 'toggle_cursor_bar': 'カーソルバー',
        'toggle_tab_bar': 'タブバー表示', 'dismiss_keyboard': 'キーボードを\n閉じる',
    }[kind]


def hold_label(key):
    data = key['longpress_actions']
    if data['repeat']:
        action = data['repeat'][0]
        if action['type'] == 'delete':
            return '長押し：左へ連続削除'
        if action['type'] == 'move_cursor':
            return '長押し：連続で' + ('左へ' if action['count'] < 0 else '右へ')
    if data['start']:
        return '長押し：' + action_label(data['start']).replace('\n', ' ')
    return None


class Diagram:
    def __init__(self, title, subtitle, height, sources=()):
        self.height = height
        fingerprints = {name + '.json': hashlib.sha256((ROOT / (name + '.json')).read_bytes()).hexdigest()
                        for name in sources}
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="title description">',
            f'<title id="title">{escape(title)}</title>',
            f'<desc id="description">{escape(subtitle)}</desc>',
            f'<metadata>{escape(json.dumps(fingerprints, ensure_ascii=False, sort_keys=True))}</metadata>',
            f'<rect width="{WIDTH}" height="{height}" rx="22" fill="{BG}"/>',
            '<g font-family="Noto Sans CJK JP, Noto Sans JP, sans-serif">',
        ]
        self.text(32, 42, title, 32, anchor='start', max_width=1016, weight=700)
        self.text(32, 81, subtitle, 24, MUTED, anchor='start', max_width=1016)

    def rect(self, x, y, w, h, color=PANEL, radius=16, stroke=None):
        extra = f' stroke="{stroke}" stroke-width="2"' if stroke else ''
        self.parts.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{radius}" fill="{color}"{extra}/>')

    def text(self, x, y, value, size=30, color=INK, anchor='middle', max_width=None, weight=400):
        if max_width and value:
            size = min(size, max_width / max(units(value), 1))
        self.parts.append(
            f'<text x="{x:g}" y="{y:g}" text-anchor="{anchor}" dominant-baseline="central" '
            f'font-size="{size:g}" font-weight="{weight}" fill="{color}">{escape(value)}</text>'
        )

    def lines(self, x, y, value, size=28, max_width=200, color=ACCENT):
        lines = value.split('\n')
        # Japanese labels wrap at the card's usable width, with no text truncation.
        wrapped = []
        for line in lines:
            part = ''
            for char in line:
                if part and units(part + char) * size > max_width:
                    wrapped.append(part)
                    part = ''
                part += char
            wrapped.append(part)
        for i, line in enumerate(wrapped):
            self.text(x, y + (i - (len(wrapped) - 1) / 2) * (size + 5),
                      line, size, color, max_width=max_width)

    def arrow(self, x1, y1, x2, y2, color=ACCENT, size=7):
        self.parts.append(f'<path d="M {x1:g} {y1:g} L {x2:g} {y2:g}" stroke="{color}" stroke-width="3" fill="none"/>')
        angle = math.atan2(y2 - y1, x2 - x1)
        points = [(x2, y2)] + [
            (x2 - size * math.cos(angle + d), y2 - size * math.sin(angle + d))
            for d in (-0.65, 0.65)
        ]
        self.parts.append(f'<polygon points="{" ".join(f"{x:g},{y:g}" for x, y in points)}" fill="{color}"/>')

    def icon(self, item, cx, cy, size=48):
        text = key_label(item)
        if text == '削除':
            scale = size / 48
            self.parts.append(
                f'<g transform="translate({cx:g} {cy:g}) scale({scale:g})" fill="none" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round">'
                '<path d="M -30 0 L -14 -20 H 26 V 20 H -14 Z"/>'
                '<path d="M -4 -9 L 14 9 M 14 -9 L -4 9"/></g>'
            )
        elif text == '地球儀':
            r = size * 0.48
            self.parts.append(
                f'<g fill="none" stroke="{INK}" stroke-width="3">'
                f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}"/>'
                f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{r / 2:g}" ry="{r:g}"/>'
                f'<path d="M {cx-r:g} {cy:g} H {cx+r:g} M {cx-r*.86:g} {cy-r*.5:g} H {cx+r*.86:g} M {cx-r*.86:g} {cy+r*.5:g} H {cx+r*.86:g}"/></g>'
            )
        elif text == '🙂記':
            r = size * 0.32
            fx = cx - size * 0.35
            self.parts.append(
                f'<g fill="none" stroke="{INK}" stroke-width="2.8">'
                f'<circle cx="{fx:g}" cy="{cy:g}" r="{r:g}"/>'
                f'<path d="M {fx-r*.46:g} {cy+r*.16:g} Q {fx:g} {cy+r*.8:g} {fx+r*.46:g} {cy+r*.16:g}"/></g>'
                f'<circle cx="{fx-r*.32:g}" cy="{cy-r*.2:g}" r="2" fill="{INK}"/>'
                f'<circle cx="{fx+r*.32:g}" cy="{cy-r*.2:g}" r="2" fill="{INK}"/>'
            )
            self.text(cx + size * 0.38, cy, '記', size * 0.75)
        else:
            self.text(cx, cy, text, size)

    def mark(self, name, index, variation):
        direction = variation['direction']
        self.parts.append(f'<g data-source="{name}.json" data-key-index="{index}" data-direction="{direction}">')
        self.parts.append(f'<desc>{escape(json.dumps(variation["key"]["press_actions"], ensure_ascii=False))}</desc>')

    def end_mark(self):
        self.parts.append('</g>')

    def save(self, name):
        (PREVIEWS / (name + '.svg')).write_text('\n'.join(self.parts + ['</g>', '</svg>']) + '\n')


def layout(name, tab):
    grid = tab['interface']['key_layout']
    rows, columns = grid['row_count'], grid['column_count']
    height = 152 + columns * 128
    d = Diagram(tab['metadata']['display_name'] + '｜配置',
                '中央の文字＝タップ　小さな文字＝JSONにある表示ヒント　特殊操作は次の図へ',
                height, [name])
    for index, item in enumerate(tab['interface']['keys']):
        p = item['specifier']
        x, y = 24 + p['x'] / rows * 1032 + 4, 108 + p['y'] * 128 + 5
        w, h = p['width'] / rows * 1032 - 8, p['height'] * 128 - 10
        special = item['key_type'] == 'system' or item['key']['design']['color'] == 'special'
        fill = '#315788' if item['key_type'] == 'system' and item['key']['type'] == 'enter' else '#25344d' if special else KEY
        d.rect(x, y, w, h, fill)
        d.parts.append(f'<g data-key-index="{index}"><desc>{escape(key_label(item))}</desc>')
        design = item['key'].get('design', {}).get('label', {})
        hints = design.get('directions', {})
        # Keep the visible label faithful: hidden variations appear in the flick guide.
        main_size = min(52, w / max(units(key_label(item)), 1) * .77)
        d.icon(item, x + w / 2, y + h / 2, main_size)
        for direction, hint in hints.items():
            hx, hy, mw = {
                'top': (x + w / 2, y + 20, w - 14),
                'bottom': (x + w / 2, y + h - 20, w - 14),
                'left': (x + w * .15, y + h / 2, w * .25),
                'right': (x + w * .85, y + h / 2, w * .25),
            }[direction]
            d.text(hx, hy, hint, 25, INPUT, max_width=mw)
        d.parts.append('</g>')
    d.text(32, height - 20, '配置とヒントの図です。色・文字サイズ・間隔・システムキー表示は本体設定に従います。',
           22, MUTED, anchor='start', max_width=1016)
    d.save(name)


def letter_wheels(name, tab):
    items = [(i, item) for i, item in enumerate(tab['interface']['keys']) if is_letter(item)]
    xs = sorted({item['specifier']['x'] for _, item in items})
    ys = sorted({item['specifier']['y'] for _, item in items})
    height = 142 + len(ys) * 250
    d = Diagram(tab['metadata']['display_name'] + '｜文字の全フリック',
                '周囲がフリック先。子音＋母音で変換。例：K → A で「か」、W → H → O で「うぉ」。',
                height, [name])
    for index, item in items:
        x = 24 + xs.index(item['specifier']['x']) * 348
        y = 108 + ys.index(item['specifier']['y']) * 250
        d.rect(x, y, 336, 238)
        key = item['key']
        d.text(x + 168, y + 27, 'タップ：' + action_label(key['press_actions']), 26, MUTED)
        d.rect(x + 123, y + 100, 90, 76, KEY, radius=12)
        d.icon(item, x + 168, y + 138, 47)
        for v in key['variations']:
            direction = v['direction']
            lx, ly, mw = {
                'top': (x + 168, y + 69, 260), 'bottom': (x + 168, y + 206, 260),
                'left': (x + 51, y + 138, 93), 'right': (x + 285, y + 138, 93),
            }[direction]
            d.mark(name, index, v)
            value = action_label(v['key']['press_actions'], v['key']['design']['label'])
            # A small letter wheel shows the result; the operation card explains paired input.
            if v['key']['press_actions'][0]['type'] == 'direct_input':
                value = value.split('\n')[0]
            d.lines(lx, ly, value, 30 if '\n' in value else 34, mw,
                    ACCENT if '\n' in value else INPUT)
            coords = {
                'top': (x + 168, y + 97, x + 168, y + 88),
                'bottom': (x + 168, y + 180, x + 168, y + 190),
                'left': (x + 120, y + 138, x + 107, y + 138),
                'right': (x + 216, y + 138, x + 229, y + 138),
            }[direction]
            d.arrow(*coords, color=INPUT)
            d.end_mark()
    d.text(32, height - 18, '│はカーソル。図にない方向は未割当。数字・括弧ペアは画像配置版のみ。小゛゜は本体設定に従います。',
           22, MUTED, anchor='start', max_width=1016)
    d.save(name + '-letters')


def qwerty_alternates(name, tab):
    items = [(i, item) for i, item in enumerate(tab['interface']['keys']) if is_letter(item)]
    d = Diagram('QWERTY（英字）｜上スワイプ・長押し',
                '上の数字・記号を、↑スワイプまたは長押しで入力。タップは下の英字です。',
                568, [name])
    for row in range(3):
        entries = sorted([(i, k) for i, k in items if k['specifier']['y'] == row],
                         key=lambda entry: entry[1]['specifier']['x'])
        start = (WIDTH - (len(entries) * 94 + (len(entries) - 1) * 10)) / 2
        for column, (index, item) in enumerate(entries):
            x, y = start + column * 104, 108 + row * 112
            d.rect(x, y, 94, 104, KEY, radius=12)
            variation = next(v for v in item['key']['variations'] if v['direction'] == 'top')
            assert variation['key']['press_actions'] == item['key']['longpress_actions']['start']
            d.mark(name, index, variation)
            d.text(x + 47, y + 18, action_label(variation['key']['press_actions']), 36, INPUT)
            d.arrow(x + 47, y + 62, x + 47, y + 46, INPUT)
            d.text(x + 47, y + 81, key_label(item), 36)
            d.end_mark()
    index, k = next((i, item) for i, item in items if key_label(item) == 'k')
    variation = next(v for v in k['key']['variations'] if v['direction'] == 'bottom')
    d.rect(32, 454, 1016, 74, '#25344d')
    d.mark(name, index, variation)
    d.text(540, 482, 'k ↓  →  ' + action_label(variation['key']['press_actions']).replace('\n', '　'), 31, ACCENT)
    d.end_mark()
    d.text(540, 510, '長押しは「(」だけ、下スワイプはペア入力。入力中の文字は先に確定します。', 22, MUTED)
    d.text(32, 550, '↑スワイプは長押しが成立する前に。Shift・Caps LockはazooKey標準の操作です。',
           22, MUTED, anchor='start', max_width=1016)
    d.save(name + '-letters')


def operation_cards(name, tab):
    items = []
    for i, item in enumerate(tab['interface']['keys']):
        if item['key_type'] != 'custom':
            continue
        key = item['key']
        if not key['variations'] and not hold_label(key):
            continue
        if is_letter(item) and key_label(item) not in ({'E', 'O', 'W'} if name == 'godan-gboard-like' else {'k'} if name == 'qwerty-gboard-like' else set()):
            continue
        items.append((i, item))
    height = 158 + math.ceil(len(items) / 2) * 396
    d = Diagram(tab['metadata']['display_name'] + '｜操作フリック',
                '中央のキーから矢印の方向へ。黄色＝文字入力、青色＝操作、紫色＝長押し、—＝未割当。',
                height, [name])
    for position, (index, item) in enumerate(items):
        x, y = 24 + (position % 2) * 526, 108 + (position // 2) * 396
        d.rect(x, y, 506, 380)
        key = item['key']
        label = key_label(item)
        heading = '絵文字・記号' if label == '🙂記' else label
        d.text(x + 253, y + 31, heading + ' キー', 32, max_width=454, weight=700)
        d.text(x + 253, y + 70, 'タップ：' + action_label(key['press_actions']).replace('\n', ' '),
               25, MUTED, max_width=454)
        d.rect(x + 201, y + 158, 104, 86, KEY, radius=13)
        d.icon(item, x + 253, y + 201, min(43, 90 / max(units(label), 1)))
        variations = {v['direction']: v for v in key['variations']}
        for direction in ('top', 'left', 'right', 'bottom'):
            lx, ly, mw = {
                'top': (x + 253, y + 117, 290), 'bottom': (x + 253, y + 291, 314),
                'left': (x + 85, y + 201, 146), 'right': (x + 421, y + 201, 146),
            }[direction]
            v = variations.get(direction)
            if not v:
                d.text(lx, ly, '—', 28, '#6c7e97')
                continue
            d.mark(name, index, v)
            value = action_label(v['key']['press_actions'], v['key']['design']['label'])
            if v['key']['longpress_actions']['repeat']:
                value += '\n保持で連続'
            kind = next(a['type'] for a in v['key']['press_actions'] if a['type'] != 'complete')
            if kind == 'delete':
                value = ('右1文字' if v['key']['press_actions'][0]['count'] < 0 else '左1文字') + '\n削除'
            color = INPUT if kind == 'input' else ACCENT
            d.lines(lx, ly, value, 27, mw, color)
            coords = {
                'top': (x + 253, y + 154, x + 253, y + 139),
                'bottom': (x + 253, y + 248, x + 253, y + 264),
                'left': (x + 197, y + 201, x + 170, y + 201),
                'right': (x + 309, y + 201, x + 336, y + 201),
            }[direction]
            d.arrow(*coords, color=color)
            d.end_mark()
        note = hold_label(key)
        if note:
            d.text(x + 253, y + 348, note, 24, HOLD, max_width=456)
    footer = ('空白の長押しでカーソルバー。指を離してから、そのバーで左右に移動します。'
              if name in ('godan-flick-hints', 'godan-android-width') else
              '貼付・履歴にはフルアクセス等の設定が必要。カーソルバーは指を離してから操作します。')
    d.text(32, height - 29, footer,
           22, MUTED, anchor='start', max_width=1016)
    d.save(name + '-flicks')


def switching(tabs):
    """Build the four-tab route map; every labelled route is looked up in JSON."""
    profiles = {tab['identifier']: (name, tab) for name, tab in tabs.items()}
    routes = []
    for source in ('godan_gboard_like', 'qwerty_gboard_like', 'numbers_gboard_like', 'symbols_gboard_like'):
        name, tab = profiles[source]
        for index, item in enumerate(tab['interface']['keys']):
            key = item['key']
            contexts = [('タップ', key.get('press_actions', []), None)]
            contexts += [('↑↓←→'[('top', 'bottom', 'left', 'right').index(v['direction'])],
                          v['key']['press_actions'], v) for v in key.get('variations', [])]
            for gesture, actions, variation in contexts:
                for action in actions:
                    if action.get('type') == 'move_tab' and action.get('tab_type') == 'custom':
                        routes.append((source, action['identifier'], key_label(item) + ' ' + gesture))
    labels = {}
    for source, target, caption in routes:
        labels.setdefault((source, target), []).append(caption)
    ids = ['godan_gboard_like', 'qwerty_gboard_like', 'numbers_gboard_like', 'symbols_gboard_like']
    d = Diagram('4タブの切替早見図', 'タップとフリックで移動できます。切替時は入力中の文字を確定します。',
                792, [profiles[i][0] for i in ids])
    for row, source in enumerate(ids):
        y = 116 + row * 158
        d.rect(24, y, 1032, 144)
        d.rect(40, y + 26, 172, 90, '#315788')
        d.text(126, y + 71, SHORT_TABS[source], 30, max_width=158, weight=700)
        targets = [(target, captions) for (origin, target), captions in labels.items() if origin == source]
        for column, (target, captions) in enumerate(targets):
            x = 242 + column * 264
            d.lines(x + 120, y + 36, '\n'.join(captions).replace('🙂記', '絵文字キー'),
                    22, 238, INPUT)
            d.arrow(x + 24, y + 78, x + 216, y + 78)
            d.text(x + 120, y + 111, SHORT_TABS[target], 29, ACCENT)
    d.text(32, 767, '絵文字・履歴など標準タブから戻るときは、タブバーでカスタムタブを選びます。',
           22, MUTED, anchor='start', max_width=1016)
    d.save('tab-switching')


def verify_coverage(tabs):
    """Ensure every JSON flick appears with its exact action payload in a guide."""
    import xml.etree.ElementTree as ET
    expected, actual = {}, {}
    for name, tab in tabs.items():
        for index, item in enumerate(tab['interface']['keys']):
            for v in item['key'].get('variations', []):
                expected[(name + '.json', str(index), v['direction'])] = v['key']['press_actions']
    for path in PREVIEWS.glob('*.svg'):
        for group in ET.parse(path).iter('{http://www.w3.org/2000/svg}g'):
            if 'data-direction' not in group.attrib:
                continue
            key = (group.attrib['data-source'], group.attrib['data-key-index'], group.attrib['data-direction'])
            desc = group.find('{http://www.w3.org/2000/svg}desc')
            value = json.loads(desc.text)
            assert key not in actual or actual[key] == value, f'Conflicting diagram action: {key}'
            actual[key] = value
    assert actual == expected, f'Diagram coverage differs: missing={expected.keys()-actual.keys()}, extra={actual.keys()-expected.keys()}'
    print(f'OK: all {len(expected)} flick directions covered with matching action payloads')


def main():
    PREVIEWS.mkdir(exist_ok=True)
    tabs = {name: json.loads((ROOT / (name + '.json')).read_text()) for name in NAMES}
    for name, tab in tabs.items():
        layout(name, tab)
        operation_cards(name, tab)
        if name.startswith('godan'):
            letter_wheels(name, tab)
        elif name.startswith('qwerty'):
            qwerty_alternates(name, tab)
    switching(tabs)
    verify_coverage(tabs)
    print('Rendered 17 diagrams: 6 layouts, 6 operation guides, 4 letter guides, and tab switching')


if __name__ == '__main__':
    main()
