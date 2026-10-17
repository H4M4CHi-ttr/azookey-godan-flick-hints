"""Check real GODAN key sequences against the in-progress composition rules.

The reference interpreter applies input actions and longest-suffix replacements
in the order used by azooKey 3.1.1 InputManager.replaceLastCharacters:
https://github.com/azooKey/azooKey/blob/754a9ad17cf300596d761845466b9faa652835f5/Keyboard/Display/InputManager.swift#L786-L817
"""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODAN_FILES = (
    'godan-gboard-like.json', 'godan-flick-hints.json', 'godan-android-width.json',
)
WH = {'wha': 'うぁ', 'whi': 'うぃ', 'whu': 'う', 'whe': 'うぇ', 'who': 'うぉ'}


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
            candidate = variation['key']
            text = candidate['design']['label'].get('text', '')
            if len(text) == 1 and text.isascii() and text.isalpha():
                routes[text.lower()] = candidate
    return routes


def compose(routes, roman, final_direction=None, prefix=''):
    text = prefix
    for index, char in enumerate(roman):
        key = routes[char]
        if index == len(roman) - 1 and final_direction:
            key = next(v['key'] for v in key['variations'] if v['direction'] == final_direction)
        for action in key['press_actions']:
            kind = action['type']
            if kind == 'input':
                text += action['text']
            elif kind == 'replace_last_characters':
                table = action['table']
                for count in sorted({len(source) for source in table}, reverse=True):
                    if len(text) >= count and text[-count:] in table:
                        text = text[:-count] + table[text[-count:]]
                        break
            else:
                raise ValueError(f'Unexpected action in character input: {kind}')
    return text


class GodanCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routes = {
            name: letter_routes(json.loads((ROOT / name).read_text()))
            for name in GODAN_FILES
        }

    def test_wh_vowels(self):
        for name, routes in self.routes.items():
            for roman, expected in WH.items():
                with self.subTest(tab=name, roman=roman):
                    self.assertEqual(compose(routes, roman), expected)

    def test_wh_with_tsu_and_n_flicks(self):
        for name, routes in self.routes.items():
            for roman, expected in WH.items():
                for direction, suffix in [('left', 'っ'), ('top', 'ん')]:
                    with self.subTest(tab=name, roman=roman, direction=direction):
                        self.assertEqual(compose(routes, roman, direction), expected + suffix)

    def test_wh_small_i_and_e(self):
        for name, routes in self.routes.items():
            for roman in ['whi', 'whe']:
                with self.subTest(tab=name, roman=roman):
                    self.assertEqual(compose(routes, roman, 'right'), WH[roman])

    def test_preceding_text_is_retained(self):
        for name, routes in self.routes.items():
            with self.subTest(tab=name):
                self.assertEqual(compose(routes, 'who', prefix='あいう'), 'あいううぉ')
                self.assertEqual(compose(routes, 'nwho'), 'んうぉ')
                self.assertEqual(compose(routes, 'wwho'), 'っうぉ')
                self.assertEqual(compose(routes, 'who', 'top', prefix='前'), '前うぉん')

    def test_existing_w_and_h_inputs(self):
        expected = {
            'wa': 'わ', 'wi': 'うぃ', 'wu': 'う', 'we': 'うぇ', 'wo': 'を',
            'ha': 'は', 'hi': 'ひ', 'hu': 'ふ', 'he': 'へ', 'ho': 'ほ',
        }
        for name, routes in self.routes.items():
            for roman, kana in expected.items():
                with self.subTest(tab=name, roman=roman):
                    self.assertEqual(compose(routes, roman), kana)
            self.assertEqual(compose(routes, 'wo', 'left'), 'をっ')
            self.assertEqual(compose(routes, 'wo', 'top'), 'をん')

    def test_existing_glides_and_extended_sounds(self):
        expected = {
            'ka': 'か', 'ga': 'が', 'kya': 'きゃ', 'gya': 'ぎゃ',
            'sha': 'しゃ', 'shi': 'し', 'she': 'しぇ', 'cho': 'ちょ',
            'che': 'ちぇ', 'thi': 'てぃ', 'dhi': 'でぃ',
            'fa': 'ふぁ', 'fi': 'ふぃ', 'fe': 'ふぇ', 'fo': 'ふぉ',
            'tsa': 'つぁ', 'tsi': 'つぃ', 'tse': 'つぇ', 'tso': 'つぉ',
            'va': 'ゔぁ', 'vi': 'ゔぃ', 've': 'ゔぇ', 'vo': 'ゔぉ',
            'qa': 'くぁ', 'nkya': 'んきゃ', 'kka': 'っか',
            'xya': 'ゃ', 'lya': 'ゃ', 'xwa': 'ゎ',
        }
        for name, routes in self.routes.items():
            for roman, kana in expected.items():
                with self.subTest(tab=name, roman=roman):
                    self.assertEqual(compose(routes, roman), kana)
            for direction, suffix in [('left', 'っ'), ('top', 'ん')]:
                self.assertEqual(compose(routes, 'kya', direction), 'きゃ' + suffix)


if __name__ == '__main__':
    unittest.main()
