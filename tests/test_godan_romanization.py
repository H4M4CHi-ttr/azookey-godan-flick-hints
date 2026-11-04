"""Exhaustively execute the distributed GODAN key actions against pinned kana data.

This is a direct-composition model of azooKey 3.1/3.1.1, not an iOS UI test.
Expectations come from data/romaji-kana.json, independently of the layout tables
and the updater. The earlier focused tests also remain in the suite.
"""

import json
import unittest
from itertools import product
from pathlib import Path

from test_godan_composition import GODAN_FILES, letter_routes

ROOT = Path(__file__).resolve().parents[1]
SYLLABLES = json.loads((ROOT / 'data/romaji-kana.json').read_text())['syllables']


class Keyboard:
    """Apply actual input/replace actions to the composing text before a cursor."""

    def __init__(self, tab):
        self.routes = letter_routes(tab)
        self.actions = {}
        for key in self.routes.values():
            for node in [key, *(v['key'] for v in key['variations'])]:
                compiled = []
                for action in node['press_actions']:
                    if action['type'] == 'input':
                        compiled.append(('input', action['text']))
                    elif action['type'] == 'replace_last_characters':
                        table = action['table']
                        lengths = sorted({len(source) for source in table}, reverse=True)
                        compiled.append(('replace', (lengths, table)))
                    else:
                        raise ValueError(f'Unexpected character action: {action["type"]}')
                self.actions[id(node)] = compiled

    def type(self, roman, direction=None, before='', after=''):
        text = before
        for index, letter in enumerate(roman):
            node = self.routes[letter]
            if direction and index == len(roman) - 1:
                node = next(v['key'] for v in node['variations'] if v['direction'] == direction)
            for kind, payload in self.actions[id(node)]:
                if kind == 'input':
                    text += payload
                else:
                    lengths, table = payload
                    for length in lengths:
                        if length <= len(text) and text[-length:] in table:
                            text = text[:-length] + table[text[-length:]]
                            break
        return text + after


class GodanRomanizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tabs = {name: json.loads((ROOT / name).read_text()) for name in GODAN_FILES}
        tabs['gboard-like-pair.json[0]'] = json.loads(
            (ROOT / 'gboard-like-pair.json').read_text()
        )[0]
        cls.keyboards = {name: Keyboard(tab) for name, tab in tabs.items()}

    def check_cases(self, cases):
        # Bound failure output without skipping any of the input cases.
        for name, keyboard in self.keyboards.items():
            failures = []
            for roman, expected, direction, before, after in cases:
                actual = keyboard.type(roman, direction, before, after)
                if actual != expected and len(failures) < 12:
                    failures.append((roman, direction, expected, actual))
            with self.subTest(tab=name):
                self.assertEqual(failures, [], f'{name}: {failures}')

    def test_every_reference_syllable(self):
        """A missing long match must not leave its consonants in the output."""
        self.check_cases([
            (roman, kana, None, '', '') for roman, kana in SYLLABLES.items()
        ])

    def test_tsu_and_n_flicks_for_every_syllable(self):
        """Left/top tables must receive the same fixes as the normal vowel."""
        self.check_cases([
            (roman, kana + suffix, direction, '', '')
            for roman, kana in SYLLABLES.items()
            for direction, suffix in [('left', 'っ'), ('top', 'ん')]
        ])

    def test_multi_consonant_right_flicks(self):
        """Explicit prefixes such as tw/kw/ch work with the right vowel too."""
        self.check_cases([
            (roman, kana, 'right', '', '')
            for roman, kana in SYLLABLES.items() if len(roman) >= 3
        ])

    def test_surrounding_kana_is_not_replaced(self):
        self.check_cases([
            (roman, '前あいう' + kana + '後えお', None, '前あいう', '後えお')
            for roman, kana in SYLLABLES.items()
        ])

    def test_leading_n_and_doubled_consonants(self):
        cases = []
        for roman, kana in SYLLABLES.items():
            if roman[0] not in 'aeioun':
                cases.append((roman[0] + roman, 'っ' + kana, None, '', ''))
                # ny is a syllable onset, rather than a standalone ん + y.
                if roman[0] != 'y':
                    cases.append(('n' + roman, 'ん' + kana, None, '', ''))
        self.check_cases(cases)

    def test_all_syllable_pairs(self):
        """No leftover consonant may combine with the next completed syllable."""
        pairs = [
            (left + right, left_kana + right_kana, None, '', '')
            for (left, left_kana), (right, right_kana)
            in product(SYLLABLES.items(), repeat=2)
        ]
        self.check_cases(pairs)

    def test_tch_and_explicit_n(self):
        expected = {
            'xn': 'ん', 'tcha': 'っちゃ', 'tchi': 'っち', 'tchu': 'っちゅ',
            'tche': 'っちぇ', 'tcho': 'っちょ', 'matcha': 'まっちゃ',
            'ttwu': 'っとぅ', 'ndwu': 'んどぅ', 'nnkwa': 'んくぁ',
            'konnnichiwa': 'こんにちは',
        }
        self.check_cases([
            (roman, kana, None, '', '') for roman, kana in expected.items()
        ])

    def test_godan_shortcuts_and_inherited_typos(self):
        expected_right = {
            'ka': 'きゃ', 'ki': 'きぃ', 'ku': 'きゅ', 'ke': 'きぇ', 'ko': 'きょ',
            'wa': 'うゎ', 'wi': 'うぃ', 'wu': 'うぅ', 'we': 'うぇ', 'wo': 'うぉ',
            'ca': 'ちゃ', 'ci': 'ちぃ', 'cu': 'ちゅ', 'ce': 'ちぇ', 'co': 'ちょ',
        }
        cases = [
            (roman, kana, 'right', '', '') for roman, kana in expected_right.items()
        ]
        # wya has no canonical syllable; it must not turn into unrelated りゃ.
        cases += [
            ('wya', 'wや', None, '', ''), ('wya', 'wやっ', 'left', '', ''),
            ('wya', 'wやん', 'top', '', ''),
            ('nn', 'ん', None, '', ''), ('nna', 'んあ', None, '', ''),
            ('nnna', 'んな', None, '', ''), ('nya', 'にゃ', None, '', ''),
        ]
        self.check_cases(cases)


if __name__ == '__main__':
    unittest.main()
