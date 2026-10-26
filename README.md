# Korean Lyric Studio

한국어 가사를 창작하고 다듬는 에이전트 스킬입니다. 주제·초안·멜로디에서 출발해 화자의 말, 표현, 곡 구조, 라임과 프레이징을 설계하고 점검합니다.

현재 **개발 중인 pre 버전(`0.1.0-pre`)**입니다. 스킬 이름은 `korean-lyric-studio`입니다.

## 할 수 있는 일

| 작업 | 제공하는 도움 |
|---|---|
| 소재·가사 창작 | 화자·관계·행동에서 소재를 찾고 요청한 장르와 분량의 초안 작성 |
| 제목·훅·구조 설계 | 핵심 발화, 반복의 역할, 구간별 정보와 정서 배치 |
| 표현·작사법 학습 | 기법의 선택·적용·효과 비교, 짧은 연습과 피드백 |
| 라임·펀치라인 | 다음절·내부운·각운, 발음에 따른 라임 지도, 의미 전환 설계 |
| 멜로디·음절 맞춤 | 제공된 슬롯·쉼에 가사를 대응하고 도치·축약·치환 등의 손익 비교 |
| 퇴고·비평 | 고정 문구와 의도를 보존하며 중요한 문제부터 수정, 요청 시 근거 있는 평가 |
| 혼합 언어·음악 도구용 출력 | 의도한 발음 검토, 가사·번역·스타일 지시의 분리 |

발라드·인디·힙합 등 장르와 원하는 말투에 맞춰 작업합니다. 기본 응답은 **초안 → 짧은 비평 1~3개 → 핵심 부분의 수정 대안**입니다. 가사만, 구조만, 분석만 요청하면 그 범위를 따릅니다.

## 설치

### Codex

사용할 범위에 따라 설치 위치를 선택하세요.

| 범위 | 설치 폴더 |
|---|---|
| 개인 — 모든 프로젝트 | `~/.agents/skills/korean-lyric-studio/` |
| 프로젝트 — 해당 저장소 | `<프로젝트 루트>/.agents/skills/korean-lyric-studio/` |

설치 폴더를 만들고 다음 파일과 폴더를 복사합니다.

```text
korean-lyric-studio/
├── SKILL.md
├── references/
├── scripts/
└── tests/
```

`SKILL.md`가 설치 폴더 바로 아래에 있어야 하며, 연결된 가이드와 검사기를 함께 복사해야 합니다. 기존 설치를 교체할 때는 사용자 수정 사항을 먼저 보관하세요. 같은 이름의 스킬을 개인과 프로젝트 양쪽에 설치하면 선택기에 중복으로 나타날 수 있습니다.

Git으로 개인용 설치를 하려면 아래 명령을 실행하세요. 대상 폴더는 비어 있어야 합니다.

```bash
mkdir -p "$HOME/.agents/skills"
git clone 'https://github.com/korgeek/korean-lyric-studio.git' "$HOME/.agents/skills/korean-lyric-studio"
```

Codex는 스킬을 자동으로 감지합니다. 목록에 나타나지 않으면 재시작하세요. 설치 위치와 선택 방식은 [공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills#where-to-save-skills)에서 확인할 수 있습니다.

## 사용

Codex CLI·IDE에서는 `$korean-lyric-studio`를 입력하거나 `/skills`에서 선택합니다. 데스크톱에서는 스킬 선택기에서 `korean-lyric-studio`를 요청에 첨부하세요.

```text
$korean-lyric-studio
새로운 동네에 적응하는 이야기를 인디 가사로 써줘.
1절 8행과 후렴 4행, 담담한 생활어로 쓰고 짧은 비평과 수정 대안도 줘.
```

```text
$korean-lyric-studio
아래 초안의 다음절 라임과 내부운을 분석해줘.
예상 발음과 대응 범위를 기준으로 A/B 그룹을 표시하고 근사운의 차이도 설명해줘.
```

주제, 장르, 화자와 대상, 분량, 보존할 문구, 음악 자료를 알고 있는 만큼 알려주세요. 이미 주어진 조건을 사용하고, 빠진 창작 조건은 짧게 가정해 진행합니다. 작업에 꼭 필요한 자료가 없거나 조건이 충돌할 때 확인합니다.

가사·제목·분석·대안에는 비속어, 인신공격, 실명, 연예인 언급, 비하를 넣지 않습니다. 입력의 해당 표현도 재인용하거나 별칭·초성으로 우회하지 않습니다. 힘 있는 표현은 화자의 행동·선택·변화와 소리의 대비로 만듭니다.

## 스킬 구성

| 파일 | 용도 |
|---|---|
| [SKILL.md](SKILL.md) | 작업 선택, 작사 절차, 라임·펀치라인, 공통 점검 기준 |
| [references/use-cases.md](references/use-cases.md) | 소재·훅·구조·학습·비평·출력의 작업별 절차 |
| [references/expression-toolkit.md](references/expression-toolkit.md) | 표현 기법의 적용, 실패 신호, 수정 방법 |
| [references/melody-and-editing.md](references/melody-and-editing.md) | 멜로디 슬롯 대응, 편집 수단, 교정 사례 |
| [scripts/lyric_meter.py](scripts/lyric_meter.py) | 한글 표기 음절 수 검사기 |
| [tests/test_lyric_meter.py](tests/test_lyric_meter.py) | 검사기 자동 테스트 |
| [tests/acceptance-cases.md](tests/acceptance-cases.md) | 창작·분석·퇴고의 행동 검증 기준과 실행 요청 |

에이전트는 핵심 지침에서 시작해 현재 작업에 필요한 가이드만 읽습니다. 가이드의 짧은 교육용 사례는 기법의 효과와 수정 판단을 설명합니다.

## 표기 음절 검사기

**Python 3.9 이상**에서 외부 패키지 없이 실행합니다. 텍스트 지침만 사용할 때는 Python이 필요하지 않습니다.

저장소 또는 설치 폴더에서 아래 명령을 실행하세요. `lyrics.txt`는 검사할 UTF-8 텍스트 파일 경로로 바꿉니다.

```bash
python3 scripts/lyric_meter.py --file lyrics.txt --target 8 --strict
python3 scripts/lyric_meter.py --file lyrics.txt --pattern 8,8,7,8 --json --strict
```

- `--target`: 모든 검사 행에 같은 목표 한글 블록 수를 적용합니다.
- `--pattern`: 빈 줄 또는 독립된 `[섹션]` 태그로 나뉜 각 연에 정확한 행 패턴을 적용합니다. 패턴은 순환하지 않습니다.
- `--json`: 구조화된 결과를 출력합니다. `all_constraints_met`와 `manual_review`는 별도로 확인합니다.
- `--strict`: 표기 제약 불일치는 종료 코드 `1`, 입력 오류는 `2`입니다. 수동 검토 경고만으로 실패하지 않습니다.

측정 대상은 **NFC로 정규화한 한글 완성형 블록 수**입니다. 영어·숫자의 발음, 실제 가창 음절·박자·호흡은 별도 확인이 필요합니다. 라임·의미·펀치라인·금지 표현도 이 검사기로 자동 판정하지 않습니다.

## 검증

```bash
python3 -m unittest discover -s tests -v
```

자동 테스트는 검사기의 계산·입력 처리·종료 코드를 확인합니다. 창작 결과는 [행동 검증 기준](tests/acceptance-cases.md)에 따라 화자의 일관성, 표현의 효과, 발음 대응, 수정의 이득과 손실을 별도로 검토합니다. 실제 가창 적합성은 음악 자료와 수행한 검증 범위에 따라 판단합니다.
