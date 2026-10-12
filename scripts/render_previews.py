#!/usr/bin/env python3
"""Render static layout diagrams from the distributable JSON (no third-party packages)."""

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIEWS = ROOT / 'previews'


def label(item):
    key = item['key']
    if item['key_type'] == 'system':
        return '改行'
    design = key['design']['label']
    if design.get('system_image') == 'delete.left':
        return '⌫'
    return design.get('main', design.get('text', ''))


def render(name):
    tab = json.loads((ROOT / f'{name}.json').read_text())
    title = tab['metadata']['display_name']
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1110" height="460" viewBox="0 0 1110 460" role="img">',
        f'<title>{escape(title)}の配置図</title>',
        '<rect width="1110" height="460" rx="18" fill="#202124"/>',
        '<g font-family="Noto Sans CJK JP, Noto Sans JP, sans-serif" fill="#ffffff">',
        f'<text x="24" y="35" font-size="24">{escape(title)} — 配置図</text>',
    ]
    for item in tab['interface']['keys']:
        p = item['specifier']
        x, y, width, height = p['x'] * 10 + 3, p['y'] * 100 + 54, p['width'] * 10 - 6, 86
        text = label(item)
        system = item['key_type'] == 'system'
        special = system or item['key'].get('design', {}).get('color') == 'special'
        color = '#4169e1' if system else '#303134' if special else '#444548'
        font_size = 39 if text in ('空白', '改行', '#+=', '?123') else 49
        svg.append(f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height}" rx="14" fill="{color}"/>')
        if item['key'].get('design', {}).get('label', {}).get('system_image') == 'delete.left':
            cx, cy = x + width / 2, y + height / 2
            svg += [
                f'<path d="M {cx - 30:g} {cy:g} L {cx - 15:g} {cy - 20:g} H {cx + 26:g} V {cy + 20:g} H {cx - 15:g} Z" fill="none" stroke="white" stroke-width="4" stroke-linejoin="round"/>',
                f'<path d="M {cx - 4:g} {cy - 9:g} L {cx + 14:g} {cy + 9:g} M {cx + 14:g} {cy - 9:g} L {cx - 4:g} {cy + 9:g}" stroke="white" stroke-width="4"/>',
            ]
        else:
            svg.append(f'<text x="{x + width / 2:g}" y="{y + 44:g}" text-anchor="middle" dominant-baseline="central" font-size="{font_size}">{escape(text)}</text>')
    svg += ['</g>', '</svg>']
    PREVIEWS.mkdir(exist_ok=True)
    (PREVIEWS / f'{name}.svg').write_text('\n'.join(svg) + '\n')


if __name__ == '__main__':
    for name in ('numbers-gboard-like', 'symbols-gboard-like'):
        render(name)
    print('Rendered numeric and symbol layout diagrams from JSON')
