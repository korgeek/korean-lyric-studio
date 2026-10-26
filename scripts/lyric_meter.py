#!/usr/bin/env python3
"""Count orthographic Korean Hangul syllables in lyric lines.

This does NOT measure musical beats, durations, Korean speech rhythm, or
actual sung syllables. It is a deterministic assistant for manual lyric editing.
Uses only Python's standard library (Python 3.9+).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

SECTION_LINE = re.compile(r"^\s*\[([^\]\n]+)\]\s*$")
SPLIT_PHRASES = re.compile(r"\s*[|/]\s*")


def count_hangul_syllables(text: str) -> int:
    """Count NFC precomposed Hangul blocks (U+AC00..U+D7A3)."""
    return sum(0xAC00 <= ord(char) <= 0xD7A3 for char in unicodedata.normalize("NFC", text))


def get_manual_review_reasons(text: str) -> list[str]:
    """Conservatively flag scripts whose sung syllables need checking."""
    reasons = []
    if re.search(r"[A-Za-z]", text):
        reasons.append("로마자/영어 발음은 별도 확인")
    if any(char.isdigit() for char in text):
        reasons.append("숫자의 실제 발음은 별도 확인")
    if any((0x3400 <= ord(char) <= 0x9FFF) or (0x20000 <= ord(char) <= 0x2FA1F) for char in text):
        reasons.append("한자의 실제 발음은 별도 확인")
    # Uncomposed/compatibility Jamo cannot be assigned a single sung syllable automatically.
    if any(
        (0x1100 <= ord(char) <= 0x11FF)
        or (0x3130 <= ord(char) <= 0x318F)
        or (0xA960 <= ord(char) <= 0xA97F)
        or (0xD7B0 <= ord(char) <= 0xD7FF)
        for char in unicodedata.normalize("NFC", text)
    ):
        reasons.append("단독 자모는 가창 음절을 수동 확인")
    if any(char in "—~～♪♬" for char in text):
        reasons.append("늘임·음악 기호는 음표 길이로 별도 확인")
    if not reasons and any(
        not (
            0xAC00 <= ord(char) <= 0xD7A3
            or char.isspace()
            or char in "/|"
            or (unicodedata.category(char).startswith("P") and char not in "&%#@")
        )
        for char in unicodedata.normalize("NFC", text)
    ):
        reasons.append("비한글 문자·결합 기호·기타 기호의 발음은 별도 확인")
    return reasons


def analyze_lyrics(text: str, target: int | None = None, pattern: list[int] | None = None) -> dict[str, Any]:
    """Analyze each nonempty lyric line; stanza resets at blank lines and [section] headings."""
    if target is not None and (target <= 0 or pattern is not None):
        raise ValueError("--target must be positive and cannot be combined with --pattern")
    if pattern is not None and (not pattern or any(p <= 0 for p in pattern)):
        raise ValueError("--pattern needs one or more positive integer values")

    normalized = unicodedata.normalize("NFC", text)
    entries: list[dict[str, Any]] = []
    stanza_sizes: dict[int, int] = {}
    current_section = ""
    stanza_num = 0
    in_stanza = False

    for physical_line, raw_line in enumerate(normalized.splitlines(), start=1):
        lyric = raw_line.strip()
        if not lyric:
            in_stanza = False
            continue
        section_match = SECTION_LINE.fullmatch(lyric)
        if section_match:
            current_section = section_match.group(1).strip()
            in_stanza = False
            continue
        if not in_stanza:
            stanza_num += 1
            stanza_sizes[stanza_num] = 0
            in_stanza = True
        stanza_sizes[stanza_num] += 1
        stanza_position = stanza_sizes[stanza_num]

        phrase_strings = [p.strip() for p in SPLIT_PHRASES.split(lyric)]
        phrases = [
            {"text": p, "hangul_syllables": count_hangul_syllables(p)}
            for p in phrase_strings if p
        ]
        actual = count_hangul_syllables(lyric)
        expected = target if target is not None else (
            pattern[stanza_position - 1]
            if pattern is not None and stanza_position <= len(pattern)
            else None
        )
        reasons = get_manual_review_reasons(lyric)
        if pattern is not None and stanza_position > len(pattern):
            reasons.append("패턴보다 줄 수가 많음")

        entries.append({
            "source_line": physical_line,
            "section": current_section,
            "stanza": stanza_num,
            "stanza_line": stanza_position,
            "text": lyric,
            "hangul_syllables": actual,
            "phrases": phrases,
            "target": expected,
            "difference": actual - expected if expected is not None else None,
            "target_met": actual == expected if expected is not None else None,
            "manual_review": bool(reasons),
            "manual_review_reasons": reasons,
        })

    mismatch_notes: list[str] = []
    if pattern is not None:
        for stanza, nlines in stanza_sizes.items():
            if nlines != len(pattern):
                mismatch_notes.append(
                    f"{stanza}번째 연: {nlines}줄이지만 지정 패턴은 {len(pattern)}줄입니다."
                )

    has_constraint = target is not None or pattern is not None
    passes = None if not has_constraint else (
        not mismatch_notes and bool(entries) and all(e["target_met"] for e in entries)
    )
    return {
        "measurement": "NFC 한글 완성형 음절 블록 수 (실제 가창 검증 아님)",
        "total_lyric_lines": len(entries),
        "stanza_count": len(stanza_sizes),
        "all_constraints_met": passes,
        "manual_review_line_count": sum(e["manual_review"] for e in entries),
        "structure_warnings": mismatch_notes,
        "lines": entries,
    }


def format_report(data: dict[str, Any]) -> str:
    lines = ["[한글 표기 음절 검수 — 음악 박자/실가창 검증이 아님]"]
    previous_stanza = None
    for entry in data["lines"]:
        if entry["stanza"] != previous_stanza:
            previous_stanza = entry["stanza"]
            label = f" / [{entry['section']}]" if entry["section"] else ""
            lines.append(f"\n연 {previous_stanza}{label}")
        phrase_note = "" if len(entry["phrases"]) <= 1 else " · 분절 " + "+".join(
            str(item["hangul_syllables"]) for item in entry["phrases"]
        )
        goal_note = "" if entry["target"] is None else (
            f" · 목표 {entry['target']} {'✓' if entry['target_met'] else '✗'}"
        )
        review_note = "" if not entry["manual_review"] else " · 수동 확인 필요"
        lines.append(f"  {entry['stanza_line']}. [{entry['hangul_syllables']}] {entry['text']}{phrase_note}{goal_note}{review_note}")
        if review_note:
            lines.append("     ↳ " + "; ".join(entry["manual_review_reasons"]))

    for warning in data["structure_warnings"]:
        lines.append(f"주의: {warning}")
    if data["all_constraints_met"] is not None:
        lines.append("\n표기 음절 제약: " + ("일치" if data["all_constraints_met"] else "불일치"))
    lines.append("주의: 영어·숫자·연음·멜리스마·쉼과 실제 가창 음절/타이밍은 별도 확인하세요.")
    return "\n".join(lines)


def parse_pattern(value: str) -> list[int]:
    try:
        values = [int(x.strip()) for x in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("쉼표로 구분한 양의 정수여야 합니다. 예: 8,8,7,8") from exc
    if not values or any(x <= 0 for x in values):
        raise argparse.ArgumentTypeError("패턴 값은 모두 양의 정수여야 합니다.")
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="검사할 가사 문자열 (개행 가능)")
    source.add_argument("--file", type=Path, help="UTF-8 텍스트 파일 (미지정 시 표준입력)")
    goal = parser.add_mutually_exclusive_group()
    goal.add_argument("--target", type=int, help="모든 줄에 적용할 목표 한글 음절 수")
    goal.add_argument("--pattern", type=parse_pattern, help="연별 줄 패턴. 예: 8,8,7,8")
    parser.add_argument("--json", action="store_true", help="기계 판독용 JSON 출력")
    parser.add_argument("--strict", action="store_true", help="목표/패턴 불일치 시 종료 코드 1")
    args = parser.parse_args(argv)

    if args.target is not None and args.target <= 0:
        parser.error("--target은 양의 정수여야 합니다.")
    try:
        raw = args.text if args.text is not None else (
            args.file.read_text(encoding="utf-8") if args.file else sys.stdin.read()
        )
    except (OSError, UnicodeError) as exc:
        parser.error(f"입력 파일을 읽을 수 없습니다: {exc}")

    if not raw or not raw.strip():
        parser.error("검사할 가사 텍스트가 없습니다.")
    result = analyze_lyrics(raw, target=args.target, pattern=args.pattern)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_report(result))
    return 1 if args.strict and result["all_constraints_met"] is False else 0


if __name__ == "__main__":
    sys.exit(main())
