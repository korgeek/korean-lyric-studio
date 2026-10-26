"""Run: python -m unittest discover -s tests -v (from skill root).

Fixtures are synthetic character sequences, not lyric examples.
"""

import argparse
import json
import subprocess
import sys
import unittest
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lyric_meter import analyze_lyrics, count_hangul_syllables, get_manual_review_reasons, parse_pattern  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "lyric_meter.py"


class CountTests(unittest.TestCase):
    def test_long_line_count(self):
        self.assertEqual(count_hangul_syllables("가나다라마바사아자차카타파하 가나다라마바 사아자"), 23)

    def test_inversion_preserves_total(self):
        self.assertEqual(count_hangul_syllables("가나다라 마바사아"), 8)
        self.assertEqual(count_hangul_syllables("마바사아, 가나다라"), 8)

    def test_decomposed_nfd_normalizes(self):
        sample = unicodedata.normalize("NFD", "마바사아")
        self.assertEqual(count_hangul_syllables(sample), 4)
        self.assertEqual(get_manual_review_reasons(sample), [])

    def test_latin_and_numbers_flagged(self):
        result = analyze_lyrics("AB가나 24다라 마바")
        self.assertEqual(result["lines"][0]["hangul_syllables"], 6)
        self.assertTrue(result["lines"][0]["manual_review"])

    def test_other_writing_and_readable_symbols_flagged(self):
        for extra in ("ก", "あ", "é", "\u0301", "😊", "&", "%", "#", "@"):
            with self.subTest(extra=extra):
                result = analyze_lyrics("마바사아 " + extra, target=4)
                self.assertTrue(result["all_constraints_met"])
                self.assertTrue(result["lines"][0]["manual_review"])
                self.assertTrue(result["lines"][0]["manual_review_reasons"])

    def test_existing_review_categories_preserved(self):
        for extra, reason in (
            ("AI", "로마자/영어"), ("24", "숫자"), ("字", "한자"),
            ("ㄱ", "단독 자모"), ("～", "늘임·음악 기호"),
        ):
            with self.subTest(extra=extra):
                self.assertTrue(any(reason in item for item in get_manual_review_reasons(extra)))

    def test_phrase_split(self):
        result = analyze_lyrics("가나다라 / 마바사아", target=8)
        self.assertEqual([p["hangul_syllables"] for p in result["lines"][0]["phrases"]], [4, 4])
        self.assertTrue(result["all_constraints_met"])

    def test_delimiters_and_punctuation_do_not_need_review(self):
        result = analyze_lyrics("가나다라 / 마 | 바사아, 자차카타!", target=12)
        self.assertEqual([p["hangul_syllables"] for p in result["lines"][0]["phrases"]], [4, 1, 7])
        self.assertTrue(result["all_constraints_met"])
        self.assertFalse(result["lines"][0]["manual_review"])

    def test_section_labels_and_stanzas(self):
        result = analyze_lyrics("[Verse 1]\n가나다라 마바사아\n\n[Chorus]\n마바사아, 가나다라")
        self.assertEqual(result["total_lyric_lines"], 2)
        self.assertEqual(result["stanza_count"], 2)
        self.assertEqual(result["lines"][1]["section"], "Chorus")

    def test_pattern_matching(self):
        result = analyze_lyrics("가나다라 마바사아\n자차카타 파하가나", pattern=[8, 8])
        self.assertTrue(result["all_constraints_met"])

    def test_pattern_line_count_mismatch(self):
        result = analyze_lyrics("가나다라 마바사아", pattern=[8, 8])
        self.assertFalse(result["all_constraints_met"])
        self.assertEqual(len(result["structure_warnings"]), 1)

    def test_pattern_does_not_cycle_on_extra_lines(self):
        result = analyze_lyrics("가\n나다라\n가\n나다라", pattern=[1, 3])
        self.assertFalse(result["all_constraints_met"])
        self.assertEqual([line["target"] for line in result["lines"]], [1, 3, None, None])
        self.assertIsNone(result["lines"][2]["target_met"])
        self.assertTrue(result["structure_warnings"])

    def test_constraint_mismatch(self):
        result = analyze_lyrics("마바사아", target=8)
        self.assertFalse(result["all_constraints_met"])
        self.assertEqual(result["lines"][0]["difference"], -4)

    def test_parse_pattern(self):
        self.assertEqual(parse_pattern("8, 8,7,8"), [8, 8, 7, 8])

    def test_invalid_patterns_and_constraints(self):
        for pattern in ("", "8,", "0,8", "-1,8", "8,x", "1.5"):
            with self.subTest(pattern=pattern), self.assertRaises(argparse.ArgumentTypeError):
                parse_pattern(pattern)
        for options in ({"target": 0}, {"target": 1, "pattern": [1]}, {"pattern": []}, {"pattern": [0]}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                analyze_lyrics("가", **options)

    def test_empty_lyrics_do_not_satisfy_constraints(self):
        for text in ("", " \n", "[Chorus]"):
            for options in ({"target": 4}, {"pattern": [4]}):
                with self.subTest(text=text, options=options):
                    self.assertFalse(analyze_lyrics(text, **options)["all_constraints_met"])


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def test_strict_json_separates_counts_from_manual_review(self):
        for text, target, expected_exit, expected_match, expected_review in (
            ("마바사아", "4", 0, True, False),
            ("마바사아", "8", 1, False, False),
            ("마바사아 ก &", "4", 0, True, True),
            ("마바사아 ก &", "8", 1, False, True),
        ):
            with self.subTest(text=text, target=target):
                result = self.run_cli("--text", text, "--target", target, "--strict", "--json")
                self.assertEqual(result.returncode, expected_exit, result.stderr)
                data = json.loads(result.stdout)
                self.assertEqual(data["all_constraints_met"], expected_match)
                self.assertEqual(data["lines"][0]["manual_review"], expected_review)

    def test_cli_rejects_invalid_or_empty_input(self):
        for args in (
            ("--text", ""), ("--text", "가", "--target", "0"),
            ("--text", "가", "--pattern", ""), ("--text", "가", "--pattern", "1,"),
        ):
            with self.subTest(args=args):
                self.assertEqual(self.run_cli(*args).returncode, 2)


if __name__ == "__main__":
    unittest.main()
