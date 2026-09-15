# 나만의 용돈 기입장 (budget_app)

Python 표준 라이브러리만으로 구현하는 콘솔 가계부 프로그램입니다.
수입/지출 기록, 검색, 월별 요약, 예산 관리, 카테고리 관리, CSV import/export까지 지원하는
파일 기반(JSONL/CSV) 영구 저장 CLI 애플리케이션을 목표로 합니다.

- 분야: AI/SW 기초 — Python과 Git 심화
- 학습 시간: 60시간

## 정책 고정 사항 (구현 시 확정)

미션 요구사항상 아래 항목은 여러 방식 중 1개를 선택해 고정해야 합니다. 현재 예정안입니다.

| 항목 | 예정안 | 비고 |
| --- | --- | --- |
| 저장 포맷 | JSONL | 구조화 데이터 + append 용이, update/delete는 원자적 재작성 |
| `update` 입력 방식 | 옵션 기반 (`--id --date --type ...`) | 스크립팅/자동화 가능, 문서화 용이 |
| 카테고리 빈 상태 정책 | (A) 기본 카테고리 자동 생성 (food/transport/rent/etc) | 초기 사용성 우선 |
| 카테고리 삭제 정책 | 사용 중이면 삭제 차단 (대체 카테고리 지정 시 삭제 허용) | |
| 기본 데이터 폴더 | `./data` (`--data-dir` 옵션으로 변경 가능) | |

> 구현을 시작하면 이 표를 실제 동작에 맞게 업데이트합니다.

## 실행 방법 (예정)

```bash
python -m budget_app <command> [options]
python -m budget_app --help
```

## 저장 파일 (예정)

`./data/` 아래 3개 파일로 분리 저장합니다.

- `transactions.jsonl` — 거래 내역
- `categories.jsonl` — 카테고리 목록
- `budgets.jsonl` — 월별 예산

## 주요 명령 예시 (미션 결과 예시 기준)

```bash
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000012

$ python -m budget_app list --limit 3
TX-000012 | 2024-01-15 | expense | food | 15000 | 점심

$ python -m budget_app search --category food --from 2024-01-01 --to 2024-01-31

$ python -m budget_app summary --month 2024-01 --top 3

$ python -m budget_app budget set --month 2024-01 --amount 500000

$ python -m budget_app category add
$ python -m budget_app category list
$ python -m budget_app category remove

$ python -m budget_app update --id TX-000012 --amount 16000
$ python -m budget_app delete --id TX-000012

$ python -m budget_app export --out export.csv --month 2024-01
$ python -m budget_app import --from import.csv
```

## import/export CSV 스키마

| column | required | 설명 |
| --- | --- | --- |
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(,) 구분 문자열 |

공통: UTF-8, 헤더 포함.

---

## 개발 체크리스트

### 0. 시작 전 정책 결정
- [x] 저장 포맷: JSONL (위 표 참고, 확정 시 체크)
- [x] `update` 방식: 옵션 기반
- [x] 카테고리 빈 상태 정책: (A) 기본 카테고리 자동 생성
- [x] 카테고리 삭제 정책: 사용 중이면 차단
- [x] 기본 데이터 폴더: `./data`

### 1. 프로젝트 구조 (최소 3개 모듈, 계층 분리)
- [x] `budget_app/__main__.py` — `python -m budget_app` 진입점
- [x] `budget_app/cli.py` — argparse 서브커맨드, `--help` 지원
- [x] `budget_app/models.py` — `Transaction` 등 dataclass (최소 2개 클래스)
- [x] `budget_app/repository.py` — 파일 I/O (스트리밍 read, 원자적 write)
- [x] `budget_app/service.py` — 검증/검색/요약/예산 로직
- [x] `budget_app/decorators.py` — 로그/예외처리/시간측정 데코레이터
- [x] `budget_app/exceptions.py` — 커스텀 예외 + 원인/힌트 메시지
- [x] 전 함수/메서드 타입 힌트 적용

### 2. 데이터 모델
- [x] `Transaction`: id, type, date, amount, category, memo, tags
- [x] id 채번 규칙 결정 (`TX-000012` 순번 방식)
- [x] 필드 검증은 서비스 계층에서 처리

### 3. 저장 정책
- [x] transactions/categories/budgets 3개 파일 분리
- [x] 파일 없으면 자동 생성 또는 초기화 안내
- [x] update/delete는 임시 파일 + rename 원자적 교체

### 4. 기능 (10개)
- [x] add — 대화형 입력, 카테고리 검증, id 출력
- [x] list — `--limit`, 최신순, 제너레이터 스트리밍
- [x] search — `--from --to --category --type --q --tag`, 최신순, 스트리밍
- [x] summary — `--month --top`, 총수입/총지출/잔액, 카테고리 TOP N, 데이터 없음 처리
- [x] budget — `budget set --month --amount`, summary 연동(사용률/초과 경고)
- [x] category — `add/list/remove`, 사용 중 카테고리 삭제 처리
- [x] update — `--id` + 옵션 필드, 없는 id 처리
- [x] delete — `--id`, 없는 id 처리
- [x] import — `--from <csv>`, 스키마 검증, 처리 건수 출력
- [x] export — `--out` + (`--month` or `--from/--to`) 필수, UTF-8/헤더, 처리 건수 출력

### 5. 공통 요구사항
- [x] 모든 서브커맨드 `--help` 동작
- [x] 옵션 표기 `--` 통일
- [x] 데코레이터(로그/예외/시간측정) 1개 이상 실제 적용
- [x] 예외 시 스택트레이스 대신 원인 + 해결 힌트 출력
- [x] 정상 종료 0 / 오류 종료 0 아님

### 6. 테스트/검증
- [x] 각 명령어 정상 케이스 수동 실행
- [x] 오류 케이스 (잘못된 날짜, 음수 금액, 없는 카테고리/id)
- [x] 재실행 후 데이터 유지 확인 (영구 저장 검증)
- [ ] list/search가 전체 로드 없이 스트리밍되는지 확인 (주의: 최신순 정렬 때문에 정렬 시점엔 메모리에 모음 — 아래 설명 참고)

### 7. 보너스 (선택)
- [ ] backup — 타임스탬프 백업 파일 생성
- [ ] 반복 내역 자동 생성
- [ ] 콘솔 테이블 정렬 포맷터
- [ ] 저장 원자성 강화 (3번과 중복 시 이미 충족)
